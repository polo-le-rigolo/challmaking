from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

device_ready = False
login_required = True
PASSWORD = "KW42v999ex3up7zNOeZsXIdFHMow87y7kkvPd2483"  

@app.route('/api/power', methods=['POST'])
def power_on():
    global device_ready, login_required
    data = request.json
    connections = data.get("connections", [])
    baud = data.get("baud", "115200")

    pairs = {f"{c['a']}|{c['b']}" for c in connections}
    pairs |= {f"{c['b']}|{c['a']}" for c in connections}
    conn = lambda a, b: f"{a}|{b}" in pairs

    baudrate_ok = baud == "115200"

    uart_ok = conn("USB:TX", "ESP:GPIO3") and conn("ESP:GPIO1", "USB:RX") and conn("ESP:GND", "USB:GND")
    spi_ok = (
        conn("ESP:GND", "FLASH:GND") and
        conn("ESP:GPIO18", "FLASH:CLK") and
        conn("ESP:GPIO19", "FLASH:D0") and
        conn("ESP:GPIO23", "FLASH:D1") and
        conn("ESP:GPIO5", "FLASH:CS")
    )

    output = "Connecting to serial monitor...\n"
    if not baudrate_ok:
        output += "Wrong baudrate\n"
        return jsonify({"terminal": output, "status": "Wrong baudrate"})

    if not uart_ok:
        output += "Communication UART non établie.\n"
        return jsonify({"terminal": output, "status": "UART incorrect"})

    output += "[BOOT] ESP32 DEVICE v1.2\n[BOOT] Initializing SPI...\n"
    if not spi_ok:
        output += "[ERR] SPI flash introuvable : impossible de charger le firmware.\n"
        return jsonify({"terminal": output, "status": "Boot échoué (SPI manquant)"})

    device_ready = True
    login_required = True  
    output += "[OK] SPI détecté. Chargement du firmware...\n[OK] Shell ouvert.\n"
    output += "Please login: >> "
    return jsonify({"terminal": output, "status": "Login required"})

@app.route('/api/cmd', methods=['POST'])
def handle_command():
    global login_required
    data = request.json
    cmd = data.get("cmd", "").strip()

    if login_required:
        if cmd.startswith("login "):
            pwd = cmd.split(" ", 1)[1]
            if pwd == PASSWORD:
                login_required = False
                return jsonify({"output": "Login successful! You can now use the flag command.\n>> "})
            else:
                return jsonify({"output": "Incorrect password. Try again.\n>> "})
        else:
            return jsonify({"output": "Please login first using: login <password>\n>> "})

    if cmd == "help":
        return jsonify({"output": "help, flag, reboot\n>> "})
    elif cmd == "flag":
        return jsonify({"output": "NBCTF{m1cr0py7h0n_5uck5!}\n>> "})
    elif cmd == "reboot":
        login_required = True
        return jsonify({"output": "[Rebooting...]\nPlease login: >> "})
    else:
        return jsonify({"output": "Commande inconnue\n>> "})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
