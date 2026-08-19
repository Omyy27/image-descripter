import base64
import io
import os
import sys

from flask import Flask, jsonify, render_template, request
from PIL import Image

from ollama_client import AVAILABLE_MODELS, DEFAULT_MODEL, describe_image

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

MAX_IMAGE_SIZE = 1280
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")


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


if __name__ == "__main__":
    app.run(host=APP_HOST, port=5000, debug=False)