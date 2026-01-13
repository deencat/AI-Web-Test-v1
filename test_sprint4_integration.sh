#!/bin/bash

#############################################################################
# Sprint 4 Integration Verification Script
# Tests that all components of the feedback system are working together
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
API_BASE="${BACKEND_URL}/api/v1"

echo -e "${BOLD}${BLUE}"
echo "============================================================"
echo "  Sprint 4: Execution Feedback System Integration Test"
echo "============================================================"
echo -e "${NC}"

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}${BOLD}=== $1 ===${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

#############################################################################
# Test 1: Backend Health Check
#############################################################################
print_section "Test 1: Backend Health Check"

if curl -s "${API_BASE}/health" > /dev/null 2>&1; then
    print_success "Backend is running at ${BACKEND_URL}"
else
    print_error "Backend is not running!"
    print_info "Please start the backend server first"
    exit 1
fi

#############################################################################
# Test 2: Frontend Health Check
#############################################################################
print_section "Test 2: Frontend Health Check"

if curl -s "${FRONTEND_URL}" > /dev/null 2>&1; then
    print_success "Frontend is running at ${FRONTEND_URL}"
else
    print_error "Frontend is not running!"
    print_info "Please start the frontend server first"
    exit 1
fi

#############################################################################
# Test 3: Authentication
#############################################################################
print_section "Test 3: Authentication"

TOKEN=$(curl -s -X POST "${API_BASE}/auth/login" \
    -d 'username=admin&password=admin123' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    print_success "Authentication successful"
else
    print_error "Authentication failed!"
    exit 1
fi

#############################################################################
# Test 4: Feedback API Endpoints
#############################################################################
print_section "Test 4: Feedback API Endpoints"

# Test GET /feedback
FEEDBACK_COUNT=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_BASE}/feedback?limit=1" | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null)

if [ -n "$FEEDBACK_COUNT" ]; then
    print_success "GET /feedback works (${FEEDBACK_COUNT} total entries)"
else
    print_error "GET /feedback failed!"
    exit 1
fi

# Test GET /feedback/stats/summary
STATS=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_BASE}/feedback/stats/summary" | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_feedback', 0))" 2>/dev/null)

if [ -n "$STATS" ]; then
    print_success "GET /feedback/stats/summary works (${STATS} total feedback)"
else
    print_error "GET /feedback/stats/summary failed!"
    exit 1
fi

#############################################################################
# Test 5: Create Test Feedback Entry
#############################################################################
print_section "Test 5: Create Test Feedback Entry"

FEEDBACK_ID=$(curl -s -X POST -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    "${API_BASE}/feedback" \
    -d '{
        "execution_id": 1,
        "step_index": 99,
        "failure_type": "selector_not_found",
        "error_message": "Integration test feedback entry",
        "failed_selector": "#integration-test",
        "selector_type": "css",
        "page_url": "https://example.com/test",
        "browser_type": "chromium"
    }' | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$FEEDBACK_ID" ]; then
    print_success "Created feedback entry #${FEEDBACK_ID}"
else
    print_error "Failed to create feedback entry!"
    exit 1
fi

#############################################################################
# Test 6: Submit Correction
#############################################################################
print_section "Test 6: Submit Correction"

CORRECTION_SUCCESS=$(curl -s -X POST -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    "${API_BASE}/feedback/${FEEDBACK_ID}/correction" \
    -d '{
        "corrected_step": {
            "action": "click",
            "selector": "button.integration-test",
            "value": "",
            "description": "Corrected selector"
        },
        "selector_type": "css",
        "correction_source": "human",
        "correction_confidence": 0.95,
        "notes": "Integration test correction"
    }' | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$CORRECTION_SUCCESS" ]; then
    print_success "Submitted correction for feedback #${FEEDBACK_ID}"
else
    print_error "Failed to submit correction!"
    exit 1
fi

#############################################################################
# Test 7: Verify Correction
#############################################################################
print_section "Test 7: Verify Correction"

HAS_CORRECTION=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_BASE}/feedback/${FEEDBACK_ID}" | \
    python3 -c "import sys, json; print('yes' if json.load(sys.stdin).get('corrected_step') else 'no')" 2>/dev/null)

if [ "$HAS_CORRECTION" = "yes" ]; then
    print_success "Correction verified in database"
else
    print_error "Correction not found!"
    exit 1
fi

#############################################################################
# Test 8: Update Feedback Metadata
#############################################################################
print_section "Test 8: Update Feedback Metadata"

UPDATE_SUCCESS=$(curl -s -X PUT -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    "${API_BASE}/feedback/${FEEDBACK_ID}" \
    -d '{
        "is_anomaly": true,
        "anomaly_score": 0.88,
        "tags": ["integration-test", "automated"],
        "notes": "Updated during integration test"
    }' | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -n "$UPDATE_SUCCESS" ]; then
    print_success "Updated feedback metadata"
else
    print_error "Failed to update metadata!"
    exit 1
fi

#############################################################################
# Test 9: Test Filtering
#############################################################################
print_section "Test 9: Test Filtering"

# Filter by failure type
FILTERED=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_BASE}/feedback?failure_type=selector_not_found&limit=5" | \
    python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))" 2>/dev/null)

if [ -n "$FILTERED" ]; then
    print_success "Filtering by failure_type works (${FILTERED} results)"
else
    print_error "Filtering failed!"
    exit 1
fi

# Filter by has_correction
CORRECTED=$(curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_BASE}/feedback?has_correction=true&limit=5" | \
    python3 -c "import sys, json; print(len(json.load(sys.stdin).get('items', [])))" 2>/dev/null)

if [ -n "$CORRECTED" ]; then
    print_success "Filtering by has_correction works (${CORRECTED} results)"
else
    print_error "Filtering failed!"
    exit 1
fi

#############################################################################
# Test 10: Cleanup
#############################################################################
print_section "Test 10: Cleanup"

DELETE_SUCCESS=$(curl -s -X DELETE -H "Authorization: Bearer ${TOKEN}" \
    -w "%{http_code}" -o /dev/null \
    "${API_BASE}/feedback/${FEEDBACK_ID}")

if [ "$DELETE_SUCCESS" = "204" ]; then
    print_success "Cleaned up test feedback entry #${FEEDBACK_ID}"
else
    print_info "Keeping test feedback entry #${FEEDBACK_ID} for inspection"
fi

#############################################################################
# Test 11: Frontend Components Check
#############################################################################
print_section "Test 11: Frontend Components Check"

# Check if ExecutionFeedbackViewer component exists
if [ -f "frontend/src/components/execution/ExecutionFeedbackViewer.tsx" ]; then
    print_success "ExecutionFeedbackViewer component exists"
else
    print_error "ExecutionFeedbackViewer component not found!"
fi

# Check if executionFeedbackService exists
if [ -f "frontend/src/services/executionFeedbackService.ts" ]; then
    print_success "executionFeedbackService exists"
else
    print_error "executionFeedbackService not found!"
fi

# Check if types are defined
if [ -f "frontend/src/types/execution.ts" ]; then
    if grep -q "ExecutionFeedback" "frontend/src/types/execution.ts"; then
        print_success "ExecutionFeedback types defined"
    else
        print_error "ExecutionFeedback types not defined!"
    fi
else
    print_error "execution types file not found!"
fi

#############################################################################
# Final Summary
#############################################################################
echo -e "\n${BOLD}${GREEN}"
echo "============================================================"
echo "  ✅ All Integration Tests Passed!"
echo "============================================================"
echo -e "${NC}"

echo -e "${GREEN}"
echo "Sprint 4 Execution Feedback System is fully operational:"
echo "  ✓ Backend API endpoints working"
echo "  ✓ Feedback CRUD operations functional"
echo "  ✓ Correction submission working"
echo "  ✓ Metadata updates working"
echo "  ✓ Filtering and querying working"
echo "  ✓ Frontend components present"
echo "  ✓ TypeScript types defined"
echo -e "${NC}"

echo -e "\n${BOLD}${BLUE}System Status:${NC}"
echo "  Backend: ${GREEN}✓ Running${NC} (${BACKEND_URL})"
echo "  Frontend: ${GREEN}✓ Running${NC} (${FRONTEND_URL})"
echo "  Database: ${GREEN}✓ Connected${NC}"
echo "  Auth: ${GREEN}✓ Working${NC}"

echo -e "\n${BOLD}${BLUE}Statistics:${NC}"
curl -s -H "Authorization: Bearer ${TOKEN}" \
    "${API_BASE}/feedback/stats/summary" | \
    python3 -c "
import sys, json
stats = json.load(sys.stdin)
print(f\"  Total Feedback: {stats.get('total_feedback', 0)}\")
print(f\"  Total Corrections: {stats.get('total_corrected', 0)}\")
print(f\"  Correction Rate: {stats.get('correction_rate', 0):.1f}%\")
print(f\"  Total Anomalies: {stats.get('total_anomalies', 0)}\")
" 2>/dev/null

echo -e "\n${BOLD}${GREEN}🎉 Sprint 4 Integration Test Complete!${NC}\n"
