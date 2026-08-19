#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=5000
OLLAMA_BIN="${OLLAMA_BIN:-$HOME/.local/ollama/bin/ollama}"
OLLAMA_MODELS_DIR="${OLLAMA_MODELS:-$HOME/.local/ollama/models}"
MODEL_DEFAULT="qwen2.5vl:3b"
LOG_DIR="$PROJECT_DIR/.logs"

mkdir -p "$LOG_DIR"

echo "== Describir imagen con IA (Flask + Ollama) =="

# 1. Binario de Ollama
if [ ! -x "$OLLAMA_BIN" ]; then
    echo "[!] No se encontró el binario de Ollama en: $OLLAMA_BIN"
    echo "    Instálalo con:  curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

ollama_running() {
    curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1
}

# 2. Servidor de Ollama
if ollama_running; then
    echo "[ok] Ollama ya está corriendo (localhost:11434)"
else
    echo "[..] Arrancando Ollama..."
    OLLAMA_MODELS="$OLLAMA_MODELS_DIR" setsid nohup "$OLLAMA_BIN" serve \
        >"$LOG_DIR/ollama.log" 2>&1 </dev/null &
    for _ in $(seq 1 30); do
        ollama_running && break
        sleep 1
    done
    if ollama_running; then
        echo "[ok] Ollama listo"
    else
        echo "[!] Ollama no arrancó. Revisa $LOG_DIR/ollama.log"
        exit 1
    fi
fi

# 3. Modelo por defecto
if OLLAMA_MODELS="$OLLAMA_MODELS_DIR" "$OLLAMA_BIN" list | grep -q "^${MODEL_DEFAULT}[[:space:]]"; then
    echo "[ok] Modelo $MODEL_DEFAULT presente"
else
    echo "[..] Descargando modelo $MODEL_DEFAULT (puede tardar)..."
    OLLAMA_MODELS="$OLLAMA_MODELS_DIR" "$OLLAMA_BIN" pull "$MODEL_DEFAULT"
fi

# 4. Entorno virtual + dependencias
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "[..] Creando entorno virtual..."
    python3 -m venv "$PROJECT_DIR/.venv"
fi
"$PROJECT_DIR/.venv/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"

# 5. App Flask
if curl -fsS "http://localhost:$PORT/" >/dev/null 2>&1; then
    echo "[ok] La app ya está corriendo en http://localhost:$PORT"
else
    echo "[..] Arrancando la app..."
    (
        cd "$PROJECT_DIR"
        setsid nohup .venv/bin/python app.py >"$LOG_DIR/app.log" 2>&1 </dev/null &
    )
    for _ in $(seq 1 30); do
        curl -fsS "http://localhost:$PORT/" >/dev/null 2>&1 && break
        sleep 1
    done
    if curl -fsS "http://localhost:$PORT/" >/dev/null 2>&1; then
        echo "[ok] App lista en http://localhost:$PORT"
    else
        echo "[!] La app no arrancó. Revisa $LOG_DIR/app.log"
        exit 1
    fi
fi

echo ""
echo "✓ Todo listo: http://localhost:$PORT"
echo "  (abre esa dirección en tu navegador de Windows)"
