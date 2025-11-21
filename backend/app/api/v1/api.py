from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, test_generation, tests, kb, executions

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(test_generation.router, prefix="/tests", tags=["test-generation"])
api_router.include_router(tests.router, prefix="/tests", tags=["test-cases"])
api_router.include_router(executions.router, tags=["test-executions"])
api_router.include_router(kb.router, prefix="/kb", tags=["knowledge-base"])

