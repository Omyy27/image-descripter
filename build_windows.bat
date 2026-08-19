@echo off
setlocal
title Compilar DescribirImagenIA.exe

echo ============================================
echo  Compilando DescribirImagenIA.exe (PyInstaller)
echo ============================================
echo.

REM Elegir lanzador de Python (py o python)
set PY=python
where py >nul 2>nul
if %errorlevel%==0 set PY=py

REM Crear venv si no existe
if not exist ".venv\Scripts\python.exe" (
    echo [..] Creando entorno virtual...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [!] No se pudo crear el venv. Revisa tu instalacion de Python.
        pause
        exit /b 1
    )
)

echo [..] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [!] Error instalando dependencias.
    pause
    exit /b 1
)

echo [..] Compilando (tarda unos minutos)...
".venv\Scripts\python.exe" -m PyInstaller --onefile --name DescribirImagenIA --add-data "templates;templates" app.py
if errorlevel 1 (
    echo [!] Error al compilar.
    pause
    exit /b 1
)

echo.
echo  [OK] Ejecutable generado: dist\DescribirImagenIA.exe
echo.
pause
