@echo off
setlocal
title Describir imagen con IA

echo ============================================
echo  Describir imagen con IA (Windows)
echo ============================================
echo.

REM --- Asegurar que Ollama este corriendo ---
curl -s -o nul http://127.0.0.1:11434/api/tags
if not errorlevel 1 (
    echo [ok] Ollama ya esta corriendo (127.0.0.1:11434)
) else (
    echo [..] Ollama no esta corriendo. Iniciandolo...
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" app.exe
    ) else (
        start "" ollama app.exe
    )
    timeout /t 4 /nobreak >nul
)

REM --- Lanzar la app ---
if not exist "dist\DescribirImagenIA.exe" (
    echo [!] No se encontro dist\DescribirImagenIA.exe
    echo     Compilalo primero ejecutando build_windows.bat
    pause
    exit /b 1
)
set APP_HOST=127.0.0.1
start "" "dist\DescribirImagenIA.exe"

REM --- Esperar a que responda ---
echo [..] Esperando a que el servidor este listo...
set /a tries=0
:waitloop
curl -s -o nul http://127.0.0.1:5000/
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% geq 40 (
    echo [!] La app no responde a tiempo. Revisa si algo ocupa el puerto 5000.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto waitloop

:ready
echo [ok] App lista.
start "" http://localhost:5000
echo.
echo Listo. Puedes cerrar esta ventana, la app seguira corriendo.
pause
