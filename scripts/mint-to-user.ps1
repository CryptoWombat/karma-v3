# Mint Karma to a Telegram user
# Usage: .\scripts\mint-to-user.ps1 -ApiUrl "https://xxx.railway.app" -UserId "123456789"
param(
    [Parameter(Mandatory=$true)] [string]$ApiUrl,
    [Parameter(Mandatory=$true)] [string]$UserId,
    [int]$Amount = 100
)

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envPath = Join-Path $projectRoot ".env"

# Read ADMIN_API_KEY from .env
$adminKey = ""
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "ADMIN_API_KEY=(.+)") { $adminKey = $matches[1].Trim() }
    }
}
if (-not $adminKey) {
    Write-Host "ADMIN_API_KEY not found in .env" -ForegroundColor Red
    exit 1
}

$url = $ApiUrl.TrimEnd("/")
$body = @{ user_id = $UserId; amount = $Amount } | ConvertTo-Json

Write-Host "Minting $Amount Karma to user $UserId..." -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "$url/v1/admin/mint" -Method Post `
        -Headers @{ "Content-Type" = "application/json"; "Authorization" = "Bearer $adminKey" } `
        -Body $body
    Write-Host "Done: $($r.message)" -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
}
