# PowerShell script to finalize merge after testing integration branch
# Usage: .\finalize-merge.ps1 [integration-branch]

param(
    [Parameter(Mandatory=$true)]
    [string]$IntegrationBranch
)

$ErrorActionPreference = "Stop"

Write-Host "=== Finalizing Merge to Main ===" -ForegroundColor Blue
Write-Host ""

# Confirm with user
$confirm = Read-Host "Have you tested the integration branch thoroughly? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Merge cancelled. Please test before finalizing." -ForegroundColor Yellow
    exit 0
}

# Step 1: Switch to main
Write-Host "Step 1: Switching to main..." -ForegroundColor Blue
git checkout main
git pull origin main

# Step 2: Merge integration branch
Write-Host "Step 2: Merging integration branch..." -ForegroundColor Blue
git merge $IntegrationBranch --no-ff -m "merge: finalize integration from $IntegrationBranch"

# Step 3: Push to remote
Write-Host "Step 3: Pushing to remote..." -ForegroundColor Blue
git push origin main

# Step 4: Clean up integration branch
Write-Host "Step 4: Cleaning up..." -ForegroundColor Blue
git branch -d $IntegrationBranch

Write-Host ""
Write-Host "=== Merge Complete ===" -ForegroundColor Green
Write-Host "✓ Changes successfully merged to main" -ForegroundColor Green
Write-Host "✓ Integration branch deleted" -ForegroundColor Green
Write-Host ""
Write-Host "Don't forget to:" -ForegroundColor Yellow
Write-Host "1. Update your development branches from main"
Write-Host "2. Notify your team about the changes"

