@echo off
title Image Descripter
echo ============================================
echo  Image Descripter (Flask + Ollama)
echo ============================================
echo.
echo Arrancando la app dentro de WSL2...
echo.
wsl -e bash -lc "cd ~/agentic/read-image-ai && bash run.sh"
echo.
echo Esperando a que el servidor esté listo...
timeout /t 6 /nobreak >nul
start "" http://localhost:5000
echo.
echo Listo. La app sigue corriendo aunque cierres esta ventana.
echo Para detenerla: cierra Ollama y mata el proceso de la app en WSL2.
echo.
pause
