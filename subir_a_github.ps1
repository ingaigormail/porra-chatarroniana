# Sube la app de producción a GitHub: ingaigormail/porra-chatarroniana
# Ejecutar desde PowerShell en C:\mundial_app_nueva:
#   Set-ExecutionPolicy -Scope Process Bypass; .\subir_a_github.ps1

$ErrorActionPreference = "Stop"
$repoUrl = "https://github.com/ingaigormail/porra-chatarroniana.git"
$rama = "main"

# Buscar git
$git = $null
foreach ($p in @(
    "git",
    "$env:ProgramFiles\Git\cmd\git.exe",
    "$env:LocalAppData\Programs\Git\cmd\git.exe"
)) {
    if (Get-Command $p -ErrorAction SilentlyContinue) {
        $git = (Get-Command $p).Source
        break
    }
}
if (-not $git) {
    Write-Host ""
    Write-Host "ERROR: Git no esta instalado." -ForegroundColor Red
    Write-Host "Instala Git desde: https://git-scm.com/download/win"
    Write-Host "O instala GitHub Desktop: https://desktop.github.com/"
    Write-Host ""
    exit 1
}

Write-Host "Usando Git: $git" -ForegroundColor Green
Set-Location $PSScriptRoot

# Init si hace falta
if (-not (Test-Path ".git")) {
    & $git init
    & $git branch -M $rama
}

# Remote
$remotes = & $git remote 2>$null
if ($remotes -notcontains "origin") {
    & $git remote add origin $repoUrl
} else {
    & $git remote set-url origin $repoUrl
}

# Solo archivos de produccion
& $git add app.py requirements.txt runtime.txt .gitignore
& $git add .streamlit/config.toml
& $git add src/ utils/ config/

# Quitar secretos por si acaso
& $git reset .streamlit/secrets.toml 2>$null

$status = & $git status --porcelain
if (-not $status) {
    Write-Host "No hay cambios que subir." -ForegroundColor Yellow
} else {
    & $git commit -m "App nueva Mundial 2026 Chatarronianos - produccion"
}

Write-Host ""
Write-Host "Descargando historial remoto..." -ForegroundColor Cyan
& $git fetch origin 2>$null

# Intentar integrar con lo que ya hay en GitHub
$remoteBranch = "origin/$rama"
$hasRemote = & $git rev-parse --verify $remoteBranch 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Integrando con rama remota existente..." -ForegroundColor Cyan
    & $git pull origin $rama --allow-unrelated-histories --no-edit 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Conflicto al mezclar. Usando version local (app nueva)..." -ForegroundColor Yellow
        & $git checkout --ours app.py 2>$null
        & $git add app.py src/ utils/ config/ requirements.txt runtime.txt .gitignore .streamlit/config.toml
        & $git commit -m "App nueva Mundial 2026 - reemplaza version anterior" 2>$null
    }
}

Write-Host ""
Write-Host "Subiendo a GitHub..." -ForegroundColor Cyan
Write-Host "(Si pide login, usa tu cuenta ingaigormail en el navegador)" -ForegroundColor Gray
& $git push -u origin $rama

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "LISTO. Codigo subido a:" -ForegroundColor Green
    Write-Host "  https://github.com/ingaigormail/porra-chatarroniana"
    Write-Host ""
    Write-Host "Streamlit redeployara en 1-3 min en:"
    Write-Host "  https://chatarronianos.streamlit.app/"
    Write-Host ""
    Write-Host "Verifica Secrets en share.streamlit.io (Supabase url + key)" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "El push fallo. Suele ser autenticacion." -ForegroundColor Red
    Write-Host "1. Instala GitHub Desktop e inicia sesion como ingaigormail"
    Write-Host "2. O ejecuta: git config credential.helper manager"
    Write-Host "3. Vuelve a ejecutar este script"
}
