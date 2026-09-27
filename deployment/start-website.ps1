param(
    [int]$Port = 8090
)

Set-Location (Split-Path -Parent $PSScriptRoot)
. .\.venv\Scripts\Activate.ps1

uvicorn web.app:app --host 127.0.0.1 --port $Port
