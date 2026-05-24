import asyncio
import threading

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

with open("/uart_bootlog.txt", "rb") as f:
    BOOTLOG_LINES = f.readlines()

with open("/firmware.bin", "rb") as f:
    FIRMWARE = f.read()

SF_SIZE = len(FIRMWARE)


state = {
    "power_on": False,
    "booting": False,
    "uart_tx_ok": False,
    "uart_rx_ok": False,
    "uart_gnd_ok": False,
    "spi_connections": set(),
    "glitched": False,
}

SPI_PIN_MAP = {
    "spi_1": "CS",
    "spi_2": "MISO",
    "spi_3": "WP",
    "spi_4": "GND",
    "spi_5": "MOSI",
    "spi_6": "CLK",
    "spi_7": "HOLD",
    "spi_8": "VCC",
}

GLITCHABLE = {"MISO", "CLK"}
PICOCOM_BANNER = """picocom v2024-07
port is        : /dev/ttyACM0
baudrate is    : 115200
"""


sessions = {}

started = False


def start_background_thread():
    threading.Thread(target=start_nc_server, daemon=True).start()
    

class Session:
    def __init__(self):
        self.alive = True
        self.mode = "menu"
        self.booting = False


RAM_BASE = 0x80000000
RAM_SIZE = 64 * 1024 * 1024

ram = bytearray(RAM_SIZE)


def uart_can_output():
    return state["uart_tx_ok"] and state["uart_gnd_ok"]


def uart_can_input():
    return state["uart_rx_ok"] and state["uart_gnd_ok"]


def spi_roles_connected_to_gnd():
    roles = set()
    for spi_pin in state["spi_connections"]:
        roles.add(SPI_PIN_MAP.get(spi_pin))
    return roles


def spi_is_broken_at_boot():
    roles = spi_roles_connected_to_gnd()

    if any(r in roles for r in ["CLK", "CS", "MOSI", "MISO"]):
        return True

    return False


def spi_vcc_fault():
    roles = spi_roles_connected_to_gnd()
    return "VCC" in roles


def spi_glitch_condition():
    roles = spi_roles_connected_to_gnd()
    return any(r in GLITCHABLE for r in roles)


def md_dump(addr, length):
    addr = int(addr, 16)
    length = int(length, 16)

    offset = addr - RAM_BASE

    if offset < 0 or offset >= len(ram):
        return ["Bad address"]

    out = []

    for i in range(0, length, 16):
        chunk = ram[offset + i : offset + i + 16]

        words = [chunk[j : j + 4].hex().ljust(8, "0") for j in range(0, len(chunk), 4)]

        out.append(f"{addr + i:08x}: " + " ".join(words))

    return out


async def safe_write(writer, data):
    try:
        if uart_can_output():
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        return False
    return True


async def safe_readline(reader, writer):
    while True:
        if await check_power(writer):
            return None

        try:
            line = await asyncio.wait_for(reader.readline(), timeout=0.1)
            return line
        except asyncio.TimeoutError:
            continue


async def check_power(writer):
    if not state["power_on"]:
        await safe_write(writer, b"\n[POWER LOST]\n")
        state["booting"] = False
        return True
    return False


def spi_is_usable():
    roles = spi_roles_connected_to_gnd()

    if any(r in roles for r in ["CLK", "CS", "MOSI", "MISO", "VCC"]):
        return False

    return True


@app.route("/")
def index():
    return render_template("index.html")


async def prompt(writer):
    await safe_write(writer, b"> ")


@app.route("/wiring", methods=["POST"])
def wiring():
    conns = request.json.get("connections", [])

    links = set()
    for c in conns:
        a, b = c["from"], c["to"]
        links.add((a, b))
        links.add((b, a))

    def connected(a, b):
        return (a, b) in links

    state["uart_tx_ok"] = connected("device_tx", "adapter_rx")
    state["uart_rx_ok"] = connected("adapter_tx", "device_rx")
    state["uart_gnd_ok"] = connected("device_gnd", "adapter_gnd")

    state["spi_connections"].clear()
    for i in range(1, 9):
        pin = f"spi_{i}"
        if (
            pin == "spi_4"
            or connected(pin, "device_gnd")
            or connected(pin, "adapter_gnd")
            or connected(pin, "spi_4")
        ):
            state["spi_connections"].add(pin)

    return jsonify(
        {
            "uart_tx": state["uart_tx_ok"],
            "uart_rx": state["uart_rx_ok"],
            "gnd": state["uart_gnd_ok"],
            "spi": list(state["spi_connections"]),
        }
    )


async def handle_nc(reader, writer):
    session = Session()
    sessions[writer] = session

    await safe_write(writer, PICOCOM_BANNER.encode())

    await safe_write(writer, b"\nCommands:\n")
    await safe_write(writer, b"  on  = power on\n")
    await safe_write(writer, b"  off = power off\n")
    await safe_write(writer, b"  b   = boot device\n")
    await safe_write(writer, b"  p   = power status\n")
    await safe_write(writer, b"> ")

    try:
        while session.alive:
            line = await reader.readline()
            if not line:
                break

            cmd = line.decode().strip()

            if cmd == "on":
                state["power_on"] = True
                await safe_write(writer, b"\n[POWER ON]\n> ")

            elif cmd == "off":
                state["power_on"] = False
                session.booting = False
                await safe_write(writer, b"\n[POWER OFF]\n> ")

            elif cmd == "p":
                status = b"ON" if state["power_on"] else b"OFF"
                await safe_write(writer, b"\nPower: " + status + b"\n> ")

            elif cmd == "b":
                if not state["power_on"]:
                    await safe_write(writer, b"\n[ERROR] POWER OFF\n> ")
                    continue

                if session.mode != "menu":
                    await safe_write(writer, b"\n[INFO] Busy\n> ")
                    continue

                session.mode = "boot"
                session.booting = True

                await safe_write(writer, b"\n[OK] Boot started\n")

                await run_boot_sequence(reader, writer, session)

                if session.mode != "uboot":
                    session.mode = "menu"

                await safe_write(writer, b"> ")

    finally:
        session.alive = False
        sessions.pop(writer, None)


async def run_boot_sequence(reader, writer, session=None):
    try:
        await safe_write(writer, b"INGENIC T23 SOC\n")
        await safe_write(writer, b"UART Initialised\n")
        await safe_write(writer, b"SPI Initialisation...\n")

        if spi_is_broken_at_boot():
            await safe_write(writer, b"\n*** SPI INIT FAILED ***\n")
            await safe_write(writer, b"Cannot communicate with SPI flash\n")
            await safe_write(writer, b"System halted\n")
            state["booting"] = False
            if session:
                session.booting = False
            return

        await safe_write(writer, b"SPI Initialised\n")
        await safe_write(writer, b"\nLoading bootloader from XM25QH64C\n")

        idx = 0
        for i, line in enumerate(BOOTLOG_LINES):
            if not state["power_on"]:
                await safe_write(writer, b"\n[POWER CUT]\n")
                return

            if b"SF: 1703936 bytes" in line:
                idx = i
                break

            await safe_write(writer, line)
            await asyncio.sleep(0.03)

        await safe_write(writer, b"\nReading firmware from SPI flash...\n")

        state["glitched"] = False
        total_steps = 50

        await safe_write(writer, b"Loading firmware: [....................] 0%")

        for i in range(total_steps):
            if not state["power_on"]:
                await safe_write(writer, b"\n[POWER CUT]\n")
                return

            await asyncio.sleep(0.2)

            for spi_pin in list(state["spi_connections"]):
                role = SPI_PIN_MAP.get(spi_pin)

                if role == "VCC":
                    await safe_write(writer, b"\n\n*** POWER FAULT ***\n")
                    state["booting"] = False
                    if session:
                        session.booting = False
                    return

                if role in GLITCHABLE:
                    state["glitched"] = True
                    break

            if state["glitched"]:
                break

            progress = int((i + 1) / total_steps * 20)
            percent = int((i + 1) / total_steps * 100)

            bar = "#" * progress + "." * (20 - progress)

            await safe_write(writer, f"\rLoading firmware: [{bar}] {percent}%".encode())

        if state["glitched"]:
            await safe_write(writer, b"\n\n*** SPI READ ERROR ***\n")
            await safe_write(writer, b"CRC mismatch during firmware load\n")
            await safe_write(writer, b"Boot failed.\n")
            await safe_write(writer, b"Entering U-Boot rescue shell...\n\n")

            state["booting"] = False
            if session:
                session.booting = False
                session.mode = "uboot"

            await uboot_shell(reader, writer, session)
            return

        await safe_write(writer, b"\n\nFirmware load complete\n")

        for line in BOOTLOG_LINES[idx:]:
            if not state["power_on"]:
                await safe_write(writer, b"\n[POWER CUT]\n")
                return

            await safe_write(writer, line)
            await asyncio.sleep(0.03)

        await login_prompt(reader, writer)

    finally:
        state["booting"] = False
        if session:
            session.mode = "menu"
            session.booting = False


async def uboot_shell(reader, writer, session):

    await safe_write(writer, b"\nU-Boot 2013.07 (Ingenic T23)\n")
    await safe_write(writer, b"Type 'help' for commands\n")

    session.mode = "uboot"

    while session.alive and session.mode == "uboot":
        if await check_power(writer):
            session.mode = "menu"
            return

        await safe_write(writer, b"=> ")

        line = await reader.readline()
        if not line:
            return

        cmd_line = line.decode().strip()
        parts = cmd_line.split()

        if not parts:
            await safe_write(writer, b"\n")
            continue

        cmd = parts[0]

        if cmd == "help":
            await safe_write(writer, b"\nCommands:\n")
            await safe_write(writer, b"  printenv\n")
            await safe_write(writer, b"  bdinfo\n")
            await safe_write(writer, b"  version\n")
            await safe_write(writer, b"  sf\n")
            await safe_write(writer, b"  md\n")

        elif cmd == "version":
            await safe_write(writer, b"\nU-Boot 2013.07 (Oct 28 2024)\n")
            await safe_write(writer, b"CPU: Ingenic T23\n")

        elif cmd == "bdinfo":
            await safe_write(writer, b"\narch_number = 0x00000\n")
            await safe_write(writer, b"boot_params = 0x80000100\n")
            await safe_write(writer, b"DRAM bank   = 0x80000000\n")
            await safe_write(writer, b"memsize     = 64 MB\n")
            await safe_write(writer, b"flash base  = 0x00000000\n")

        elif cmd == "printenv":
            await safe_write(writer, b"\nbootcmd=run boot_normal\n")
            await safe_write(
                writer, b"bootargs=console=ttyS1,115200 mem=46M root=/dev/mtdblock5\n"
            )
            await safe_write(
                writer, b"mtdparts=jz_sfc:256k(UBT),32k(ENV),32k(N/A),...\n"
            )

        elif cmd == "sf":
            if len(parts) > 1 and parts[1] == "probe":
                if not spi_is_usable():
                    await safe_write(writer, b"SF: probe failed\n")
                else:
                    await safe_write(writer, b"SF: Detected XM25QH64C (8MB)\n")

            elif len(parts) > 1 and parts[1] == "read":
                if len(parts) < 5:
                    await safe_write(writer, b"Usage: sf read <addr> <offset> <len>\n")
                    continue

                if not spi_is_usable():
                    await safe_write(writer, b"SF: ERROR - SPI bus fault\n")
                    continue

                addr = int(parts[2], 16)
                offset = int(parts[3], 16)
                length = int(parts[4], 16)

                ram_offset = addr - RAM_BASE

                if ram_offset < 0 or (ram_offset + length) > RAM_SIZE:
                    await safe_write(writer, b"Bad RAM address\n")
                    continue

                if offset < 0 or (offset + length) > SF_SIZE:
                    await safe_write(writer, b"Bad flash offset\n")
                    continue

                ram[ram_offset : ram_offset + length] = FIRMWARE[
                    offset : offset + length
                ]

                await safe_write(writer, b"SF: read OK\n")

            else:
                await safe_write(writer, b"Usage: sf probe or sf read\n")

        elif cmd == "md":
            if len(parts) < 3:
                await safe_write(writer, b"Usage: md <addr> <len>\n")
                continue

            addr, length = parts[1], parts[2]

            lines = md_dump(addr, length)

            for l in lines:
                await safe_write(writer, (l + "\n").encode())

        else:
            await safe_write(writer, b"Unknown command\n")


async def login_prompt(reader, writer):
    await safe_write(writer, b"\nTuya Wi-Fi IP Indoor Camera\n")

    while True:
        if await check_power(writer):
            return

        await safe_write(writer, b"\nlogin: ")

        if not uart_can_input():
            await asyncio.sleep(0.2)
            continue

        await reader.readline()

        await safe_write(writer, b"Password: ")
        await reader.readline()

        await safe_write(writer, b"\nLogin incorrect\n")


def start_nc_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = loop.run_until_complete(asyncio.start_server(handle_nc, "0.0.0.0", 1337))

    loop.run_forever()


if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=5000)