# Start Karma API with validator keys and open Validator Dashboard
# Usage: .\scripts\start-validator-dashboard.ps1 [port]

param([int]$Port = 8001)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-Host "Karma Validator Dashboard" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Setting VALIDATOR_API_KEYS so Snapshot/Inflation/Leaderboard/Transactions work" -ForegroundColor Yellow
Write-Host "API: http://127.0.0.1:$Port" -ForegroundColor Yellow
Write-Host "Dashboard: http://127.0.0.1:$Port/app/validator.html" -ForegroundColor Yellow
Write-Host ""

Set-Location $projectRoot

# Ensure validator keys are set (env takes precedence over .env)
$env:VALIDATOR_API_KEYS = "validator-key-1,validator-key-2"
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = "sqlite:///./karma.db" }
if (-not $env:ADMIN_API_KEY) { $env:ADMIN_API_KEY = "test-admin-key" }

# Open dashboard after a short delay (server will be starting)
Start-Job -ScriptBlock { Start-Sleep 4; Start-Process "http://127.0.0.1:$using:Port/app/validator.html" } | Out-Null

# Start API (foreground; Ctrl+C to stop)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
