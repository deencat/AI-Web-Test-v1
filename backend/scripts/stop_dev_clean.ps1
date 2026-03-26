<#
.SYNOPSIS
  Stop local dev stack leftovers after killing the API mid-workflow (generate-tests / browser-use).

.DESCRIPTION
  - Frees TCP port 8000 (uvicorn/start_server.py) if a process is still bound.
  - Optionally stops Playwright/Chromium processes launched from ms-playwright (automation browsers).
  Does NOT kill normal Google Chrome unless you use -KillAllChrome (destructive).

.PARAMETER Port
  API port to free (default 8000).

.PARAMETER KillPlaywrightBrowsers
  Stop processes whose path contains "ms-playwright" (Chromium used by Playwright/browser-use).

.PARAMETER KillAllChrome
  Force-stop ALL chrome.exe processes. Use only if no important Chrome windows are open.

.EXAMPLE
  .\scripts\stop_dev_clean.ps1
.EXAMPLE
  .\scripts\stop_dev_clean.ps1 -KillPlaywrightBrowsers
#>
param(
    [int] $Port = 8000,
    [switch] $KillPlaywrightBrowsers,
    [switch] $KillAllChrome
)

$ErrorActionPreference = "Continue"

Write-Host "=== stop_dev_clean.ps1 ===" -ForegroundColor Cyan

# 1) Free API port
try {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Listen" }
    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if ($procId -and $procId -gt 0) {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            Write-Host "Stopping PID $procId ($($p.ProcessName)) on port $Port" -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    if (-not $pids) {
        Write-Host "No listener on port $Port (already free)." -ForegroundColor Green
    }
} catch {
    Write-Host "Port check failed: $_" -ForegroundColor Red
}

# 2) Playwright-managed Chromium (safe subset)
if ($KillPlaywrightBrowsers) {
    $pw = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -and ($_.Path -like "*ms-playwright*" -or $_.Path -like "*\.cache\ms-playwright*")
    }
    if ($pw) {
        $pw | ForEach-Object {
            Write-Host "Stopping Playwright browser: $($_.Name) PID $($_.Id) — $($_.Path)" -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "No ms-playwright processes found." -ForegroundColor Green
    }
}

# 3) Nuclear option
if ($KillAllChrome) {
    Write-Host "Stopping ALL chrome.exe (as requested)..." -ForegroundColor Red
    Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

Write-Host "Done. Start fresh: cd backend; .\venv\Scripts\Activate.ps1; python .\start_server.py" -ForegroundColor Cyan
