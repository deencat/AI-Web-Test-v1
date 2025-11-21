# PowerShell script to activate venv and start FastAPI server
# Usage: .\run_server.ps1

Write-Host "Starting AI Web Test Backend..." -ForegroundColor Green

# Check if venv exists
if (-Not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "Then run: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Use venv python directly (no need to activate in script)
$venvPython = "venv\Scripts\python.exe"

# Display Python info
Write-Host "`nPython environment:" -ForegroundColor Cyan
& $venvPython --version
Write-Host "Location: $(Resolve-Path $venvPython)" -ForegroundColor Gray

# Check if dependencies are installed
Write-Host "`nChecking dependencies..." -ForegroundColor Cyan
$uvicornCheck = & $venvPython -c "import uvicorn; print('OK')" 2>&1
if ($uvicornCheck -notlike "*OK*") {
    Write-Host "ERROR: Dependencies not installed!" -ForegroundColor Red
    Write-Host "Please run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "Then run: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
Write-Host "Dependencies: OK" -ForegroundColor Green

# Start server
Write-Host "`nStarting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "Press CTRL+C to stop`n" -ForegroundColor Yellow

& $venvPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

