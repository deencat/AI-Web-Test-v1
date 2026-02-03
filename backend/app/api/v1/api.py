from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, test_generation, tests, kb, executions, test_templates, test_scenarios, test_suites, settings, debug, versions, execution_feedback, browser_profiles

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(test_generation.router, prefix="/tests", tags=["test-generation"])
api_router.include_router(tests.router, prefix="/tests", tags=["test-cases"])
api_router.include_router(versions.router, prefix="/tests", tags=["test-versions"])  # Phase 2: Version control
api_router.include_router(executions.router, prefix="/executions", tags=["test-executions"])
api_router.include_router(execution_feedback.router, tags=["execution-feedback"])
api_router.include_router(kb.router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(test_templates.router, prefix="/test-templates", tags=["test-templates"])
api_router.include_router(test_scenarios.router, prefix="/scenarios", tags=["test-scenarios"])
api_router.include_router(test_suites.router, prefix="/suites", tags=["test-suites"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(debug.router, tags=["debug"])
api_router.include_router(browser_profiles.router, tags=["browser-profiles"])

