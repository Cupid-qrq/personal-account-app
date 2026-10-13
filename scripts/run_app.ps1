param([switch]$SkipInstall, [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$ledgerRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ledgerRoot
try {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        python -m venv .venv
        if ($LASTEXITCODE) { throw 'Python environment creation failed.' }
    }
    $ledgerPython = Join-Path $ledgerRoot '.venv\Scripts\python.exe'
    if (-not $SkipInstall) {
        & $ledgerPython -m pip install -r requirements.txt
        if ($LASTEXITCODE) { throw 'Python dependency installation failed.' }
        npm ci --prefix frontend
        if ($LASTEXITCODE) { throw 'Frontend dependency installation failed.' }
    }
    if (-not $SkipBuild) {
        npm run build --prefix frontend
        if ($LASTEXITCODE) { throw 'Frontend build failed.' }
    }
    & $ledgerPython scripts\rebuild_atlas.py
    if ($LASTEXITCODE) { throw 'Ledger rebuild failed.' }
    & $ledgerPython scripts\validate_atlas.py
    if ($LASTEXITCODE) { throw 'Ledger validation failed.' }
    Write-Host 'Ledger Atlas: http://localhost:8000'
    & $ledgerPython server.py
} finally {
    Pop-Location
}
