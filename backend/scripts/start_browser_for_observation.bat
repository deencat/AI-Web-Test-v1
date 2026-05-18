@echo off
:: ============================================================
:: start_browser_for_observation.bat
::
:: Launches a persistent Chrome browser with remote debugging
:: enabled on port 9222.  browser-use connects to this browser
:: instead of spawning its own, so the session (cookies, login
:: state) is preserved across multiple crawl-and-save runs.
::
:: USAGE:
::   1. Double-click this file (or run from cmd).
::   2. Make sure BROWSER_CDP_URL=http://127.0.0.1:9222 is
::      uncommented in backend/.env.
::   3. Start (or restart) the backend server.
::   4. Keep this Chrome window open during all crawl sessions.
::      Closing it will break any in-progress crawl.
:: ============================================================

set PORT=9222
set PROFILE_DIR=%LOCALAPPDATA%\browser-use-cdp-profile

echo Starting Chrome with remote debugging on port %PORT% ...
echo Profile directory: %PROFILE_DIR%
echo.
echo Keep this window / Chrome open during crawl sessions.
echo Close Chrome only after the server has been stopped.
echo.

:: Try standard Chrome locations
set CHROME=
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" (
    set CHROME="%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
) else if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" (
    set CHROME="%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if "%CHROME%"=="" (
    echo ERROR: Chrome not found in standard locations.
    echo Please edit this file and set CHROME= to your chrome.exe path.
    pause
    exit /b 1
)

start "" %CHROME% ^
    --remote-debugging-port=%PORT% ^
    --user-data-dir="%PROFILE_DIR%" ^
    --no-first-run ^
    --no-default-browser-check ^
    --disable-extensions ^
    --start-maximized ^
    --disable-blink-features=AutomationControlled ^
    about:blank

echo Chrome started. You can close this command window now.
echo (Chrome itself must remain open.)
timeout /t 3 >nul
