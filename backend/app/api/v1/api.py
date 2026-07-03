from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, test_generation, tests, kb, executions, test_templates, test_scenarios, test_suites, settings, debug, versions, execution_feedback, browser_profiles, uploads, email_credentials, step_library, requirements, hermes, schedules, notifications
from app.api.v1.endpoints.agent import jobs as agent_jobs, chat as agent_chat
from app.api.v1.endpoints.agent import conversations as agent_conversations
from app.api.v1.endpoints.agent import registry as agent_registry, backlog as agent_backlog
from app.api.v1.endpoints.agent import heal_review as agent_heal_review
from app.api.v1.endpoints.agent import observatory as agent_observatory
from app.api.v1.endpoints.agent import bridge as agent_bridge

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
api_router.include_router(uploads.router, tags=["uploads"])
api_router.include_router(email_credentials.router, tags=["email-credentials"])
api_router.include_router(step_library.router, tags=["step-library"])
api_router.include_router(requirements.router, prefix="/requirements", tags=["reqiq-proxy"])
api_router.include_router(hermes.router, tags=["hermes"])
api_router.include_router(schedules.router, tags=["schedules"])
api_router.include_router(agent_jobs.router, prefix="/agent", tags=["agent-factory"])
api_router.include_router(agent_chat.router, prefix="/agent", tags=["agent-factory"])
api_router.include_router(agent_conversations.router, prefix="/agent", tags=["agent-factory"])
api_router.include_router(agent_registry.router, prefix="/agent", tags=["agent-factory"])
api_router.include_router(agent_backlog.router, prefix="/agent", tags=["agent-factory"])
api_router.include_router(agent_heal_review.router, prefix="/agent", tags=["agent-factory"])
api_router.include_router(agent_observatory.router, prefix="/agent", tags=["agent-observatory"])
api_router.include_router(agent_bridge.router, prefix="/agent", tags=["hermes-bridge"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

