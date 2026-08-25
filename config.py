"""Configuración centralizada de la aplicación."""

import os

# --- Ollama ---
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_GENERATE = f"{OLLAMA_HOST}/api/generate"
OLLAMA_API_CHAT = f"{OLLAMA_HOST}/api/chat"
OLLAMA_API_TAGS = f"{OLLAMA_HOST}/api/tags"

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5vl:3b")

MODEL_META = [
    {"value": "qwen2.5vl:3b", "label": "qwen2.5vl:3b (mejor calidad)"},
    {"value": "gemma3:4b", "label": "gemma3:4b (ligero)"},
]
AVAILABLE_MODELS = [m["value"] for m in MODEL_META]

# Modelo de texto dedicado a generar código/mockups (no ve imágenes).
MOCKUP_MODEL = os.environ.get("OLLAMA_MOCKUP_MODEL", "qwen2.5-coder:3b")

# --- Servidor ---
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = 5000
MAX_CONTENT_LENGTH = 15 * 1024 * 1024

# --- Imágenes ---
MAX_IMAGE_SIZE = 1280

# --- Chat / Ollama ---
CHAT_MAX_MESSAGES = 20
KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "5m")
TIMEOUT_CHAT = 300
TIMEOUT_WARM = 120
TIMEOUT_PING = 2