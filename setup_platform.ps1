<#
.SYNOPSIS
    Panamá PortOps-AI v2.0 — Setup MLOps Open-Source Soberano & Orchestrator
.DESCRIPTION
    Profiles host hardware (CPU, RAM, NVIDIA GPU RTX 3050), checks Administrator privileges,
    prompts for UAC elevation if desired, establishes Lakehouse medallion layers, Gobernanza RBAC,
    and validates the 8-algorithm ML tournament.
.AUTHOR
    Desarrollado v1.0 Miguel Benítez
.LICENSE
    GNU General Public License v3.0 (GPL-3.0)
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "   🚢 PANAMÁ PORTOPS-AI v2.0 — INSTALADOR Y ORQUESTADOR MLOPS SOBERANO" -ForegroundColor Cyan
Write-Host "   Autor: Desarrollado v1.0 Miguel Benítez | Licencia: GNU GPL-3.0" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "[✓] Ejecutando con Privilegios Elevados de Administrador." -ForegroundColor Green
    python scripts/bootstrap_platform.py --user-mode
} else {
    Write-Host "[i] Ejecutando en Modo Usuario Estándar." -ForegroundColor Yellow
    Write-Host "¿Desea solicitar elevación de permisos de Administrador vía UAC?" -ForegroundColor White
    Write-Host "(Recomendado para optimización de puertos y aceleración de hardware)" -ForegroundColor Gray
    
    $elevateChoice = Read-Host "¿Solicitar Administrador? (S/N, Enter para Modo Seguro Usuario)"
    if ($elevateChoice -match "^[sSyY]") {
        Write-Host "Solicitando elevación UAC a Windows..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "scripts/bootstrap_platform.py --elevate" -Verb RunAs
        exit
    } else {
        python scripts/bootstrap_platform.py --user-mode
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Se produjo un fallo durante la inicialización." -ForegroundColor Red
    Read-Host "Presione Enter para salir"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "¿Desea iniciar los servicios de la plataforma ahora?" -ForegroundColor White
Write-Host "1. Iniciar Servidor API REST / MCP (FastAPI en puerto 8000)"
Write-Host "2. Iniciar Estación de Control Ejecutivo (Streamlit en puerto 8501)"
Write-Host "3. Iniciar Ambos Servicios en ventanas independientes"
Write-Host "4. Salir"
Write-Host "================================================================================" -ForegroundColor Cyan
$startChoice = Read-Host "Seleccione una opción (1-4)"

switch ($startChoice) {
    "1" { Start-Process python -ArgumentList "-m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000" }
    "2" { Start-Process streamlit -ArgumentList "run apps/dashboard.py" }
    "3" {
        Start-Process python -ArgumentList "-m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000"
        Start-Sleep -Seconds 2
        Start-Process streamlit -ArgumentList "run apps/dashboard.py"
    }
    default { Write-Host "[✓] Plataforma lista. Puede iniciar los servicios manualmente cuando lo desee." -ForegroundColor Green }
}
