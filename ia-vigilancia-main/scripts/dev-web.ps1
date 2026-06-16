$root = Split-Path -Parent $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$root\scripts\dev-api.ps1`""
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$root\scripts\dev-dashboard.ps1`""

Write-Host "Backend:   http://localhost:8000"
Write-Host "Dashboard: http://localhost:3000"
