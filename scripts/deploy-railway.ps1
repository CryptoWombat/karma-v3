# Deploy Karma API to Railway
# Prereqs: npm install -g @railway/cli  AND  railway login

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $projectRoot

Write-Host "Karma v3 - Railway Deploy" -ForegroundColor Cyan
Write-Host ""

# Check Railway CLI
$railway = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railway) {
    Write-Host "Railway CLI not found. Install:" -ForegroundColor Yellow
    Write-Host "  npm install -g @railway/cli" -ForegroundColor White
    Write-Host "  railway login" -ForegroundColor White
    exit 1
}

# Link or init
if (-not (Test-Path ".railway")) {
    Write-Host "Linking to Railway (opens browser if needed)..." -ForegroundColor Yellow
    railway init
}

# Deploy
Write-Host "Deploying..." -ForegroundColor Yellow
railway up --detach

# Get URL
Start-Sleep -Seconds 5
$url = railway domain 2>$null
if (-not $url) { $url = "https://$(railway status 2>$null | Select-String 'https://' | ForEach-Object { $_.Matches.Value })" }
$url = ($url -split "`n")[0].Trim()

Write-Host ""
Write-Host "Deployed!" -ForegroundColor Green
Write-Host "API URL: $url" -ForegroundColor White
Write-Host "Mini App URL: $url/app/" -ForegroundColor White
Write-Host ""
Write-Host "Next: Set BotFather Menu Button URL to: $url/app/" -ForegroundColor Yellow
Write-Host "      Get your Telegram ID from @userinfobot, then run:" -ForegroundColor Yellow
Write-Host "      .\scripts\mint-to-user.ps1 -ApiUrl $url -UserId YOUR_TELEGRAM_ID" -ForegroundColor White
