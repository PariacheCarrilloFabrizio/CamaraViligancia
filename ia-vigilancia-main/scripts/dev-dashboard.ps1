Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) "dashboard")

bun run dev
