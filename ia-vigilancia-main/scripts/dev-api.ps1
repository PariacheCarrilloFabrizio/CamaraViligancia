Set-Location (Split-Path -Parent $PSScriptRoot)

.\venv\Scripts\python.exe -m uvicorn server:app --app-dir app --host 127.0.0.1 --port 8000
