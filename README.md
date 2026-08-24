# Image Descripter

Mini app web que **conversa con un modelo de visión local (Ollama)** sobre tus imágenes: súbela, pregúntale lo que quieras y mantén un hilo de conversación. Sin API keys ni costos; las imágenes se procesan en tu máquina.

## Características

- **Chat multi-turno** con 2 modelos de visión elegibles desde el header: `qwen2.5vl:3b` (mejor calidad) y `gemma3:4b` (ligero).
- **Adjunta imágenes en cualquier momento** del chat (se comprimen en el navegador antes de enviarse).
- **Conversaciones guardadas temporalmente** en `sessionStorage` del navegador (hasta 10, con panel lateral y buscador).
- **Respuestas con markdown** (listas, código, tablas) y **tiempo de respuesta** del modelo (total + evaluación).
- **Controles del servidor** en el header (recargar modelo, reiniciar, detener) y **estadísticas en vivo** (uptime, CPU, RAM, modelo).
- **Lanzadores de un clic**: WSL2 (`run.sh` / `start.bat`) y Windows nativo (`.exe`).
- **Privacidad**: el modelo corre localmente; las imágenes no salen de tu máquina.

## Requisitos

- Linux/WSL2 o Windows.
- [Ollama](https://ollama.com) instalado con los modelos de visión `qwen2.5vl:3b` y `gemma3:4b`.
- Python 3.10+ (solo para desarrollo y para compilar el `.exe`).
- ~4 GB de RAM libre para el modelo `qwen2.5vl:3b`.
- **Internet en la primera carga**: los estilos e iconos (Tailwind, Phosphor, Google Fonts) y las librerías de markdown (`marked`, `DOMPurify`) se cargan desde CDN.

## Inicio rápido

### WSL2 (navegador en Windows)

```bash
./run.sh
```

o doble clic en `start.bat` desde Windows (arranca Ollama, la app y abre el navegador).

### Windows nativo (sin WSL)

1. Instala Ollama en Windows: https://ollama.com/download
2. Descarga los modelos: `ollama pull qwen2.5vl:3b` y `ollama pull gemma3:4b`
3. Doble clic en `build_windows.bat` → genera `dist\ImageDescripter.exe`
4. Doble clic en `start_windows.bat`

## Uso

Abre http://localhost:5000 y:

1. **Panel lateral**: elige una conversación guardada, búscalas o pulsa **"+ Nueva conversación"**.
2. **Estado vacío**: sube una imagen (opcional), escribe un mensaje inicial o contexto y pulsa **Iniciar chat**. Sin imagen también puedes conversar solo con texto.
3. **En el chat**:
   - Escribe en la barra inferior y pulsa Enter/Enviar.
   - Adjunta imágenes con el **paperclip** (aparecen como miniaturas antes de enviar).
   - Usa los **chips** rápidos ("Describe la imagen", "Genera HTML", "Extrae texto") para rellenar el mensaje.
   - Cambia el **modelo** desde el selector del header (aplica a los turnos siguientes de la misma conversación).
   - Cada respuesta muestra su **tiempo** junto a la hora: `· 17.2 s · eval 1.3 s`.

### Controles del servidor

Icono de **servidor** (`ph-server`) en el header:

| Acción | Qué hace |
|---|---|
| **Recargar modelo** | Pre-carga el modelo elegido en memoria (acelera la primera respuesta). |
| **Reiniciar servidor** | Detiene y relanza la app automáticamente (la página se recarga). |
| **Detener procesos** | Detiene la app (Ollama sigue corriendo). Relánzala con `run.sh` / `start_windows.bat`. |

El panel inferior de la card muestra **estadísticas en vivo**: uptime, CPU, RAM y modelo activo (refresco cada ~4 s).

## Configuración

- El modelo por defecto es `qwen2.5vl:3b`; cámbialo con la variable de entorno `OLLAMA_MODEL`:

  ```bash
  OLLAMA_MODEL=gemma3:4b .venv/bin/python app.py
  ```

- Para añadir otro modelo: `ollama pull <modelo>` y agrégalo a `AVAILABLE_MODELS` en `ollama_client.py`.
- La app escucha en `0.0.0.0:5000` (variable `APP_HOST`); en Windows nativo liga a `127.0.0.1` (solo acceso local).

## Windows nativo (paso a paso)

### 1. Copiar el proyecto
Copia la carpeta desde WSL2:
`\\wsl$\Ubuntu\home\<tu_usuario>\agentic\read-image-ai` → `C:\Users\<tu_usuario>\read-image-ai`
No hace falta copiar `.venv`, `.logs` ni `__pycache__`.

### 2. Instalar Ollama en Windows
Descárgalo de https://ollama.com/download (app de bandeja en `127.0.0.1:11434`).

### 3. Transferir los modelos (sin re-descargar)
Copia estas carpetas de WSL2:
- `\\wsl$\Ubuntu\home\<tu_usuario>\.local\ollama\models\manifests`
- `\\wsl$\Ubuntu\home\<tu_usuario>\.local\ollama\models\blobs`

a `C:\Users\<tu_usuario>\.ollama\models\` (crea la carpeta si no existe).

Verifica con `ollama list` → deben aparecer `qwen2.5vl:3b` y `gemma3:4b`.
Si no los detecta (versión distinta de Ollama), alternativa: `ollama pull qwen2.5vl:3b` y `ollama pull gemma3:4b`.

### 4. Compilar el ejecutable
Doble clic en `build_windows.bat` → genera `dist\ImageDescripter.exe`
(requiere Python 3.13 con "Add to PATH"). El `.exe` no necesita Python para ejecutarse.

### 5. Usar
Doble clic en `start_windows.bat` → arranca Ollama si hace falta, lanza la app y abre
`http://localhost:5000` en el navegador.

## Endpoints

| Ruta | Método | Descripción |
|---|---|---|
| `/` | GET | Interfaz web |
| `/api/chat` | POST | Chat multi-turno (`model`, `messages` con `images` opcional); devuelve `reply` + `timing` |
| `/api/stats` | GET | `uptime`, `cpu`, `ram`, `ollama` |
| `/api/reload-model` | POST | Pre-carga el modelo en memoria |
| `/api/restart` | POST | Reinicia la app |
| `/api/stop` | POST | Detiene la app (Ollama sigue) |
| `/describe` | POST | Descripción de una sola pasada (legacy) |

## Estructura

```
read-image-ai/
├── app.py                 # Servidor Flask + endpoints
├── ollama_client.py       # Cliente de la API local de Ollama (chat, describe, warm)
├── templates/
│   └── index.html         # Interfaz web (Tailwind + Phosphor + markdown)
├── run.sh                 # Lanzador WSL2 (arranca Ollama, modelo y app)
├── start.bat              # Doble clic desde Windows (WSL2) + abre el navegador
├── build_windows.bat      # Compila el .exe con PyInstaller (en Windows)
├── start_windows.bat      # Lanzador Windows nativo (Ollama + .exe + navegador)
└── requirements.txt       # flask, requests, pillow, psutil
```

## Solución de problemas

- **El modelo no aparece tras transferirlo**: vuelve a instalarlo con
  `ollama pull qwen2.5vl:3b` / `ollama pull gemma3:4b`.
- **Puerto 5000 ocupado**: detén lo que lo use o cambia el puerto en `app.py` (`app.run(..., port=5000)`).
- **La app se detuvo**: relánzala con `./run.sh` (WSL2) o `start_windows.bat` (Windows).
- **La interfaz se ve sin estilos**: falta internet (los CDNs no cargaron); reconéctate y recarga.
- **La primera respuesta tarda**: el modelo se está cargando en memoria; usa **Recargar modelo** para pre-cargarlo.

## Ramas

- **`main`** — versión Flask + Ollama con chat (la que documenta este README).
- **`webgpu`** — versión alternativa que corre el modelo en el navegador con WebGPU (sin servidor de IA).