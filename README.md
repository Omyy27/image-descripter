# Image Descripter

Mini app web que recibe una imagen y un texto de contexto, y genera una descripción con un modelo de visión local (**Ollama**). Sin API keys, sin costos y 100 % local: las imágenes no salen de tu máquina.

## Características

- **2 modelos de visión** elegibles desde la interfaz: `qwen2.5vl:3b` (mejor calidad) y `gemma3:4b` (ligero).
- **Contexto libre**: escribe qué quieres que destaque la descripción.
- **Controles del servidor** en la propia UI: recargar modelo, reiniciar servidor y detener procesos.
- **Lanzadores de un clic**: WSL2 (`run.sh` / `start.bat`) y Windows nativo (`.exe`).
- **Privacidad**: todo el procesamiento es local; no requiere internet ni API keys.

## Requisitos

- Linux/WSL2 o Windows.
- [Ollama](https://ollama.com) instalado con los modelos de visión `qwen2.5vl:3b` y `gemma3:4b`.
- Python 3.10+ (solo para desarrollo y para compilar el `.exe`).
- ~4 GB de RAM libre para el modelo `qwen2.5vl:3b`.

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

1. **Sube una imagen** (clic o arrástrala).
2. **Escribe un contexto** (opcional), por ejemplo:
   *"describe este producto para una tienda online, destacando colores y qué sensación transmite"*.
3. **Elige el modelo** en el desplegable.
4. Pulsa **Describir imagen**.

### Controles del servidor

En la parte inferior de la página:

| Botón | Qué hace |
|---|---|
| **Recargar modelo** | Pre-carga el modelo elegido en memoria (acelera la primera descripción). |
| **Reiniciar servidor** | Detiene y relanza la app automáticamente. |
| **Detener procesos** | Detiene la app (Ollama sigue corriendo). Relánzala con `run.sh` / `start_windows.bat`. |

## Configuración

- El modelo por defecto es `qwen2.5vl:3b`; cámbialo con la variable de entorno `OLLAMA_MODEL`:

  ```bash
  OLLAMA_MODEL=gemma3:4b .venv/bin/python app.py
  ```

- Para añadir otro modelo: `ollama pull <modelo>` y agrégalo a `AVAILABLE_MODELS` en `ollama_client.py`.
- La app escucha en `0.0.0.0:5000`; en Windows nativo liga a `127.0.0.1` (solo acceso local).

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

## Estructura

```
read-image-ai/
├── app.py                 # Servidor Flask + endpoints
├── ollama_client.py       # Cliente de la API local de Ollama
├── templates/
│   └── index.html         # Interfaz web
├── run.sh                 # Lanzador WSL2 (arranca Ollama, modelo y app)
├── start.bat              # Doble clic desde Windows (WSL2) + abre el navegador
├── build_windows.bat      # Compila el .exe con PyInstaller (en Windows)
├── start_windows.bat      # Lanzador Windows nativo (Ollama + .exe + navegador)
└── requirements.txt
```

## Solución de problemas

- **El modelo no aparece tras transferirlo**: vuelve a instalarlo con
  `ollama pull qwen2.5vl:3b` / `ollama pull gemma3:4b`.
- **Puerto 5000 ocupado**: detén lo que lo use o cambia el puerto en `app.py` (`app.run(..., port=5000)`).
- **La app se detuvo**: relánzala con `./run.sh` (WSL2) o `start_windows.bat` (Windows).
- **La primera descripción tarda**: el modelo se está cargando en memoria; usa **Recargar modelo**
  para pre-cargarlo.

## Ramas

- **`main`** — versión Flask + Ollama (la que documenta este README).
- **`webgpu`** — versión alternativa que corre el modelo en el navegador con WebGPU (sin servidor de IA).
