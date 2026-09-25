# scripts/deploy_github.ps1
# Script interactivo de despliegue y auditoría de higiene para GitHub
# Autor: Desarrollado v1.0 Miguel Benítez

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   PANAMÁ PORTOPS-AI v1.0: DESPLIEGUE SEGURO EN GITHUB                " -ForegroundColor Green
Write-Host "   Autor: Miguel Benítez (mbeni) | Desarrollado v1.0 Miguel Benítez   " -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Verificar si git está instalado
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git no está instalado o no se encuentra en el PATH." -ForegroundColor Red
    exit 1
}

# 2. Verificar o inicializar repositorio local
if (-not (Test-Path .git)) {
    Write-Host "[1/5] Inicializando repositorio Git local..." -ForegroundColor Cyan
    git init
} else {
    Write-Host "[1/5] Repositorio Git ya inicializado." -ForegroundColor Green
}

# 3. Validar higiene estricta: datasets y modelos excluidos
Write-Host "[2/5] Validando reglas de exclusión en .gitignore..." -ForegroundColor Cyan
$sampleDataIgnored = git check-ignore data/raw/sample.csv 2>$null
$modelIgnored = git check-ignore models/champion_models.joblib 2>$null

if ($sampleDataIgnored -and $modelIgnored) {
    Write-Host "   -> ÉXITO: Datasets (*.csv, *.parquet) y binarios (*.joblib) están correctamente excluidos." -ForegroundColor Green
} else {
    Write-Host "   -> [ADVERTENCIA] Verifica el archivo .gitignore antes de continuar." -ForegroundColor Yellow
}

# 4. Agregar archivos al Staging Area
Write-Host "[3/5] Preparando archivos en el Staging Area (git add .)..." -ForegroundColor Cyan
git add .

# 5. Crear Commit inicial si no hay commits previos
$commitCount = git rev-list --count HEAD 2>$null
if (-not $commitCount -or $commitCount -eq 0) {
    Write-Host "[4/5] Creando commit maestro inicial..." -ForegroundColor Cyan
    $commitMsg = "feat(core): initial release panama-portops-ai v1.0 - MLOps, multi-algorithm benchmark and stochastic simulation"
    git commit -m $commitMsg
} else {
    Write-Host "[4/5] Commit previo detectado. Verificando cambios pendientes..." -ForegroundColor Cyan
    $status = git status --porcelain
    if ($status) {
        git commit -m "chore(update): sync documentation, CI security workflow and deployment scripts"
    } else {
        Write-Host "   -> Árbol de trabajo limpio, nada pendiente por commitear." -ForegroundColor Green
    }
}

# 6. Configurar rama principal main
git branch -M main

# 7. Configuración del Remote Origin
Write-Host "[5/5] Configurando repositorio remoto en GitHub..." -ForegroundColor Cyan
$remotes = git remote -v
if (-not $remotes) {
    Write-Host "No se ha configurado el repositorio remoto 'origin'." -ForegroundColor Yellow
    $defaultRepo = "https://github.com/miguelbenitez09/amp-cont-ai.git"
    $userRepo = Read-Host "Ingresa la URL de tu repositorio GitHub (Presiona ENTER para '$defaultRepo')"
    if (-not $userRepo) {
        $userRepo = $defaultRepo
    }
    git remote add origin $userRepo
    Write-Host "   -> Remote 'origin' configurado hacia: $userRepo" -ForegroundColor Green
} else {
    Write-Host "   -> Remote 'origin' ya configurado:" -ForegroundColor Green
    git remote -v
}

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "   LISTO PARA EL PUSH A GITHUB                                        " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "Para subir tu código de forma segura, ejecuta:" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host "`n(Git Credential Manager abrirá una ventana de inicio de sesión seguro si es necesario)" -ForegroundColor Gray
