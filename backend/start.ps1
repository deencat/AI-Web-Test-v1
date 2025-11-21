# Simple PowerShell script to start the backend server
# Usage: .\start.ps1

# Just run uvicorn with the venv python directly
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

