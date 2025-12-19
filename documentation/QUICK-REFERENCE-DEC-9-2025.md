# AI Web Test v1.0 - Quick Reference Guide

**Version**: 1.0.0  
**Date**: December 9, 2025  
**Status**: Production Ready ✅

---

## 🚀 Quick Start

### Start Backend Server
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Start Frontend Server
```bash
cd frontend
npm run dev
```

### Access URLs
- **Frontend**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/api/v1/docs
- **ReDoc**: http://127.0.0.1:8000/api/v1/redoc

### Default Login
- **Username**: admin@aiwebtest.com
- **Password**: admin123

---

## 📊 System Overview

### What It Does
**AI Web Test** is a complete test automation platform that:
1. Generates test cases from natural language using AI
2. Executes tests in real browsers with Playwright
3. Manages test execution queue (5 concurrent tests)
4. Captures screenshots of every step
5. Provides real-time execution monitoring
6. Groups tests into suites for complex workflows

### Key Statistics
- **API Endpoints**: 68+ operational
- **Database Models**: 14 models
- **Frontend Pages**: 10 pages
- **Test Coverage**: 100% (111+ tests)
- **AI Providers**: 3 (Google, Cerebras, OpenRouter)
- **Concurrent Tests**: Up to 5 simultaneous

---

## 🎯 Core Features

### 1. Test Generation (AI-Powered)
**How to Use**:
1. Navigate to Tests page
2. Click "Generate Test"
3. Describe what you want to test in natural language
4. Select AI provider (Google recommended - FREE)
5. Wait 5-90 seconds for AI to generate test
6. Review and save generated test

**API Endpoint**: `POST /api/v1/tests/generate`

**Example Request**:
```json
{
  "requirement": "Test login flow on three.com.hk",
  "test_type": "e2e",
  "num_tests": 3
}
```

---

### 2. Test Execution (Browser Automation)
**How to Use**:
1. Navigate to test detail page
2. Click "Run Test" button
3. Test is queued for execution
4. View real-time progress on execution page
5. See step-by-step results with screenshots
6. Review final results (passed/failed)

**API Endpoint**: `POST /api/v1/tests/{id}/run`

**Features**:
- Real browser automation (Chromium, Firefox, Webkit)
- Screenshot capture every step
- Queue management (max 5 concurrent)
- Priority-based execution
- Real-time monitoring

---

### 3. Test Suites (Group Testing)
**How to Use**:
1. Navigate to Test Suites page
2. Click "Create Suite"
3. Enter suite name and description
4. Select tests to include
5. Add tags for organization
6. Run entire suite with one click

**API Endpoint**: `POST /api/v1/suites`

**Features**:
- Group multiple tests
- Sequential execution
- Tag-based organization
- Suite execution history
- Stop-on-failure option

---

### 4. Knowledge Base (Document Management)
**How to Use**:
1. Navigate to Knowledge Base page
2. Click "Upload Document"
3. Select file (PDF, DOCX, TXT, MD)
4. Choose category
5. Document is uploaded and text extracted
6. Search and filter documents

**API Endpoint**: `POST /api/v1/kb/upload`

**Supported Formats**:
- PDF (PyPDF2)
- DOCX (python-docx)
- TXT (plain text)
- MD (markdown)

---

### 5. Execution History (Audit Trail)
**How to Use**:
1. Navigate to Executions page
2. View list of all test executions
3. Filter by status (pending/running/completed/failed)
4. Filter by result (passed/failed/error)
5. Click execution to view details
6. Delete old executions

**API Endpoint**: `GET /api/v1/executions`

**Features**:
- Complete execution history
- Filtering and search
- Step-by-step results
- Screenshot viewer
- Statistics dashboard
- Delete functionality

---

## 🔧 Configuration

### AI Provider Setup

#### Option 1: Google Gemini (Recommended - FREE)
```env
MODEL_PROVIDER=google
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-2.5-flash
```

**Get API Key**: https://aistudio.google.com/apikey

#### Option 2: Cerebras (Ultra-Fast)
```env
MODEL_PROVIDER=cerebras
CEREBRAS_API_KEY=your-cerebras-api-key-here
CEREBRAS_MODEL=llama-3.1-70b
```

**Get API Key**: https://cloud.cerebras.ai/

#### Option 3: OpenRouter (Fallback)
```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

**Get API Key**: https://openrouter.ai/

---

### Queue Configuration
```env
MAX_CONCURRENT_EXECUTIONS=5  # Max simultaneous tests
QUEUE_CHECK_INTERVAL=2       # Check interval in seconds
EXECUTION_TIMEOUT=300        # Max execution time in seconds
```

---

## 📁 Project Structure

### Backend (`/backend`)
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API routes
│   ├── core/                 # Config, security
│   ├── crud/                 # Database operations
│   ├── db/                   # Database setup
│   ├── models/               # SQLAlchemy models (14)
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── main.py              # FastAPI app
├── artifacts/screenshots/    # Test screenshots
├── uploads/                  # KB documents
└── aiwebtest.db             # SQLite database
```

### Frontend (`/frontend`)
```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   ├── pages/               # Page components (10)
│   ├── services/            # API clients
│   ├── types/               # TypeScript types
│   └── App.tsx             # Main app
└── public/                  # Static assets
```

---

## 🗄️ Database Models

1. **User** - Authentication
2. **TestCase** - Test definitions
3. **TestExecution** - Execution records
4. **ExecutionStep** - Step results
5. **KBDocument** - Documents
6. **KBCategory** - Categories
7. **TestTemplate** - Templates
8. **TestScenario** - Scenarios
9. **TestSuite** - Suites
10. **TestSuiteItem** - Suite items
11. **SuiteExecution** - Suite runs
12. **PasswordResetToken** - Reset tokens
13. **UserSession** - Sessions
14. **Plus junction tables**

---

## 🔌 API Endpoints (68+)

### Authentication (6 endpoints)
- POST `/api/v1/auth/login` - Login
- POST `/api/v1/auth/register` - Register
- POST `/api/v1/auth/logout` - Logout
- GET `/api/v1/auth/me` - Current user
- POST `/api/v1/auth/forgot-password` - Forgot password
- POST `/api/v1/auth/reset-password` - Reset password

### Test Generation (3 endpoints)
- POST `/api/v1/tests/generate` - Generate test
- POST `/api/v1/tests/generate/page` - Generate page test
- POST `/api/v1/tests/generate/api` - Generate API test

### Test Management (6 endpoints)
- POST `/api/v1/tests` - Create test
- GET `/api/v1/tests` - List tests
- GET `/api/v1/tests/{id}` - Get test
- PUT `/api/v1/tests/{id}` - Update test
- DELETE `/api/v1/tests/{id}` - Delete test
- GET `/api/v1/tests/stats` - Statistics

### Test Execution (11 endpoints)
- POST `/api/v1/tests/{id}/run` - Run test
- GET `/api/v1/executions/{id}` - Get execution
- GET `/api/v1/executions` - List executions
- DELETE `/api/v1/executions/{id}` - Delete execution
- GET `/api/v1/executions/stats` - Stats
- GET `/api/v1/executions/queue/status` - Queue status
- GET `/api/v1/executions/queue/statistics` - Queue stats
- GET `/api/v1/executions/queue/active` - Active executions
- POST `/api/v1/executions/queue/clear` - Clear queue
- GET `/artifacts/screenshots/{filename}` - Screenshot
- Plus more...

### Test Suites (7 endpoints)
- POST `/api/v1/suites` - Create suite
- GET `/api/v1/suites` - List suites
- GET `/api/v1/suites/{id}` - Get suite
- PUT `/api/v1/suites/{id}` - Update suite
- DELETE `/api/v1/suites/{id}` - Delete suite
- POST `/api/v1/suites/{id}/run` - Run suite
- GET `/api/v1/suites/{id}/executions` - Suite history

### Knowledge Base (9 endpoints)
- POST `/api/v1/kb/upload` - Upload document
- GET `/api/v1/kb/documents` - List documents
- GET `/api/v1/kb/documents/{id}` - Get document
- PUT `/api/v1/kb/documents/{id}` - Update document
- DELETE `/api/v1/kb/documents/{id}` - Delete document
- Plus categories...

---

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest test_auth.py

# Run integration tests
pytest test_integration_template_to_execution.py
```

### Frontend Tests
```bash
cd frontend

# Run Playwright tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test tests/navigation.spec.ts
```

---

## 📈 Performance Benchmarks

| Metric | Value | Target |
|--------|-------|--------|
| Test Generation | 5-90s | <120s |
| Queue Response | <50ms | <100ms |
| API Response | <200ms | <500ms |
| Execution Success | 100% | >95% |
| Frontend Load | <2s | <3s |

---

## 🔒 Security Features

- ✅ JWT authentication
- ✅ Rate limiting (10/min auth, 50/min general)
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ Input validation (SQL injection, XSS, path traversal)
- ✅ Password hashing (bcrypt)
- ✅ CORS configuration
- ✅ Session management
- ✅ Token refresh

---

## 📚 Documentation

### User Guides
- **QUICK-START-NEW-PC.md** - Setup on new computer
- **QUICK-TEST-INSTRUCTIONS.md** - Run your first test
- **HOW-TO-GENERATE-THREE-HK-TEST.md** - Real-world example
- **HOW-TO-USE-PLAYWRIGHT-TESTS.md** - Testing guide

### Developer Guides
- **FRONTEND-DEVELOPER-QUICK-START.md** - Frontend setup
- **BACKEND-DEVELOPER-QUICK-START.md** - Backend setup
- **FRONTEND-BACKEND-INTEGRATION-GUIDE.md** - Integration

### Feature Guides
- **TEST-SUITES-IMPLEMENTATION-STATUS.md** - Test suites
- **CEREBRAS-INTEGRATION-GUIDE.md** - AI providers
- **MODEL-PROVIDER-COMPARISON.md** - Provider comparison
- **TIMEOUT-FIX-DEC-9.md** - Timeout configuration

### Technical Docs
- **API-CHANGELOG.md** - API changes
- **BACKEND-AUTOMATION-BEST-PRACTICES.md** - Best practices
- **SPRINT-3-TESTING-GUIDE.md** - Testing guide

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Test Generation Timeout
**Problem**: Test generation times out after 30 seconds

**Solution**: Already fixed! Timeouts increased to 120s frontend, 90s backend

#### 2. Queue Full
**Problem**: Can't run test, queue is full

**Solution**: Wait for running tests to complete, or clear queue via admin endpoint

#### 3. Screenshot Not Found
**Problem**: Screenshot path is broken

**Solution**: Ensure `backend/artifacts/screenshots/` directory exists

#### 4. Login Failed
**Problem**: Can't login with default credentials

**Solution**: Ensure backend is running and database is initialized

---

## 🚀 Next Steps

### For Users
1. **Start with Quick Test** - Follow QUICK-TEST-INSTRUCTIONS.md
2. **Generate First Test** - Use natural language
3. **Run Test** - Execute and view results
4. **Create Suite** - Group related tests
5. **Upload Documents** - Build knowledge base

### For Developers
1. **Review Architecture** - Understand code structure
2. **Read API Docs** - Explore Swagger UI
3. **Run Tests** - Ensure everything works
4. **Contribute** - Follow git workflow

---

## 📞 Support

### Resources
- **API Documentation**: http://127.0.0.1:8000/api/v1/docs
- **GitHub Repository**: (Internal)
- **Project Documents**: `/project-documents/`

### Contact
- **Development Team**: development@team.com
- **Issue Tracking**: (Internal system)

---

**Quick Reference Guide - Version 1.0.0**  
**Last Updated**: December 9, 2025  
**Status**: Production Ready ✅
