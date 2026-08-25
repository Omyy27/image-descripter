"""Servidor Flask de Image Descripter."""

import json
import os
import subprocess
import sys
import time

from flask import Flask, jsonify, render_template, request

try:
    import psutil

    psutil.cpu_percent(interval=None)
except ImportError:  # pragma: no cover
    psutil = None

from config import (
    APP_HOST,
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    MAX_CONTENT_LENGTH,
    MODEL_META,
    PORT,
)
from image_utils import prepare_image
from ollama_client import (
    chat_image,
    describe_image,
    is_oom_error,
    ping_ollama,
    unload_model,
    warm_model,
)

START_TIME = time.time()

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _detach(cmd: str) -> None:
    kwargs: dict = {
        "shell": True,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if not _is_windows():
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


def _pick_model(raw: str) -> str:
    model = (raw or "").strip()
    return model if model in AVAILABLE_MODELS else DEFAULT_MODEL


def _friendly_error(exc: Exception) -> str:
    if is_oom_error(exc):
        return (
            "No hay suficiente memoria para cargar el modelo. "
            "Cierra otros programas o usa un modelo más ligero, y pulsa "
            "'Descargar modelo' para liberar la RAM."
        )
    return str(exc)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/models", methods=["GET"])
def models():
    return jsonify({"models": MODEL_META})


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

    model = _pick_model(request.form.get("model") or "")

    try:
        image_b64 = prepare_image(file.read())
        description = describe_image(image_b64, context, model=model)
        if not description:
            return jsonify({"error": "El modelo no devolvió una descripción."}), 500
        return jsonify({"description": description})
    except Exception as exc:
        app.logger.exception("Error generando la descripción")
        return jsonify({"error": f"Error generando la descripción: {_friendly_error(exc)}"}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    model = _pick_model(request.form.get("model") or "")

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
        reply, timing = chat_image(image_b64, messages, model=model)
        if not reply:
            return jsonify({"error": "El modelo no devolvió una respuesta."}), 500
        return jsonify({"reply": reply, "timing": timing})
    except Exception as exc:
        app.logger.exception("Error en el chat")
        return jsonify({"error": f"Error en el chat: {_friendly_error(exc)}"}), 500


@app.route("/api/stats", methods=["GET"])
def stats():
    uptime = round(time.time() - START_TIME)
    cpu = None
    ram = None
    if psutil is not None:
        cpu = round(psutil.cpu_percent(interval=None) or 0)
        vm = psutil.virtual_memory()
        ram = {
            "used_mb": round(vm.used / (1024 * 1024)),
            "total_mb": round(vm.total / (1024 * 1024)),
            "percent": round(vm.percent),
        }
    return jsonify(
        {
            "uptime": uptime,
            "cpu": cpu,
            "ram": ram,
            "ollama": ping_ollama(),
        }
    )


@app.route("/api/reload-model", methods=["POST"])
def reload_model():
    model = _pick_model(request.form.get("model") or "")
    try:
        warm_model(model)
        return jsonify({"ok": True, "message": f"Modelo {model} pre-cargado en memoria."})
    except Exception as exc:
        app.logger.exception("Error pre-cargando el modelo")
        return jsonify({"ok": False, "error": f"Error pre-cargando el modelo: {_friendly_error(exc)}"}), 500


@app.route("/api/unload-model", methods=["POST"])
def unload_model_route():
    model = _pick_model(request.form.get("model") or "")
    try:
        unload_model(model)
        return jsonify({"ok": True, "message": f"Modelo {model} detenido (liberado de la memoria)."})
    except Exception as exc:
        app.logger.exception("Error descargando el modelo")
        return jsonify({"ok": False, "error": f"Error descargando el modelo: {_friendly_error(exc)}"}), 500


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
    from waitress import serve

    serve(app, host=APP_HOST, port=PORT, threads=8)