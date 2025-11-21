# Team Split Handoff Guide
## Frontend Developer (VS Code + Copilot) & Backend Developer (Cursor/VS Code)

**Date:** November 19, 2025  
**Sprint 1 Status:** ✅ 100% Complete  
**Next Phase:** Sprint 2 - Test Generation Agent  

---

## 📋 Table of Contents

1. [Quick Start for Both Developers](#quick-start-for-both-developers)
2. [Frontend Developer Setup](#frontend-developer-setup)
3. [Backend Developer Setup](#backend-developer-setup)
4. [Git Workflow & Collaboration](#git-workflow--collaboration)
5. [Communication & Coordination](#communication--coordination)
6. [Sprint 2 Task Division](#sprint-2-task-division)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start for Both Developers

### **Prerequisites**
- ✅ Git installed and configured
- ✅ Node.js 18+ (for frontend)
- ✅ Python 3.11+ (for backend)
- ✅ VS Code or Cursor IDE

### **Initial Setup (Both)**

```bash
# 1. Clone the repository (or pull latest)
git clone <repository-url>
cd AI-Web-Test-v1

# 2. Create your own branch
git checkout -b <your-name>/sprint-2-dev

# 3. Pull latest changes
git pull origin main
```

---

## 🎨 Frontend Developer Setup

### **Your Friend's Workspace**

**IDE:** VS Code with GitHub Copilot Agent  
**Focus:** Frontend development (React + TypeScript)  
**Working Directory:** `frontend/`

### **Step 1: Install Dependencies**

```bash
cd frontend
npm install
```

### **Step 2: Environment Configuration**

Create `frontend/.env`:

```env
# For development with live backend
VITE_USE_MOCK=false
VITE_API_URL=http://localhost:8000/api

# For development without backend (mock data)
# VITE_USE_MOCK=true
```

### **Step 3: Start Development Server**

```bash
# From frontend/ directory
npm run dev
```

Frontend will run on: **http://localhost:5173**

### **Step 4: Run Tests**

```bash
# Make sure backend is running first!
npm test

# Run tests in UI mode
npm run test:ui

# Run tests in headed mode (see browser)
npm run test:headed
```

### **Frontend Project Structure**

```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── ui/           # Base components (Button, Input, Card)
│   │   └── layout/       # Layout components (Header, Sidebar)
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── TestsPage.tsx
│   │   ├── KnowledgeBasePage.tsx
│   │   └── SettingsPage.tsx
│   ├── services/         # API services
│   │   ├── api.ts        # Axios instance
│   │   ├── authService.ts
│   │   ├── testService.ts
│   │   ├── kbService.ts
│   │   └── settingsService.ts
│   ├── types/            # TypeScript types
│   │   └── api.ts        # API types
│   ├── mock/             # Mock data
│   │   ├── users.ts
│   │   ├── tests.ts
│   │   └── knowledgeBase.ts
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx
│   ├── hooks/            # Custom hooks
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── tests/
│   └── e2e/              # Playwright E2E tests
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── playwright.config.ts
```

### **Key Files to Know**

| File | Purpose |
|------|---------|
| `src/services/api.ts` | Axios instance, interceptors, token management |
| `src/types/api.ts` | All TypeScript types for API entities |
| `src/contexts/AuthContext.tsx` | Authentication state management |
| `src/App.tsx` | Routing and protected routes |

### **Frontend Development Workflow**

1. **Always work with backend running** (or use mock mode)
2. **Run tests frequently** (`npm test`)
3. **Check TypeScript errors** (`npm run type-check`)
4. **Follow existing component patterns**
5. **Update types in `types/api.ts` when API changes**

### **VS Code Extensions Recommended**

```json
{
  "recommendations": [
    "GitHub.copilot",
    "GitHub.copilot-chat",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-playwright.playwright"
  ]
}
```

### **Frontend Sprint 2 Tasks**

**Your friend should focus on:**

1. **Test Generation UI** (Week 3)
   - Natural language input form
   - Test case display component
   - Test case list with filtering
   - Test case detail view

2. **Knowledge Base Upload UI** (Week 3)
   - File upload component
   - Document list view
   - Category management UI

3. **Test Management UI** (Week 4)
   - Edit test cases
   - Delete test cases
   - Bulk operations
   - Test execution UI (placeholder)

4. **Dashboard Updates** (Week 4)
   - Add charts (Recharts)
   - Update stats to show real data
   - Recent activity feed

---

## 🔧 Backend Developer Setup

### **Your Workspace**

**IDE:** Cursor (or VS Code with Copilot as fallback)  
**Focus:** Backend development (FastAPI + Python)  
**Working Directory:** `backend/`

### **Step 1: Create Virtual Environment**

```powershell
# Windows PowerShell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# Or use the provided script
.\run_server.ps1
```

```bash
# macOS/Linux
cd backend
python3 -m venv venv
source venv/bin/activate
```

### **Step 2: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 3: Environment Configuration**

Create `backend/.env`:

```env
# Database
DATABASE_URL=sqlite:///./aiwebtest.db

# Security
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Project
PROJECT_NAME=AI Web Test API
API_V1_STR=/api/v1

# OpenRouter (for Sprint 2)
OPENROUTER_API_KEY=your-key-here
```

### **Step 4: Start Backend Server**

```powershell
# Windows (recommended - auto-activates venv)
.\run_server.ps1

# Or manually
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# macOS/Linux
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will run on: **http://127.0.0.1:8000**  
API Docs (Swagger): **http://127.0.0.1:8000/docs**

### **Step 5: Test Backend**

```bash
# Test authentication flow
python test_auth.py

# Test JWT tokens
python test_jwt.py

# Check database
python check_db.py
```

### **Backend Project Structure**

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── deps.py          # Dependencies (auth, db)
│   │   └── v1/
│   │       ├── api.py       # Router aggregation
│   │       └── endpoints/   # API endpoints
│   │           ├── auth.py      # Login, register, me
│   │           ├── users.py     # User CRUD
│   │           ├── health.py    # Health checks
│   │           ├── tests.py     # Test cases (Sprint 2)
│   │           └── kb.py        # Knowledge base (Sprint 2)
│   ├── core/
│   │   ├── config.py        # Settings (Pydantic)
│   │   └── security.py      # JWT, password hashing
│   ├── crud/
│   │   ├── user.py          # User CRUD operations
│   │   ├── test.py          # Test CRUD (Sprint 2)
│   │   └── kb.py            # KB CRUD (Sprint 2)
│   ├── db/
│   │   ├── base.py          # SQLAlchemy base
│   │   ├── session.py       # Database session
│   │   └── init_db.py       # DB initialization
│   ├── models/
│   │   ├── user.py          # User model
│   │   ├── test.py          # Test model (Sprint 2)
│   │   └── kb.py            # KB model (Sprint 2)
│   ├── schemas/
│   │   ├── user.py          # User schemas
│   │   ├── token.py         # Token schemas
│   │   ├── test.py          # Test schemas (Sprint 2)
│   │   └── kb.py            # KB schemas (Sprint 2)
│   └── services/
│       ├── openrouter.py    # OpenRouter integration (Sprint 2)
│       ├── generation.py    # Test generation (Sprint 2)
│       └── kb_processor.py  # KB processing (Sprint 2)
├── tests/                   # Backend tests
├── venv/                    # Virtual environment (gitignored)
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (gitignored)
└── run_server.ps1          # Server startup script
```

### **Key Files to Know**

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, CORS, router inclusion |
| `app/core/config.py` | All configuration settings |
| `app/core/security.py` | JWT creation/verification, password hashing |
| `app/api/deps.py` | Dependency injection (get_db, get_current_user) |
| `app/models/` | SQLAlchemy database models |
| `app/schemas/` | Pydantic schemas for validation |

### **Backend Development Workflow**

1. **Always test endpoints in Swagger UI** (http://127.0.0.1:8000/docs)
2. **Use Pydantic for all request/response validation**
3. **Follow existing patterns** (CRUD, endpoints, schemas)
4. **Update frontend types** when adding new endpoints
5. **Write test scripts** for complex flows
6. **Document API changes** in `docs/API-REQUIREMENTS.md`

### **Cursor/VS Code Extensions Recommended**

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "GitHub.copilot",
    "GitHub.copilot-chat"
  ]
}
```

### **Backend Sprint 2 Tasks**

**You should focus on:**

1. **OpenRouter Integration** (Week 3, Day 1-2)
   - Create `services/openrouter.py`
   - Implement chat completion API
   - Add error handling and retries
   - Test with GPT-4 and Claude

2. **Test Generation Service** (Week 3, Day 2-3)
   - Create `services/generation.py`
   - Design prompt templates
   - Implement test case generation logic
   - Add validation and formatting

3. **Test Case CRUD** (Week 3, Day 3-4)
   - Create `models/test.py` (SQLAlchemy)
   - Create `schemas/test.py` (Pydantic)
   - Create `crud/test.py` (CRUD operations)
   - Create `endpoints/tests.py` (API endpoints)

4. **Knowledge Base System** (Week 3-4)
   - Create `models/kb.py`
   - Create `schemas/kb.py`
   - Create `crud/kb.py`
   - Create `endpoints/kb.py`
   - Implement file upload
   - Add text extraction (PDF, DOCX)

5. **Database Schema Updates** (Week 3)
   - Design test_cases table
   - Design kb_documents table
   - Design kb_categories table
   - Create Alembic migrations

---

## 🔄 Git Workflow & Collaboration

### **Branch Strategy**

```
main (protected)
├── frontend-dev (your friend's work)
│   ├── feature/test-generation-ui
│   ├── feature/kb-upload-ui
│   └── feature/dashboard-charts
└── backend-dev (your work)
    ├── feature/openrouter-integration
    ├── feature/test-generation-service
    └── feature/kb-crud
```

### **Daily Workflow**

**Morning (Both):**
```bash
# 1. Pull latest changes
git checkout main
git pull origin main

# 2. Merge into your branch
git checkout <your-branch>
git merge main

# 3. Start working
```

**Evening (Both):**
```bash
# 1. Commit your work
git add .
git commit -m "feat(area): description"

# 2. Push to your branch
git push origin <your-branch>

# 3. Create PR if feature is complete
```

### **Commit Message Convention**

Follow this format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```bash
# Frontend
git commit -m "feat(ui): Add test generation input form"
git commit -m "fix(auth): Fix token refresh on 401"
git commit -m "style(dashboard): Update card styling"

# Backend
git commit -m "feat(api): Add test generation endpoint"
git commit -m "fix(auth): Fix JWT token expiration"
git commit -m "docs(api): Update OpenAPI schema"
```

### **Merge Strategy**

**Option 1: Feature Branches (Recommended)**
```bash
# Frontend developer
git checkout -b feature/test-generation-ui
# ... work ...
git commit -m "feat(ui): Add test generation form"
git push origin feature/test-generation-ui
# Create PR to main

# Backend developer
git checkout -b feature/test-generation-api
# ... work ...
git commit -m "feat(api): Add test generation endpoint"
git push origin feature/test-generation-api
# Create PR to main
```

**Option 2: Long-lived Dev Branches**
```bash
# Frontend developer works on frontend-dev
git checkout frontend-dev
# ... daily commits ...
git push origin frontend-dev

# Backend developer works on backend-dev
git checkout backend-dev
# ... daily commits ...
git push origin backend-dev

# Merge to main weekly or when feature complete
```

### **Handling Conflicts**

**If frontend and backend touch the same files:**

1. **Communication first!** Discuss who should make the change
2. **Pull before push:**
   ```bash
   git pull origin main
   # Resolve conflicts
   git add .
   git commit -m "merge: Resolve conflicts with main"
   git push
   ```

3. **Common conflict areas:**
   - `docs/API-REQUIREMENTS.md` - Backend updates, frontend reads
   - `frontend/src/types/api.ts` - Backend defines, frontend uses
   - `README.md` - Both may update

**Resolution strategy:**
- Backend defines API contracts first
- Frontend implements UI based on contracts
- Use PR reviews to catch issues early

---

## 💬 Communication & Coordination

### **Daily Sync (Recommended)**

**Quick 10-minute call or chat:**
1. What did you complete yesterday?
2. What are you working on today?
3. Any blockers or questions?
4. Any API changes needed?

### **API Contract Communication**

**When Backend adds/changes an endpoint:**

1. **Update `docs/API-REQUIREMENTS.md`**
2. **Notify frontend developer:**
   ```
   Hey! Added new endpoint:
   POST /api/v1/tests/generate
   Request: { prompt: string }
   Response: { test_cases: TestCase[] }
   
   Updated types needed in frontend/src/types/api.ts
   ```

3. **Frontend developer updates types:**
   ```typescript
   // frontend/src/types/api.ts
   export interface GenerateTestRequest {
     prompt: string;
   }
   
   export interface GenerateTestResponse {
     test_cases: TestCase[];
   }
   ```

### **Shared Documentation**

**Both developers should update:**
- `docs/API-REQUIREMENTS.md` - API contracts
- `CHANGELOG.md` - Notable changes
- `README.md` - Setup instructions

**Backend updates:**
- `backend/README.md` - Backend-specific docs
- Swagger/OpenAPI docs (auto-generated)

**Frontend updates:**
- `frontend/README.md` - Frontend-specific docs
- Component documentation (Storybook if added)

### **Issue Tracking**

**Create issues for:**
- New features
- Bugs
- API changes needed
- Questions/discussions

**Label them:**
- `frontend` / `backend`
- `bug` / `feature` / `question`
- `sprint-2` / `sprint-3`
- `blocked` / `in-progress` / `ready-for-review`

---

## 📋 Sprint 2 Task Division

### **Week 3: Test Generation Feature**

| Day | Frontend (Your Friend) | Backend (You) |
|-----|------------------------|---------------|
| **Mon** | Design test generation UI mockups | OpenRouter API integration |
| **Tue** | Build input form component | Test generation service logic |
| **Wed** | Build test case display component | Test case CRUD endpoints |
| **Thu** | Integrate with API | KB document upload endpoint |
| **Fri** | Testing & bug fixes | Testing & bug fixes |

### **Week 4: Knowledge Base & Polish**

| Day | Frontend (Your Friend) | Backend (You) |
|-----|------------------------|---------------|
| **Mon** | KB upload UI | KB CRUD operations |
| **Tue** | KB document list view | Text extraction service |
| **Wed** | Test management UI | Test execution planning |
| **Thu** | Dashboard charts | Performance optimization |
| **Fri** | E2E testing | API documentation |

### **Parallel Work (No Conflicts)**

**Frontend can work independently on:**
- UI components and styling
- Mock data for new features
- Playwright tests (with mocks)
- Dashboard charts
- Settings page updates

**Backend can work independently on:**
- OpenRouter integration
- Database models
- CRUD operations
- Background jobs
- Admin endpoints

### **Sequential Work (Requires Coordination)**

**Backend must complete first:**
1. API endpoint definition → Frontend can build UI
2. Response schema → Frontend can update types
3. Database models → Frontend knows data structure

**Frontend should provide:**
1. UI mockups → Backend knows what data to return
2. User flow → Backend understands requirements
3. Error scenarios → Backend handles edge cases

---

## 🐛 Troubleshooting

### **Frontend Issues**

**Problem:** Tests failing with "Failed to fetch"
```bash
# Solution: Make sure backend is running
cd backend
.\run_server.ps1

# Or use mock mode
# In frontend/.env
VITE_USE_MOCK=true
```

**Problem:** TypeScript errors after backend changes
```bash
# Solution: Update types in frontend/src/types/api.ts
# Ask backend developer for new schema
```

**Problem:** CORS errors
```bash
# Solution: Check backend/.env has correct CORS origins
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

### **Backend Issues**

**Problem:** Database locked
```bash
# Solution: Stop all backend processes
# Delete aiwebtest.db
# Restart server (will recreate DB)
```

**Problem:** Module not found
```bash
# Solution: Activate venv and reinstall
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Problem:** Port 8000 already in use
```powershell
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Or change port in run_server.ps1
```

### **Git Issues**

**Problem:** Merge conflicts
```bash
# Solution: Pull and resolve
git pull origin main
# Edit conflicted files
git add .
git commit -m "merge: Resolve conflicts"
```

**Problem:** Accidentally committed to main
```bash
# Solution: Create branch from current state
git branch my-work
git reset --hard origin/main
git checkout my-work
```

---

## 📚 Key Resources

### **Documentation**

| Document | Purpose | Owner |
|----------|---------|-------|
| `README.md` | Project overview | Both |
| `docs/API-REQUIREMENTS.md` | API contracts | Backend |
| `project-documents/AI-Web-Test-v1-Sprint-1-Plan.md` | Sprint 1 summary | Both |
| `project-documents/AI-Web-Test-v1-Project-Management-Plan.md` | Overall plan | Both |
| `backend/README.md` | Backend setup | Backend |
| `frontend/README.md` | Frontend setup | Frontend |

### **Quick Commands**

**Frontend:**
```bash
npm run dev          # Start dev server
npm test            # Run Playwright tests
npm run build       # Production build
npm run type-check  # Check TypeScript
```

**Backend:**
```bash
.\run_server.ps1              # Start server (Windows)
python test_auth.py           # Test auth flow
python -m pytest              # Run tests
alembic revision --autogenerate  # Create migration
alembic upgrade head          # Apply migrations
```

### **API Testing**

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health Check:** http://127.0.0.1:8000/api/v1/health

### **Test Credentials**

```
Username: admin
Password: admin123
```

---

## 🎯 Success Checklist

### **Frontend Developer (Your Friend)**

- [ ] Cloned repo and created branch
- [ ] `npm install` completed successfully
- [ ] Frontend runs on http://localhost:5173
- [ ] Can login with admin/admin123
- [ ] All 69 tests passing
- [ ] VS Code with Copilot configured
- [ ] Understands `src/types/api.ts` structure
- [ ] Knows how to toggle mock mode

### **Backend Developer (You)**

- [ ] Cloned repo and created branch
- [ ] Virtual environment created
- [ ] `pip install -r requirements.txt` completed
- [ ] Backend runs on http://127.0.0.1:8000
- [ ] Can access Swagger UI
- [ ] `test_auth.py` passes
- [ ] Cursor (or VS Code) configured
- [ ] Understands project structure
- [ ] Knows how to create migrations

### **Both Developers**

- [ ] Agreed on branch strategy
- [ ] Agreed on daily sync time
- [ ] Agreed on communication channel
- [ ] Read Sprint 2 plan
- [ ] Understand task division
- [ ] Know how to handle conflicts
- [ ] Have each other's contact info

---

## 🚀 Ready to Start!

**Frontend Developer:** Focus on UI/UX, let backend define APIs  
**Backend Developer:** Focus on APIs, provide clear contracts to frontend

**Communication is key!** 🗣️

Good luck with Sprint 2! 🎉

---

**Questions?**
- Check existing documentation first
- Ask your teammate
- Review Sprint 1 code for patterns
- Check commit history for context

