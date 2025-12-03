# Quick Start - Integration Testing
## Run Backend + Frontend Together

echo "==================================="
echo "Sprint 3 Integration Testing Setup"
echo "==================================="
echo ""

# Check we're on integration branch
$branch = git branch --show-current
if ($branch -ne "integration/sprint-3") {
    Write-Host "❌ ERROR: Not on integration/sprint-3 branch!" -ForegroundColor Red
    Write-Host "Current branch: $branch" -ForegroundColor Yellow
    Write-Host "Run: git checkout integration/sprint-3" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ On integration/sprint-3 branch" -ForegroundColor Green
echo ""

# Check backend .env
if (Test-Path "backend\.env") {
    Write-Host "✅ Backend .env file exists" -ForegroundColor Green
} else {
    Write-Host "❌ Backend .env file missing!" -ForegroundColor Red
    Write-Host "Copy from backend/env.example and add your OpenRouter API key" -ForegroundColor Yellow
    exit 1
}

# Check frontend .env
if (Test-Path "frontend\.env") {
    Write-Host "✅ Frontend .env file exists" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend .env file missing - creating it..." -ForegroundColor Yellow
    Set-Content -Path "frontend\.env" -Value "VITE_API_URL=http://localhost:8000"
    Write-Host "✅ Created frontend/.env with VITE_API_URL=http://localhost:8000" -ForegroundColor Green
}

echo ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Ready to start integration testing!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
echo ""

Write-Host "📝 Next steps:" -ForegroundColor Yellow
echo ""
echo "1. Open TWO separate terminals:"
echo ""
echo "   Terminal 1 (Backend):"
echo "   ---------------------"
echo "   cd backend"
echo "   .\venv\Scripts\activate"
echo "   python start_server.py"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   ----------------------"
echo "   cd frontend"
echo "   npm install    # First time only"
echo "   npm run dev"
echo ""
echo "2. Open browser:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API Docs: http://localhost:8000/docs"
echo ""
echo "3. Test the integration:"
echo "   - Login with: admin@aiwebtest.com / admin123"
echo "   - Generate a test"
echo "   - Run the test (Sprint 3 feature!)"
echo "   - Watch execution progress in real-time"
echo ""
Write-Host "📖 See INTEGRATION-TESTING-CHECKLIST.md for full test plan" -ForegroundColor Cyan
echo ""
