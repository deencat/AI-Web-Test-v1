#!/bin/bash
# Script to safely merge development branches to main via integration branch
# Usage: ./merge-to-main.sh [backend-branch] [frontend-branch]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default branch names
BACKEND_BRANCH="${1:-backend-dev-sprint-2}"
FRONTEND_BRANCH="${2:-frontend-dev}"
INTEGRATION_BRANCH="integration-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}=== Git Workflow: Merge to Main ===${NC}"
echo -e "${YELLOW}Backend Branch: ${BACKEND_BRANCH}${NC}"
echo -e "${YELLOW}Frontend Branch: ${FRONTEND_BRANCH}${NC}"
echo -e "${YELLOW}Integration Branch: ${INTEGRATION_BRANCH}${NC}"
echo ""

# Step 1: Fetch latest changes
echo -e "${BLUE}Step 1: Fetching latest changes...${NC}"
git fetch origin

# Step 2: Ensure we're on main and it's up to date
echo -e "${BLUE}Step 2: Updating main branch...${NC}"
git checkout main
git pull origin main

# Step 3: Create integration branch
echo -e "${BLUE}Step 3: Creating integration branch...${NC}"
git checkout -b "$INTEGRATION_BRANCH"

# Step 4: Merge backend
echo -e "${BLUE}Step 4: Merging backend branch (${BACKEND_BRANCH})...${NC}"
if git merge "origin/$BACKEND_BRANCH" --no-ff -m "merge: integrate backend from $BACKEND_BRANCH"; then
    echo -e "${GREEN}✓ Backend merge successful${NC}"
else
    echo -e "${RED}✗ Backend merge failed - please resolve conflicts${NC}"
    echo -e "${YELLOW}After resolving conflicts, run:${NC}"
    echo -e "  git add ."
    echo -e "  git commit"
    echo -e "  ./merge-to-main.sh --continue"
    exit 1
fi

# Step 5: Merge frontend
echo -e "${BLUE}Step 5: Merging frontend branch (${FRONTEND_BRANCH})...${NC}"
if git merge "origin/$FRONTEND_BRANCH" --no-ff -m "merge: integrate frontend from $FRONTEND_BRANCH"; then
    echo -e "${GREEN}✓ Frontend merge successful${NC}"
else
    echo -e "${RED}✗ Frontend merge failed - please resolve conflicts${NC}"
    echo -e "${YELLOW}After resolving conflicts, run:${NC}"
    echo -e "  git add ."
    echo -e "  git commit"
    echo -e "  ./merge-to-main.sh --continue"
    exit 1
fi

# Step 6: Show summary
echo ""
echo -e "${GREEN}=== Integration Complete ===${NC}"
echo -e "${YELLOW}Integration branch '${INTEGRATION_BRANCH}' created successfully${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Test the integration thoroughly"
echo "2. If tests pass, run: git checkout main && git merge $INTEGRATION_BRANCH"
echo "3. Push to remote: git push origin main"
echo "4. Delete integration branch: git branch -d $INTEGRATION_BRANCH"
echo ""
echo -e "${YELLOW}Or use the helper script:${NC}"
echo "  ./.git-workflow/finalize-merge.sh $INTEGRATION_BRANCH"

