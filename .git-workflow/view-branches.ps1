# PowerShell script to view all branches with useful information
# Usage: .\view-branches.ps1 [-Graph]

param(
    [switch]$Graph
)

Write-Host "=== Git Branch Overview ===" -ForegroundColor Blue
Write-Host ""

# Current branch
$current = git branch --show-current
Write-Host "Current Branch: $current" -ForegroundColor Green
Write-Host ""

# Local branches
Write-Host "Local Branches:" -ForegroundColor Cyan
git branch -v
Write-Host ""

# Remote branches
Write-Host "Remote Branches:" -ForegroundColor Cyan
git branch -r -v
Write-Host ""

# Branches merged into main
Write-Host "Branches Merged into Main:" -ForegroundColor Cyan
$merged = git branch --merged main | Where-Object { $_ -notmatch "main" }
if ($merged) {
    $merged | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  None"
}
Write-Host ""

# Branches not yet merged into main
Write-Host "Branches NOT Merged into Main:" -ForegroundColor Cyan
$notMerged = git branch --no-merged main
if ($notMerged) {
    $notMerged | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  None"
}
Write-Host ""

# Show graph if requested
if ($Graph) {
    Write-Host "Branch Graph (last 20 commits):" -ForegroundColor Cyan
    git log --graph --oneline --all --decorate -20
    Write-Host ""
}

# Show remote tracking status
Write-Host "Remote Tracking Status:" -ForegroundColor Cyan
$tracking = git for-each-ref --format='%(refname:short) -> %(upstream:short)' refs/heads | Where-Object { $_ -ne "" }
if ($tracking) {
    $tracking | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "  None"
}
Write-Host ""

# Show last commit on each branch
Write-Host "Last Commit on Each Branch:" -ForegroundColor Cyan
$branches = git branch -a | ForEach-Object { $_.Trim('* ').Trim() } | Where-Object { $_ -notmatch "HEAD" -and $_ -ne "" }
foreach ($branch in $branches) {
    $cleanBranch = $branch -replace "remotes/origin/", ""
    try {
        $lastCommit = git log -1 --format="%h - %s (%cr)" $branch 2>$null
        if ($lastCommit) {
            Write-Host "  " -NoNewline
            Write-Host "$cleanBranch" -ForegroundColor Yellow -NoNewline
            Write-Host ": $lastCommit"
        }
    }
    catch {
        # Skip branches that can't be accessed
    }
}

