"""Pipeline de procesamiento de imágenes."""

import base64
import io

from PIL import Image

from config import MAX_IMAGE_SIZE


def prepare_image(raw: bytes) -> str:
    """Convierte bytes de imagen en JPEG base64 redimensionado."""
    img = Image.open(io.BytesIO(raw))
    img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()