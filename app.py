from flask import Flask, abort, render_template, request, jsonify, send_from_directory, send_file
from flask_socketio import SocketIO, emit
import subprocess
import threading
import socket
import os
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ESP_PROJECT_PATH = r"C:\\Users\\shuyi\\Temp_sensor"
ELF_FILE_PATH = os.path.join(ESP_PROJECT_PATH, "build", "Temp_sensor.elf")
BIN_FILE_PATH = os.path.join(ESP_PROJECT_PATH, "build", "Temp_sensor.bin")
UPLOAD_FOLDER = r'C:\Users\shuyi\RemoteDashBoard\uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Telnet
TELNET_PORT = 4444
gdb_process= None


@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("file")
    if uploaded_file:
        filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        uploaded_file.save(filepath)
        return jsonify({"status": "uploaded", "filename": uploaded_file.filename})
    return jsonify({"error": "no file"}), 400


@app.route('/get-elf', methods=['GET'])
def get_elf():
    if os.path.exists(ELF_FILE_PATH):
        print(f"✅ ELF file found at: {ELF_FILE_PATH}")
        return send_file(ELF_FILE_PATH, as_attachment=True)
    else:
        error_msg = f"❌ ELF file not found at: {ELF_FILE_PATH}"
        print(error_msg)
        return jsonify({"error": error_msg}), 404

@app.route('/get-bin', methods=['GET'])
def get_bin():
    if os.path.exists(BIN_FILE_PATH):
        print(f"✅ BIN file found at: {BIN_FILE_PATH}")
        return send_file(BIN_FILE_PATH, as_attachment=True)
    else:
        error_msg = f"❌ BIN file not found at: {BIN_FILE_PATH}"
        print(error_msg)
        return jsonify({"error": error_msg}), 404

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(file_path):
        print(f"✅ Downloading file: {file_path}")
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    else:
        error_msg = f"❌ File '{filename}' not found in uploads folder."
        print(error_msg)
        return jsonify({"error": error_msg}), 404

@app.route("/latest")
def latest_file():
    try:
        files = sorted(
            [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(('.bin', '.elf'))],
            key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)),
            reverse=True
        )
        if files:
            print(f"✅ Latest file found: {files[0]}")
            return jsonify({"filename": files[0]})
        else:
            error_msg = "❌ No .bin or .elf files found in uploads folder."
            print(error_msg)
            return jsonify({"error": error_msg}), 404
    except Exception as e:
        error_msg = f"❌ Exception occurred while checking uploads: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    

@app.route("/api/debug/start", methods=["POST"])
def start_debugging():
    try:
        process = subprocess.Popen(["openocd", "-f", "interface/esp_usb_jtag.cfg", "-f", "target/esp32s3.cfg"],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        threading.Thread(target=stream_openocd_output, args=(process,), daemon=True).start()
        return jsonify({"status": "OpenOCD started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def stream_openocd_output(process):
    for line in iter(process.stdout.readline, ''):
        socketio.emit('log', {'data': line.strip()})

@socketio.on("telnet_command")
def handle_telnet_command(data):
    command = data.get("command", "")
    try:
        with socket.create_connection(("localhost", TELNET_PORT), timeout=5) as s:
            s.sendall((command + "\n").encode())
            time.sleep(0.1)
            output = s.recv(4096).decode(errors="ignore")
        emit("telnet_response", {"output": output})
    except Exception as e:
        emit("telnet_response", {"output": f"Error: {str(e)}"})

@socketio.on("gdb_command")
def handle_gdb_command(data):
    global gdb_process
    command = data.get("command", "")
    if gdb_process and gdb_process.poll() is None:
        try:
            gdb_process.stdin.write(command + "\n")
            gdb_process.stdin.flush()
        except Exception as e:
            emit("gdb_output", {"data": f"Error sending GDB command: {e}\n"})
            
@socketio.on("start_gdb")
def handle_start_gdb():
    global gdb_process
    if gdb_process is None or gdb_process.poll() is not None:
        start_gdb()
    else:
        emit("gdb_output", {"data": "GDB is already running.\n"})


def start_gdb():
    global gdb_process
    try:
        gdb_process = subprocess.Popen(
            ["xtensa-esp32s3-elf-gdb", ELF_FILE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        gdb_process.stdin.write("set remotetimeout 5\n")
        gdb_process.stdin.write("target remote localhost:3333\n")
        gdb_process.stdin.flush()

        def read_output():
            for line in iter(gdb_process.stdout.readline, ''):
                socketio.emit("gdb_output", {"data": line})

        threading.Thread(target=read_output, daemon=True).start()
    except Exception as e:
        socketio.emit("gdb_output", {"data": f"GDB launch error: {str(e)}"})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
