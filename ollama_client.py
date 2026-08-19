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