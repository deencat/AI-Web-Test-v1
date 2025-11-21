# PowerShell script to sync your current branch with main
# Usage: .\sync-with-main.ps1 [-Rebase]

param(
    [switch]$Rebase
)

$ErrorActionPreference = "Stop"

# Get current branch
$currentBranch = git branch --show-current

if ($currentBranch -eq "main") {
    Write-Host "Already on main branch. Just pulling latest changes..." -ForegroundColor Yellow
    git pull origin main
    exit 0
}

Write-Host "=== Syncing $currentBranch with main ===" -ForegroundColor Blue
Write-Host ""

# Step 1: Fetch latest changes
Write-Host "Step 1: Fetching latest changes..." -ForegroundColor Blue
git fetch origin

# Step 2: Save current work if there are uncommitted changes
$hasChanges = git diff-index --quiet HEAD --; $LASTEXITCODE -ne 0
$stashed = $false

if ($hasChanges) {
    Write-Host "Uncommitted changes detected. Stashing..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git stash save "Auto-stash before sync $timestamp"
    $stashed = $true
}

# Step 3: Sync with main
try {
    if ($Rebase) {
        Write-Host "Step 2: Rebasing on main..." -ForegroundColor Blue
        git rebase origin/main
        Write-Host "✓ Rebase successful" -ForegroundColor Green
    }
    else {
        Write-Host "Step 2: Merging from main..." -ForegroundColor Blue
        git merge origin/main -m "merge: sync $currentBranch with main"
        Write-Host "✓ Merge successful" -ForegroundColor Green
    }
}
catch {
    Write-Host "✗ Sync failed - conflicts detected" -ForegroundColor Red
    if ($Rebase) {
        Write-Host "Resolve conflicts, then run: git rebase --continue" -ForegroundColor Yellow
    }
    else {
        Write-Host "Resolve conflicts, then run: git commit" -ForegroundColor Yellow
    }
    exit 1
}

# Step 4: Restore stashed changes
if ($stashed) {
    Write-Host "Step 3: Restoring stashed changes..." -ForegroundColor Blue
    try {
        git stash pop
        Write-Host "✓ Stashed changes restored" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Conflict while restoring stash" -ForegroundColor Red
        Write-Host "Resolve conflicts, then run: git stash drop" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "=== Sync Complete ===" -ForegroundColor Green
Write-Host "✓ $currentBranch is now up to date with main" -ForegroundColor Green

