"""Cliente de la API local de Ollama (generate, chat, warm-up, ping)."""

from typing import Any

import requests

from config import (
    DEFAULT_MODEL,
    KEEP_ALIVE,
    MOCKUP_MODEL,
    OLLAMA_API_CHAT,
    OLLAMA_API_GENERATE,
    OLLAMA_API_TAGS,
    TIMEOUT_CHAT,
    TIMEOUT_PING,
    TIMEOUT_WARM,
)


SYSTEM_CODE = (
    "Eres un experto en diseño frontend. Genera SOLO un documento HTML completo y "
    "autocontenido (con CSS incrustado en <style> y, si hace falta, JS en <script>) "
    "que sirva como mockup del diseño solicitado. Usa estilos modernos, responsive y "
    "limpios, sin dependencias externas. NO uses bloques de código (```), NO añadas "
    "explicaciones ni texto fuera del HTML. El documento debe empezar por "
    "<!DOCTYPE html>."
)


def describe_image(
    image_base64: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = TIMEOUT_CHAT,
) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
    }
    resp = requests.post(OLLAMA_API_GENERATE, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


def chat_image(
    image_b64: str | None,
    messages: list[dict[str, Any]],
    model: str = DEFAULT_MODEL,
    timeout: int = TIMEOUT_CHAT,
    max_messages: int = 20,
) -> tuple[str, dict[str, int]]:
    msgs: list[dict[str, Any]] = []
    for m in messages:
        clean: dict[str, Any] = {
            "role": m.get("role"),
            "content": (m.get("content") or "").strip(),
        }
        imgs = m.get("images") or []
        if isinstance(imgs, list):
            imgs = [i for i in imgs if isinstance(i, str) and i]
            if imgs:
                clean["images"] = imgs
        msgs.append(clean)
    if image_b64:
        first_user = next((i for i, m in enumerate(msgs) if m.get("role") == "user"), 0)
        msgs[first_user]["images"] = msgs[first_user].get("images", []) + [image_b64]
    if len(msgs) > max_messages:
        msgs = [msgs[0]] + msgs[-(max_messages - 1):]

    payload = {"model": model, "messages": msgs, "stream": False, "keep_alive": KEEP_ALIVE}
    resp = requests.post(OLLAMA_API_CHAT, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    message = data.get("message") or {}
    content = message.get("content", "").strip()
    timing = {
        "total_ms": round(data.get("total_duration", 0) / 1e6),
        "eval_ms": round(data.get("eval_duration", 0) / 1e6),
        "load_ms": round(data.get("load_duration", 0) / 1e6),
    }
    return content, timing


def warm_model(
    model: str,
    keep_alive: str = KEEP_ALIVE,
    timeout: int = TIMEOUT_WARM,
) -> bool:
    payload = {
        "model": model,
        "prompt": "Describe.",
        "stream": False,
        "keep_alive": keep_alive,
        "options": {"num_predict": 1},
    }
    resp = requests.post(OLLAMA_API_GENERATE, json=payload, timeout=timeout)
    resp.raise_for_status()
    return True


def ping_ollama(timeout: int = TIMEOUT_PING) -> bool:
    try:
        requests.get(OLLAMA_API_TAGS, timeout=timeout)
        return True
    except requests.RequestException:
        return False


def unload_model(model: str, timeout: int = TIMEOUT_WARM) -> bool:
    """Libera el modelo de la memoria de Ollama (keep_alive=0)."""
    payload = {
        "model": model,
        "prompt": "x",
        "stream": False,
        "keep_alive": 0,
        "options": {"num_predict": 1},
    }
    resp = requests.post(OLLAMA_API_GENERATE, json=payload, timeout=timeout)
    resp.raise_for_status()
    return True


def is_oom_error(exc: Exception) -> bool:
    """Detecta si la excepción de Ollama corresponde a falta de memoria (OOM)."""
    text = str(exc).lower()
    return (
        "llama-server process has terminated" in text
        or "out of memory" in text
        or "oom" in text
        or "signal: killed" in text
    )


def generate_code(
    prompt: str,
    model: str = MOCKUP_MODEL,
    timeout: int = TIMEOUT_CHAT,
) -> tuple[str, dict[str, int]]:
    """Genera un mockup HTML/CSS con el modelo de código (solo texto)."""
    messages = [
        {"role": "system", "content": SYSTEM_CODE},
        {"role": "user", "content": prompt.strip()},
    ]
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": KEEP_ALIVE,
    }
    resp = requests.post(OLLAMA_API_CHAT, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    message = data.get("message") or {}
    content = message.get("content", "").strip()
    timing = {
        "total_ms": round(data.get("total_duration", 0) / 1e6),
        "eval_ms": round(data.get("eval_duration", 0) / 1e6),
        "load_ms": round(data.get("load_duration", 0) / 1e6),
    }
    return content, timing


def extract_html(text: str) -> str:
    """Extrae el HTML del texto del modelo (quita fences ```html ... ```)."""
    t = (text or "").strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t