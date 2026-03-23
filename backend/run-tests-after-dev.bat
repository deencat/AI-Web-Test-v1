@echo off
REM Run tests after development - uses venv
REM Usage: run-tests-after-dev.bat [test_path]
REM Example: run-tests-after-dev.bat
REM Example: run-tests-after-dev.bat tests/agents/test_observation_agent_http_credentials.py

cd /d "%~dp0"

echo ========================================
echo Running tests (venv environment)
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

if not exist venv\Scripts\activate.bat (
    echo ERROR: venv not found at backend\venv
    echo Create it with: python -m venv venv
    exit /b 1
)

echo.
if "%~1"=="" (
    python -m pytest tests/agents/test_observation_agent_http_credentials.py tests/agents/test_observation_agent_browser_use.py -v
) else (
    python -m pytest %* -v
)
exit /b %ERRORLEVEL%
