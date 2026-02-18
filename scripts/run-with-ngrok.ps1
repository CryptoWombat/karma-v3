# Start API + ngrok for quick Telegram testing (no deploy needed)
# Prereqs: ngrok (https://ngrok.com/download)

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

Write-Host "Karma v3 - Local + ngrok" -ForegroundColor Cyan
Write-Host ""

# Check ngrok
$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    Write-Host "ngrok not found. Install from https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "Or: winget install ngrok" -ForegroundColor White
    exit 1
}

# Start API in background
Write-Host "Starting API on port 8000..." -ForegroundColor Yellow
$job = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}

Start-Sleep -Seconds 3

# Start ngrok
Write-Host "Starting ngrok (public HTTPS URL)..." -ForegroundColor Yellow
$ngrokJob = Start-Job -ScriptBlock { ngrok http 8000 }

Start-Sleep -Seconds 4

# Try to get URL from ngrok API
try {
    $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction SilentlyContinue
    $url = ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
    if ($url) {
        Write-Host ""
        Write-Host "Ready!" -ForegroundColor Green
        Write-Host "API: $url" -ForegroundColor White
        Write-Host "Mini App: $url/app/" -ForegroundColor White
        Write-Host ""
        Write-Host "Set BotFather Menu Button to: $url/app/" -ForegroundColor Yellow
        Write-Host "Then open your bot in Telegram!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    }
} catch {
    Write-Host "ngrok may still be starting. Check http://127.0.0.1:4040 for your URL" -ForegroundColor Yellow
}

Wait-Job $job -ErrorAction SilentlyContinue
