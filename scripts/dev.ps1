param([switch]$Seed)
$ErrorActionPreference = 'Stop'
$fattechRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $fattechRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    uv venv --python 3.12 .venv
    uv pip install --python .venv/Scripts/python.exe -r apps/api/requirements.txt
}
$env:PYTHONPATH = Join-Path $fattechRoot 'apps/api'
$env:FATTECH_DATABASE_URL = 'sqlite:///' + (Join-Path $fattechRoot '.local/dev.db').Replace('\','/')
$env:FATTECH_ENV = 'development'
$env:FATTECH_BOOTSTRAP_EMAIL = if ($env:FATTECH_BOOTSTRAP_EMAIL) { $env:FATTECH_BOOTSTRAP_EMAIL } else { 'admin@fattech.com.br' }
$env:FATTECH_ALLOWED_ORIGINS = 'http://localhost:3000,http://127.0.0.1:3000'
New-Item -ItemType Directory -Force -Path '.local' | Out-Null
& '.venv/Scripts/python.exe' -m fattech.migrate
if ($LASTEXITCODE -ne 0) { throw 'Migration failed' }
if ($Seed) {
    if (-not $env:FATTECH_BOOTSTRAP_PASSWORD) { throw 'Set FATTECH_BOOTSTRAP_PASSWORD (12+ characters) before -Seed.' }
    & '.venv/Scripts/python.exe' -m fattech.seed --demo
    if ($LASTEXITCODE -ne 0) { throw 'Seed failed' }
}
Write-Output 'API: http://127.0.0.1:8000/api/docs. In a second terminal: npm run dev'
& '.venv/Scripts/python.exe' -m uvicorn fattech.main:app --host 127.0.0.1 --port 8000 --reload
