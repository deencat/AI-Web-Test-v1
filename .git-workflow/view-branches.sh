#!/bin/bash
# Script to view all branches with useful information
# Usage: ./view-branches.sh [--graph]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SHOW_GRAPH=false
if [ "$1" == "--graph" ]; then
    SHOW_GRAPH=true
fi

echo -e "${BLUE}=== Git Branch Overview ===${NC}"
echo ""

# Current branch
CURRENT=$(git branch --show-current)
echo -e "${GREEN}Current Branch: ${CURRENT}${NC}"
echo ""

# Local branches
echo -e "${CYAN}Local Branches:${NC}"
git branch -v
echo ""

# Remote branches
echo -e "${CYAN}Remote Branches:${NC}"
git branch -r -v
echo ""

# Branches merged into main
echo -e "${CYAN}Branches Merged into Main:${NC}"
git branch --merged main | grep -v "main" | sed 's/^/  /' || echo "  None"
echo ""

# Branches not yet merged into main
echo -e "${CYAN}Branches NOT Merged into Main:${NC}"
git branch --no-merged main | sed 's/^/  /' || echo "  None"
echo ""

# Show graph if requested
if [ "$SHOW_GRAPH" == true ]; then
    echo -e "${CYAN}Branch Graph (last 20 commits):${NC}"
    git log --graph --oneline --all --decorate -20
    echo ""
fi

# Show remote tracking status
echo -e "${CYAN}Remote Tracking Status:${NC}"
git for-each-ref --format='%(refname:short) -> %(upstream:short)' refs/heads | grep -v "^$" | sed 's/^/  /'
echo ""

# Show last commit on each branch
echo -e "${CYAN}Last Commit on Each Branch:${NC}"
for branch in $(git branch -a | grep -v HEAD | sed 's/^[* ]*//' | sed 's/remotes\/origin\///'); do
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
        last_commit=$(git log -1 --format="%h - %s (%cr)" "$branch" 2>/dev/null)
        echo -e "  ${YELLOW}${branch}${NC}: ${last_commit}"
    fi
done

