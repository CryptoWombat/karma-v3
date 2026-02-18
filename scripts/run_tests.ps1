# Karma v3 - Test runner
# Usage:
#   .\scripts\run_tests.ps1           # API + E2E + regression
#   .\scripts\run_tests.ps1 -Coverage # With coverage report
#   .\scripts\run_tests.ps1 -Visual   # Include visual tests (needs Playwright)
#   .\scripts\run_tests.ps1 -Regress # Regression only

param(
    [switch]$Coverage,
    [switch]$Visual,
    [switch]$Regress
)

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot\..

try {
    $pytestArgs = @("tests/", "-v", "--tb=short")
    
    if ($Regress) {
        $pytestArgs = @("tests/test_regression.py", "-v", "--tb=short")
    } elseif (-not $Visual) {
        # Exclude UI tests by default (need Playwright)
        $pytestArgs += "--ignore=tests/ui/"
    }
    
    if ($Coverage) {
        $pytestArgs += "--cov=app", "--cov-report=html", "--cov-report=term-missing"
    }
    
    python -m pytest @pytestArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
