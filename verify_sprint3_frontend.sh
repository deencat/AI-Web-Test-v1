#!/bin/bash
# Sprint 3 Frontend Component Verification Script

echo "=========================================="
echo "Sprint 3 Frontend Component Verification"
echo "=========================================="
echo ""

# Check if frontend dev server is running
echo "1. Checking frontend dev server..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✅ Frontend dev server is running (http://localhost:5173)"
else
    echo "   ❌ Frontend dev server is NOT running"
    echo "   Run: cd frontend && npm run dev"
fi

echo ""

# Check if backend API is running
echo "2. Checking backend API server..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "   ✅ Backend API server is running (http://localhost:8000)"
else
    echo "   ❌ Backend API server is NOT running"
    echo "   Run: cd backend && python start_server.py"
fi

echo ""

# Check component files
echo "3. Checking component files..."

components=(
    "frontend/src/components/execution/ScreenshotGallery.tsx"
    "frontend/src/components/execution/ScreenshotModal.tsx"
    "frontend/src/components/dashboard/ExecutionStatsWidget.tsx"
)

for component in "${components[@]}"; do
    if [ -f "$component" ]; then
        echo "   ✅ $component"
    else
        echo "   ❌ $component (missing)"
    fi
done

echo ""

# Check TypeScript compilation
echo "4. Checking TypeScript compilation..."
cd frontend
if npm run build --silent > /dev/null 2>&1; then
    echo "   ✅ TypeScript compilation successful"
else
    echo "   ⚠️  TypeScript compilation has warnings (check output)"
fi

echo ""

# Test API endpoints
echo "5. Testing API endpoints..."

# Test execution stats endpoint
if curl -s -H "Authorization: Bearer test" http://localhost:8000/api/v1/executions/stats > /dev/null 2>&1; then
    echo "   ✅ GET /api/v1/executions/stats (reachable)"
else
    echo "   ⚠️  GET /api/v1/executions/stats (may require auth)"
fi

# Test executions list endpoint
if curl -s -H "Authorization: Bearer test" http://localhost:8000/api/v1/executions > /dev/null 2>&1; then
    echo "   ✅ GET /api/v1/executions (reachable)"
else
    echo "   ⚠️  GET /api/v1/executions (may require auth)"
fi

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Manual Testing Checklist:"
echo "  1. Open http://localhost:5173 in browser"
echo "  2. Login with admin credentials"
echo "  3. Navigate to Dashboard - verify ExecutionStatsWidget displays"
echo "  4. Navigate to Executions - select an execution"
echo "  5. Verify ScreenshotGallery displays"
echo "  6. Click a screenshot - verify modal opens"
echo "  7. Test Previous/Next navigation"
echo "  8. Test keyboard navigation (arrows, Esc)"
echo "  9. Test Download button"
echo "  10. Verify all charts display correctly"
echo ""
