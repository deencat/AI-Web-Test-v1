@echo off
echo ========================================
echo Starting AI Web Test Backend Server
echo ========================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting server...
echo Server will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
