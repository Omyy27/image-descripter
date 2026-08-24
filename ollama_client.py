import os

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5vl:3b")

AVAILABLE_MODELS = [
    "qwen2.5vl:3b",
    "gemma3:4b",
]


def describe_image(image_base64, prompt, model=DEFAULT_MODEL, timeout=300):
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


def chat_image(image_b64, messages, model=DEFAULT_MODEL, timeout=300, max_messages=20):
    msgs = list(messages)
    if image_b64:
        first_user = next((i for i, m in enumerate(msgs) if m.get("role") == "user"), 0)
        if "images" not in msgs[first_user]:
            msgs[first_user] = {**msgs[first_user], "images": [image_b64]}
    if len(msgs) > max_messages:
        msgs = [msgs[0]] + msgs[-(max_messages - 1):]
    payload = {"model": model, "messages": msgs, "stream": False}
    resp = requests.post(
        "http://localhost:11434/api/chat", json=payload, timeout=timeout
    )
    resp.raise_for_status()
    data = resp.json()
    message = data.get("message") or {}
    return message.get("content", "").strip()


def warm_model(model, keep_alive="30m", timeout=120):
    payload = {
        "model": model,
        "prompt": "Describe.",
        "stream": False,
        "keep_alive": keep_alive,
        "options": {"num_predict": 1},
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return True