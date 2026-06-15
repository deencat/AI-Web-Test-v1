# HF-3.1d — AWT prerequisite checks (Windows / AWT host)
# Run from repo root before Ubuntu integration smoke.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$EnvFile = Join-Path $RepoRoot "backend\.env"

function Read-DotEnv([string]$Path) {
    $map = @{}
    if (-not (Test-Path $Path)) { return $map }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^\s*#' -or $line -eq "") { return }
        if ($line -match '^([^=]+)=(.*)$') {
            $map[$Matches[1].Trim()] = $Matches[2].Trim().Trim('"')
        }
    }
    return $map
}

Write-Host "[HF-3.1d] AWT prerequisite smoke" -ForegroundColor Cyan
$dotenv = Read-DotEnv $EnvFile

$mcpSecret = $dotenv["AWT_MCP_SECRET"]
$mcpPort = if ($dotenv["AWT_MCP_PORT"]) { $dotenv["AWT_MCP_PORT"] } else { "8001" }
$apiBase = if ($dotenv["AWT_BASE_URL"]) { $dotenv["AWT_BASE_URL"] } else { "http://127.0.0.1:8000/api/v1" }
$mcpUrl = "http://127.0.0.1:$mcpPort"
$apiRoot = $apiBase -replace '/api/v1$', ''

$fail = $false

function Test-Ok([string]$Name, [scriptblock]$Block) {
    Write-Host -NoNewline "  $Name ... "
    try {
        & $Block
        Write-Host "OK" -ForegroundColor Green
    } catch {
        Write-Host "FAIL" -ForegroundColor Red
        Write-Host "    $($_.Exception.Message)" -ForegroundColor Yellow
        $script:fail = $true
    }
}

Test-Ok "backend/.env exists" {
    if (-not (Test-Path $EnvFile)) { throw "missing $EnvFile" }
}
Test-Ok "AWT_MCP_SECRET set" {
    if (-not $mcpSecret) { throw "AWT_MCP_SECRET empty" }
}
Test-Ok "MCP health" {
    $headers = @{ Authorization = "Bearer $mcpSecret" }
    $null = Invoke-RestMethod -Uri "$mcpUrl/health" -Headers $headers -TimeoutSec 15
}
Test-Ok "API health" {
    try {
        $null = Invoke-RestMethod -Uri "$apiRoot/health" -TimeoutSec 15
    } catch {
        $null = Invoke-RestMethod -Uri "$apiBase/health" -TimeoutSec 15
    }
}

$svcUser = $dotenv["AWT_SERVICE_USERNAME"]
$svcPass = $dotenv["AWT_SERVICE_PASSWORD"]
if ($svcUser -and $svcPass) {
    Test-Ok "Service login and pending backlog" {
        $loginBody = @{ username = $svcUser; password = $svcPass }
        $token = (Invoke-RestMethod -Method Post -Uri "$apiBase/auth/login" -Body $loginBody -ContentType "application/x-www-form-urlencoded").access_token
        $headers = @{ Authorization = "Bearer $token" }
        $backlogUri = '{0}/agent/backlog?status=pending&limit=5' -f $apiBase
        $backlog = Invoke-RestMethod -Uri $backlogUri -Headers $headers
        $count = if ($null -ne $backlog.total) { $backlog.total } else { @($backlog.items).Count }
        Write-Host -NoNewline "($count pending) "
        if ($count -eq 0) {
            Write-Host ""
            Write-Host "    WARN: no pending backlog items. Enqueue a journey before HF-3.1d full run." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  SKIP backlog check (set AWT_SERVICE_USERNAME/PASSWORD in backend/.env)" -ForegroundColor DarkYellow
}

if ($fail) {
    Write-Host ""
    Write-Host "AWT prereq FAILED. Fix before Ubuntu HF-3.1d run." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "AWT prereq passed. Next: Ubuntu deploy and smoke-integration-3.1d.sh" -ForegroundColor Green
Write-Host "  docs/hermes-profiles/HF-3.1d_Integration_Smoke.md"
