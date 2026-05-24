import asyncio
import random
import threading

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

BASE_DELAY = 75
BASE_DURATION = 5

CORRECT_DELAY = BASE_DELAY + random.randint(-3, 3)
CORRECT_DURATION = BASE_DURATION + random.randint(-1, 1)

state = {
    "wiring_correct": False,
    "uart_active": False,
    "last_delay": 0,
    "last_duration": 0,
    "multimeter": {"mode": "voltage", "red": None, "black": None},
}

PICOCOM_BANNER = """picocom v2024-07
port is        : /dev/ttyACM0
baudrate is    : 115200
"""

started = False



def start_background_thread():
    threading.Thread(target=start_nc_server, daemon=True).start()
    
def parse_call(code):
    code = code.strip()

    if "(" not in code or not code.endswith(")"):
        return None, None

    func_name = code[: code.index("(")].strip()
    args_str = code[code.index("(") + 1 : -1].strip()

    args = {}

    if args_str:
        parts = [p.strip() for p in args_str.split(",")]

        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                args[k.strip()] = v.strip()
            else:
                args[part.strip()] = None

    return func_name, args


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/wiring", methods=["POST"])
def wiring():
    data = request.json

    state["wiring_correct"] = (
        data.get("camera_rx") == "uart_tx"
        and data.get("camera_tx") == "uart_rx"
        and data.get("gnd") == "gnd"
    )

    return jsonify({"ok": True, "correct": state["wiring_correct"]})


@app.route("/multimeter", methods=["POST"])
def multimeter():
    data = request.json

    state["multimeter"]["mode"] = data.get("mode")
    state["multimeter"]["red"] = data.get("red")
    state["multimeter"]["black"] = data.get("black")

    return jsonify({"ok": True})


@app.route("/run_code", methods=["POST"])
def run_code():
    code = request.json.get("code", "")

    func, args = parse_call(code)

    if not func:
        return jsonify({"output": "invalid"})

    if func == "help":
        return jsonify(
            {
                "output": (
                    "Available functions:\n"
                    "- help()\n"
                    "- available_pins()\n"
                    "- glitch(delay=<int>, duration=<int>)\n (delay being the delta between t=O boot time and t=delay the time where the pin will be glitched\n duration being for how long the pin will be glitched for)"
                    "- get_pin_voltage('<pin>')"
                )
            }
        )

    if func == "available_pins":
        return jsonify({"output": "vcc, gnd, uart_tx, uart_rx"})

    if func == "glitch":
        try:
            delay = int(args.get("delay"))
            duration = int(args.get("duration"))
        except:
            return jsonify({"output": "invalid arguments"})

        state["last_delay"] = delay
        state["last_duration"] = duration

        return jsonify({"output": "OK"})

    if func == "get_pin_voltage":
        if not args:
            return jsonify({"output": "invalid"})

        pin = list(args.keys())[0]
        pin = pin.strip("'\"")

        meter = state["multimeter"]

        if meter["mode"] != "voltage":
            return jsonify({"output": "multimeter not in voltage mode"})

        if meter["red"] != pin or meter["black"] != "gnd":
            return jsonify({"output": "wrong multimeter probes"})

        if not state["wiring_correct"]:
            return jsonify({"output": "0.0"})

        if pin == "vcc":
            return jsonify({"output": "3.3"})

        if pin in ["gnd", "uart_rx"]:
            return jsonify({"output": "0.0"})

        if pin != "uart_tx":
            return jsonify({"output": "0.0"})

        delay = state["last_delay"]
        duration = state["last_duration"]

        delay_distance = abs(delay - CORRECT_DELAY)

        if delay_distance > 3:
            return jsonify({"output": "0.0"})

        if delay_distance > 0:
            return jsonify({"output": str(round(random.uniform(0.8, 2.5), 2))})

        delay_ok = delay == CORRECT_DELAY
        duration_ok = duration == CORRECT_DURATION

        if delay_ok and duration_ok:
            if random.random() < 0.4:
                state["uart_active"] = True
                return jsonify({"output": "3.3"})

        return jsonify({"output": str(round(random.uniform(0.8, 2.5), 2))})

    return jsonify(
        {"output": "not supported, use help() to get the list of supported functions"}
    )


@app.route("/reset")
def reset():
    state["uart_active"] = False
    return jsonify({"ok": True})


async def handle_nc(reader, writer):
    writer.write(PICOCOM_BANNER.encode())
    await writer.drain()

    while True:
        await asyncio.sleep(0.1)

        if state["uart_active"]:
            state["uart_active"] = False
            try:
                with open("/uart_bootlog.txt", "rb") as f:
                    for line in f:
                        writer.write(line)
                        await writer.drain()
                        await asyncio.sleep(0.05)
            except Exception as e:
                writer.write(f"[ERROR] bootlog missing: {e}\n".encode())
                await writer.drain()


def start_nc_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = loop.run_until_complete(asyncio.start_server(handle_nc, "0.0.0.0", 1337))

    loop.run_forever()


if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=5000)
