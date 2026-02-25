# Run 4-Agent E2E Real Test
# Usage: From repo root or backend: .\backend\scripts\run_e2e_real.ps1  or  .\scripts\run_e2e_real.ps1
# Requires: venv activated, AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT set (see tests/integration/E2E_REAL_RUN_GUIDE.md)

$ErrorActionPreference = "Stop"
$backendRoot = $PSScriptRoot + "\.."
if (-not (Test-Path (Join-Path $backendRoot "tests\integration\test_four_agent_e2e_real.py"))) {
    Write-Host "Run this script from the repo root or from backend. Current dir: $(Get-Location)" -ForegroundColor Red
    exit 1
}
Push-Location $backendRoot | Out-Null
try {
    # Check required env vars
    $missing = @()
    if (-not $env:AZURE_OPENAI_API_KEY) { $missing += "AZURE_OPENAI_API_KEY" }
    if (-not $env:AZURE_OPENAI_ENDPOINT) { $missing += "AZURE_OPENAI_ENDPOINT" }
    if ($missing.Count -gt 0) {
        Write-Host "Missing required environment variables: $($missing -join ', ')" -ForegroundColor Red
        Write-Host "See backend/tests/integration/E2E_REAL_RUN_GUIDE.md for setup." -ForegroundColor Yellow
        exit 1
    }
    # Optional reminders
    if (-not $env:USER_INSTRUCTION) {
        Write-Host "[INFO] USER_INSTRUCTION not set - test will run without multi-page flow instruction." -ForegroundColor Yellow
    }
    if ($env:LOGIN_EMAIL -and -not $env:GMAIL_EMAIL -and $env:LOGIN_EMAIL -match "\+") {
        Write-Host "[INFO] LOGIN_EMAIL contains '+'; Gmail login will use base address (see E2E_REAL_RUN_GUIDE.md)." -ForegroundColor Cyan
    }
    Write-Host "Running 4-Agent E2E Real test (use -s for real-time logs)..." -ForegroundColor Green
    python -u -m pytest tests/integration/test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location | Out-Null
}
exit $exitCode
