# Karma v3 - One-click setup for Telegram Mini App testing
# Runs: API + Cloudflare tunnel (no ngrok interstitial!)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

Write-Host ""
Write-Host "Karma v3 - Telegram Mini App Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# 1. Ensure venv exists and deps installed
if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -q 2>$null

# 2. Start API in new window (keeps running)
Write-Host "Starting API on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; .\.venv\Scripts\Activate.ps1; Write-Host 'API running on http://localhost:8000' -ForegroundColor Green; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized
Start-Sleep -Seconds 5

# 3. Start Cloudflare tunnel
$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $cloudflared)) { $cloudflared = "cloudflared" }

Write-Host "Starting Cloudflare tunnel (no interstitial!)..." -ForegroundColor Yellow
Write-Host ""
& $cloudflared tunnel --url http://localhost:8000
