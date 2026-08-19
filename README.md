# Describir imagen con IA (WebGPU)

Mini app web que recibe una imagen y un texto de contexto, y genera una descripción
**en tu navegador** usando WebGPU con el modelo de visión **SmolVLM-500M** (Transformers.js).
No hay inferencia en el servidor: la imagen nunca sale de tu equipo.

## Requisitos

- Navegador con WebGPU: Chrome/Edge 113+ (recomendado), Firefox 141+, Safari 26+.
- Python 3.10+ (solo para servir la página estática).
- GPU con WebGPU (opcional): si no hay, el modelo corre en CPU (WASM), más lento.

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uso

```bash
.venv/bin/python app.py
```

Abre **http://localhost:5000** (debe ser `localhost`, no la IP de WSL, porque WebGPU
requiere un contexto seguro).

1. Pulsa **Cargar modelo** (primera vez descarga ~340 MB, luego queda cacheado en el navegador).
2. Sube una imagen, escribe el contexto y pulsa **Describir imagen**.

> El modelo SmolVLM-500M entiende mejor el inglés; escribe el contexto en inglés para
> mejores resultados.

## Cambiar de versión (Ollama)

Este proyecto guarda dos versiones en dos ramas de git:

| Rama      | Descripción                                             |
|-----------|---------------------------------------------------------|
| `main`    | Versión anterior: Flask + Ollama (modelo local en el servidor). |
| `webgpu`  | Versión actual: todo en el navegador con WebGPU.        |

```bash
git checkout main     # versión Ollama
git checkout webgpu   # versión WebGPU
```

## Estructura

```
read-image-ai/
├── app.py                 # Flask: solo sirve la página web
├── templates/
│   └── index.html         # UI + lógica WebGPU (SmolVLM-500M)
└── requirements.txt
```