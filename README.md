# Image Descripter

Mini app web que **conversa con un modelo de visión local (Ollama)** sobre tus imágenes: súbela, pregúntale lo que quieras y mantén un hilo de conversación. Sin API keys ni costos; las imágenes se procesan en tu máquina.

## Características

- **Chat multi-turno** con 3 modelos elegibles desde el selector del header: `qwen2.5vl:3b` (mejor calidad), `gemma3:4b` (ligero) y `qwen2.5-coder:3b` (código · sin visión).
- **Adjunta imágenes en cualquier momento** del chat (se comprimen en el navegador antes de enviarse).
- **Conversaciones guardadas temporalmente** en `sessionStorage` del navegador (hasta 10, con panel lateral y buscador).
- **Respuestas con markdown** (listas, código, tablas) y **tiempo de respuesta** del modelo (total + evaluación).
- **Controles del servidor** en el header (recargar modelo, reiniciar, detener) y **estadísticas en vivo** (uptime, CPU, RAM, modelo).
- **Generador de mockups**: en la pestaña **Mockups** describe un diseño y el modelo de código local (`qwen2.5-coder:3b`) genera un HTML/CSS funcional con vista previa y opciones Copiar / Descargar / Abrir.
- **Lanzadores de un clic**: WSL2 (`run.sh` / `start.bat`) y Windows nativo (`.exe`).
- **Privacidad**: el modelo corre localmente; las imágenes no salen de tu máquina.

## Requisitos

- Linux/WSL2 o Windows.
- [Ollama](https://ollama.com) instalado con los modelos de visión `qwen2.5vl:3b` y `gemma3:4b`.
- Opcional para Mockups: `ollama pull qwen2.5-coder:3b` (~2 GB).
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
| **Descargar modelo** | Libera el modelo de la memoria de Ollama (libera la RAM). |
| **Reiniciar servidor** | Detiene y relanza la app automáticamente (la página se recarga). |
| **Detener procesos** | Detiene la app (Ollama sigue corriendo). Relánzala con `run.sh` / `start_windows.bat`. |

El panel inferior de la card muestra **estadísticas en vivo**: uptime, CPU, RAM y modelo activo (refresco cada ~4 s).

### Generar mockups (HTML/CSS)

Pestaña **Mockups** (arriba de la card): una herramienta de codificación IA de respaldo con el modelo de texto `qwen2.5-coder:3b`.

1. Escribe el diseño que quieres (o usa los chips de ejemplo) y pulsa **Generar mockup**.
2. El modelo devuelve un HTML/CSS autocontenido que se previsualiza en un `<iframe>` aislado (`sandbox`).
3. Con **Copiar HTML**, **Descargar .html** o **Abrir en pestaña** te llevas el mockup.

Notas:
- Requiere el modelo: `ollama pull qwen2.5-coder:3b` (opcional, solo si quieres usar Mockups o el selector).
- Es un modelo de **texto** (no ve imágenes): si lo eliges en el selector y lo usas con imágenes, la app avisa "Este modelo no ve imágenes".
- Cámbialo con la variable de entorno `OLLAMA_MOCKUP_MODEL`.
- Usa **Descargar modelo** del header para liberar su RAM al terminar (libera los dos modelos).

## Optimizar el uso de RAM

El modelo de visión cargado por Ollama ocupa varios GB de RAM. Consejos:

- **Descargar modelo** (botón del header) libera la memoria al instante cuando termines (descarga el modelo de visión y el de mockup).
- El modelo se queda en RAM un máximo de **5 minutos** sin uso (configurable con
  `OLLAMA_KEEP_ALIVE`, ej. `OLLAMA_KEEP_ALIVE=2m` o `0` para descargar al instante).
- Si ves el aviso de **RAM alta** (superior al 90 %), usa "Descargar modelo" o cierra otros programas.
- Si el modelo no puede cargarse por falta de memoria, la app muestra un mensaje claro
  (no un error 500) indicándote que liberes RAM.

## Configuración

- El modelo por defecto es `qwen2.5vl:3b`; cámbialo con la variable de entorno `OLLAMA_MODEL`:

  ```bash
  OLLAMA_MODEL=gemma3:4b .venv/bin/python app.py
  ```

- Para añadir otro modelo: `ollama pull <modelo>` y agrégalo a `MODEL_META` en `config.py`
  (el frontend lo muestra automáticamente vía `GET /api/models`).
- El modelo de mockups es `qwen2.5-coder:3b`; cámbialo con `OLLAMA_MOCKUP_MODEL`.
- La app escucha en `0.0.0.0:5000` (variables `APP_HOST`/`PORT`); en Windows nativo liga a `127.0.0.1` (solo acceso local).
- Si Ollama no está en `localhost:11434`, usa la variable `OLLAMA_HOST` (ej. `OLLAMA_HOST=http://192.168.1.10:11434`).

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
| `/api/models` | GET | Modelos disponibles (`[{value, label}]`) |
| `/api/chat` | POST | Chat multi-turno (`model`, `messages` con `images` opcional); devuelve `reply` + `timing` |
| `/api/stats` | GET | `uptime`, `cpu`, `ram`, `ollama` |
| `/api/reload-model` | POST | Pre-carga el modelo en memoria |
| `/api/restart` | POST | Reinicia la app |
| `/api/stop` | POST | Detiene la app (Ollama sigue) |
| `/describe` | POST | Descripción de una sola pasada (legacy) |

## Estructura

```
read-image-ai/
├── app.py                 # Servidor Flask + endpoints (sirve con waitress)
├── ollama_client.py       # Cliente de la API local de Ollama (chat, describe, warm, ping)
├── config.py              # Configuración centralizada (modelos, puerto, límites, timeouts)
├── image_utils.py         # Pipeline de imágenes (redimensionar + base64)
├── templates/
│   └── index.html         # Markup de la interfaz (Tailwind + Phosphor + markdown)
├── static/
│   ├── app.js             # Lógica del frontend (chats, adjuntar, stats)
│   └── style.css          # Estilos propios
├── tests/
│   └── test_app.py        # Tests de endpoints y lógica (pytest)
├── docs/
│   └── architecture.md    # Arquitectura y decisiones (diagrama Mermaid)
├── run.sh                 # Lanzador WSL2 (arranca Ollama, modelo y app)
├── start.bat              # Doble clic desde Windows (WSL2) + abre el navegador
├── build_windows.bat      # Compila el .exe con PyInstaller (en Windows)
├── start_windows.bat      # Lanzador Windows nativo (Ollama + .exe + navegador)
├── Dockerfile             # Imagen de la app (opcional)
├── docker-compose.yml     # App + Ollama (opcional)
├── Makefile               # Atajos: make run / make test / make clean
└── requirements.txt       # Dependencias con versiones fijadas
```

## Desarrollo

```bash
# Tests
make test                  # o: .venv/bin/python -m pytest tests/

# Limpiar artefactos
make clean
```

### Docker (opcional)

```bash
docker compose up --build   # levanta Ollama + app en http://localhost:5000
```

> Nota: en Docker la app apunta a `OLLAMA_HOST=http://ollama:11434` (el contenedor de Ollama).

## Solución de problemas

- **El modelo no aparece tras transferirlo**: vuelve a instalarlo con
  `ollama pull qwen2.5vl:3b` / `ollama pull gemma3:4b`.
- **Puerto 5000 ocupado**: detén lo que lo use o cambia `PORT` en `config.py`.
- **La app se detuvo**: relánzala con `./run.sh` (WSL2) o `start_windows.bat` (Windows).
- **La interfaz se ve sin estilos**: falta internet (los CDNs no cargaron); reconéctate y recarga.
- **La primera respuesta tarda**: el modelo se está cargando en memoria; usa **Recargar modelo** para pre-cargarlo.

## Ramas

- **`main`** — versión Flask + Ollama con chat (la que documenta este README).
- **`webgpu`** — versión alternativa que corre el modelo en el navegador con WebGPU (sin servidor de IA).