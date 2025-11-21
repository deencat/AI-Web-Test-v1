#!/bin/bash
# Script to sync your current branch with main
# Usage: ./sync-with-main.sh [--rebase]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

USE_REBASE=false
if [ "$1" == "--rebase" ]; then
    USE_REBASE=true
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" == "main" ]; then
    echo -e "${YELLOW}Already on main branch. Just pulling latest changes...${NC}"
    git pull origin main
    exit 0
fi

echo -e "${BLUE}=== Syncing ${CURRENT_BRANCH} with main ===${NC}"
echo ""

# Step 1: Fetch latest changes
echo -e "${BLUE}Step 1: Fetching latest changes...${NC}"
git fetch origin

# Step 2: Save current work if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Uncommitted changes detected. Stashing...${NC}"
    git stash save "Auto-stash before sync $(date)"
    STASHED=true
else
    STASHED=false
fi

# Step 3: Sync with main
if [ "$USE_REBASE" == true ]; then
    echo -e "${BLUE}Step 2: Rebasing on main...${NC}"
    if git rebase origin/main; then
        echo -e "${GREEN}✓ Rebase successful${NC}"
    else
        echo -e "${RED}✗ Rebase failed - conflicts detected${NC}"
        echo -e "${YELLOW}Resolve conflicts, then run: git rebase --continue${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Step 2: Merging from main...${NC}"
    if git merge origin/main -m "merge: sync $CURRENT_BRANCH with main"; then
        echo -e "${GREEN}✓ Merge successful${NC}"
    else
        echo -e "${RED}✗ Merge failed - conflicts detected${NC}"
        echo -e "${YELLOW}Resolve conflicts, then run: git commit${NC}"
        exit 1
    fi
fi

# Step 4: Restore stashed changes
if [ "$STASHED" == true ]; then
    echo -e "${BLUE}Step 3: Restoring stashed changes...${NC}"
    if git stash pop; then
        echo -e "${GREEN}✓ Stashed changes restored${NC}"
    else
        echo -e "${RED}✗ Conflict while restoring stash${NC}"
        echo -e "${YELLOW}Resolve conflicts, then run: git stash drop${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}=== Sync Complete ===${NC}"
echo -e "${GREEN}✓ ${CURRENT_BRANCH} is now up to date with main${NC}"

