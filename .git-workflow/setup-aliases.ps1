# PowerShell script to set up useful Git aliases
# Usage: .\setup-aliases.ps1

Write-Host "=== Setting Up Git Aliases ===" -ForegroundColor Blue
Write-Host ""

Write-Host "Setting up workflow aliases..." -ForegroundColor Yellow

# Core workflow aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# Branch management
git config --global alias.branches "branch -a -v"
git config --global alias.current "branch --show-current"
git config --global alias.merged "branch --merged"
git config --global alias.unmerged "branch --no-merged"

# Log aliases
git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.overview "log --all --graph --decorate --oneline -20"

# Sync aliases
git config --global alias.sync "!git fetch origin && git merge origin/main"
git config --global alias.syncrb "!git fetch origin && git rebase origin/main"

# Compare aliases
git config --global alias.diff-main "diff main...HEAD"
git config --global alias.changes "diff --name-status"

# Commit aliases (using your project's conventional commit style)
git config --global alias.feat "!f() { git commit -m \"feat($1): $2\"; }; f"
git config --global alias.fix "!f() { git commit -m \"fix($1): $2\"; }; f"
git config --global alias.docs "!f() { git commit -m \"docs($1): $2\"; }; f"
git config --global alias.refactor "!f() { git commit -m \"refactor($1): $2\"; }; f"

# Undo aliases
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.unstage "reset HEAD --"

# Cleanup aliases
git config --global alias.cleanup "!git branch --merged main | grep -v 'main' | xargs git branch -d"

Write-Host ""
Write-Host "=== Aliases Set Up Successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "Available aliases:" -ForegroundColor Blue
Write-Host ""
Write-Host "Basic Commands:" -ForegroundColor Yellow
Write-Host "  git co <branch>       - Checkout branch"
Write-Host "  git br               - List branches"
Write-Host "  git ci               - Commit"
Write-Host "  git st               - Status"
Write-Host ""
Write-Host "Branch Management:" -ForegroundColor Yellow
Write-Host "  git branches         - List all branches with details"
Write-Host "  git current          - Show current branch"
Write-Host "  git merged           - Show merged branches"
Write-Host "  git unmerged         - Show unmerged branches"
Write-Host ""
Write-Host "Viewing History:" -ForegroundColor Yellow
Write-Host "  git lg               - Pretty log graph"
Write-Host "  git last             - Show last commit"
Write-Host "  git overview         - Graph overview (20 commits)"
Write-Host ""
Write-Host "Syncing:" -ForegroundColor Yellow
Write-Host "  git sync             - Fetch and merge from main"
Write-Host "  git syncrb           - Fetch and rebase on main"
Write-Host ""
Write-Host "Comparing:" -ForegroundColor Yellow
Write-Host "  git diff-main        - Show changes vs main"
Write-Host "  git changes          - Show changed files"
Write-Host ""
Write-Host "Conventional Commits:" -ForegroundColor Yellow
Write-Host "  git feat <scope> <msg>     - Create feat commit"
Write-Host "  git fix <scope> <msg>      - Create fix commit"
Write-Host "  git docs <scope> <msg>     - Create docs commit"
Write-Host "  git refactor <scope> <msg> - Create refactor commit"
Write-Host ""
Write-Host "Utilities:" -ForegroundColor Yellow
Write-Host "  git undo             - Undo last commit (keep changes)"
Write-Host "  git unstage          - Unstage files"
Write-Host "  git cleanup          - Delete merged branches"

