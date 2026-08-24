import base64
import io
import json
import os
import subprocess
import sys

from flask import Flask, jsonify, render_template, request
from PIL import Image

from ollama_client import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    chat_image,
    describe_image,
    warm_model,
)

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

MAX_IMAGE_SIZE = 1280
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")


def _is_windows():
    return sys.platform.startswith("win")


def _detach(cmd):
    kwargs = {
        "shell": True,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if not _is_windows():
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **kwargs)


def prepare_image(raw: bytes) -> str:
    img = Image.open(io.BytesIO(raw))
    img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/describe", methods=["POST"])
def describe():
    if "image" not in request.files:
        return jsonify({"error": "No se subió ninguna imagen."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "El archivo de imagen está vacío."}), 400

    context = (request.form.get("context") or "").strip()
    if not context:
        context = "Describe esta imagen en detalle."

    model = (request.form.get("model") or "").strip()
    if model not in AVAILABLE_MODELS:
        model = DEFAULT_MODEL

    try:
        image_b64 = prepare_image(file.read())
        description = describe_image(image_b64, context, model=model)
        if not description:
            return jsonify({"error": "El modelo no devolvió una descripción."}), 500
        return jsonify({"description": description})
    except Exception as exc:
        app.logger.exception("Error generando la descripción")
        return jsonify({"error": f"Error generando la descripción: {exc}"}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    model = (request.form.get("model") or "").strip()
    if model not in AVAILABLE_MODELS:
        model = DEFAULT_MODEL

    messages_raw = (request.form.get("messages") or "").strip()
    if not messages_raw:
        return jsonify({"error": "No hay mensajes en la conversación."}), 400
    try:
        messages = json.loads(messages_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Historial de mensajes inválido."}), 400
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Historial de mensajes vacío."}), 400
    if not all(
        isinstance(m, dict)
        and m.get("role") in ("user", "assistant", "system")
        and isinstance(m.get("content"), str)
        and m["content"].strip()
        and (
            "images" not in m
            or (
                isinstance(m["images"], list)
                and all(isinstance(i, str) and i for i in m["images"])
            )
        )
        for m in messages
    ):
        return jsonify({"error": "Formato de mensajes inválido."}), 400

    image_b64 = (request.form.get("image") or "").strip() or None

    try:
        reply = chat_image(image_b64, messages, model=model)
        if not reply:
            return jsonify({"error": "El modelo no devolvió una respuesta."}), 500
        return jsonify({"reply": reply})
    except Exception as exc:
        app.logger.exception("Error en el chat")
        return jsonify({"error": f"Error en el chat: {exc}"}), 500


@app.route("/api/reload-model", methods=["POST"])
def reload_model():
    model = (request.form.get("model") or "").strip()
    if model not in AVAILABLE_MODELS:
        model = DEFAULT_MODEL
    try:
        warm_model(model)
        return jsonify({"ok": True, "message": f"Modelo {model} pre-cargado en memoria."})
    except Exception as exc:
        app.logger.exception("Error pre-cargando el modelo")
        return jsonify({"ok": False, "error": f"Error pre-cargando el modelo: {exc}"}), 500


@app.route("/api/restart", methods=["POST"])
def restart_server():
    pid = os.getpid()
    if _is_windows():
        if getattr(sys, "frozen", False):
            target = sys.executable
            args = ""
        else:
            target = sys.executable
            args = f" -ArgumentList '{os.path.abspath(__file__)}'"
        cmd = (
            "powershell -NoProfile -Command "
            f"\"Start-Sleep -Seconds 1; Stop-Process -Id {pid} -Force; "
            f"Start-Process -FilePath '{target}'{args}\""
        )
    else:
        log = os.path.join(BASE_DIR, ".logs", "app.log")
        os.makedirs(os.path.join(BASE_DIR, ".logs"), exist_ok=True)
        cmd = (
            f"bash -c 'sleep 1; kill {pid} 2>/dev/null || true; sleep 1; "
            f"cd {BASE_DIR!r} && setsid nohup .venv/bin/python app.py "
            f">> {log!r} 2>&1 &'"
        )
    _detach(cmd)
    return jsonify({"ok": True, "message": "Reiniciando el servidor…"}), 200


@app.route("/api/stop", methods=["POST"])
def stop_server():
    pid = os.getpid()
    if _is_windows():
        cmd = (
            "powershell -NoProfile -Command "
            f"\"Start-Sleep -Seconds 1; Stop-Process -Id {pid} -Force\""
        )
    else:
        cmd = f"bash -c 'sleep 1; kill {pid} 2>/dev/null || true'"
    _detach(cmd)
    return jsonify({"ok": True, "message": "Deteniendo la app…"}), 200


if __name__ == "__main__":
    app.run(host=APP_HOST, port=5000, debug=False)