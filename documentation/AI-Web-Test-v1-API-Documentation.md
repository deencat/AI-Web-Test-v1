# AI-Web-Test v1 - API Documentation Standards

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-01-31
- **Status**: Architecture Specification
- **Related Documents**: 
  - [PRD](../AI-Web-Test-v1-PRD.md)
  - [SRS](../AI-Web-Test-v1-SRS.md)
  - [Integration Testing](./AI-Web-Test-v1-Integration-Testing.md)

---

## Executive Summary

This document defines the **comprehensive API documentation standards** for the AI-Web-Test v1 platform, implementing OpenAPI 3.0 specification, Swagger UI, ReDoc, API versioning, request/response schemas, and developer-friendly documentation.

### Key API Documentation Capabilities

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **OpenAPI Specification** | OpenAPI 3.0.3 | Machine-readable API contract |
| **Interactive Docs** | Swagger UI | Try-it-out API explorer |
| **Readable Docs** | ReDoc | Beautiful, searchable API docs |
| **Schema Validation** | Pydantic | Type-safe request/response models |
| **API Versioning** | URL-based (v1, v2) | Backward compatibility |
| **Code Examples** | Multi-language | Python, JavaScript, cURL |
| **SDK Generation** | OpenAPI Generator | Auto-generated client SDKs |

### Implementation Timeline
- **Total Effort**: 2 days
- **Phase 1** (Day 1): OpenAPI setup + Swagger UI + ReDoc
- **Phase 2** (Day 2): Advanced documentation + SDK generation

---

## Table of Contents
1. [OpenAPI 3.0 Specification](#openapi-30-specification)
2. [Swagger UI Integration](#swagger-ui-integration)
3. [ReDoc Integration](#redoc-integration)
4. [API Versioning Strategy](#api-versioning-strategy)
5. [Request/Response Schemas](#requestresponse-schemas)
6. [Authentication Documentation](#authentication-documentation)
7. [Error Response Standards](#error-response-standards)
8. [Code Examples](#code-examples)
9. [SDK Generation](#sdk-generation)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Summary & Integration](#summary--integration)

---

## OpenAPI 3.0 Specification

### 1.1 FastAPI OpenAPI Configuration

**Basic Setup**:
```python
# app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="AI Web Test API",
    description="""
    **Multi-Agent AI Test Automation Platform**
    
    This API provides comprehensive test automation capabilities powered by 
    6 specialized AI agents:
    
    - **Requirements Agent**: Analyzes requirements and generates test scenarios
    - **Generation Agent**: Creates executable test code
    - **Execution Agent**: Runs tests in various environments
    - **Observation Agent**: Monitors test execution in real-time
    - **Analysis Agent**: Analyzes test results and identifies patterns
    - **Evolution Agent**: Continuously improves test quality using reinforcement learning
    
    ## Features
    
    - 🤖 Multi-agent AI-powered test generation
    - 🚀 Automated test execution (Chrome, Firefox, Edge)
    - 📊 Real-time monitoring and analytics
    - 🔄 Continuous learning and improvement
    - 🔒 Enterprise-grade security (OAuth 2.0, MFA, RBAC)
    - 📈 MLOps integration (MLflow, Feast, DVC)
    
    ## Getting Started
    
    1. **Authenticate**: Use `/api/v1/auth/login` to obtain JWT token
    2. **Generate Tests**: POST to `/api/v1/tests/generate` with requirements
    3. **Execute Tests**: POST to `/api/v1/tests/execute` with test IDs
    4. **View Results**: GET `/api/v1/tests/executions` to see results
    
    ## Support
    
    - Documentation: https://docs.aiwebtest.com
    - GitHub: https://github.com/yourusername/aiwebtest
    - Email: support@aiwebtest.com
    """,
    version="1.0.0",
    terms_of_service="https://aiwebtest.com/terms",
    contact={
        "name": "AI Web Test Support",
        "url": "https://aiwebtest.com/support",
        "email": "support@aiwebtest.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints. Supports OAuth 2.0, JWT tokens, and MFA.",
        },
        {
            "name": "Tests",
            "description": "Test case management endpoints. Create, read, update, delete test cases.",
        },
        {
            "name": "Test Execution",
            "description": "Test execution endpoints. Execute tests, view results, download artifacts.",
        },
        {
            "name": "Agents",
            "description": "AI agent operations. Monitor agent status, view agent decisions, configure agents.",
        },
        {
            "name": "Projects",
            "description": "Project management endpoints. Organize tests into projects.",
        },
        {
            "name": "Users",
            "description": "User management endpoints. Admin-only access.",
        },
        {
            "name": "Analytics",
            "description": "Analytics and reporting endpoints. Test metrics, trends, insights.",
        },
        {
            "name": "ML Models",
            "description": "ML model management. MLflow integration, model registry, A/B testing.",
        },
    ],
    servers=[
        {
            "url": "https://api.aiwebtest.com",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.aiwebtest.com",
            "description": "Staging server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development server",
        },
    ],
)

def custom_openapi():
    """Customize OpenAPI schema with additional metadata"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /api/v1/auth/login",
        },
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://api.aiwebtest.com/oauth/authorize",
                    "tokenUrl": "https://api.aiwebtest.com/oauth/token",
                    "scopes": {
                        "read": "Read access to resources",
                        "write": "Write access to resources",
                        "admin": "Admin access to all resources",
                    },
                }
            },
        },
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom extensions
    openapi_schema["x-tagGroups"] = [
        {
            "name": "Core API",
            "tags": ["Authentication", "Tests", "Test Execution"],
        },
        {
            "name": "Advanced",
            "tags": ["Agents", "ML Models", "Analytics"],
        },
        {
            "name": "Admin",
            "tags": ["Projects", "Users"],
        },
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 1.2 Endpoint Documentation Best Practices

**Example: Test Generation Endpoint**:
```python
# app/api/v1/tests.py
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.test import TestGenerationRequest, TestGenerationResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/tests", tags=["Tests"])

@router.post(
    "/generate",
    response_model=TestGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate test cases from requirements",
    description="""
    Generate test cases from natural language requirements using AI.
    
    This endpoint uses the **Requirements Agent** and **Generation Agent** to:
    
    1. Analyze the provided requirements text
    2. Identify test scenarios (happy path, edge cases, error cases)
    3. Generate executable test code for each scenario
    4. Return the generated tests with metadata
    
    ## Process Flow
    
    ```
    Requirements Text → Requirements Agent → Scenarios → Generation Agent → Tests
    ```
    
    ## Expected Response Time
    
    - Simple requirements (1-2 scenarios): 10-20 seconds
    - Complex requirements (5-10 scenarios): 30-60 seconds
    
    ## Rate Limits
    
    - Standard users: 100 requests/hour
    - Premium users: 1000 requests/hour
    - Admin users: Unlimited
    """,
    response_description="Generated test cases with metadata",
    responses={
        201: {
            "description": "Test cases generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "workflow_id": "workflow_1706716800",
                        "tests": [
                            {
                                "test_id": "TEST-000001",
                                "title": "Test user login with valid credentials",
                                "description": "Verify user can login with correct username and password",
                                "test_type": "integration",
                                "priority": "high",
                                "code": "def test_user_login_valid():\n    ...",
                                "expected_output": "Login successful",
                            }
                        ],
                        "generation_time_ms": 15234.5,
                        "confidence": 0.92,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request (missing requirements or invalid parameters)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "requirements_text is required and must be at least 10 characters"
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized (missing or invalid JWT token)",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Try again in 3600 seconds.",
                        "retry_after": 3600,
                    }
                }
            },
        },
        500: {
            "description": "Internal server error (agent failure, database error)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Generation Agent is unavailable. Please try again later.",
                        "error_code": "AGENT_UNAVAILABLE",
                    }
                }
            },
        },
    },
)
async def generate_tests(
    request: TestGenerationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate test cases from requirements using AI agents.
    
    Args:
        request: Test generation request with requirements text and options
        current_user: Authenticated user (injected by dependency)
    
    Returns:
        TestGenerationResponse with generated test cases
    
    Raises:
        HTTPException: 400 for invalid request, 401 for unauthorized, 
                      429 for rate limit, 500 for server error
    """
    # Implementation
    pass
```

---

## Swagger UI Integration

### 2.1 Custom Swagger UI Configuration

**Enhanced Swagger UI**:
```python
# app/main.py
from fastapi.openapi.docs import get_swagger_ui_html

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with additional features"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "syntaxHighlight.theme": "monokai",
            "tryItOutEnabled": True,
            "persistAuthorization": True,
        },
    )
```

### 2.2 Swagger UI Features

**Available at**: `http://localhost:8000/docs`

**Features**:
- 🔍 **Search bar**: Filter endpoints by name, tag, or description
- 🎯 **Try it out**: Execute API calls directly from the browser
- 🔐 **Authentication**: Persist JWT token across requests
- 📊 **Response visualization**: Syntax-highlighted JSON responses
- ⏱️ **Request duration**: Display response times
- 🔗 **Deep linking**: Share links to specific endpoints
- 📖 **Expandable sections**: Collapse/expand endpoint groups
- 🌙 **Dark mode**: Monokai syntax highlighting

---

## ReDoc Integration

### 3.1 Custom ReDoc Configuration

**Enhanced ReDoc**:
```python
# app/main.py
from fastapi.openapi.docs import get_redoc_html

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc with additional features"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico",
        with_google_fonts=True,
    )
```

### 3.2 ReDoc Features

**Available at**: `http://localhost:8000/redoc`

**Features**:
- 📚 **Three-panel layout**: Navigation, content, code examples
- 🔍 **Powerful search**: Full-text search across all endpoints
- 📱 **Responsive design**: Mobile-friendly documentation
- 🎨 **Beautiful UI**: Clean, professional design
- 🔗 **Permanent links**: Share links to specific sections
- 📥 **Downloadable**: Export as PDF (browser print)
- 🌐 **Multi-language examples**: cURL, Python, JavaScript
- 📊 **Schema visualization**: Interactive request/response models

---

## API Versioning Strategy

### 4.1 URL-Based Versioning

**Version Routing**:
```python
# app/api/__init__.py
from fastapi import APIRouter
from app.api.v1 import router as v1_router
from app.api.v2 import router as v2_router

# API version routers
api_router = APIRouter()

# Mount v1 (current stable)
api_router.include_router(v1_router, prefix="/v1", tags=["v1"])

# Mount v2 (beta - optional)
api_router.include_router(v2_router, prefix="/v2", tags=["v2"])

# Default to latest stable version
api_router.include_router(v1_router, prefix="", tags=["default"])
```

**Version Headers**:
```python
# app/middleware/versioning.py
from fastapi import Request, HTTPException

async def api_version_middleware(request: Request, call_next):
    """Add API version headers to responses"""
    response = await call_next(request)
    
    # Add version headers
    response.headers["X-API-Version"] = "1.0.0"
    response.headers["X-API-Deprecated"] = "false"
    response.headers["X-API-Sunset-Date"] = ""  # Empty if not deprecated
    
    # For deprecated endpoints
    if request.url.path.startswith("/api/v0"):
        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Sunset-Date"] = "2025-12-31"
        response.headers["X-API-Deprecation-Info"] = "https://docs.aiwebtest.com/migration/v0-to-v1"
    
    return response
```

### 4.2 Deprecation Strategy

**Deprecation Notice**:
```python
# app/api/v1/deprecated.py
from fastapi import APIRouter, status
from warnings import warn

router = APIRouter(prefix="/api/v1", tags=["Tests (Deprecated)"])

@router.post(
    "/test/create",
    deprecated=True,
    summary="Create test (DEPRECATED - Use POST /tests instead)",
    description="""
    ⚠️ **DEPRECATED**: This endpoint will be removed on 2025-12-31.
    
    Please migrate to the new endpoint:
    - Old: `POST /api/v1/test/create`
    - New: `POST /api/v1/tests`
    
    Migration guide: https://docs.aiwebtest.com/migration/test-create
    """,
    responses={
        410: {
            "description": "Gone - Endpoint has been removed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "This endpoint has been removed. Use POST /api/v1/tests instead.",
                        "migration_guide": "https://docs.aiwebtest.com/migration/test-create",
                    }
                }
            },
        },
    },
)
async def create_test_deprecated():
    """Deprecated endpoint - redirects to new endpoint"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been removed. Use POST /api/v1/tests instead.",
        headers={
            "X-API-Deprecated": "true",
            "X-API-Sunset-Date": "2025-12-31",
            "Location": "/api/v1/tests",
        },
    )
```

---

## Request/Response Schemas

### 5.1 Pydantic Models with Examples

**Request Schema**:
```python
# app/schemas/test.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum

class TestType(str, Enum):
    """Supported test types"""
    unit = "unit"
    integration = "integration"
    e2e = "e2e"
    performance = "performance"

class Priority(str, Enum):
    """Test priority levels"""
    high = "high"
    medium = "medium"
    low = "low"

class TestGenerationRequest(BaseModel):
    """Request model for test generation"""
    
    requirements_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Natural language requirements describing what to test",
        example="Test user login with valid and invalid credentials. "
                "Should handle 2FA, remember me, and password reset.",
    )
    
    test_types: List[TestType] = Field(
        default=[TestType.integration],
        description="Types of tests to generate",
        example=["unit", "integration"],
    )
    
    max_tests: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of tests to generate",
        example=10,
    )
    
    priority: Optional[Priority] = Field(
        default=Priority.medium,
        description="Priority level for generated tests",
        example="high",
    )
    
    include_edge_cases: bool = Field(
        default=True,
        description="Generate edge case and error scenario tests",
        example=True,
    )
    
    target_browser: Optional[str] = Field(
        default="chrome",
        regex="^(chrome|firefox|edge)$",
        description="Target browser for E2E tests",
        example="chrome",
    )
    
    @validator("requirements_text")
    def validate_requirements(cls, v):
        """Validate requirements text is not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError("requirements_text cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "requirements_text": "Test user login with email and password. "
                                    "Handle valid login, invalid credentials, and locked accounts.",
                "test_types": ["unit", "integration"],
                "max_tests": 10,
                "priority": "high",
                "include_edge_cases": True,
                "target_browser": "chrome",
            }
        }
```

**Response Schema**:
```python
# app/schemas/test.py
class GeneratedTest(BaseModel):
    """Generated test case model"""
    
    test_id: str = Field(..., description="Unique test identifier", example="TEST-000001")
    title: str = Field(..., description="Test title", example="Test user login with valid credentials")
    description: str = Field(..., description="Test description")
    test_type: TestType = Field(..., description="Test type")
    priority: Priority = Field(..., description="Test priority")
    code: str = Field(..., description="Executable test code")
    expected_output: str = Field(..., description="Expected test output")
    tags: List[str] = Field(default=[], description="Test tags", example=["login", "authentication"])
    estimated_duration: int = Field(..., description="Estimated execution time in seconds", example=30)
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "TEST-000001",
                "title": "Test user login with valid credentials",
                "description": "Verify user can login with correct email and password",
                "test_type": "integration",
                "priority": "high",
                "code": "def test_user_login_valid():\n    ...",
                "expected_output": "Login successful, redirected to dashboard",
                "tags": ["login", "authentication", "happy-path"],
                "estimated_duration": 30,
            }
        }

class TestGenerationResponse(BaseModel):
    """Response model for test generation"""
    
    workflow_id: str = Field(..., description="Workflow ID for tracking", example="workflow_1706716800")
    tests: List[GeneratedTest] = Field(..., description="Generated test cases")
    generation_time_ms: float = Field(..., description="Time taken to generate tests in milliseconds", example=15234.5)
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score", example=0.92)
    scenarios_identified: int = Field(..., description="Number of scenarios identified", example=5)
    
    class Config:
        schema_extra = {
            "example": {
                "workflow_id": "workflow_1706716800",
                "tests": [
                    {
                        "test_id": "TEST-000001",
                        "title": "Test user login with valid credentials",
                        "description": "Verify user can login with correct email and password",
                        "test_type": "integration",
                        "priority": "high",
                        "code": "def test_user_login_valid():\n    ...",
                        "expected_output": "Login successful",
                        "tags": ["login", "authentication"],
                        "estimated_duration": 30,
                    }
                ],
                "generation_time_ms": 15234.5,
                "confidence": 0.92,
                "scenarios_identified": 5,
            }
        }
```

---

## Authentication Documentation

### 6.1 Security Schemes in OpenAPI

**JWT Authentication Example**:
```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.schemas.auth import TokenResponse, LoginRequest

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain JWT token",
    description="""
    Authenticate with username/email and password to obtain a JWT access token.
    
    ## Authentication Flow
    
    1. Submit credentials (username/email + password)
    2. Server validates credentials and checks MFA if enabled
    3. Server generates JWT token (expires in 1 hour)
    4. Client includes token in subsequent requests via `Authorization: Bearer <token>` header
    
    ## Token Format
    
    The JWT token contains:
    - `sub`: User ID
    - `username`: Username
    - `role`: User role (admin, qa_lead, qa_engineer, developer, business_user)
    - `exp`: Expiration timestamp (1 hour from issue)
    - `iat`: Issued at timestamp
    
    ## Example Usage
    
    ```bash
    # Login
    curl -X POST https://api.aiwebtest.com/api/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "user@example.com", "password": "secret123"}'
    
    # Use token
    curl -X GET https://api.aiwebtest.com/api/v1/tests \\
      -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    ```
    """,
    responses={
        200: {
            "description": "Login successful, JWT token returned",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": 123,
                            "username": "user@example.com",
                            "role": "qa_engineer",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect username or password"}
                }
            },
        },
        403: {
            "description": "Account locked or MFA required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "MFA verification required",
                        "mfa_required": True,
                        "mfa_token": "temp_mfa_token_abc123",
                    }
                }
            },
        },
    },
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token"""
    # Implementation
    pass
```

---

## Error Response Standards

### 7.1 Standardized Error Format

**Error Response Model**:
```python
# app/schemas/error.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ValidationError(BaseModel):
    """Validation error detail"""
    loc: List[str] = Field(..., description="Location of error (e.g., ['body', 'username'])")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type (e.g., 'value_error.missing')")

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    validation_errors: Optional[List[ValidationError]] = Field(None, description="Validation errors")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "validation_errors": [
                    {
                        "loc": ["body", "requirements_text"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ],
                "trace_id": "trace_abc123xyz",
            }
        }
```

**Custom Exception Handler**:
```python
# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation error handler"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "validation_errors": exc.errors(),
            "trace_id": request.state.trace_id if hasattr(request.state, "trace_id") else None,
        },
    )
```

---

## Code Examples

### 8.1 Multi-Language Code Examples

**Python Example**:
```python
# Example: Generate tests using Python
import requests

# Authenticate
response = requests.post(
    "https://api.aiwebtest.com/api/v1/auth/login",
    json={"username": "user@example.com", "password": "secret123"}
)
token = response.json()["access_token"]

# Generate tests
response = requests.post(
    "https://api.aiwebtest.com/api/v1/tests/generate",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "requirements_text": "Test user login with valid and invalid credentials",
        "test_types": ["unit", "integration"],
        "max_tests": 10,
    }
)

tests = response.json()["tests"]
print(f"Generated {len(tests)} tests")
```

**JavaScript Example**:
```javascript
// Example: Generate tests using JavaScript (axios)
const axios = require('axios');

async function generateTests() {
  // Authenticate
  const authResponse = await axios.post(
    'https://api.aiwebtest.com/api/v1/auth/login',
    {
      username: 'user@example.com',
      password: 'secret123'
    }
  );
  const token = authResponse.data.access_token;
  
  // Generate tests
  const response = await axios.post(
    'https://api.aiwebtest.com/api/v1/tests/generate',
    {
      requirements_text: 'Test user login with valid and invalid credentials',
      test_types: ['unit', 'integration'],
      max_tests: 10
    },
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  
  console.log(`Generated ${response.data.tests.length} tests`);
}

generateTests();
```

**cURL Example**:
```bash
# Example: Generate tests using cURL

# Authenticate
TOKEN=$(curl -X POST https://api.aiwebtest.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"secret123"}' \
  | jq -r '.access_token')

# Generate tests
curl -X POST https://api.aiwebtest.com/api/v1/tests/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements_text": "Test user login with valid and invalid credentials",
    "test_types": ["unit", "integration"],
    "max_tests": 10
  }'
```

---

## SDK Generation

### 9.1 OpenAPI Generator

**Generate Python SDK**:
```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python SDK
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./sdks/python \
  --package-name aiwebtest_sdk \
  --additional-properties=packageVersion=1.0.0

# Generated SDK usage
from aiwebtest_sdk import ApiClient, Configuration, TestsApi

config = Configuration(
    host="https://api.aiwebtest.com",
    access_token="your_jwt_token"
)

with ApiClient(config) as api_client:
    api = TestsApi(api_client)
    response = api.generate_tests(
        test_generation_request={
            "requirements_text": "Test user login",
            "test_types": ["unit"],
            "max_tests": 5
        }
    )
    print(f"Generated {len(response.tests)} tests")
```

**Generate TypeScript SDK**:
```bash
# Generate TypeScript SDK
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./sdks/typescript \
  --additional-properties=npmName=@aiwebtest/sdk,npmVersion=1.0.0

# Generated SDK usage
import { Configuration, TestsApi } from '@aiwebtest/sdk';

const config = new Configuration({
  basePath: 'https://api.aiwebtest.com',
  accessToken: 'your_jwt_token'
});

const api = new TestsApi(config);

const response = await api.generateTests({
  requirementsText: 'Test user login',
  testTypes: ['unit'],
  maxTests: 5
});

console.log(`Generated ${response.data.tests.length} tests`);
```

---

## Implementation Roadmap

### Phase 1: OpenAPI Setup + Swagger UI + ReDoc (Day 1)

**Tasks**:
- [ ] Configure FastAPI with comprehensive OpenAPI metadata
- [ ] Define security schemes (BearerAuth, OAuth2)
- [ ] Add detailed endpoint documentation with examples
- [ ] Set up custom Swagger UI with enhanced features
- [ ] Set up custom ReDoc with enhanced features
- [ ] Test all endpoints in Swagger UI

**Deliverables**: 
- `app/main.py` with OpenAPI configuration (300 lines)
- All API endpoints with detailed docstrings (1000+ lines)
- Custom Swagger UI and ReDoc pages

### Phase 2: Advanced Documentation + SDK Generation (Day 2)

**Tasks**:
- [ ] Create comprehensive request/response schemas with examples
- [ ] Document authentication flow (JWT, OAuth2, MFA)
- [ ] Standardize error responses
- [ ] Add multi-language code examples (Python, JavaScript, cURL)
- [ ] Generate Python SDK with OpenAPI Generator
- [ ] Generate TypeScript SDK with OpenAPI Generator
- [ ] Create API usage guide with examples
- [ ] Test SDKs with sample code

**Deliverables**:
- `app/schemas/` with all Pydantic models (800 lines)
- `documentation/API-USAGE-GUIDE.md` (500 lines)
- `sdks/python/` (generated Python SDK)
- `sdks/typescript/` (generated TypeScript SDK)

---

## Cost Analysis

### Infrastructure Costs (Monthly)
| Component | Cost | Notes |
|-----------|------|-------|
| OpenAPI/Swagger/ReDoc | $0 | Open-source, no additional cost |
| SDK Generation | $0 | OpenAPI Generator is free |
| Documentation Hosting | $0-10 | GitHub Pages (free) or custom domain |
| **Total** | **$0-10/month** | Essentially free |

### Developer Productivity Gains

**Without API Documentation**:
- Developer onboarding: 2-5 days (reading code, asking questions)
- API integration: 3-7 days (trial and error, debugging)
- Support tickets: 10-20 per month (how to use API?)
- **Total cost**: 5-12 days of development time wasted per developer

**With API Documentation**:
- Developer onboarding: 2-4 hours (read docs, try examples)
- API integration: 1-2 days (follow examples, use SDK)
- Support tickets: 1-2 per month (only complex questions)
- **Total cost**: 1-2 days of development time per developer

**ROI Calculation**:
- Time saved: 4-10 days per developer
- Developer cost: $500/day
- Savings: $2,000-$5,000 per developer
- Documentation investment: $0-10/month
- **ROI**: Infinite (saves 4-10 days per developer, costs $0-10)

**Conclusion**: API documentation is a **no-brainer investment** that pays for itself immediately!

---

## Summary & Integration

### Key Achievements

✅ **OpenAPI 3.0 Specification**: Comprehensive, machine-readable API contract  
✅ **Swagger UI**: Interactive API explorer with try-it-out functionality  
✅ **ReDoc**: Beautiful, searchable API documentation  
✅ **API Versioning**: URL-based versioning with deprecation strategy  
✅ **Request/Response Schemas**: Type-safe Pydantic models with examples  
✅ **Authentication Documentation**: Detailed JWT and OAuth2 flow documentation  
✅ **Error Standards**: Standardized error responses with validation details  
✅ **Code Examples**: Multi-language examples (Python, JavaScript, cURL)  
✅ **SDK Generation**: Auto-generated Python and TypeScript SDKs  

### Integration with Other Components

| Component | Integration Point |
|-----------|------------------|
| **Authentication** | Security schemes documented in OpenAPI, JWT flow examples |
| **Testing** | Contract tests validate API schemas match OpenAPI spec |
| **CI/CD** | Auto-generate and publish API docs on every deployment |
| **Deployment** | Health check endpoint documented, API versioning for zero-downtime |

### Next Steps

1. **Review** this API Documentation architecture document
2. **Update PRD** with API documentation functional requirement
3. **Update SRS** with API documentation tools
4. **Begin Phase 1** implementation (Day 1)

---

**End of API Documentation Standards Architecture Document**

This architecture provides **comprehensive API documentation** for the AI-Web-Test v1 platform, enhancing developer experience and API adoption.

