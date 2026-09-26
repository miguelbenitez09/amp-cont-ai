@echo off
chcp 65001 >nul
title Panamá PortOps-AI v2.0 — Setup MLOps Open-Source Soberano

echo ================================================================================
echo    🚢 PANAMÁ PORTOPS-AI v2.0 — INSTALADOR Y ORQUESTADOR MLOPS SOBERANO
echo    Autor: Desarrollado v1.0 Miguel Benítez ^| Licencia: GNU GPL-3.0
echo ================================================================================
echo.

:: Verificar privilegios de administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] Ejecutando con Privilegios Elevados de Administrador.
    goto RUN_BOOTSTRAP
) else (
    echo [i] Ejecutando en Modo Usuario Estándar.
    echo.
    echo ¿Desea solicitar elevación de permisos de Administrador vía UAC?
    echo (Recomendado para optimización de puertos y aceleración de hardware)
    echo.
    set /p ELEVATE_CHOICE="¿Solicitar Administrador? (S/N, Enter para Modo Seguro Usuario): "
)

if /i "%ELEVATE_CHOICE%"=="S" (
    echo.
    echo Solicitando elevación UAC a Windows...
    powershell -Command "Start-Process python -ArgumentList 'scripts/bootstrap_platform.py --elevate' -Verb RunAs"
    exit /b 0
)

:RUN_BOOTSTRAP
echo.
echo Iniciando Orquestador Plataforma MLOps Open-Source...
python scripts/bootstrap_platform.py --user-mode

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Se produjo un fallo durante la inicialización.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo ¿Desea iniciar los servicios de la plataforma ahora?
echo 1. Iniciar Servidor API REST / MCP (FastAPI en puerto 8000)
echo 2. Iniciar Estación de Control Ejecutivo (Streamlit en puerto 8501)
echo 3. Iniciar Ambos Servicios en ventanas independientes
echo 4. Salir
echo ================================================================================
set /p START_CHOICE="Seleccione una opción (1-4): "

if "%START_CHOICE%"=="1" (
    start "Panamá PortOps-AI API (8000)" python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
)
if "%START_CHOICE%"=="2" (
    start "Panamá PortOps-AI Streamlit (8501)" streamlit run apps/dashboard.py
)
if "%START_CHOICE%"=="3" (
    start "Panamá PortOps-AI API (8000)" python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
    timeout /t 2 /nobreak >nul
    start "Panamá PortOps-AI Streamlit (8501)" streamlit run apps/dashboard.py
)

echo.
echo [✓] Operación completada. Plataforma lista.
pause
