# PowerShell script to compare two branches
# Usage: .\compare-branches.ps1 [branch1] [branch2]

param(
    [string]$Branch1 = "main",
    [string]$Branch2 = (git branch --show-current)
)

Write-Host "=== Comparing Branches ===" -ForegroundColor Blue
Write-Host "Branch 1: $Branch1" -ForegroundColor Yellow
Write-Host "Branch 2: $Branch2" -ForegroundColor Yellow
Write-Host ""

# Commits in branch2 not in branch1
Write-Host "Commits in $Branch2 not in ${Branch1}:" -ForegroundColor Cyan
$commits2 = git log "$Branch1..$Branch2" --oneline --no-merges
if ($commits2) {
    $commits2 | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  None"
}
Write-Host ""

# Commits in branch1 not in branch2
Write-Host "Commits in $Branch1 not in ${Branch2}:" -ForegroundColor Cyan
$commits1 = git log "$Branch2..$Branch1" --oneline --no-merges
if ($commits1) {
    $commits1 | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  None"
}
Write-Host ""

# Files changed
Write-Host "Files changed between branches:" -ForegroundColor Cyan
$files = git diff --name-status "$Branch1...$Branch2"
if ($files) {
    $files | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  None"
}
Write-Host ""

# Statistics
Write-Host "Statistics:" -ForegroundColor Cyan
git diff --stat "$Branch1...$Branch2"
Write-Host ""

# Check for potential conflicts
Write-Host "Checking for potential merge conflicts..." -ForegroundColor Cyan
$mergeBase = git merge-base $Branch1 $Branch2
$conflicts = git merge-tree $mergeBase $Branch1 $Branch2 | Select-String "changed in both" -Context 0,3
if ($conflicts) {
    $conflicts | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  No obvious conflicts detected" -ForegroundColor Green
}

