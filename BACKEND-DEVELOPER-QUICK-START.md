# Backend Developer Quick Start
## For You (Cursor or VS Code + Copilot)

**Your Focus:** FastAPI + Python backend development  
**Working Directory:** `backend/`  
**IDE:** Cursor (or VS Code with Copilot as fallback)

---

## ⚡ 5-Minute Setup

```powershell
# Windows PowerShell
cd AI-Web-Test-v1/backend

# Use the startup script (auto-activates venv)
.\run_server.ps1
```

```bash
# macOS/Linux
cd AI-Web-Test-v1/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Backend API:** http://127.0.0.1:8000  
**Swagger UI:** http://127.0.0.1:8000/docs  
**Test Login:** admin / admin123

---

## 🎯 Your Sprint 2 Tasks

### **Week 3: Test Generation Backend**

**Status:** ✅ Days 1-5 COMPLETE | 🎯 Days 6-10 In Progress

---

#### **Day 1-2: OpenRouter Integration** ✅ COMPLETE
```python
# Create: backend/app/services/openrouter.py

import httpx
from app.core.config import settings

class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "openai/gpt-4-turbo"
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages
                }
            )
            return response.json()
```

**Achievements:**
- ✅ 14 working free models discovered
- ✅ Mixtral 8x7B selected as default (best quality, free)
- ✅ Zero-cost API integration
- ✅ File created: `backend/app/services/openrouter.py`

---

#### **Day 2: Test Generation Service** ✅ COMPLETE
```python
# Create: backend/app/services/generation.py

from app.services.openrouter import OpenRouterService

class TestGenerationService:
    def __init__(self):
        self.openrouter = OpenRouterService()
    
    async def generate_tests(self, prompt: str) -> list[dict]:
        system_prompt = """You are a test case generator.
        Generate detailed test cases in JSON format.
        Each test case should have: title, description, steps, expected_result"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.openrouter.chat_completion(messages)
        # Parse and return test cases
        return self._parse_test_cases(response)
```

**Achievements:**
- ✅ Structured JSON output from LLM
- ✅ High-quality test case generation
- ✅ File created: `backend/app/services/test_generation.py`
- ✅ Prompt engineering completed

---

#### **Day 3: Database Models & API Endpoints** ✅ COMPLETE

**1. Create Model** (`app/models/test.py`):
```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
import datetime

class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    steps = Column(Text)  # JSON string
    expected_result = Column(Text)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="test_cases")
```

**2. Create Schema** (`app/schemas/test.py`):
```python
from pydantic import BaseModel
from datetime import datetime

class TestCaseBase(BaseModel):
    title: str
    description: str | None = None
    steps: list[str]
    expected_result: str
    status: str = "pending"

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    steps: list[str] | None = None
    expected_result: str | None = None
    status: str | None = None

class TestCase(TestCaseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True

class GenerateTestRequest(BaseModel):
    prompt: str

class GenerateTestResponse(BaseModel):
    test_cases: list[TestCase]
```

**3. Create CRUD** (`app/crud/test.py`):
```python
from sqlalchemy.orm import Session
from app.models.test import TestCase
from app.schemas.test import TestCaseCreate, TestCaseUpdate
import json

def create_test(db: Session, test: TestCaseCreate, user_id: int) -> TestCase:
    db_test = TestCase(
        **test.model_dump(exclude={"steps"}),
        steps=json.dumps(test.steps),
        user_id=user_id
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

def get_tests(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(TestCase).filter(
        TestCase.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_test(db: Session, test_id: int, user_id: int):
    return db.query(TestCase).filter(
        TestCase.id == test_id,
        TestCase.user_id == user_id
    ).first()

def update_test(db: Session, test_id: int, test: TestCaseUpdate, user_id: int):
    db_test = get_test(db, test_id, user_id)
    if not db_test:
        return None
    
    update_data = test.model_dump(exclude_unset=True)
    if "steps" in update_data:
        update_data["steps"] = json.dumps(update_data["steps"])
    
    for key, value in update_data.items():
        setattr(db_test, key, value)
    
    db.commit()
    db.refresh(db_test)
    return db_test

def delete_test(db: Session, test_id: int, user_id: int):
    db_test = get_test(db, test_id, user_id)
    if db_test:
        db.delete(db_test)
        db.commit()
        return True
    return False
```

**4. Create Endpoint** (`app/api/v1/endpoints/tests.py`):
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas import test as schemas
from app.crud import test as crud
from app.services.generation import TestGenerationService
from app.models.user import User

router = APIRouter()
test_gen_service = TestGenerationService()

@router.post("/generate", response_model=schemas.GenerateTestResponse)
async def generate_tests(
    request: schemas.GenerateTestRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Generate test cases from natural language prompt."""
    test_cases = await test_gen_service.generate_tests(request.prompt)
    
    # Save to database
    saved_tests = []
    for tc in test_cases:
        db_test = crud.create_test(
            db, 
            schemas.TestCaseCreate(**tc),
            current_user.id
        )
        saved_tests.append(db_test)
    
    return {"test_cases": saved_tests}

@router.get("/", response_model=list[schemas.TestCase])
def get_tests(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get all test cases for current user."""
    return crud.get_tests(db, current_user.id, skip, limit)

@router.get("/{test_id}", response_model=schemas.TestCase)
def get_test(
    test_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get a specific test case."""
    test = crud.get_test(db, test_id, current_user.id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.put("/{test_id}", response_model=schemas.TestCase)
def update_test(
    test_id: int,
    test: schemas.TestCaseUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Update a test case."""
    updated = crud.update_test(db, test_id, test, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Test not found")
    return updated

@router.delete("/{test_id}")
def delete_test(
    test_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Delete a test case."""
    if not crud.delete_test(db, test_id, current_user.id):
        raise HTTPException(status_code=404, detail="Test not found")
    return {"message": "Test deleted successfully"}
```

**5. Register Router** (`app/api/v1/api.py`):
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, health, tests

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(tests.router, prefix="/tests", tags=["tests"])  # Add this
```

**Achievements:**
- ✅ 6 new files created (~1,370 lines)
- ✅ 9 API endpoints (3 generation + 6 CRUD)
- ✅ Database: TestCase model + 3 enums
- ✅ Validation: 10 Pydantic schemas
- ✅ CRUD: 9 database functions
- ✅ Authentication & authorization
- ✅ Auto-generated Swagger docs
- ✅ All tests passing (9/9 - 100%)
- ✅ Repository cleaned (Python cache removed)

**Files Created:**
1. `backend/app/models/test_case.py` (90 lines)
2. `backend/app/schemas/test_case.py` (200 lines)
3. `backend/app/crud/test_case.py` (240 lines)
4. `backend/app/api/v1/endpoints/test_generation.py` (150 lines)
5. `backend/app/api/v1/endpoints/tests.py` (310 lines)
6. `backend/test_api_endpoints.py` (380 lines)

**API Endpoints Available:**
- `POST /api/v1/tests/generate` - Generate tests from requirements
- `POST /api/v1/tests/generate/page` - Generate for specific page
- `POST /api/v1/tests/generate/api` - Generate for API endpoint
- `GET /api/v1/tests/stats` - Get test statistics
- `GET /api/v1/tests` - List tests (with filters)
- `POST /api/v1/tests` - Create test case
- `GET /api/v1/tests/{id}` - Get test case
- `PUT /api/v1/tests/{id}` - Update test case
- `DELETE /api/v1/tests/{id}` - Delete test case

**Test it now:**
- Open: http://127.0.0.1:8000/docs
- Authorize with admin/admin123
- Try POST /api/v1/tests/generate

---

#### **Day 4: Knowledge Base System** ✅ COMPLETE

**Achievements:**
- ✅ 9 API endpoints (upload, list, CRUD, download, stats)
- ✅ File upload handling (PDF, DOCX, TXT, MD)
- ✅ Text extraction from documents
- ✅ 8 predefined categories
- ✅ Full authentication & authorization
- ✅ Search & filtering
- ✅ Usage tracking (reference count)

**Files Created:**
1. `backend/app/models/kb_document.py` - KBDocument + KBCategory models
2. `backend/app/schemas/kb_document.py` - 10 Pydantic schemas
3. `backend/app/services/file_upload.py` - File upload service
4. `backend/app/crud/kb_document.py` - 9 CRUD functions
5. `backend/app/api/v1/endpoints/kb.py` - 9 API endpoints
6. `backend/app/db/init_kb_categories.py` - Category seeding
7. `backend/test_kb_api.py` - Testing script

**API Endpoints:**
- `GET /api/v1/kb/categories` - List categories (public)
- `POST /api/v1/kb/categories` - Create category (admin)
- `POST /api/v1/kb/upload` - Upload document
- `GET /api/v1/kb` - List documents (with filters)
- `GET /api/v1/kb/stats` - Get statistics
- `GET /api/v1/kb/{id}` - Get document details
- `PUT /api/v1/kb/{id}` - Update document
- `DELETE /api/v1/kb/{id}` - Delete document
- `GET /api/v1/kb/{id}/download` - Download file

**Test it:**
```powershell
# Verify KB system
.\venv\Scripts\python.exe verify_day4.py

# Full API tests
.\venv\Scripts\python.exe test_kb_api.py

# Or use Swagger UI
# http://127.0.0.1:8000/docs
```

---

#### **Day 5: Backend Enhancements & Polish** ✅ COMPLETE

**Achievements:**
- ✅ Custom exception handling (9 exception types)
- ✅ Response wrapper schemas (standard API format)
- ✅ Pagination helpers (consistent pagination)
- ✅ Enhanced search (multi-field test case search)
- ✅ Performance monitoring (timing middleware)
- ✅ Enhanced health check (detailed system info)
- ✅ API documentation (version endpoint)
- ✅ All tests passing (7/7 - 100%)

**Files Created:**
1. `backend/app/core/exceptions.py` - 9 custom exception classes
2. `backend/app/schemas/response.py` - Standard response wrappers
3. `backend/app/schemas/pagination.py` - Pagination helpers
4. `backend/app/middleware/__init__.py` - Middleware package
5. `backend/app/middleware/timing.py` - Performance monitoring
6. `backend/test_day5_enhancements.py` - Verification tests
7. `DAY-5-COMPLETION-REPORT.md` - Comprehensive report

**Files Modified:**
1. `backend/app/main.py` - Exception handlers, middleware, version endpoint
2. `backend/app/crud/test_case.py` - Added search function
3. `backend/app/api/v1/endpoints/health.py` - Enhanced health checks

**New Features:**
- **Custom Exceptions:** 9 exception types (ValidationError, NotFoundError, etc.)
- **Response Wrappers:** Standard format with success/error, data, metadata
- **Pagination:** Consistent pagination with total, page, per_page, has_next/prev
- **Search:** Multi-field search across title, description, expected_result, preconditions
- **Performance:** Request timing headers (X-Process-Time, X-Request-ID)
- **Health Check:** Detailed system info (services, statistics, features)
- **API Version:** Capability discovery endpoint

**New Endpoints:**
- `GET /api/version` - API version & capabilities
- `GET /api/v1/health/detailed` - Comprehensive health check

**Test it:**
```powershell
# Verify Day 5 enhancements
.\venv\Scripts\python.exe test_day5_enhancements.py

# Check API version
curl http://127.0.0.1:8000/api/version

# Check detailed health
curl http://127.0.0.1:8000/api/v1/health/detailed

# Or use Swagger UI
# http://127.0.0.1:8000/docs
```

**Benefits for Frontend:**
- ✅ Consistent API responses (easy parsing)
- ✅ Clear error messages (user-friendly)
- ✅ Pagination metadata (easy UI controls)
- ✅ Powerful search (across multiple fields)
- ✅ Performance tracking (monitor speed)
- ✅ System health visibility (backend status)

---

## 🔧 Daily Commands

```powershell
# Start server (Windows)
.\run_server.ps1

# Test authentication
python test_auth.py

# Check database
python check_db.py

# Create migration
alembic revision --autogenerate -m "Add test_cases table"

# Apply migration
alembic upgrade head

# Run tests
python -m pytest
```

---

## 📁 Project Structure

```
backend/app/
├── main.py              # FastAPI app
├── api/
│   ├── deps.py         # Dependencies
│   └── v1/
│       ├── api.py      # Router aggregation
│       └── endpoints/
│           ├── auth.py
│           ├── users.py
│           ├── tests.py    ← Create this
│           └── kb.py       ← Create this
├── core/
│   ├── config.py       # Settings
│   └── security.py     # JWT, passwords
├── crud/
│   ├── user.py
│   ├── test.py         ← Create this
│   └── kb.py           ← Create this
├── models/
│   ├── user.py
│   ├── test.py         ← Create this
│   └── kb.py           ← Create this
├── schemas/
│   ├── user.py
│   ├── token.py
│   ├── test.py         ← Create this
│   └── kb.py           ← Create this
└── services/
    ├── openrouter.py   ← Create this
    ├── generation.py   ← Create this
    └── kb_processor.py ← Create this
```

---

## 🔄 When Frontend Needs New Endpoint

**Frontend will ask:**
```
Need endpoint to get all test cases with filtering:
GET /api/v1/tests?status=pending&page=1&limit=10
```

**Your steps:**

1. **Add to CRUD** (`crud/test.py`):
```python
def get_tests_filtered(
    db: Session,
    user_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(TestCase).filter(TestCase.user_id == user_id)
    if status:
        query = query.filter(TestCase.status == status)
    return query.offset(skip).limit(limit).all()
```

2. **Add endpoint** (`endpoints/tests.py`):
```python
@router.get("/", response_model=list[schemas.TestCase])
def get_tests(
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    return crud.get_tests_filtered(db, current_user.id, status, skip, limit)
```

3. **Test in Swagger UI** (http://127.0.0.1:8000/docs)

4. **Notify frontend:**
```
Endpoint ready:
GET /api/v1/tests?status=pending&skip=0&limit=10

Response:
[
  {
    "id": 1,
    "title": "Test login",
    "description": "...",
    "steps": ["Step 1", "Step 2"],
    "expected_result": "...",
    "status": "pending",
    "user_id": 1,
    "created_at": "2025-11-19T10:00:00",
    "updated_at": null
  }
]

Update types in frontend/src/types/api.ts
```

---

## 🗄️ Database Migrations

### **Create Migration**

```bash
# After adding new model
alembic revision --autogenerate -m "Add test_cases table"

# Review the migration file in alembic/versions/
# Edit if needed

# Apply migration
alembic upgrade head
```

### **Common Migration Issues**

**Issue:** "Target database is not up to date"
```bash
# Solution: Check current version
alembic current

# Upgrade to latest
alembic upgrade head
```

**Issue:** Need to rollback
```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

---

## 🧪 Testing Your Endpoints

### **1. Swagger UI (Recommended)**

1. Go to http://127.0.0.1:8000/docs
2. Click "Authorize" button
3. Login with admin/admin123
4. Test your endpoints

### **2. Python Script**

```python
# test_generation.py
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Generate tests
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/tests/generate",
    json={"prompt": "Test login flow for Three HK"},
    headers=headers
)
print(response.json())
```

### **3. curl**

```bash
# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token
curl -X GET http://127.0.0.1:8000/api/v1/tests \
  -H "Authorization: Bearer <token>"
```

---

## 🐛 Common Issues & Solutions

### **Issue: OpenRouter API key not set**

```python
# In backend/.env
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Get key from: https://openrouter.ai/keys
```

### **Issue: Database locked**

```bash
# Stop all processes
# Delete database
rm aiwebtest.db

# Restart server (will recreate)
.\run_server.ps1
```

### **Issue: Import errors**

```bash
# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### **Issue: CORS errors from frontend**

```python
# In backend/.env
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Restart server
```

---

## 📞 Communication with Frontend Developer

### **When you complete an endpoint:**

```
Endpoint ready: POST /api/v1/tests/generate

Request:
{
  "prompt": "Test login flow for Three HK"
}

Response:
{
  "test_cases": [
    {
      "id": 1,
      "title": "Verify login with valid credentials",
      "description": "Test that users can login with correct username/password",
      "steps": [
        "Navigate to login page",
        "Enter username: testuser",
        "Enter password: Test123!",
        "Click login button"
      ],
      "expected_result": "User is redirected to dashboard",
      "status": "pending",
      "user_id": 1,
      "created_at": "2025-11-19T10:00:00"
    }
  ]
}

Please update frontend/src/types/api.ts with TestCase type
```

### **When you need frontend input:**

```
Planning KB upload endpoint. Questions:
1. What file types? (PDF, DOCX, TXT?)
2. Max file size? (10MB?)
3. Need categories immediately or can add later?
4. Should I extract text automatically or just store file?

Let me know so I can design the API correctly.
```

### **Daily sync:**

```
Yesterday: Completed OpenRouter integration
Today: Working on test generation service
Blocked: Need OpenRouter API key (getting it today)
```

---

## 📚 Resources

**Documentation:**
- `TEAM-SPLIT-HANDOFF-GUIDE.md` - Full guide
- `backend/README.md` - Backend docs
- `docs/API-REQUIREMENTS.md` - API contracts

**Code Examples:**
- `app/api/v1/endpoints/auth.py` - Endpoint patterns
- `app/crud/user.py` - CRUD patterns
- `app/models/user.py` - Model patterns

**External:**
- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- OpenRouter Docs: https://openrouter.ai/docs

---

## ✅ Setup Checklist

- [ ] Cloned repo
- [ ] Virtual environment created
- [ ] `pip install -r requirements.txt` completed
- [ ] Backend runs on http://127.0.0.1:8000
- [ ] Can access Swagger UI
- [ ] `test_auth.py` passes
- [ ] Cursor (or VS Code) configured
- [ ] Got OpenRouter API key
- [ ] Read Sprint 2 tasks
- [ ] Created your git branch
- [ ] Contacted frontend developer

---

## 🎯 Your Goal This Week

**Build the Test Generation API that:**
1. Accepts natural language prompts
2. Calls OpenRouter (GPT-4/Claude)
3. Generates structured test cases
4. Saves to database
5. Returns to frontend

**Make it work, then make it fast, then make it perfect!** 🚀

---

**Need Help?**
1. Check `TEAM-SPLIT-HANDOFF-GUIDE.md`
2. Ask frontend developer
3. Review existing code patterns
4. Use Cursor/Copilot for suggestions

**Good luck! 💪**

