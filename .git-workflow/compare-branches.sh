#!/bin/bash
# Script to compare two branches
# Usage: ./compare-branches.sh [branch1] [branch2]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

BRANCH1="${1:-main}"
BRANCH2="${2:-$(git branch --show-current)}"

echo -e "${BLUE}=== Comparing Branches ===${NC}"
echo -e "${YELLOW}Branch 1: ${BRANCH1}${NC}"
echo -e "${YELLOW}Branch 2: ${BRANCH2}${NC}"
echo ""

# Commits in branch2 not in branch1
echo -e "${CYAN}Commits in ${BRANCH2} not in ${BRANCH1}:${NC}"
git log "${BRANCH1}..${BRANCH2}" --oneline --no-merges | sed 's/^/  /' || echo "  None"
echo ""

# Commits in branch1 not in branch2
echo -e "${CYAN}Commits in ${BRANCH1} not in ${BRANCH2}:${NC}"
git log "${BRANCH2}..${BRANCH1}" --oneline --no-merges | sed 's/^/  /' || echo "  None"
echo ""

# Files changed
echo -e "${CYAN}Files changed between branches:${NC}"
git diff --name-status "${BRANCH1}...${BRANCH2}" | sed 's/^/  /'
echo ""

# Statistics
echo -e "${CYAN}Statistics:${NC}"
git diff --stat "${BRANCH1}...${BRANCH2}"
echo ""

# Check for potential conflicts
echo -e "${CYAN}Checking for potential merge conflicts...${NC}"
git merge-tree "$(git merge-base ${BRANCH1} ${BRANCH2})" "${BRANCH1}" "${BRANCH2}" | grep -A 3 "changed in both" | sed 's/^/  /' || echo -e "  ${GREEN}No obvious conflicts detected${NC}"

