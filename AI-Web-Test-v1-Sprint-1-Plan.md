# AI Web Test v1.0 - Sprint 1 Detailed Plan
## Infrastructure & Foundation (2-Developer Team)

**Sprint Duration:** 3 weeks (adjusted from 2 weeks due to team size)  
**Team Size:** 2 developers  
**Sprint Goal:** Development environment ready, basic architecture in place, hello world working  

---

## Table of Contents

1. [Team Composition & Roles](#team-composition--roles)
2. [Sprint 1 Objectives](#sprint-1-objectives)
3. [Week-by-Week Breakdown](#week-by-week-breakdown)
4. [Daily Task Assignments](#daily-task-assignments)
5. [Deliverables & Acceptance Criteria](#deliverables--acceptance-criteria)
6. [Risk Management](#risk-management)
7. [Sprint Schedule](#sprint-schedule)
8. [Success Metrics](#success-metrics)

---

## Team Composition & Roles

### Backend Developer (Full-Time)
**Primary Responsibilities:**
- Python FastAPI backend setup
- PostgreSQL database design and setup
- Redis configuration
- Authentication system (JWT)
- API endpoints
- Docker configuration for backend services
- Basic DevOps tasks (shared with Frontend)

**Skills Required:**
- Python 3.11+, FastAPI
- PostgreSQL, SQLAlchemy
- Docker, Docker Compose
- REST API design
- JWT authentication
- Basic Linux/command line

---

### Frontend Developer (Full-Time)
**Primary Responsibilities:**
- React + TypeScript application setup
- TailwindCSS styling setup
- Login/authentication UI
- Basic dashboard layout
- API integration with backend
- Docker configuration for frontend
- Basic DevOps tasks (shared with Backend)

**Skills Required:**
- React 18+, TypeScript
- TailwindCSS, modern CSS
- REST API consumption
- JWT token management
- Vite build tools
- Basic Docker knowledge

---

## Sprint 1 Objectives

### Primary Goal
✅ **Establish foundational infrastructure** so that Sprint 2 can focus on AI agent development.

### Specific Deliverables
1. ✅ Development environment running locally (Docker Compose)
2. ✅ FastAPI backend responding to health check
3. ✅ React frontend displaying login page
4. ✅ PostgreSQL database with initial schema
5. ✅ Authentication working (login → JWT token → protected route)
6. ✅ GitHub repository with basic CI/CD
7. ✅ Documentation for setup and deployment

### What's IN Scope ✅
- ✅ Local development environment (Docker Compose)
- ✅ Basic FastAPI backend with 3-4 endpoints
- ✅ Basic React frontend with login + dashboard skeleton
- ✅ PostgreSQL with users and projects tables
- ✅ Redis setup (for future use)
- ✅ JWT authentication
- ✅ GitHub repo + basic CI pipeline

### What's OUT of Scope ❌
- ❌ OpenRouter API integration (Sprint 2)
- ❌ Knowledge Base features (Sprint 2)
- ❌ Test case generation (Sprint 2)
- ❌ Production deployment (Sprint 4)
- ❌ Advanced CI/CD (later sprints)
- ❌ Monitoring/observability (later sprints)

---

## Week-by-Week Breakdown

### Week 1: Environment Setup & Backend Foundation
**Focus:** Get development environment running, backend basics

**Backend Developer:**
- Days 1-2: Project structure, Docker setup, FastAPI skeleton
- Days 3-4: PostgreSQL schema, SQLAlchemy models
- Day 5: Basic API endpoints (health check, user CRUD)

**Frontend Developer:**
- Days 1-2: React + Vite + TypeScript setup, TailwindCSS config
- Days 3-4: Component structure, routing setup
- Day 5: API client setup, environment configuration

---

### Week 2: Authentication & Integration
**Focus:** Make login work end-to-end

**Backend Developer:**
- Days 1-2: JWT authentication implementation
- Day 3: Auth middleware and protected routes
- Days 4-5: API documentation (Swagger), testing

**Frontend Developer:**
- Days 1-2: Login form UI with validation
- Day 3: JWT token storage and management
- Days 4-5: Protected routes, auth context

---

### Week 3: Polish, Testing & Documentation
**Focus:** Make everything production-ready for Sprint 2

**Backend Developer:**
- Days 1-2: Error handling, logging, validation
- Day 3: Database migrations (Alembic)
- Days 4-5: Integration testing, CI/CD setup

**Frontend Developer:**
- Days 1-2: Dashboard skeleton, navigation
- Day 3: Error handling, loading states
- Days 4-5: E2E testing, documentation

---

## Daily Task Assignments

### Week 1: Environment Setup & Backend Foundation

#### Day 1 (Monday) - Project Initialization

**Backend Developer (8 hours):**
- [ ] **Task 1.1: Create project directory structure** (1 hour)
  - Create `ai-web-test/` root directory
  - Create subdirectories: `backend/`, `frontend/`, `docker/`, `docs/`
  - Initialize Git repository
  - Create `.gitignore` for Python and Node
  
- [ ] **Task 1.2: Setup Docker Compose** (2 hours)
  - Create `docker-compose.yml` in root
  - Define services: `postgres`, `redis`, `backend` (commented out initially)
  - Configure PostgreSQL with environment variables
  - Configure Redis with basic settings
  - Test: `docker-compose up postgres redis` should start both
  
- [ ] **Task 1.3: Initialize FastAPI project** (3 hours)
  - Create `backend/requirements.txt` with dependencies:
    ```
    fastapi==0.104.1
    uvicorn[standard]==0.24.0
    sqlalchemy==2.0.23
    psycopg2-binary==2.9.9
    alembic==1.12.1
    python-jose[cryptography]==3.3.0
    passlib[bcrypt]==1.7.4
    python-multipart==0.0.6
    pydantic==2.5.0
    pydantic-settings==2.1.0
    redis==5.0.1
    ```
  - Create `backend/app/main.py` with FastAPI app initialization
  - Create `backend/app/__init__.py`
  - Create `backend/Dockerfile` for containerization
  
- [ ] **Task 1.4: Test FastAPI hello world** (2 hours)
  - Create simple GET `/` endpoint returning `{"message": "Hello World"}`
  - Create GET `/health` endpoint returning system status
  - Test locally: `uvicorn app.main:app --reload`
  - Update Docker Compose to include backend service
  - Test via Docker: `docker-compose up backend`
  - Verify http://localhost:8000/docs shows Swagger UI

**Deliverable:** FastAPI responding with "Hello World" at http://localhost:8000/

---

**Frontend Developer (8 hours):**
- [ ] **Task 1.1: Initialize React project with Vite** (2 hours)
  - Run: `npm create vite@latest frontend -- --template react-ts`
  - Navigate to `frontend/` directory
  - Install dependencies: `npm install`
  - Test: `npm run dev` should show Vite welcome page
  - Configure Vite for proxy to backend (port 8000)
  
- [ ] **Task 1.2: Setup TailwindCSS** (2 hours)
  - Install: `npm install -D tailwindcss postcss autoprefixer`
  - Run: `npx tailwindcss init -p`
  - Configure `tailwind.config.js`:
    ```js
    content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"]
    ```
  - Update `src/index.css` with Tailwind directives
  - Test with a colored div to verify Tailwind working
  
- [ ] **Task 1.3: Project structure and routing** (3 hours)
  - Install React Router: `npm install react-router-dom`
  - Create directory structure:
    - `src/components/` - reusable components
    - `src/pages/` - page components
    - `src/services/` - API clients
    - `src/hooks/` - custom React hooks
    - `src/types/` - TypeScript types
    - `src/utils/` - utility functions
  - Create basic routing in `App.tsx`:
    - `/` - Home/Landing
    - `/login` - Login page
    - `/dashboard` - Dashboard (protected)
  - Create placeholder components for each route
  
- [ ] **Task 1.4: Create Frontend Dockerfile** (1 hour)
  - Create `frontend/Dockerfile` for production build
  - Create `frontend/.dockerignore`
  - Update `docker-compose.yml` to include frontend service
  - Test: `docker-compose up frontend` should serve the app

**Deliverable:** React app with routing accessible at http://localhost:5173/

---

#### Day 2 (Tuesday) - Database & Component Foundation

**Backend Developer (8 hours):**
- [ ] **Task 2.1: Database configuration** (2 hours)
  - Create `backend/app/core/config.py` for settings:
    ```python
    from pydantic_settings import BaseSettings
    
    class Settings(BaseSettings):
        DATABASE_URL: str = "postgresql://user:pass@postgres:5432/aiwebtest"
        REDIS_URL: str = "redis://redis:6379/0"
        SECRET_KEY: str = "dev-secret-key-change-in-production"
        JWT_ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        
        class Config:
            env_file = ".env"
    ```
  - Create `.env` file with development settings
  - Create `backend/app/core/database.py` for SQLAlchemy setup:
    ```python
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from .config import Settings
    
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    ```
  
- [ ] **Task 2.2: Create database models** (3 hours)
  - Create `backend/app/models/user.py`:
    ```python
    from sqlalchemy import Column, String, Boolean, DateTime
    from sqlalchemy.dialects.postgresql import UUID
    from datetime import datetime
    import uuid
    from app.core.database import Base
    
    class User(Base):
        __tablename__ = "users"
        
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        email = Column(String(255), unique=True, index=True, nullable=False)
        username = Column(String(100), unique=True, index=True, nullable=False)
        hashed_password = Column(String(255), nullable=False)
        full_name = Column(String(255))
        is_active = Column(Boolean, default=True)
        is_superuser = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ```
  - Create `backend/app/models/project.py` (basic structure for future use)
  - Create `backend/app/models/__init__.py` to import all models
  
- [ ] **Task 2.3: Initialize Alembic for migrations** (2 hours)
  - Run: `alembic init alembic` in backend directory
  - Configure `alembic.ini` with DATABASE_URL
  - Update `alembic/env.py` to import Base and models
  - Create first migration: `alembic revision --autogenerate -m "Initial tables"`
  - Apply migration: `alembic upgrade head`
  - Verify tables created in PostgreSQL
  
- [ ] **Task 2.4: Test database connection** (1 hour)
  - Create test script to verify DB connection
  - Create test user in database
  - Query user back to verify
  - Document database setup in `docs/database.md`

**Deliverable:** PostgreSQL with users table, migrations working

---

**Frontend Developer (8 hours):**
- [ ] **Task 2.1: Create reusable UI components** (4 hours)
  - Create `src/components/Button.tsx`:
    - Props: variant (primary, secondary), size, onClick, disabled, loading
    - TailwindCSS styling with hover states
    - TypeScript interfaces for props
  - Create `src/components/Input.tsx`:
    - Props: type, label, error, placeholder, value, onChange
    - Validation states (success, error, default)
    - TailwindCSS styling
  - Create `src/components/Card.tsx`:
    - Generic card container with padding and shadow
  - Create `src/components/Spinner.tsx`:
    - Loading spinner for async operations
  - Create Storybook or simple demo page to test components
  
- [ ] **Task 2.2: Create Login page UI** (3 hours)
  - Create `src/pages/LoginPage.tsx`:
    - Use Card component for login form container
    - Two Input components (email, password)
    - Button component for submit
    - Link to "Forgot Password" (placeholder)
    - TailwindCSS for centering and responsive layout
  - Add validation UI (show errors under inputs)
  - Add loading state (disable button, show spinner)
  - Make it look professional (logo placeholder, nice colors)
  
- [ ] **Task 2.3: Create Dashboard skeleton** (1 hour)
  - Create `src/pages/DashboardPage.tsx`:
    - Header with logo and user menu
    - Sidebar navigation (placeholder links)
    - Main content area with welcome message
    - Use TailwindCSS grid for layout
    - Responsive design (mobile: stack, desktop: sidebar)

**Deliverable:** Professional-looking login page and dashboard skeleton

---

#### Day 3 (Wednesday) - API Endpoints & API Client

**Backend Developer (8 hours):**
- [ ] **Task 3.1: Create Pydantic schemas** (2 hours)
  - Create `backend/app/schemas/user.py`:
    ```python
    from pydantic import BaseModel, EmailStr, UUID4
    from datetime import datetime
    from typing import Optional
    
    class UserBase(BaseModel):
        email: EmailStr
        username: str
        full_name: Optional[str] = None
    
    class UserCreate(UserBase):
        password: str
    
    class UserUpdate(UserBase):
        password: Optional[str] = None
    
    class UserInDB(UserBase):
        id: UUID4
        is_active: bool
        is_superuser: bool
        created_at: datetime
        updated_at: datetime
        
        class Config:
            from_attributes = True
    
    class UserResponse(UserBase):
        id: UUID4
        is_active: bool
        created_at: datetime
    ```
  - Create `backend/app/schemas/auth.py` for login/token schemas
  
- [ ] **Task 3.2: Create CRUD operations** (3 hours)
  - Create `backend/app/crud/user.py`:
    ```python
    from sqlalchemy.orm import Session
    from app.models.user import User
    from app.schemas.user import UserCreate
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(db: Session, username: str):
        return db.query(User).filter(User.username == username).first()
    
    def create_user(db: Session, user: UserCreate):
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def verify_password(plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)
    ```
  
- [ ] **Task 3.3: Create API routes** (3 hours)
  - Create `backend/app/api/routes/users.py`:
    - POST `/api/v1/users/` - Create user
    - GET `/api/v1/users/me` - Get current user (protected)
    - GET `/api/v1/users/{user_id}` - Get user by ID (protected)
  - Create `backend/app/api/routes/__init__.py` to register routes
  - Update `main.py` to include routers:
    ```python
    from app.api.routes import users
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    ```
  - Test endpoints with Swagger UI

**Deliverable:** 3 user API endpoints working and documented in Swagger

---

**Frontend Developer (8 hours):**
- [ ] **Task 3.1: Setup API client** (3 hours)
  - Create `src/services/api.ts`:
    ```typescript
    import axios from 'axios';
    
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    const api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Request interceptor to add JWT token
    api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    
    // Response interceptor for error handling
    api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Clear token and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
    
    export default api;
    ```
  - Create environment variables in `.env`:
    ```
    VITE_API_URL=http://localhost:8000
    ```
  
- [ ] **Task 3.2: Create TypeScript types** (2 hours)
  - Create `src/types/user.ts`:
    ```typescript
    export interface User {
      id: string;
      email: string;
      username: string;
      full_name?: string;
      is_active: boolean;
      created_at: string;
    }
    
    export interface UserCreate {
      email: string;
      username: string;
      password: string;
      full_name?: string;
    }
    
    export interface LoginRequest {
      username: string;
      password: string;
    }
    
    export interface TokenResponse {
      access_token: string;
      token_type: string;
    }
    ```
  
- [ ] **Task 3.3: Create API service methods** (3 hours)
  - Create `src/services/authService.ts`:
    ```typescript
    import api from './api';
    import { LoginRequest, TokenResponse, User } from '../types/user';
    
    export const authService = {
      async login(credentials: LoginRequest): Promise<TokenResponse> {
        const response = await api.post('/api/v1/auth/login', credentials);
        return response.data;
      },
      
      async getCurrentUser(): Promise<User> {
        const response = await api.get('/api/v1/users/me');
        return response.data;
      },
      
      logout() {
        localStorage.removeItem('access_token');
      }
    };
    ```
  - Test API client by calling health check endpoint
  - Add error handling and TypeScript types

**Deliverable:** API client setup with type-safe methods

---

#### Day 4 (Thursday) - JWT Authentication Implementation

**Backend Developer (8 hours):**
- [ ] **Task 4.1: Implement JWT utilities** (3 hours)
  - Create `backend/app/core/security.py`:
    ```python
    from datetime import datetime, timedelta
    from typing import Optional
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    from app.core.config import Settings
    
    settings = Settings()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
    ```
  
- [ ] **Task 4.2: Create authentication dependency** (2 hours)
  - Create `backend/app/api/deps.py`:
    ```python
    from fastapi import Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordBearer
    from sqlalchemy.orm import Session
    from app.core.database import get_db
    from app.core.security import verify_token
    from app.crud import user as crud_user
    from app.models.user import User
    
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
    
    async def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
    ) -> User:
        username = verify_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = crud_user.get_user_by_username(db, username=username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
    
    async def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    ```
  
- [ ] **Task 4.3: Create login endpoint** (2 hours)
  - Create `backend/app/api/routes/auth.py`:
    ```python
    from datetime import timedelta
    from fastapi import APIRouter, Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordRequestForm
    from sqlalchemy.orm import Session
    from app.core.database import get_db
    from app.core.config import Settings
    from app.core.security import create_access_token
    from app.crud import user as crud_user
    from app.schemas.auth import Token
    
    router = APIRouter()
    settings = Settings()
    
    @router.post("/login", response_model=Token)
    async def login(
        db: Session = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
    ):
        user = crud_user.get_user_by_username(db, username=form_data.username)
        if not user or not crud_user.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    ```
  - Register router in `main.py`
  
- [ ] **Task 4.4: Test authentication flow** (1 hour)
  - Create test user via Swagger UI
  - Test login endpoint, verify JWT token returned
  - Test `/users/me` with token in Authorization header
  - Test `/users/me` without token (should fail with 401)
  - Document authentication flow in `docs/authentication.md`

**Deliverable:** JWT authentication working end-to-end

---

**Frontend Developer (8 hours):**
- [ ] **Task 4.1: Create Auth Context** (3 hours)
  - Create `src/contexts/AuthContext.tsx`:
    ```typescript
    import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
    import { User } from '../types/user';
    import { authService } from '../services/authService';
    
    interface AuthContextType {
      user: User | null;
      loading: boolean;
      login: (username: string, password: string) => Promise<void>;
      logout: () => void;
      isAuthenticated: boolean;
    }
    
    const AuthContext = createContext<AuthContextType | undefined>(undefined);
    
    export const AuthProvider = ({ children }: { children: ReactNode }) => {
      const [user, setUser] = useState<User | null>(null);
      const [loading, setLoading] = useState(true);
      
      useEffect(() => {
        // Check if user is logged in on mount
        const token = localStorage.getItem('access_token');
        if (token) {
          authService.getCurrentUser()
            .then(setUser)
            .catch(() => localStorage.removeItem('access_token'))
            .finally(() => setLoading(false));
        } else {
          setLoading(false);
        }
      }, []);
      
      const login = async (username: string, password: string) => {
        const { access_token } = await authService.login({ username, password });
        localStorage.setItem('access_token', access_token);
        const user = await authService.getCurrentUser();
        setUser(user);
      };
      
      const logout = () => {
        authService.logout();
        setUser(null);
      };
      
      return (
        <AuthContext.Provider value={{ user, loading, login, logout, isAuthenticated: !!user }}>
          {children}
        </AuthContext.Provider>
      );
    };
    
    export const useAuth = () => {
      const context = useContext(AuthContext);
      if (!context) throw new Error('useAuth must be used within AuthProvider');
      return context;
    };
    ```
  - Wrap App with AuthProvider in `main.tsx`
  
- [ ] **Task 4.2: Implement login form logic** (3 hours)
  - Update `LoginPage.tsx` to use auth context:
    - Form state management (username, password)
    - Form validation (required fields, email format)
    - Submit handler calling `login()` from context
    - Error handling (display API errors)
    - Loading state (disable form during login)
    - Redirect to dashboard on successful login
  - Add "Remember me" checkbox (optional)
  - Add form validation feedback
  
- [ ] **Task 4.3: Create Protected Route component** (2 hours)
  - Create `src/components/ProtectedRoute.tsx`:
    ```typescript
    import { Navigate } from 'react-router-dom';
    import { useAuth } from '../contexts/AuthContext';
    import Spinner from './Spinner';
    
    export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
      const { isAuthenticated, loading } = useAuth();
      
      if (loading) {
        return <div className="flex justify-center items-center h-screen"><Spinner /></div>;
      }
      
      if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
      }
      
      return <>{children}</>;
    };
    ```
  - Update router to wrap Dashboard with ProtectedRoute
  - Test: accessing /dashboard without login should redirect to /login

**Deliverable:** Login form working, redirects to dashboard on success

---

#### Day 5 (Friday) - Testing & Documentation

**Backend Developer (8 hours):**
- [ ] **Task 5.1: Add error handling middleware** (2 hours)
  - Create `backend/app/core/exceptions.py`:
    - Custom exception classes
    - Exception handlers for common errors
  - Add global exception handler to `main.py`
  - Test various error scenarios
  
- [ ] **Task 5.2: Add request validation** (2 hours)
  - Add Pydantic validators to all schemas
  - Add input sanitization
  - Test with invalid inputs (SQL injection attempts, etc.)
  
- [ ] **Task 5.3: Setup logging** (2 hours)
  - Create `backend/app/core/logging.py`:
    - Configure Python logging
    - Log format with timestamps
    - Log to file and console
  - Add logging to all endpoints
  - Test log output
  
- [ ] **Task 5.4: Write API tests** (2 hours)
  - Create `backend/tests/test_auth.py`:
    - Test user creation
    - Test login with valid credentials
    - Test login with invalid credentials
    - Test protected endpoint with/without token
  - Run tests: `pytest`
  - Aim for >80% coverage on critical paths

**Deliverable:** Robust error handling, logging, and tests

---

**Frontend Developer (8 hours):**
- [ ] **Task 5.1: Add error handling UI** (2 hours)
  - Create `src/components/ErrorBoundary.tsx`:
    - Catch React errors
    - Display user-friendly error message
  - Create `src/components/Toast.tsx`:
    - Success/error toast notifications
    - Use for API error messages
  - Wrap App with ErrorBoundary
  
- [ ] **Task 5.2: Add loading states** (2 hours)
  - Create loading spinner component
  - Add loading states to login form
  - Add skeleton loaders for dashboard
  - Test loading experience
  
- [ ] **Task 5.3: Responsive design polish** (2 hours)
  - Test on mobile viewport (375px)
  - Test on tablet viewport (768px)
  - Test on desktop viewport (1920px)
  - Fix any layout issues
  - Ensure touch targets are 44px minimum
  
- [ ] **Task 5.4: Create README and documentation** (2 hours)
  - Create `frontend/README.md`:
    - Setup instructions
    - Available scripts
    - Environment variables
    - Project structure
  - Add inline code comments
  - Document component props with JSDoc

**Deliverable:** Polished UI with proper error handling and documentation

---

### Week 2: Integration & Polish

#### Day 6 (Monday) - GitHub & CI/CD Setup

**Backend Developer (8 hours):**
- [ ] **Task 6.1: Setup GitHub repository** (2 hours)
  - Create GitHub repository
  - Push initial code
  - Create `.github/` directory
  - Add README.md for project
  - Add LICENSE file
  
- [ ] **Task 6.2: Create CI pipeline** (4 hours)
  - Create `.github/workflows/backend-ci.yml`:
    ```yaml
    name: Backend CI
    
    on:
      push:
        branches: [ main, develop ]
      pull_request:
        branches: [ main ]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        
        services:
          postgres:
            image: postgres:15
            env:
              POSTGRES_PASSWORD: testpass
              POSTGRES_DB: testdb
            options: >-
              --health-cmd pg_isready
              --health-interval 10s
              --health-timeout 5s
              --health-retries 5
        
        steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        - name: Install dependencies
          run: |
            cd backend
            pip install -r requirements.txt
            pip install pytest pytest-cov
        - name: Run tests
          run: |
            cd backend
            pytest --cov=app tests/
        - name: Lint
          run: |
            cd backend
            pip install flake8
            flake8 app/ --max-line-length=120
    ```
  - Test CI by pushing code
  
- [ ] **Task 6.3: Setup pre-commit hooks** (2 hours)
  - Install pre-commit: `pip install pre-commit`
  - Create `.pre-commit-config.yaml`:
    - Black for formatting
    - Flake8 for linting
    - isort for imports
  - Test hooks

**Deliverable:** GitHub repo with working CI pipeline

---

**Frontend Developer (8 hours):**
- [ ] **Task 6.1: Create Frontend CI pipeline** (3 hours)
  - Create `.github/workflows/frontend-ci.yml`:
    ```yaml
    name: Frontend CI
    
    on:
      push:
        branches: [ main, develop ]
      pull_request:
        branches: [ main ]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        
        steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-node@v3
          with:
            node-version: '18'
        - name: Install dependencies
          run: |
            cd frontend
            npm ci
        - name: Lint
          run: |
            cd frontend
            npm run lint
        - name: Type check
          run: |
            cd frontend
            npx tsc --noEmit
        - name: Build
          run: |
            cd frontend
            npm run build
    ```
  
- [ ] **Task 6.2: Setup ESLint and Prettier** (2 hours)
  - Install: `npm install -D eslint prettier eslint-config-prettier`
  - Create `.eslintrc.json`
  - Create `.prettierrc`
  - Add lint scripts to `package.json`
  - Fix any linting errors
  
- [ ] **Task 6.3: Add unit tests** (3 hours)
  - Install Vitest: `npm install -D vitest @testing-library/react`
  - Create `src/components/__tests__/Button.test.tsx`
  - Create `src/services/__tests__/authService.test.ts`
  - Add test script to `package.json`
  - Run tests: `npm test`

**Deliverable:** Frontend CI pipeline with linting and tests

---

#### Day 7 (Tuesday) - Docker Optimization

**Backend Developer (8 hours):**
- [ ] **Task 7.1: Optimize Backend Dockerfile** (3 hours)
  - Multi-stage build for smaller image
  - Use Python slim image
  - Cache pip dependencies layer
  - Add healthcheck
  - Test build time and image size
  
- [ ] **Task 7.2: Create docker-compose for development** (3 hours)
  - Update `docker-compose.yml` with hot reload:
    ```yaml
    version: '3.8'
    services:
      postgres:
        image: postgres:15-alpine
        environment:
          POSTGRES_DB: aiwebtest
          POSTGRES_USER: aiwebtest
          POSTGRES_PASSWORD: devpassword
        volumes:
          - postgres_data:/var/lib/postgresql/data
        ports:
          - "5432:5432"
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U aiwebtest"]
          interval: 5s
          timeout: 5s
          retries: 5
      
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
        healthcheck:
          test: ["CMD", "redis-cli", "ping"]
          interval: 5s
          timeout: 5s
          retries: 5
      
      backend:
        build: ./backend
        command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        volumes:
          - ./backend:/app
        ports:
          - "8000:8000"
        environment:
          - DATABASE_URL=postgresql://aiwebtest:devpassword@postgres:5432/aiwebtest
          - REDIS_URL=redis://redis:6379/0
        depends_on:
          postgres:
            condition: service_healthy
          redis:
            condition: service_healthy
      
      frontend:
        build: ./frontend
        command: npm run dev -- --host 0.0.0.0
        volumes:
          - ./frontend:/app
          - /app/node_modules
        ports:
          - "5173:5173"
        environment:
          - VITE_API_URL=http://localhost:8000
        depends_on:
          - backend
    
    volumes:
      postgres_data:
    ```
  - Test full stack startup: `docker-compose up`
  
- [ ] **Task 7.3: Create setup script** (2 hours)
  - Create `scripts/setup.sh`:
    ```bash
    #!/bin/bash
    echo "Setting up AI Web Test development environment..."
    
    # Check Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Create .env files
    cp backend/.env.example backend/.env
    cp frontend/.env.example frontend/.env
    
    # Build containers
    docker-compose build
    
    # Start services
    docker-compose up -d postgres redis
    
    # Wait for postgres
    echo "Waiting for PostgreSQL..."
    sleep 5
    
    # Run migrations
    docker-compose run backend alembic upgrade head
    
    # Create admin user
    docker-compose run backend python scripts/create_admin.py
    
    echo "Setup complete! Run 'docker-compose up' to start the application."
    ```
  - Make executable: `chmod +x scripts/setup.sh`
  - Test script

**Deliverable:** One-command setup for new developers

---

**Frontend Developer (8 hours):**
- [ ] **Task 7.1: Optimize Frontend Dockerfile** (2 hours)
  - Multi-stage build (build stage + nginx stage)
  - Optimize for production
  - Add nginx configuration
  - Test production build
  
- [ ] **Task 7.2: Environment configuration** (2 hours)
  - Create `.env.example` with all variables
  - Document environment variables in README
  - Add validation for required env vars
  - Create separate configs for dev/staging/prod
  
- [ ] **Task 7.3: Add dashboard navigation** (4 hours)
  - Create `src/components/Layout.tsx`:
    - Top navigation bar with logo
    - User menu (dropdown with logout)
    - Sidebar navigation
    - Main content area
  - Create `src/components/Sidebar.tsx`:
    - Navigation links (Dashboard, Tests, KB, Settings)
    - Responsive (collapsible on mobile)
    - Active link highlighting
  - Update Dashboard to use Layout
  - Add icons (lucide-react or heroicons)

**Deliverable:** Production-ready Docker setup, polished dashboard layout

---

#### Day 8 (Wednesday) - Database Seeding & Additional Features

**Backend Developer (8 hours):**
- [ ] **Task 8.1: Create database seeding** (3 hours)
  - Create `backend/scripts/seed_db.py`:
    - Create admin user
    - Create sample projects
    - Create test data for development
  - Add seed command to `Makefile`
  - Document seeding process
  
- [ ] **Task 8.2: Add pagination to list endpoints** (2 hours)
  - Update user list endpoint with pagination
  - Add query parameters: `skip`, `limit`
  - Return pagination metadata (total, page, pages)
  - Test with large datasets
  
- [ ] **Task 8.3: Add API versioning** (2 hours)
  - Organize routes under `/api/v1/`
  - Document versioning strategy
  - Prepare for future v2 API
  
- [ ] **Task 8.4: Performance optimization** (1 hour)
  - Add database indexes
  - Optimize SQL queries
  - Add Redis caching for user sessions
  - Run performance tests

**Deliverable:** Optimized, scalable backend

---

**Frontend Developer (8 hours):**
- [ ] **Task 8.1: Create user profile page** (3 hours)
  - Create `src/pages/ProfilePage.tsx`:
    - Display user information
    - Edit profile form
    - Change password form
    - Use Card components
  - Add route `/profile`
  - Link from user menu
  
- [ ] **Task 8.2: Add form validation library** (2 hours)
  - Install react-hook-form: `npm install react-hook-form`
  - Install zod: `npm install zod @hookform/resolvers`
  - Refactor login form to use react-hook-form
  - Create reusable form components
  
- [ ] **Task 8.3: Improve accessibility** (3 hours)
  - Add ARIA labels to all interactive elements
  - Ensure keyboard navigation works
  - Test with screen reader (NVDA/JAWS)
  - Fix contrast issues
  - Add focus indicators
  - Test with Lighthouse (aim for 90+ accessibility score)

**Deliverable:** Accessible, user-friendly interface

---

#### Day 9 (Thursday) - Final Integration Testing

**Both Developers Working Together (8 hours each):**

**Morning Session (4 hours):**
- [ ] **Task 9.1: End-to-end integration test** (2 hours)
  - Test complete flow: signup → login → dashboard → logout
  - Test with different browsers (Chrome, Firefox)
  - Test on different devices (desktop, tablet, mobile)
  - Document any issues found
  
- [ ] **Task 9.2: Performance testing** (2 hours)
  - Test with 10 concurrent users
  - Measure API response times
  - Measure page load times
  - Check database connection pooling
  - Identify bottlenecks

**Afternoon Session (4 hours):**
- [ ] **Task 9.3: Security review** (2 hours)
  - Check for SQL injection vulnerabilities
  - Test XSS prevention
  - Verify CORS configuration
  - Check password hashing
  - Review authentication flow
  - Test rate limiting (if implemented)
  
- [ ] **Task 9.4: Bug fixes** (2 hours)
  - Fix any issues found during testing
  - Polish UI based on feedback
  - Update documentation
  - Prepare for Sprint 1 demo

**Deliverable:** Fully tested, production-ready MVP foundation

---

#### Day 10 (Friday) - Documentation & Sprint Review

**Backend Developer (8 hours):**
- [ ] **Task 10.1: API documentation** (3 hours)
  - Review and enhance Swagger/OpenAPI docs
  - Add descriptions to all endpoints
  - Add example requests/responses
  - Document error codes
  - Create Postman collection
  
- [ ] **Task 10.2: Deployment documentation** (2 hours)
  - Create `docs/deployment.md`:
    - Production deployment guide
    - Environment setup
    - Database migration process
    - Backup and recovery
    - Monitoring setup
  
- [ ] **Task 10.3: Sprint 1 retrospective prep** (1 hour)
  - Document completed vs planned work
  - Note technical debt
  - Prepare demo script
  
- [ ] **Task 10.4: Sprint 2 preparation** (2 hours)
  - Review Sprint 2 requirements
  - Set up OpenRouter API account
  - Create Sprint 2 task board
  - Identify blockers

**Deliverable:** Complete documentation package

---

**Frontend Developer (8 hours):**
- [ ] **Task 10.1: Component documentation** (3 hours)
  - Document all reusable components
  - Add PropTypes/TypeScript interfaces
  - Create component usage examples
  - Create style guide document
  
- [ ] **Task 10.2: User documentation** (2 hours)
  - Create `docs/user-guide.md`:
    - How to login
    - How to navigate the dashboard
    - Common troubleshooting
    - FAQs
  - Add inline help text in UI
  
- [ ] **Task 10.3: Code cleanup** (2 hours)
  - Remove console.logs
  - Remove unused imports
  - Remove commented code
  - Format all files with Prettier
  - Run linter and fix warnings
  
- [ ] **Task 10.4: Sprint 1 demo preparation** (1 hour)
  - Prepare demo script
  - Create demo user accounts
  - Test demo flow
  - Prepare slides (optional)

**Deliverable:** Sprint 1 complete and ready for demo

---

### Week 3: Extra Buffer & Advanced Setup

#### Days 11-15 (Week 3) - Buffer Week & Production Readiness

This week serves as:
1. **Buffer time** for any tasks that took longer than expected
2. **Production readiness** improvements
3. **Sprint 2 preparation** with OpenRouter API setup

**Flexible Tasks (Pick based on what's needed):**

**Backend Developer:**
- [ ] Add API rate limiting (slowapi library)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Create backup scripts
- [ ] Add health check endpoints for all services
- [ ] Optimize Docker images further
- [ ] Set up staging environment
- [ ] Configure OpenRouter API access for Sprint 2
- [ ] Create initial prompts for test generation (Sprint 2 prep)

**Frontend Developer:**
- [ ] Add analytics (Google Analytics or Plausible)
- [ ] Implement dark mode toggle
- [ ] Add keyboard shortcuts
- [ ] Create onboarding tour for new users
- [ ] Add help documentation modal
- [ ] Performance optimization (code splitting, lazy loading)
- [ ] Set up error tracking (Sentry)
- [ ] Create placeholder pages for Sprint 2 features

---

## Deliverables & Acceptance Criteria

### Sprint 1 Must-Have Deliverables ✅

#### 1. Development Environment
- [ ] Docker Compose running all services (postgres, redis, backend, frontend)
- [ ] One-command setup: `./scripts/setup.sh`
- [ ] Environment variables documented
- [ ] README with setup instructions

**Acceptance Criteria:**
- New developer can set up environment in < 30 minutes
- All services start without errors
- Hot reload works for both frontend and backend

---

#### 2. Backend API
- [ ] FastAPI application with Swagger UI at `/docs`
- [ ] PostgreSQL database with users and projects tables
- [ ] JWT authentication (login endpoint)
- [ ] User CRUD endpoints
- [ ] Health check endpoint
- [ ] Proper error handling and logging

**Acceptance Criteria:**
- Health check returns 200 OK
- Can create user via API
- Can login and receive JWT token
- Protected endpoints reject requests without valid token
- API returns proper HTTP status codes (200, 401, 404, etc.)

---

#### 3. Frontend Application
- [ ] React app with TypeScript and TailwindCSS
- [ ] Login page with form validation
- [ ] Dashboard skeleton with navigation
- [ ] Protected routes working
- [ ] API client with JWT token management
- [ ] Error handling and loading states

**Acceptance Criteria:**
- Login page is professional-looking
- Login with valid credentials redirects to dashboard
- Login with invalid credentials shows error message
- Dashboard is only accessible when logged in
- Logout clears token and redirects to login
- UI is responsive (mobile, tablet, desktop)

---

#### 4. GitHub Repository & CI/CD
- [ ] GitHub repository with code
- [ ] CI pipeline for backend (test + lint)
- [ ] CI pipeline for frontend (test + lint + build)
- [ ] README with project overview
- [ ] Documentation folder with guides

**Acceptance Criteria:**
- CI pipeline passes on main branch
- PRs automatically trigger CI
- Code is organized and well-documented
- Git history is clean (meaningful commit messages)

---

#### 5. Documentation
- [ ] API documentation (Swagger)
- [ ] Setup guide (README)
- [ ] Database schema documentation
- [ ] Authentication flow documentation
- [ ] Deployment guide

**Acceptance Criteria:**
- All major features are documented
- Documentation is clear and accurate
- Code has inline comments where needed
- Architecture decisions are documented

---

## Risk Management

### Risks for 2-Developer Team

#### Risk 1: Both Developers Blocked Simultaneously
**Probability:** Medium | **Impact:** High

**Scenario:** Both developers hit blockers at the same time (e.g., Docker networking issues).

**Mitigation:**
- Daily standup to identify blockers early
- Set up pair programming sessions when needed
- Document solutions to common problems
- Have contingency tasks ready (documentation, cleanup)

**Contingency:**
- Use Slack/Discord for quick help from community
- Extend sprint by 2-3 days if needed
- Skip non-essential tasks (dark mode, advanced features)

---

#### Risk 2: Learning Curve Steeper Than Expected
**Probability:** Medium | **Impact:** Medium

**Scenario:** Developer unfamiliar with FastAPI or React TypeScript takes longer than planned.

**Mitigation:**
- Front-load learning tasks (Day 1-2)
- Provide starter templates and examples
- Use boilerplate code from trusted sources
- Pair programming for knowledge sharing

**Contingency:**
- Extend sprint to 4 weeks
- Reduce scope (skip user profile page, advanced features)
- Focus on MVP only

---

#### Risk 3: Docker/Environment Issues
**Probability:** High | **Impact:** Medium

**Scenario:** Docker networking, volume mounting, or platform-specific issues (M1 Mac, Windows).

**Mitigation:**
- Test on multiple platforms early
- Document platform-specific issues
- Use stable, well-tested Docker images
- Have fallback to local development without Docker

**Contingency:**
- Developers run services locally (no Docker)
- Provide platform-specific setup guides
- Use cloud development environment (GitHub Codespaces)

---

#### Risk 4: Scope Creep
**Probability:** High | **Impact:** High

**Scenario:** Team tries to add features like KB upload, test generation in Sprint 1.

**Mitigation:**
- Clear scope definition at start
- "Out of scope" list prominently displayed
- Weekly scope review
- Say "no" to new features

**Contingency:**
- Immediately cut low-priority tasks
- Move new features to Sprint 2 backlog
- Focus on core deliverables only

---

## Sprint Schedule

### Daily Schedule (Both Developers)

**9:00 AM - 9:15 AM:** Daily Standup (15 min)
- What did you do yesterday?
- What will you do today?
- Any blockers?

**9:15 AM - 12:00 PM:** Focused Work (2.75 hours)
- No meetings
- Deep work on assigned tasks

**12:00 PM - 1:00 PM:** Lunch Break

**1:00 PM - 3:00 PM:** Focused Work (2 hours)

**3:00 PM - 3:30 PM:** Pair Programming / Code Review (30 min)
- Review each other's PRs
- Pair on difficult problems
- Share knowledge

**3:30 PM - 5:00 PM:** Focused Work (1.5 hours)

**5:00 PM - 5:15 PM:** End of Day Sync (15 min)
- Quick update on progress
- Plan for tomorrow
- Update task board

---

### Weekly Milestones

**End of Week 1:**
- [ ] Docker environment fully functional
- [ ] Backend API with 4-5 endpoints working
- [ ] Frontend showing login page and dashboard skeleton
- [ ] Can create user and login manually via Swagger UI

**End of Week 2:**
- [ ] Authentication flow working end-to-end
- [ ] User can login via UI and see dashboard
- [ ] GitHub repository with CI pipeline
- [ ] All tests passing

**End of Week 3:**
- [ ] All documentation complete
- [ ] Sprint 1 demo ready
- [ ] Sprint 2 requirements reviewed
- [ ] OpenRouter API access configured

---

## Success Metrics

### Sprint 1 Definition of Done ✅

**Technical Metrics:**
- [ ] Backend API test coverage > 80%
- [ ] Frontend has no linting errors
- [ ] CI pipeline passes consistently
- [ ] Docker Compose starts all services in < 60 seconds
- [ ] API response time < 200ms (p95)
- [ ] Frontend Lighthouse score > 90

**Functional Metrics:**
- [ ] User can register and login successfully
- [ ] JWT authentication works correctly
- [ ] Dashboard displays after login
- [ ] Logout clears session
- [ ] Protected routes redirect to login

**Process Metrics:**
- [ ] All planned tasks completed
- [ ] Git commits follow conventions
- [ ] Code reviews done for all PRs
- [ ] Documentation is up-to-date
- [ ] No critical bugs in production

---

## Communication & Collaboration

### Daily Communication
- **Tool:** Slack or Discord
- **Standup:** Every morning at 9:00 AM
- **Ad-hoc:** Ping each other for quick questions
- **Pair Programming:** Schedule as needed (Zoom/Google Meet)

### Weekly Sync
- **Friday 4:00 PM:** Sprint review
  - Demo what was built this week
  - Discuss what went well
  - Identify improvements for next week

### Documentation
- **Where:** GitHub Wiki or `/docs` folder
- **What:** Setup guides, API docs, architecture decisions
- **When:** Document as you build (not at the end)

### Code Review
- **Tool:** GitHub Pull Requests
- **Process:**
  - Create feature branch
  - Make changes
  - Create PR with description
  - Request review from other developer
  - Address feedback
  - Merge when approved

---

## Sprint 1 Retrospective Template

**At the end of Sprint 1, discuss:**

### What Went Well? ✅
- What worked better than expected?
- What should we continue doing?

### What Didn't Go Well? ❌
- What took longer than expected?
- What blocked us?

### What Should We Improve? 🔄
- What processes should we change?
- What tools do we need?

### Action Items for Sprint 2 📋
- Specific improvements to implement
- Who is responsible
- Target completion date

---

## Next Steps After Sprint 1

### Sprint 2 Preparation
1. **OpenRouter API Account:**
   - Sign up at openrouter.ai
   - Get API key
   - Test API with simple request
   - Understand pricing and rate limits

2. **Knowledge Base Planning:**
   - Review KB requirements from PRD
   - Design database schema for KB documents
   - Plan MinIO/S3 integration
   - Create upload UI mockups

3. **AI Agent Research:**
   - Research LangChain or similar frameworks
   - Study prompt engineering techniques
   - Review Stagehand SDK documentation
   - Test Playwright for browser automation

4. **Sprint 2 Task Breakdown:**
   - Break down Sprint 2 into daily tasks
   - Identify dependencies
   - Estimate effort
   - Assign tasks

---

## Appendix A: Technology Reference

### Backend Stack
- **Python:** 3.11+
- **FastAPI:** 0.104+ (modern async web framework)
- **SQLAlchemy:** 2.0+ (ORM)
- **Alembic:** 1.12+ (database migrations)
- **PostgreSQL:** 15+ (relational database)
- **Redis:** 7+ (caching, sessions)
- **Pydantic:** 2.5+ (data validation)
- **python-jose:** 3.3+ (JWT tokens)
- **passlib:** 1.7+ (password hashing)
- **pytest:** 7.4+ (testing)

### Frontend Stack
- **React:** 18+ (UI library)
- **TypeScript:** 5+ (type safety)
- **Vite:** 5+ (build tool)
- **TailwindCSS:** 3+ (styling)
- **React Router:** 6+ (routing)
- **Axios:** 1.6+ (HTTP client)
- **React Hook Form:** 7+ (form validation)
- **Zod:** 3+ (schema validation)
- **Vitest:** 1+ (testing)

### DevOps Stack
- **Docker:** 24+ (containerization)
- **Docker Compose:** 2+ (orchestration)
- **GitHub Actions:** (CI/CD)
- **Nginx:** 1.25+ (production web server)

---

## Appendix B: Useful Commands

### Backend Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Create migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/

# Format code
black app/

# Lint code
flake8 app/
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

### Docker Commands
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service]

# Run command in container
docker-compose exec backend bash

# Reset everything (careful!)
docker-compose down -v
```

---

## Appendix C: Folder Structure

```
ai-web-test/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── project.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── auth.py
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── deps.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           └── users.py
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_auth.py
│   ├── alembic/
│   ├── scripts/
│   │   └── seed_db.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── authService.ts
│   │   ├── types/
│   │   │   └── user.ts
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
├── docker/
│   └── nginx.conf
├── docs/
│   ├── setup.md
│   ├── api.md
│   ├── database.md
│   ├── authentication.md
│   └── deployment.md
├── scripts/
│   └── setup.sh
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
├── docker-compose.yml
├── .gitignore
├── README.md
└── LICENSE
```

---

**END OF SPRINT 1 DETAILED PLAN**

**Next Steps:**
1. Review this plan with both developers
2. Set up communication channels (Slack/Discord)
3. Schedule daily standups
4. Start Day 1 tasks!

**Questions or Concerns:**
- Discuss any questions before starting
- Adjust timeline if needed
- Identify learning needs early
- Set realistic expectations

**Remember:**
- Communication is key with a small team
- Help each other when blocked
- Document as you go
- Ask for help when needed
- Celebrate small wins!

Good luck with Sprint 1! 🚀

