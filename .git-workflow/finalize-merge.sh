#!/bin/bash
# Script to finalize merge after testing integration branch
# Usage: ./finalize-merge.sh [integration-branch]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INTEGRATION_BRANCH="${1}"

if [ -z "$INTEGRATION_BRANCH" ]; then
    echo -e "${RED}Error: Please provide integration branch name${NC}"
    echo "Usage: ./finalize-merge.sh <integration-branch>"
    exit 1
fi

echo -e "${BLUE}=== Finalizing Merge to Main ===${NC}"
echo ""

# Confirm with user
read -p "Have you tested the integration branch thoroughly? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Merge cancelled. Please test before finalizing.${NC}"
    exit 0
fi

# Step 1: Switch to main
echo -e "${BLUE}Step 1: Switching to main...${NC}"
git checkout main
git pull origin main

# Step 2: Merge integration branch
echo -e "${BLUE}Step 2: Merging integration branch...${NC}"
git merge "$INTEGRATION_BRANCH" --no-ff -m "merge: finalize integration from $INTEGRATION_BRANCH"

# Step 3: Push to remote
echo -e "${BLUE}Step 3: Pushing to remote...${NC}"
git push origin main

# Step 4: Clean up integration branch
echo -e "${BLUE}Step 4: Cleaning up...${NC}"
git branch -d "$INTEGRATION_BRANCH"

echo ""
echo -e "${GREEN}=== Merge Complete ===${NC}"
echo -e "${GREEN}✓ Changes successfully merged to main${NC}"
echo -e "${GREEN}✓ Integration branch deleted${NC}"
echo ""
echo -e "${YELLOW}Don't forget to:${NC}"
echo "1. Update your development branches from main"
echo "2. Notify your team about the changes"

