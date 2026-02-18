# Start Karma API and open UI test harness
# Usage: .\scripts\start-for-ui-test.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$harnessPath = Join-Path $projectRoot "tests\ui\test_harness.html"

Write-Host "Karma Platform v3 - UI Testing" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Ensure .env has ADMIN_API_KEY=test-admin-key" -ForegroundColor Yellow
Write-Host "2. API will start on http://localhost:8000" -ForegroundColor Yellow
Write-Host "3. Opening test harness in browser..." -ForegroundColor Yellow
Write-Host ""

Set-Location $projectRoot

# Open harness in default browser
Start-Process $harnessPath

# Start API (foreground - Ctrl+C to stop)
python -m uvicorn app.main:app --reload --port 8000
