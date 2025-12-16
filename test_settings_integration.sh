#!/bin/bash

# Settings Page Dynamic Configuration - Integration Test
# This script verifies that user settings work for both test generation and execution

echo "======================================================================"
echo "Settings Page Dynamic Configuration - Integration Test"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Prerequisites:${NC}"
echo "1. Backend server running on http://localhost:8000"
echo "2. Admin user credentials: admin / admin123"
echo "3. Database migration applied (user_settings table exists)"
echo ""

read -p "Press Enter to start tests or Ctrl+C to cancel..."
echo ""

# Test 1: Backend API Test
echo -e "${YELLOW}Test 1: Backend API Tests${NC}"
echo "Running backend/test_settings_api.py..."
cd backend
python test_settings_api.py
API_RESULT=$?

if [ $API_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ API Tests Passed${NC}"
else
    echo -e "${RED}❌ API Tests Failed${NC}"
    exit 1
fi
echo ""

# Test 2: Execution Settings Test
echo -e "${YELLOW}Test 2: Execution Settings Persistence${NC}"
echo "Running backend/test_execution_settings.py..."
python test_execution_settings.py
EXEC_RESULT=$?

if [ $EXEC_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Execution Settings Test Passed${NC}"
else
    echo -e "${RED}❌ Execution Settings Test Failed${NC}"
    exit 1
fi
echo ""

# Summary
echo "======================================================================"
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo "======================================================================"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Open frontend at http://localhost:5173"
echo "2. Navigate to Settings page"
echo "3. Configure Test Generation provider (e.g., Google Gemini)"
echo "4. Configure Test Execution provider (e.g., Cerebras)"
echo "5. Generate a test case and check backend logs for:"
echo "   [DEBUG] 🎯 Loaded user generation config: provider=google, model=gemini-2.5-flash"
echo "6. Run a test execution and check backend logs for:"
echo "   [DEBUG] 🎯 Using user's configured provider: cerebras"
echo ""
echo -e "${GREEN}Settings Page Dynamic Configuration is ready for use!${NC}"
echo ""
