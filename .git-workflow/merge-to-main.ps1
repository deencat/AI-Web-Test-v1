# PowerShell script to safely merge development branches to main via integration branch
# Usage: .\merge-to-main.ps1 [backend-branch] [frontend-branch]

param(
    [string]$BackendBranch = "backend-dev-sprint-2",
    [string]$FrontendBranch = "frontend-dev"
)

$ErrorActionPreference = "Stop"

# Generate integration branch name with timestamp
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$IntegrationBranch = "integration-$timestamp"

Write-Host "=== Git Workflow: Merge to Main ===" -ForegroundColor Blue
Write-Host "Backend Branch: $BackendBranch" -ForegroundColor Yellow
Write-Host "Frontend Branch: $FrontendBranch" -ForegroundColor Yellow
Write-Host "Integration Branch: $IntegrationBranch" -ForegroundColor Yellow
Write-Host ""

# Step 1: Fetch latest changes
Write-Host "Step 1: Fetching latest changes..." -ForegroundColor Blue
git fetch origin

# Step 2: Ensure we're on main and it's up to date
Write-Host "Step 2: Updating main branch..." -ForegroundColor Blue
git checkout main
git pull origin main

# Step 3: Create integration branch
Write-Host "Step 3: Creating integration branch..." -ForegroundColor Blue
git checkout -b $IntegrationBranch

# Step 4: Merge backend
Write-Host "Step 4: Merging backend branch ($BackendBranch)..." -ForegroundColor Blue
try {
    git merge "origin/$BackendBranch" --no-ff -m "merge: integrate backend from $BackendBranch"
    Write-Host "✓ Backend merge successful" -ForegroundColor Green
}
catch {
    Write-Host "✗ Backend merge failed - please resolve conflicts" -ForegroundColor Red
    Write-Host "After resolving conflicts, run:" -ForegroundColor Yellow
    Write-Host "  git add ."
    Write-Host "  git commit"
    Write-Host "  .\merge-to-main.ps1 -continue"
    exit 1
}

# Step 5: Merge frontend
Write-Host "Step 5: Merging frontend branch ($FrontendBranch)..." -ForegroundColor Blue
try {
    git merge "origin/$FrontendBranch" --no-ff -m "merge: integrate frontend from $FrontendBranch"
    Write-Host "✓ Frontend merge successful" -ForegroundColor Green
}
catch {
    Write-Host "✗ Frontend merge failed - please resolve conflicts" -ForegroundColor Red
    Write-Host "After resolving conflicts, run:" -ForegroundColor Yellow
    Write-Host "  git add ."
    Write-Host "  git commit"
    Write-Host "  .\merge-to-main.ps1 -continue"
    exit 1
}

# Step 6: Show summary
Write-Host ""
Write-Host "=== Integration Complete ===" -ForegroundColor Green
Write-Host "Integration branch '$IntegrationBranch' created successfully" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Blue
Write-Host "1. Test the integration thoroughly"
Write-Host "2. If tests pass, run: git checkout main; git merge $IntegrationBranch"
Write-Host "3. Push to remote: git push origin main"
Write-Host "4. Delete integration branch: git branch -d $IntegrationBranch"
Write-Host ""
Write-Host "Or use the helper script:" -ForegroundColor Yellow
Write-Host "  .\.git-workflow\finalize-merge.ps1 $IntegrationBranch"

