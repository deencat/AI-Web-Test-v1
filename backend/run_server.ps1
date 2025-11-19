# PowerShell script to activate venv and start FastAPI server
# Usage: .\run_server.ps1

Write-Host "Starting AI Web Test Backend..." -ForegroundColor Green

# Check if venv exists
if (-Not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Check if activation worked
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment!" -ForegroundColor Red
    exit 1
}

# Display Python info
Write-Host "`nPython environment:" -ForegroundColor Cyan
python --version
Write-Host "Location: $(Get-Command python | Select-Object -ExpandProperty Source)" -ForegroundColor Gray

# Check if dependencies are installed
Write-Host "`nChecking dependencies..." -ForegroundColor Cyan
$uvicornCheck = python -c "import uvicorn; print('OK')" 2>&1
if ($uvicornCheck -ne "OK") {
    Write-Host "ERROR: Dependencies not installed!" -ForegroundColor Red
    Write-Host "Please run: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
Write-Host "Dependencies: OK" -ForegroundColor Green

# Start server
Write-Host "`nStarting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "Press CTRL+C to stop`n" -ForegroundColor Yellow

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

