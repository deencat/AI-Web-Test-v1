#!/bin/bash
# Script to set up useful Git aliases
# Usage: ./setup-aliases.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Setting Up Git Aliases ===${NC}"
echo ""

# Core workflow aliases
echo -e "${YELLOW}Setting up workflow aliases...${NC}"

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
git config --global alias.feat "!f() { git commit -m \"feat(\$1): \$2\"; }; f"
git config --global alias.fix "!f() { git commit -m \"fix(\$1): \$2\"; }; f"
git config --global alias.docs "!f() { git commit -m \"docs(\$1): \$2\"; }; f"
git config --global alias.refactor "!f() { git commit -m \"refactor(\$1): \$2\"; }; f"

# Undo aliases
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.unstage "reset HEAD --"

# Cleanup aliases
git config --global alias.cleanup "!git branch --merged main | grep -v 'main' | xargs git branch -d"

echo ""
echo -e "${GREEN}=== Aliases Set Up Successfully ===${NC}"
echo ""
echo -e "${BLUE}Available aliases:${NC}"
echo ""
echo -e "${YELLOW}Basic Commands:${NC}"
echo "  git co <branch>       - Checkout branch"
echo "  git br               - List branches"
echo "  git ci               - Commit"
echo "  git st               - Status"
echo ""
echo -e "${YELLOW}Branch Management:${NC}"
echo "  git branches         - List all branches with details"
echo "  git current          - Show current branch"
echo "  git merged           - Show merged branches"
echo "  git unmerged         - Show unmerged branches"
echo ""
echo -e "${YELLOW}Viewing History:${NC}"
echo "  git lg               - Pretty log graph"
echo "  git last             - Show last commit"
echo "  git overview         - Graph overview (20 commits)"
echo ""
echo -e "${YELLOW}Syncing:${NC}"
echo "  git sync             - Fetch and merge from main"
echo "  git syncrb           - Fetch and rebase on main"
echo ""
echo -e "${YELLOW}Comparing:${NC}"
echo "  git diff-main        - Show changes vs main"
echo "  git changes          - Show changed files"
echo ""
echo -e "${YELLOW}Conventional Commits:${NC}"
echo "  git feat <scope> <msg>     - Create feat commit"
echo "  git fix <scope> <msg>      - Create fix commit"
echo "  git docs <scope> <msg>     - Create docs commit"
echo "  git refactor <scope> <msg> - Create refactor commit"
echo ""
echo -e "${YELLOW}Utilities:${NC}"
echo "  git undo             - Undo last commit (keep changes)"
echo "  git unstage          - Unstage files"
echo "  git cleanup          - Delete merged branches"

