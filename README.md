# Describir imagen con IA

Mini app web que recibe una imagen y un texto de contexto, y devuelve una descripción generada por un modelo de visión local (Ollama). Sin API keys ni costos.

## Requisitos

- Linux (x86_64)
- Python 3.10+
- ~4 GB de RAM libre (modelo `qwen2.5vl:3b`)

## Instalación

### 1. Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

> Si no tienes `sudo` disponible, descarga el binario desde
> https://github.com/ollama/ollama/releases y extráelo en tu carpeta de usuario:

```bash
mkdir -p ~/.local/ollama
curl -fsSL -o /tmp/ollama.tar.zst https://github.com/ollama/ollama/releases/download/v0.32.14/ollama-linux-amd64.tar.zst
# extraer requiere el paquete `zstandard`: pip install zstandard
export PATH="$HOME/.local/ollama/bin:$PATH"
```

Inicia el servidor de Ollama (mantenlo corriendo):

```bash
ollama serve
```

Descarga los modelos de visión (solo la primera vez):

```bash
ollama pull qwen2.5vl:3b   # mejor calidad
ollama pull gemma3:4b      # ligero
```

### 2. Dependencias de Python

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uso

### Ejecución fácil (WSL2 + Windows)

Si trabajas en WSL2 y abres la app desde el navegador de Windows:

- **Doble clic** en `start.bat` (desde Windows) → arranca Ollama si hace falta,
  descarga el modelo si no está, levanta la app y abre el navegador automáticamente.
- O directamente en WSL2: `./run.sh`

El proyecto debe estar en `~/agentic/read-image-ai` (la ruta que usa `start.bat`).
El script es idempotente: si la app u Ollama ya están corriendo, no los duplica.

### Manual

```bash
.venv/bin/python app.py
```

Abre http://localhost:5000, sube una imagen, escribe un contexto, elige el modelo
en el desplegable (`qwen2.5vl:3b` o `gemma3:4b`) y pulsa **Describir imagen**.

## Configuración

- El modelo se elige desde la propia interfaz (desplegable).
- Por defecto usa `qwen2.5vl:3b`; puedes cambiarlo con la variable de entorno
  `OLLAMA_MODEL` (por ejemplo `OLLAMA_MODEL=gemma3:4b .venv/bin/python app.py`).
- Para añadir otro modelo: descárgalo con `ollama pull <modelo>` y agrégalo a
  `AVAILABLE_MODELS` en `ollama_client.py`.

## Estructura

```
read-image-ai/
├── app.py                 # Servidor Flask + endpoints
├── ollama_client.py       # Cliente de la API local de Ollama
├── templates/
│   └── index.html         # Interfaz web
├── run.sh                 # Lanzador WSL2 (arranca Ollama, modelo y app)
├── start.bat              # Doble clic desde Windows (llama a run.sh y abre el navegador)
└── requirements.txt
```