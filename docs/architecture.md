# Arquitectura de Image Descripter

## Visión general

Aplicación local de escritorio/navegador que conversa con un modelo de visión
(Ollama) sobre imágenes. Sin API keys, sin cloud: el modelo y las imágenes viven
en la máquina del usuario.

```mermaid
graph TD
    subgraph Navegador (Windows/WSL2)
        UI[static/app.js + static/style.css]
        SESSION[(sessionStorage: 10 chats)]
        UI -- "POST /api/chat (form-data)" --> S
        UI -- "GET /api/stats" --> S
        UI -- "GET /api/models" --> S
    end

    subgraph Servidor local (Flask + waitress)
        S[app.py]
        CONFIG[config.py]
        IMG[image_utils.py]
        OC[ollama_client.py]
        S --> CONFIG
        S --> IMG
        S --> OC
        S --> STATS["/api/stats · psutil"]
        S --> CTRL["/api/reload-model · /api/unload-model · /api/restart · /api/stop"]
        S --> MOCK["/api/mockup · qwen2.5-coder:3b"]
    end

    OC -- "HTTP localhost:11434 /api/chat · /api/generate · /api/tags" --> OLLAMA[(Ollama)]
    OLLAMA -- "qwen2.5vl:3b · gemma3:4b" --> MODELS[(Modelos de visión)]
    OLLAMA -- "qwen2.5-coder:3b" --> CODEMODEL[(Modelo de código)]

    TEMPLATES[templates/index.html] --> UI
```

## Flujo principal (chat)

1. El navegador carga `index.html` (markup) + `static/app.js` + `static/style.css`.
2. `app.js` obtiene los modelos disponibles de `GET /api/models` y rellena los
   `<select>` del header y del formulario.
3. El usuario envía un turno → `POST /api/chat` con `model`, `messages`
   (historial completo, con `images` base64 opcionales por mensaje).
4. `app.py` valida y delega en `ollama_client.chat_image()`, que llama a
   `/api/chat` de Ollama y devuelve `(respuesta, timing)`.
5. El historial se conserva en `sessionStorage` del navegador (sin estado en el
   servidor) y se reenvía completo en cada turno.

## Decisiones clave (ADR resumido)

| Decisión | Opción | Motivo |
|---|---|---|
| **Estado de conversaciones** | `sessionStorage` en el navegador | Sin estado en servidor; funciona igual en `.exe`; privacidad (se limpia al cerrar la pestaña). Límite ~5 MB → máx. 10 chats, compresión de imágenes en cliente. |
| **Imágenes** | Base64 inline por mensaje + compresión `<canvas>` (máx 1024px, JPEG q0.8) | El modelo de visión necesita verlas; la compresión evita llenar sessionStorage y reduce payload. |
| **Markdown** | `marked` + `DOMPurify` (sanitizado) | Respuestas ricas del modelo sin riesgo de XSS. |
| **Servidor** | Flask + **waitress** (WSGI) | Robusto para local y para el `.exe`; evita el dev server de Werkzeug. |
| **CDNs** | Tailwind, Phosphor, Google Fonts, marked, DOMPurify (versiones fijadas) | Diseño sin build-step; se cachean en el navegador. **Requiere internet en la primera carga.** |
| **Configuración** | `config.py` centralizado | Un solo lugar para modelos, puertos, límites y timeouts. |
| **Modelos disponibles** | `GET /api/models` (desde `config.MODEL_META`) | El frontend renderiza los `<option>` dinámicamente → sin duplicación. |
| **Mockups (HTML/CSS)** | Pestaña Mockups → `POST /api/mockup` → `ollama_client.generate_code()` con `qwen2.5-coder:3b` | Herramienta de codificación IA de respaldo; modelo de texto dedicado (`MOCKUP_MODEL`), no aparece en el selector de visión. Preview en `<iframe sandbox="allow-scripts">`. |
| **Reiniciar/Detener** | Subproceso desacoplado por PID (por plataforma) | Evita matar el propio helper; funciona en Linux/WSL2 y Windows (.exe). |
| **Distribución Windows** | PyInstaller `--onefile` (`ImageDescripter.exe`) | Sin Python en la máquina destino; empaqueta `templates/` y `static/`. |

## Tecnologías

- **Backend**: Python 3.11+, Flask 3, waitress, requests, Pillow, psutil.
- **Frontend**: HTML + Tailwind (CDN), Phosphor Icons, Inter/JetBrains Mono, `marked`, `DOMPurify`.
- **IA**: Ollama local (visión: `qwen2.5vl:3b`, `gemma3:4b`; código: `qwen2.5-coder:3b`).
- **Pruebas**: pytest (test client de Flask + monkeypatch, sin red).
- **Opcional**: Docker Compose (app + ollama), Makefile.

## Rama `webgpu`

Variante alternativa que ejecuta el modelo en el navegador con WebGPU
(sin servidor de IA). La arquitectura documentada aquí corresponde a `main`.