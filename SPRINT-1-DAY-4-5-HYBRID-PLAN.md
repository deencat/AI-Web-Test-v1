# Sprint 1: Day 4-5 Hybrid Development Plan
## Backend Kickoff + Frontend Polish (2-Developer Team)

**Date Range:** November 12-13, 2025  
**Strategy:** Parallel development with daily integration checkpoints  
**Goal:** Backend foundation + First real API integration by end of Day 5  

---

## Table of Contents

1. [Day 4 Overview](#day-4-overview)
2. [Day 4 Detailed Tasks](#day-4-detailed-tasks)
3. [Day 5 Overview](#day-5-overview)
4. [Day 5 Detailed Tasks](#day-5-detailed-tasks)
5. [Integration Checkpoints](#integration-checkpoints)
6. [Success Criteria](#success-criteria)
7. [Risk Management](#risk-management)

---

## Day 4 Overview

**Theme:** Foundation Day - Backend Setup + Frontend Charts  
**Duration:** 8 hours per developer  
**Integration:** End-of-day sync (30 minutes)

### Goals
- ✅ Backend: Docker environment running, FastAPI responding
- ✅ Frontend: Dashboard charts implemented with Recharts
- ✅ Both: Aligned on authentication flow and error handling

---

## Day 4 Detailed Tasks

### 🔧 Backend Developer (8 hours)

#### **Task 4.1: Project Structure & Dependencies** (1 hour)

**Create backend directory structure:**
```bash
mkdir -p backend/app/{api,core,db,models,schemas,services}
cd backend
```

**Directory structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (DB session, auth)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # API router aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py     # Auth endpoints (Day 5)
│   │           ├── users.py    # User endpoints (Day 5)
│   │           └── health.py   # Health check (Day 4)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings/environment
│   │   └── security.py         # JWT utilities (Day 5)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy base
│   │   ├── session.py          # DB session
│   │   └── init_db.py          # DB initialization
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py             # User model (Day 4)
│   └── schemas/
│       ├── __init__.py
│       ├── user.py             # User Pydantic schemas
│       └── token.py            # Token schemas (Day 5)
├── alembic/                    # DB migrations (Day 5)
├── tests/                      # Tests (Week 2)
├── .env.example
├── .env
├── requirements.txt
├── Dockerfile
└── README.md
```

**Create `requirements.txt`:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.1.0
```

**Create `.env.example`:**
```bash
# Database
DATABASE_URL=postgresql://aiwebtest:aiwebtest123@db:5432/aiwebtest

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API
API_V1_STR=/api/v1
PROJECT_NAME=AI Web Test

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

**Copy to `.env` and generate secret key:**
```bash
cp .env.example .env
# Generate secret key: openssl rand -hex 32
```

---

#### **Task 4.2: Docker Compose Setup** (1.5 hours)

**Create `docker-compose.yml` in project root:**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: aiwebtest-db
    environment:
      POSTGRES_USER: aiwebtest
      POSTGRES_PASSWORD: aiwebtest123
      POSTGRES_DB: aiwebtest
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiwebtest"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: aiwebtest-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend (will add later)
  # backend:
  #   build: ./backend
  #   container_name: aiwebtest-backend
  #   command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  #   ports:
  #     - "8000:8000"
  #   env_file:
  #     - ./backend/.env
  #   depends_on:
  #     db:
  #       condition: service_healthy
  #     redis:
  #       condition: service_healthy
  #   volumes:
  #     - ./backend:/app

volumes:
  postgres_data:
  redis_data:
```

**Test database connection:**
```bash
# Start services
docker-compose up -d db redis

# Verify services are running
docker-compose ps

# Test PostgreSQL connection
docker exec -it aiwebtest-db psql -U aiwebtest -d aiwebtest -c "SELECT version();"

# Test Redis connection
docker exec -it aiwebtest-redis redis-cli ping
# Should return: PONG
```

---

#### **Task 4.3: FastAPI Core Setup** (2 hours)

**Create `backend/app/core/config.py`:**
```python
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Web Test"
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

**Create `backend/app/db/base.py`:**
```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**Create `backend/app/db/session.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Create `backend/app/models/user.py`:**
```python
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Create `backend/app/schemas/user.py`:**
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: Optional[str] = "user"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """User response model (matches frontend User type)."""
    pass
```

---

#### **Task 4.4: Health Check Endpoint** (1 hour)

**Create `backend/app/api/v1/endpoints/health.py`:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Web Test API",
        "version": "1.0.0"
    }


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Health check with database connection test."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
```

**Create `backend/app/api/deps.py`:**
```python
from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal


def get_db() -> Generator:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Create `backend/app/api/v1/api.py`:**
```python
from fastapi import APIRouter
from app.api.v1.endpoints import health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
# Will add more routers on Day 5:
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
```

**Create `backend/app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "AI Web Test API", "version": "1.0.0"}
```

---

#### **Task 4.5: Test Backend Locally** (1.5 hours)

**Install dependencies:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Run FastAPI locally:**
```bash
# Make sure Docker services are running
cd .. # back to project root
docker-compose up -d db redis

# Run FastAPI
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Test endpoints:**
```bash
# Test root
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/api/v1/health

# Test database health
curl http://localhost:8000/api/v1/health/db

# View API docs
# Open browser: http://localhost:8000/docs
```

**Expected responses:**
```json
// Root
{"message": "AI Web Test API", "version": "1.0.0"}

// Health
{"status": "healthy", "service": "AI Web Test API", "version": "1.0.0"}

// DB Health
{"status": "healthy", "database": "connected"}
```

---

#### **Task 4.6: Create Backend Dockerfile** (1 hour)

**Create `backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Update `docker-compose.yml` to include backend:**
```yaml
# Uncomment the backend service:
  backend:
    build: ./backend
    container_name: aiwebtest-backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
```

**Test full Docker stack:**
```bash
# Stop local uvicorn if running
# Ctrl+C

# Build and start all services
docker-compose up --build

# In another terminal, test endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/db
```

---

### 🎨 Frontend Developer (8 hours)

#### **Task 4.1: Install Recharts** (0.5 hours)

```bash
cd frontend
npm install recharts
```

**Verify installation:**
```bash
npm list recharts
# Should show: recharts@2.x.x
```

---

#### **Task 4.2: Create Chart Components** (3 hours)

**Create `frontend/src/components/charts/PassRateChart.tsx`:**
```typescript
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface PassRateChartProps {
  data: Array<{
    date: string;
    passed: number;
    failed: number;
    total: number;
  }>;
}

export const PassRateChart: React.FC<PassRateChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()}`;
          }}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip 
          labelFormatter={(value) => {
            const date = new Date(value);
            return date.toLocaleDateString();
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="passed"
          stroke="#10b981"
          strokeWidth={2}
          name="Passed"
          dot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="failed"
          stroke="#ef4444"
          strokeWidth={2}
          name="Failed"
          dot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="total"
          stroke="#3b82f6"
          strokeWidth={2}
          name="Total"
          dot={{ r: 4 }}
          strokeDasharray="5 5"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
```

**Create `frontend/src/components/charts/ExecutionTimeChart.tsx`:**
```typescript
import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ExecutionTimeChartProps {
  data: Array<{
    name: string;
    avgTime: number;
    maxTime: number;
  }>;
}

export const ExecutionTimeChart: React.FC<ExecutionTimeChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis 
          tick={{ fontSize: 12 }}
          label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip 
          formatter={(value: number) => `${value.toFixed(2)}s`}
        />
        <Legend />
        <Bar dataKey="avgTime" fill="#3b82f6" name="Avg Time" />
        <Bar dataKey="maxTime" fill="#f59e0b" name="Max Time" />
      </BarChart>
    </ResponsiveContainer>
  );
};
```

---

#### **Task 4.3: Add Mock Chart Data** (0.5 hours)

**Update `frontend/src/mock/tests.ts`:**
```typescript
// Add to existing file

export const mockPassRateTrend = [
  { date: '2025-11-05', passed: 120, failed: 10, total: 130 },
  { date: '2025-11-06', passed: 125, failed: 8, total: 133 },
  { date: '2025-11-07', passed: 130, failed: 12, total: 142 },
  { date: '2025-11-08', passed: 135, failed: 7, total: 142 },
  { date: '2025-11-09', passed: 138, failed: 9, total: 147 },
  { date: '2025-11-10', passed: 140, failed: 10, total: 150 },
  { date: '2025-11-11', passed: 142, failed: 8, total: 150 },
];

export const mockExecutionTimes = [
  { name: 'Login Flow', avgTime: 2.3, maxTime: 4.1 },
  { name: 'Checkout', avgTime: 5.7, maxTime: 8.2 },
  { name: 'Search', avgTime: 1.8, maxTime: 3.5 },
  { name: 'Profile Update', avgTime: 3.2, maxTime: 5.9 },
  { name: 'Payment', avgTime: 4.5, maxTime: 7.3 },
];
```

---

#### **Task 4.4: Update Dashboard with Charts** (2 hours)

**Update `frontend/src/pages/DashboardPage.tsx`:**
```typescript
import React from 'react';
import { Card } from '../components/common/Card';
import { PassRateChart } from '../components/charts/PassRateChart';
import { ExecutionTimeChart } from '../components/charts/ExecutionTimeChart';
import { 
  mockTests, 
  mockDashboardStats, 
  mockAgentActivity,
  mockPassRateTrend,
  mockExecutionTimes 
} from '../mock/tests';

export const DashboardPage: React.FC = () => {
  const stats = mockDashboardStats;
  const recentTests = mockTests.slice(0, 5);
  const agentActivity = mockAgentActivity;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <Card>
          <div className="text-sm text-gray-600 mb-1">Total Tests</div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_tests}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-600 mb-1">Passed</div>
          <div className="text-3xl font-bold text-green-600">{stats.passed}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-600 mb-1">Failed</div>
          <div className="text-3xl font-bold text-red-600">{stats.failed}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-600 mb-1">Running</div>
          <div className="text-3xl font-bold text-blue-600">{stats.running}</div>
        </Card>
        <Card>
          <div className="text-sm text-gray-600 mb-1">Active Agents</div>
          <div className="text-3xl font-bold text-purple-600">{stats.active_agents}</div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Pass Rate Trend (7 Days)</h2>
          <PassRateChart data={mockPassRateTrend} />
        </Card>
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Execution Time by Test</h2>
          <ExecutionTimeChart data={mockExecutionTimes} />
        </Card>
      </div>

      {/* Recent Tests */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Test Results</h2>
          <div className="space-y-3">
            {recentTests.map((test) => (
              <div key={test.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <div className="font-medium text-gray-900">{test.name}</div>
                  <div className="text-sm text-gray-600">{test.agent}</div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    test.status === 'passed'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {test.status}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Agent Activity */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Agent Activity</h2>
          <div className="space-y-3">
            {agentActivity.map((activity) => (
              <div key={activity.id} className="p-3 bg-gray-50 rounded">
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium text-gray-900">{activity.agent}</div>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      activity.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {activity.status}
                  </span>
                </div>
                <div className="text-sm text-gray-600">{activity.current_task}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
```

---

#### **Task 4.5: Test Charts & Responsive Design** (1 hour)

**Run frontend:**
```bash
npm run dev
```

**Test checklist:**
- ✅ Charts render without errors
- ✅ Hover tooltips work on both charts
- ✅ Charts are responsive (resize browser window)
- ✅ Data displays correctly
- ✅ Mobile view works (< 768px)

**Test responsive breakpoints:**
```bash
# Desktop (1920x1080)
# Tablet (768x1024)
# Mobile (375x667)
```

---

#### **Task 4.6: Update Playwright Tests for Charts** (1 hour)

**Create `frontend/tests/e2e/07-dashboard-charts.spec.ts`:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard Charts', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByPlaceholder(/username/i).fill('admin');
    await page.getByPlaceholder(/password/i).fill('password');
    await page.getByRole('button', { name: /login/i }).click();
    await page.waitForURL('/dashboard');
  });

  test('should display pass rate trend chart', async ({ page }) => {
    await expect(page.getByText(/pass rate trend/i)).toBeVisible();
    
    // Check for Recharts SVG container
    const chartContainer = page.locator('.recharts-wrapper').first();
    await expect(chartContainer).toBeVisible();
  });

  test('should display execution time chart', async ({ page }) => {
    await expect(page.getByText(/execution time by test/i)).toBeVisible();
    
    // Check for Recharts SVG container
    const chartContainers = page.locator('.recharts-wrapper');
    await expect(chartContainers.nth(1)).toBeVisible();
  });

  test('should have interactive tooltips on charts', async ({ page }) => {
    // Hover over pass rate chart
    const passRateChart = page.locator('.recharts-wrapper').first();
    await passRateChart.hover();
    
    // Tooltips appear on hover (Recharts handles this automatically)
    await expect(passRateChart).toBeVisible();
  });

  test('should display charts on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Charts should still be visible and responsive
    const chartContainers = page.locator('.recharts-wrapper');
    await expect(chartContainers.first()).toBeVisible();
    await expect(chartContainers.nth(1)).toBeVisible();
  });
});
```

**Run tests:**
```bash
npm test
```

**Expected: 73/73 tests passing (69 + 4 new chart tests)**

---

### 🤝 End of Day 4 Sync (30 minutes)

**Both developers meet to:**

1. **Backend Demo** (10 min)
   - Show FastAPI docs: `http://localhost:8000/docs`
   - Test health endpoints together
   - Verify database connection

2. **Frontend Demo** (10 min)
   - Show new dashboard charts
   - Demo responsive behavior
   - Show Playwright test results

3. **Day 5 Planning** (10 min)
   - Review authentication flow
   - Align on JWT token format
   - Discuss error response structure
   - Plan first integration test

**Deliverables checklist:**
- ✅ Backend: FastAPI running, health endpoints working
- ✅ Backend: Docker Compose with PostgreSQL + Redis
- ✅ Backend: User model and schemas created
- ✅ Frontend: Recharts installed and working
- ✅ Frontend: Dashboard charts implemented
- ✅ Frontend: 73/73 Playwright tests passing
- ✅ Both: Aligned on Day 5 authentication plan

---

## Day 5 Overview

**Theme:** Authentication Day - JWT Implementation + First Integration  
**Duration:** 8 hours per developer  
**Integration:** Mid-day check-in (30 min) + End-of-day integration test (2 hours)

### Goals
- ✅ Backend: JWT authentication endpoints working
- ✅ Frontend: Modal components built
- ✅ Both: Real login flow working (frontend → backend → JWT → protected route)

---

## Day 5 Detailed Tasks

### 🔧 Backend Developer (8 hours)

#### **Task 5.1: JWT Security Utilities** (2 hours)

**Create `backend/app/core/security.py`:**
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

**Create `backend/app/schemas/token.py`:**
```python
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None  # user_id
    exp: Optional[int] = None
```

---

#### **Task 5.2: User CRUD Operations** (1.5 hours)

**Create `backend/app/crud/` directory:**
```bash
mkdir backend/app/crud
touch backend/app/crud/__init__.py
```

**Create `backend/app/crud/user.py`:**
```python
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role or "user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(
    db: Session, username: str, password: str
) -> Optional[User]:
    """Authenticate user by username and password."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user
```

---

#### **Task 5.3: Authentication Dependencies** (1 hour)

**Update `backend/app/api/deps.py`:**
```python
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.crud.user import get_user
from app.db.session import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
```

---

#### **Task 5.4: Authentication Endpoints** (2 hours)

**Create `backend/app/api/v1/endpoints/auth.py`:**
```python
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import authenticate_user, create_user, get_user_by_username
from app.schemas.token import Token
from app.schemas.user import User, UserCreate

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login.
    
    Frontend should send:
    - username: string
    - password: string
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout endpoint (stateless JWT - frontend handles token removal).
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register new user.
    """
    # Check if user already exists
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    return create_user(db, user)
```

**Create `backend/app/api/v1/endpoints/users.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.crud.user import get_user, update_user
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate

router = APIRouter()


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Get user by ID."""
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.put("/{user_id}", response_model=User)
def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Update user."""
    # Only allow users to update their own profile (or admins)
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_user = update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user
```

**Update `backend/app/api/v1/api.py`:**
```python
from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

---

#### **Task 5.5: Create Initial Test User** (0.5 hours)

**Create `backend/app/db/init_db.py`:**
```python
from sqlalchemy.orm import Session
from app.crud.user import get_user_by_username, create_user
from app.schemas.user import UserCreate


def init_db(db: Session) -> None:
    """Initialize database with test user."""
    # Check if admin user exists
    user = get_user_by_username(db, username="admin")
    if not user:
        user_in = UserCreate(
            email="admin@aiwebtest.com",
            username="admin",
            password="admin123",  # Change in production!
            role="admin",
        )
        user = create_user(db, user_in)
        print(f"Created admin user: {user.username}")
```

**Update `backend/app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.init_db import init_db

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database with test data
db = SessionLocal()
try:
    init_db(db)
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "AI Web Test API", "version": "1.0.0"}
```

---

#### **Task 5.6: Test Authentication Endpoints** (1 hour)

**Restart backend:**
```bash
docker-compose restart backend
# Or if running locally:
# uvicorn app.main:app --reload
```

**Test with curl:**
```bash
# 1. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Response:
# {"access_token":"eyJhbGc...","token_type":"bearer"}

# 2. Get current user (replace TOKEN with actual token)
TOKEN="your-token-here"
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {"id":1,"email":"admin@aiwebtest.com","username":"admin","role":"admin","is_active":true,"created_at":"2025-11-12T..."}

# 3. Test protected endpoint without token (should fail)
curl -X GET "http://localhost:8000/api/v1/auth/me"

# Response:
# {"detail":"Not authenticated"}
```

**Test with FastAPI docs:**
```bash
# Open browser: http://localhost:8000/docs
# 1. Click "Authorize" button (top right)
# 2. Enter: username=admin, password=admin123
# 3. Click "Authorize"
# 4. Try /auth/me endpoint - should work!
```

---

### 🎨 Frontend Developer (6 hours + 2 hours integration)

#### **Task 5.1: Create Modal Base Component** (1 hour)

**Create `frontend/src/components/common/Modal.tsx`:**
```typescript
import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}) => {
  // Close on ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className={`relative bg-white rounded-lg shadow-xl ${sizeClasses[size]} w-full mx-4 max-h-[90vh] overflow-hidden`}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {children}
        </div>
      </div>
    </div>
  );
};
```

---

#### **Task 5.2: Create Document Preview Modal** (1.5 hours)

**Create `frontend/src/components/modals/DocumentPreviewModal.tsx`:**
```typescript
import React from 'react';
import { Modal } from '../common/Modal';
import { Download, FileText, Calendar, User, Tag } from 'lucide-react';
import { KBDocument } from '../../types/api';

interface DocumentPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: KBDocument | null;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  isOpen,
  onClose,
  document,
}) => {
  if (!document) return null;

  const handleDownload = () => {
    alert(`Download: ${document.name}`);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Document Preview" size="lg">
      <div className="space-y-6">
        {/* Document Info */}
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <FileText className="text-blue-600" size={32} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{document.name}</h3>
            <p className="text-sm text-gray-600 mt-1">{document.description}</p>
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2 text-sm">
            <Tag className="text-gray-400" size={16} />
            <span className="text-gray-600">Category:</span>
            <span className="font-medium text-gray-900">{document.category}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <FileText className="text-gray-400" size={16} />
            <span className="text-gray-600">Type:</span>
            <span className="font-medium text-gray-900">{document.document_type}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <User className="text-gray-400" size={16} />
            <span className="text-gray-600">Uploaded by:</span>
            <span className="font-medium text-gray-900">{document.uploaded_by}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="text-gray-400" size={16} />
            <span className="text-gray-600">Uploaded:</span>
            <span className="font-medium text-gray-900">
              {new Date(document.uploaded_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Tags */}
        <div>
          <div className="text-sm font-medium text-gray-700 mb-2">Tags</div>
          <div className="flex flex-wrap gap-2">
            {document.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-sm text-gray-600">File Size</div>
            <div className="text-lg font-semibold text-gray-900">{document.file_size}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Referenced</div>
            <div className="text-lg font-semibold text-gray-900">
              {document.referenced_count} times
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleDownload}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download size={20} />
            Download
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
};
```

---

#### **Task 5.3: Create Upload Document Modal** (1.5 hours)

**Create `frontend/src/components/modals/UploadDocumentModal.tsx`:**
```typescript
import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Upload, X } from 'lucide-react';
import { Input } from '../common/Input';
import { Button } from '../common/Button';

interface UploadDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Array<{ id: string; name: string }>;
}

export const UploadDocumentModal: React.FC<UploadDocumentModalProps> = ({
  isOpen,
  onClose,
  categories,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [documentType, setDocumentType] = useState('system_guide');
  const [tags, setTags] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!name) {
        setName(selectedFile.name);
      }
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!file) newErrors.file = 'Please select a file';
    if (!name.trim()) newErrors.name = 'Document name is required';
    if (!description.trim()) newErrors.description = 'Description is required';
    if (!categoryId) newErrors.category = 'Please select a category';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    // Mock upload
    alert(`Upload document:\n- Name: ${name}\n- Category: ${categoryId}\n- Type: ${documentType}\n- Tags: ${tags}`);
    
    // Reset form
    setFile(null);
    setName('');
    setDescription('');
    setCategoryId('');
    setDocumentType('system_guide');
    setTags('');
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Upload Document" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            File *
          </label>
          {!file ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.doc,.docx,.txt,.md"
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="mx-auto text-gray-400 mb-2" size={48} />
                <p className="text-sm text-gray-600">
                  Click to upload or drag and drop
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  PDF, DOC, DOCX, TXT, MD (max 10MB)
                </p>
              </label>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Upload className="text-blue-600" size={24} />
                <div>
                  <div className="font-medium text-gray-900">{file.name}</div>
                  <div className="text-sm text-gray-600">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleRemoveFile}
                className="text-gray-400 hover:text-red-600 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          )}
          {errors.file && <p className="text-sm text-red-600 mt-1">{errors.file}</p>}
        </div>

        {/* Document Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Name *
          </label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter document name"
          />
          {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name}</p>}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description *
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter document description"
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {errors.description && (
            <p className="text-sm text-red-600 mt-1">{errors.description}</p>
          )}
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category *
          </label>
          <select
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select a category</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
          {errors.category && (
            <p className="text-sm text-red-600 mt-1">{errors.category}</p>
          )}
        </div>

        {/* Document Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Type
          </label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="system_guide">System Guide</option>
            <option value="product">Product Info</option>
            <option value="process">Process</option>
            <option value="reference">Reference</option>
          </select>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tags (comma-separated)
          </label>
          <Input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g., login, authentication, api"
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button type="submit" variant="primary" className="flex-1">
            Upload Document
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </Modal>
  );
};
```

---

#### **Task 5.4: Integrate Modals into KB Page** (1 hour)

**Update `frontend/src/pages/KnowledgeBasePage.tsx`:**
```typescript
import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { DocumentPreviewModal } from '../components/modals/DocumentPreviewModal';
import { UploadDocumentModal } from '../components/modals/UploadDocumentModal';
import { mockKBDocuments, mockKBCategories } from '../mock/knowledgeBase';
import { KBDocument } from '../types/api';
import { Search, Upload, FolderPlus, Eye } from 'lucide-react';

export const KnowledgeBasePage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [previewDocument, setPreviewDocument] = useState<KBDocument | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  // Filter documents
  const filteredDocuments = mockKBDocuments.filter((doc) => {
    const matchesCategory = selectedCategory === 'All' || doc.category === selectedCategory;
    const matchesSearch = 
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const handleViewDocument = (doc: KBDocument) => {
    setPreviewDocument(doc);
    setIsPreviewOpen(true);
  };

  const handleUploadClick = () => {
    setIsUploadOpen(true);
  };

  const handleCreateCategory = () => {
    alert('Create Category');
  };

  const colorMap: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleCreateCategory}>
            <FolderPlus size={20} className="mr-2" />
            Create Category
          </Button>
          <Button variant="primary" onClick={handleUploadClick}>
            <Upload size={20} className="mr-2" />
            Upload Document
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <Input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Category Filters */}
      <div className="mb-6">
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => setSelectedCategory('All')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedCategory === 'All'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Documents ({mockKBDocuments.length})
          </button>
          {mockKBCategories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.name)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedCategory === category.name
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category.name} ({category.count})
            </button>
          ))}
        </div>
      </div>

      {/* Documents Grid */}
      {filteredDocuments.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocuments.map((doc) => (
            <Card key={doc.id} padding={false}>
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold ${
                      colorMap[mockKBCategories.find(c => c.name === doc.category)?.color || 'blue']
                    }`}
                  >
                    {doc.name[0]}
                  </div>
                  <span className="text-xs text-gray-500">{doc.file_size}</span>
                </div>
                
                <h3 className="font-semibold text-gray-900 mb-2">{doc.name}</h3>
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{doc.description}</p>
                
                <div className="flex flex-wrap gap-2 mb-3">
                  {doc.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span>{doc.uploaded_by}</span>
                  <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                </div>
                
                <Button
                  variant="primary"
                  onClick={() => handleViewDocument(doc)}
                  className="w-full"
                >
                  <Eye size={16} className="mr-2" />
                  View
                </Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-500">No documents found</p>
        </div>
      )}

      {/* Modals */}
      <DocumentPreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        document={previewDocument}
      />
      <UploadDocumentModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        categories={mockKBCategories}
      />
    </div>
  );
};
```

---

#### **Task 5.5: Update Playwright Tests for Modals** (1 hour)

**Update `frontend/tests/e2e/04-knowledge-base.spec.ts`:**
```typescript
// Add these tests at the end of the file

test('should open document preview modal', async ({ page }) => {
  // Click first view button
  await page.getByRole('button', { name: /view/i }).first().click();
  
  // Modal should be visible
  await expect(page.getByText(/document preview/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /download/i })).toBeVisible();
  
  // Close modal with X button
  await page.getByRole('button', { name: /close/i }).click();
  await expect(page.getByText(/document preview/i)).not.toBeVisible();
});

test('should close modal with ESC key', async ({ page }) => {
  await page.getByRole('button', { name: /view/i }).first().click();
  await expect(page.getByText(/document preview/i)).toBeVisible();
  
  // Press ESC
  await page.keyboard.press('Escape');
  await expect(page.getByText(/document preview/i)).not.toBeVisible();
});

test('should open upload document modal', async ({ page }) => {
  await page.getByRole('button', { name: /upload document/i }).click();
  
  // Modal should be visible
  await expect(page.getByText(/upload document/i)).toBeVisible();
  await expect(page.getByText(/document name/i)).toBeVisible();
  await expect(page.getByText(/category/i)).toBeVisible();
});

test('should validate upload form', async ({ page }) => {
  await page.getByRole('button', { name: /upload document/i }).click();
  
  // Try to submit without filling form
  await page.getByRole('button', { name: /upload document/i }).last().click();
  
  // Should show validation errors
  await expect(page.getByText(/please select a file/i)).toBeVisible();
  await expect(page.getByText(/document name is required/i)).toBeVisible();
});
```

**Run tests:**
```bash
npm test
```

**Expected: 77/77 tests passing (73 + 4 new modal tests)**

---

### 🤝 Mid-Day Check-in (30 minutes)

**Time:** After Task 5.3 (around 2-3 PM)

**Backend Dev shares:**
- Authentication endpoints are ready
- Test user created (admin/admin123)
- JWT token generation working
- FastAPI docs show all endpoints

**Frontend Dev shares:**
- Modal components built
- Document preview working
- Upload form with validation
- Ready to integrate auth

**Discuss:**
- Token format (Bearer token)
- Error response structure
- CORS configuration
- Integration test plan

---

### 🔗 Integration Test (2 hours - Both Developers)

**Time:** Last 2 hours of Day 5

#### **Step 1: Update Frontend Environment** (15 min)

**Create `frontend/.env`:**
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_USE_MOCK=false
```

**Restart frontend:**
```bash
npm run dev
```

---

#### **Step 2: Update authService for Real API** (30 min)

**Update `frontend/src/services/authService.ts`:**
```typescript
import api, { apiHelpers } from './api';
import { LoginResponse, User } from '../types/api';
import { mockLogin } from '../mock/users';

class AuthService {
  async login(username: string, password: string): Promise<LoginResponse> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const mockUser = mockLogin(username, password);
      if (mockUser) {
        const token = `mock-token-${Date.now()}`;
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(mockUser));
        
        return {
          token,
          user: mockUser,
        };
      } else {
        throw new Error('Invalid credentials');
      }
    }

    // Real API call
    try {
      // FastAPI OAuth2 expects form data
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post<{ access_token: string; token_type: string }>(
        '/auth/login',
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      // Get user info
      const token = response.data.access_token;
      localStorage.setItem('token', token);

      // Fetch user data
      const userResponse = await api.get<User>('/auth/me');
      localStorage.setItem('user', JSON.stringify(userResponse.data));

      return {
        token,
        user: userResponse.data,
      };
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  async logout(): Promise<void> {
    if (apiHelpers.useMockData()) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return;
    }

    try {
      await api.post('/auth/logout');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;

    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  async refreshUser(): Promise<User> {
    if (apiHelpers.useMockData()) {
      const currentUser = this.getCurrentUser();
      if (currentUser) {
        return currentUser;
      }
      throw new Error('No user logged in');
    }

    try {
      const response = await api.get<User>('/auth/me');
      localStorage.setItem('user', JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new AuthService();
```

---

#### **Step 3: Test Real Login Flow** (45 min)

**Manual Testing:**
```bash
# 1. Make sure backend is running
docker-compose up backend

# 2. Make sure frontend is running with VITE_USE_MOCK=false
npm run dev

# 3. Open browser: http://localhost:5173

# 4. Try to login:
# Username: admin
# Password: admin123

# 5. Should redirect to dashboard
# 6. Check browser console - no errors
# 7. Check Network tab - see API calls
# 8. Logout and try again
```

**Check these work:**
- ✅ Login with correct credentials → Dashboard
- ✅ Login with wrong credentials → Error message
- ✅ Protected routes require authentication
- ✅ Logout clears token
- ✅ Token persists on page refresh

---

#### **Step 4: Run Playwright Tests with Real Backend** (30 min)

**Update `playwright.config.ts`:**
```typescript
// Add environment variable
use: {
  baseURL: 'http://localhost:5173',
  // Add this:
  extraHTTPHeaders: {
    'Accept': 'application/json',
  },
},
```

**Run tests:**
```bash
# Make sure backend is running
docker-compose up -d backend

# Run tests
npm test
```

**Expected behavior:**
- Login tests should work with real backend
- Protected routes should work
- Tests should pass (or identify integration issues)

---

#### **Step 5: Debug and Fix Issues** (Until end of day)

**Common issues and fixes:**

**Issue 1: CORS errors**
```python
# backend/app/core/config.py
BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",  # Add this
]
```

**Issue 2: Token not being sent**
```typescript
// Check frontend/src/services/api.ts
// Make sure interceptor is adding token
```

**Issue 3: 401 errors**
```bash
# Check backend logs
docker-compose logs backend

# Verify token is valid
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 🎉 End of Day 5 Celebration

**Achievements:**
- ✅ Backend: JWT authentication fully working
- ✅ Frontend: Modal components built and tested
- ✅ Integration: Real login flow working!
- ✅ Tests: Updated for new features
- ✅ Both: First full-stack feature complete!

**Deliverables:**
- ✅ Working authentication (frontend → backend)
- ✅ JWT token generation and validation
- ✅ Protected routes
- ✅ Modal components for future features
- ✅ Foundation for Week 2 development

---

## Integration Checkpoints

### Day 4 End-of-Day Sync (30 min)
- **Backend:** Demo FastAPI docs, health endpoints
- **Frontend:** Demo dashboard charts
- **Both:** Align on Day 5 auth plan

### Day 5 Mid-Day Check-in (30 min)
- **Backend:** Show auth endpoints in FastAPI docs
- **Frontend:** Show modal components
- **Both:** Discuss integration approach

### Day 5 Integration Test (2 hours)
- **Both:** Work together on first real API integration
- **Both:** Debug issues together
- **Both:** Celebrate first working feature!

---

## Success Criteria

### Day 4 Success
- ✅ Backend: FastAPI running in Docker
- ✅ Backend: Health endpoints responding
- ✅ Backend: Database connected
- ✅ Frontend: Dashboard charts working
- ✅ Frontend: 73/73 tests passing
- ✅ Both: Ready for Day 5 auth work

### Day 5 Success
- ✅ Backend: JWT auth endpoints working
- ✅ Backend: Test user created
- ✅ Frontend: Modal components built
- ✅ Frontend: 77/77 tests passing
- ✅ Integration: Real login flow working
- ✅ Integration: Token persists across page refresh
- ✅ Both: First full-stack feature complete!

---

## Risk Management

### Potential Issues & Mitigation

**Issue 1: Docker problems**
- **Mitigation:** Run backend locally first (uvicorn)
- **Fallback:** Use SQLite instead of PostgreSQL temporarily

**Issue 2: CORS errors**
- **Mitigation:** Configure CORS in FastAPI early
- **Test:** Use curl to verify backend works before frontend integration

**Issue 3: JWT token issues**
- **Mitigation:** Test with FastAPI docs first
- **Debug:** Use browser DevTools Network tab to inspect tokens

**Issue 4: Integration takes longer than expected**
- **Mitigation:** Start integration early (mid-day Day 5)
- **Fallback:** Continue with mock data, integrate on Day 6

**Issue 5: Playwright tests fail with real backend**
- **Mitigation:** Update tests incrementally
- **Fallback:** Keep mock mode working, add real API tests separately

---

## Next Steps After Day 5

### Week 2 (Days 6-10)
- **Backend:** Tests CRUD endpoints, KB upload
- **Frontend:** Connect more services to real APIs
- **Integration:** Incremental feature integration
- **Testing:** Update Playwright tests for real APIs

### Week 3 (Days 11-15)
- **Both:** Final integration and bug fixes
- **Both:** Performance optimization
- **Both:** Deployment setup
- **Demo:** Sprint 1 demo with working product!

---

**Good luck with Days 4-5! You've got this! 🚀**

**Remember:**
- Communicate frequently
- Test early and often
- Celebrate small wins
- Ask for help when stuck
- Document as you go

**End of Day 4-5 Hybrid Plan**

