# AI Web Test - Backend API

FastAPI backend with three-tier test execution (Playwright → Hybrid → Stagehand), queue system, and AI-powered test generation.

**Last Updated:** 2026-06-30  
**Codemap:** [`docs/CODEMAPS/backend.md`](../docs/CODEMAPS/backend.md)  
**Execution engine ADR:** [`documentation/ADR-002-test-execution-engine.md`](../documentation/ADR-002-test-execution-engine.md)

## Current Status

**API:** `/api/v1` (CRUD, execution, KB, settings) + `/api/v2` (agent workflow)  
**Execution:** Three-tier engine via `ThreeTierExecutionService` (fallback strategies A/B/C)  
**Database:** SQLite (dev) or PostgreSQL (production)

## ✨ Features

- ✅ **JWT Authentication** - Secure user authentication
- ✅ **Test Management** - CRUD operations for test cases
- ✅ **AI Test Generation** - Natural language to automated tests
- ✅ **Knowledge Base** - Document upload and categorization
- ✅ **Browser Automation** - Three-tier execution: Playwright (T1), observe+Playwright (T2), Stagehand act (T3)
- ✅ **Queue System** - Concurrent execution management (max 5)
- ✅ **Screenshot Capture** - Every test step documented
- ✅ **Real-time Monitoring** - Live execution progress

## 🚀 Quick Start

### Prerequisites
- Python 3.12.x (tested on 3.12.10)
- OpenRouter API key (for AI features)

### Installation

1. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
```

2. Install dependencies (includes Stagehand + Playwright):
```bash
pip install -r requirements.txt
```

3. Install Chromium browser for Playwright/Stagehand:
```bash
playwright install chromium
```

**Note:** Stagehand (0.5.6) is included in requirements.txt and installed automatically in step 2. Step 3 downloads the actual Chromium browser binary that Stagehand uses for test execution.

4. Configure environment:
```bash
copy env.example .env  # Windows
# cp env.example .env  # Mac/Linux

# Edit .env with your OpenRouter API key
notepad .env  # Windows
# nano .env  # Mac/Linux
```

### Running the Server

**Method 1: Using start_server.py (Recommended)**
```bash
python start_server.py
```

**Method 2: Using uvicorn directly**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Access the API

- **API Root:** http://127.0.0.1:8000/
- **Swagger UI:** http://127.0.0.1:8000/api/v1/docs
- **ReDoc:** http://127.0.0.1:8000/api/v1/redoc
- **OpenAPI Schema:** http://127.0.0.1:8000/api/v1/openapi.json

### Test Login

**Default Admin Account:**
- Email: `admin@aiwebtest.com`
- Password: `admin123`

**Test in Swagger UI:**
1. Open http://127.0.0.1:8000/api/v1/docs
2. Click on POST `/api/v1/auth/login`
3. Click "Try it out"
4. Enter credentials
5. Click "Execute"
6. Copy the `access_token` from response
7. Click "Authorize" button at top
8. Paste token
9. Now all endpoints will work!

## 📌 API Endpoints (47 total)

### Authentication (2)
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/register` - Register new user

### Test Management (6)
- `POST /api/v1/tests` - Create test case
- `GET /api/v1/tests` - List all tests
- `GET /api/v1/tests/{id}` - Get test details
- `PUT /api/v1/tests/{id}` - Update test
- `DELETE /api/v1/tests/{id}` - Delete test
- `POST /api/v1/tests/generate` - AI test generation

### Test Execution (9) ✨ Sprint 3
- `POST /api/v1/tests/{id}/run` - Execute test (queues execution)
- `GET /api/v1/executions/{id}` - Get execution details
- `GET /api/v1/executions` - List executions (with filters)
- `GET /api/v1/executions/stats` - Execution statistics
- `DELETE /api/v1/executions/{id}` - Delete execution
- `GET /api/v1/executions/queue/status` - Queue status
- `GET /api/v1/executions/queue/statistics` - Queue stats
- `GET /api/v1/executions/queue/active` - Active executions
- `POST /api/v1/executions/queue/clear` - Clear queue (admin)

### Knowledge Base (13)
- `POST /api/v1/kb/upload` - Upload document
- `GET /api/v1/kb/documents` - List documents
- `GET /api/v1/kb/documents/{id}` - Get document
- `PUT /api/v1/kb/documents/{id}` - Update document
- `DELETE /api/v1/kb/documents/{id}` - Delete document
- `GET /api/v1/kb/categories` - List categories
- `POST /api/v1/kb/categories` - Create category
- `GET /api/v1/kb/statistics` - KB statistics
- + 5 more endpoints

### Users (2)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user

### Health (2)
- `GET /api/v1/health` - API health check
- `GET /api/v1/health/db` - Database health check

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (DB session, auth)
│   │   └── v1/
│   │       ├── api.py           # API router aggregator
│   │       └── endpoints/
│   │           ├── auth.py      # Authentication endpoints
│   │           ├── users.py     # User endpoints
│   │           └── health.py    # Health check endpoints
│   ├── core/
│   │   ├── config.py            # Settings/environment
│   │   └── security.py          # JWT utilities
│   ├── crud/
│   │   └── user.py              # User CRUD operations
│   ├── db/
│   │   ├── base.py              # SQLAlchemy base
│   │   ├── session.py           # DB session
│   │   └── init_db.py           # DB initialization
│   ├── models/
│   │   └── user.py              # User model
│   ├── schemas/
│   │   ├── user.py              # User Pydantic schemas
│   │   └── token.py             # Token schemas
│   ├── services/                # Business logic services
│   └── main.py                  # FastAPI app entry point
├── tests/                       # Tests
├── .env                         # Environment variables
├── env.example                  # Example environment variables
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Development

### Test User (Created on Startup)
- Username: `admin`
- Password: `admin123`
- Email: `admin@aiwebtest.com`
- Role: `admin`

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🧪 Testing

### Quick Verification

```bash
# Activate venv first
.\venv\Scripts\activate

# Run quick verification (5 tests)
python test_final_verification.py
```

**Expected Output:**
```
[OK] Login successful
[OK] Test case retrieved
[OK] 5 tests queued
[OK] 3/5 completed
[OK] ALL SYSTEMS GO!
```

### Integration Tests

```bash
# Run complete integration test (13 tests)
python test_integration_e2e.py
```

**Expected Output:**
```
[✓] ALL TESTS PASSED!
13/13 tests succeeded
```

### Generate Sample Data

```bash
# Create 10 tests + 30 executions
python generate_sample_data.py
```

This creates realistic data for frontend development.

### Postman Collection

Import `AI-Web-Test-Postman-Collection.json` into Postman to test all endpoints interactively.

### Clear 3-tier execution xpath cache
1. activate backend venv
2. 
python -c "
from app.db.session import SessionLocal
from app.models.execution_settings import XPathCache
db = SessionLocal()
n = db.query(XPathCache).delete()
db.commit()
db.close()
print(f'Deleted {n} xpath cache entries')
"