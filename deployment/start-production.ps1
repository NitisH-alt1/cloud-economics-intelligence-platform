param(
    [int]$Port = 8081
)

Set-Location (Split-Path -Parent $PSScriptRoot)
. .\.venv\Scripts\Activate.ps1

$env:APP_ENV = "production"

uvicorn dashboard.app:app --host 0.0.0.0 --port $Port
