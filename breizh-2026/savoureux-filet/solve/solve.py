import argparse
import base64
import json
import struct
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util import Counter

KEY = base64.b64decode("AQ==").ljust(16, b"\x00")

_NATO: dict[str, str] = {
    "alfa": "A",
    "alpha": "A",
    "bravo": "B",
    "charlie": "C",
    "delta": "D",
    "echo": "E",
    "foxtrot": "F",
    "golf": "G",
    "hotel": "H",
    "india": "I",
    "juliett": "J",
    "juliet": "J",
    "kilo": "K",
    "lima": "L",
    "mike": "M",
    "november": "N",
    "oscar": "O",
    "papa": "P",
    "quebec": "Q",
    "romeo": "R",
    "sierra": "S",
    "tango": "T",
    "uniform": "U",
    "victor": "V",
    "whiskey": "W",
    "xray": "X",
    "yankee": "Y",
    "zulu": "Z",
}
_NATO_SORTED = sorted(_NATO.items(), key=lambda kv: len(kv[0]), reverse=True)


def decode_nato(text: str) -> str:
    lower = text.lower()
    result: list[str] = []
    i = 0
    while i < len(lower):
        matched = False
        for word, letter in _NATO_SORTED:
            if lower[i:].startswith(word):
                result.append(letter)
                i += len(word)
                matched = True
                break
        if not matched:
            i += 1
    return "".join(result)


def build_nonce(packet_id: int, sender: int) -> bytes:
    return struct.pack("<Q", packet_id) + struct.pack("<Q", sender)


def decrypt(payload_b64: str, packet_id: int, sender: int) -> bytes:
    ciphertext = base64.b64decode(payload_b64)
    nonce = build_nonce(packet_id, sender)
    ctr = Counter.new(128, initial_value=int.from_bytes(nonce, "big"))
    cipher = AES.new(KEY, AES.MODE_CTR, counter=ctr)
    return cipher.decrypt(ciphertext)


def solve(path: Path) -> list[str]:
    data: dict[str, list[dict[str, int | str]]] = json.loads(path.read_text())
    messages: list[str] = []
    for pkt in data["packets"]:
        raw = decrypt(str(pkt["payload"]), int(pkt["id"]), int(pkt["from"]))
        try:
            messages.append(raw.decode())
        except UnicodeDecodeError:
            messages.append(raw.hex())
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        default=Path("../files/intercepted.json"),
        help="Path to the intercepted JSON file",
    )
    args = parser.parse_args()

    messages = solve(args.file)

    assert messages[0] == "BravoZuluHotelCharlieTangoFoxtrot", (
        f"Unexpected first message: {messages[0]!r}"
    )

    for msg in messages:
        print(f"{msg} -> {decode_nato(msg)}")

    flag = "_".join(decode_nato(m) for m in messages)
    flag = flag.replace("_", "{", 1) + "}"
    print()
    print(flag)


if __name__ == "__main__":
    main()
