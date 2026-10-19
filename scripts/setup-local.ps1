$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { python -m venv .venv }
    & '.\.venv\Scripts\python.exe' -m pip install -r backend/requirements-dev.lock
    if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación de Python' }
    Push-Location frontend
    try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Falló npm ci' } } finally { Pop-Location }
    Write-Host 'Entorno local preparado. Ver README.md para ejecutar y comprobar.'
} finally { Pop-Location }
