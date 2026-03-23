# Run tests after development - uses venv
# Usage: .\run-tests-after-dev.ps1 [test_path]
# Example: .\run-tests-after-dev.ps1
# Example: .\run-tests-after-dev.ps1 tests/agents/test_observation_agent_http_credentials.py

param(
    [string]$TestPath = "tests/agents/test_observation_agent_http_credentials.py tests/agents/test_observation_agent_browser_use.py"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running tests (venv environment)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Use venv Python directly (ensures venv is used)
$venvPython = Join-Path $scriptDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv not found at backend\venv" -ForegroundColor Red
    Write-Host "Create it with: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using: $venvPython" -ForegroundColor Green
Write-Host ""

& $venvPython -m pytest $TestPath.Split() -v
exit $LASTEXITCODE
