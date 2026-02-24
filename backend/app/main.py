import sys
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.exceptions import APIException
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.timing import add_timing_middleware
from app.middleware.security import add_security_middleware
from app.api.v1.api import api_router
from app.api.v2.api import api_router as api_v2_router
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.init_db import init_db
from app.services.queue_manager import start_queue_manager
from app.db.init_templates import seed_system_templates

# Fix for Windows: Set event loop policy to support subprocess
# This is required for Playwright to work on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database with test data
db = SessionLocal()
try:
    init_db(db)
    seed_system_templates(db)  # Seed built-in templates (Day 7)
finally:
    db.close()

# Start queue manager (Sprint 3 Day 2)
start_queue_manager(
    max_concurrent=settings.MAX_CONCURRENT_EXECUTIONS,
    check_interval=settings.QUEUE_CHECK_INTERVAL
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Add rate limiter state
app.state.limiter = limiter

# Add security middleware
add_security_middleware(app)

# Add timing middleware
add_timing_middleware(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"],
)


# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return rate_limit_exceeded_handler(request, exc)


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    import traceback
    print(f"Unexpected error: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_v2_router, prefix=settings.API_V2_STR)  # Sprint 10: Agent Workflow API


@app.on_event("startup")
async def startup_event():
    """Startup event to ensure Windows event loop policy is set and to log loop type."""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.get_event_loop()
        kind = type(loop).__name__
        if isinstance(loop, asyncio.ProactorEventLoop):
            print("[STARTUP] Windows ProactorEventLoop active (Playwright/browser-use subprocesses supported)")
        else:
            print(f"[STARTUP] WARNING: event loop is {kind}, not ProactorEventLoop. "
                  "Browser/Playwright may fail. Run with: python start_server.py (no reload on Windows)")


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Agentic QA API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "documentation": f"{settings.API_V1_STR}/docs",
        "health_check": f"{settings.API_V1_STR}/health/detailed"
    }


@app.get("/api/version")
def get_api_version():
    """Get API version and capabilities."""
    return {
        "version": "1.0.0",
        "build": "sprint-2-day-5",
        "release_date": "2025-11-20",
        "endpoints": {
            "authentication": 4,
            "users": 3,
            "test_generation": 3,
            "test_management": 6,
            "knowledge_base": 9,
            "health": 3,
            "total": 28
        },
        "features": {
            "authentication": {
                "jwt_tokens": True,
                "oauth2_password_flow": True
            },
            "test_generation": {
                "ai_powered": True,
                "free_models": True,
                "model": "mistralai/mixtral-8x7b-instruct"
            },
            "test_management": {
                "crud_operations": True,
                "search": True,
                "statistics": True,
                "filters": ["type", "status", "priority"]
            },
            "knowledge_base": {
                "file_upload": True,
                "supported_formats": ["PDF", "DOCX", "TXT", "MD"],
                "text_extraction": True,
                "max_file_size": "10MB",
                "categories": 8,
                "search": True
            }
        },
        "enhancements": {
            "custom_exceptions": True,
            "response_wrappers": True,
            "pagination": True,
            "performance_monitoring": True,
            "detailed_health_check": True
        }
    }

