"""
API v2: Generate Tests Endpoint

POST /api/v2/generate-tests
Triggers the 4-agent workflow to generate tests for a given URL.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from app.schemas.workflow import (
    GenerateTestsRequest,
    WorkflowStatusResponse,
    WorkflowErrorResponse,
)
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state
import asyncio
import uuid
from datetime import datetime

router = APIRouter()


@router.post(
    "/generate-tests",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": WorkflowErrorResponse, "description": "Invalid request"},
    },
    summary="Generate tests using 4-agent workflow",
    description="""
    Triggers the 4-agent workflow to analyze a URL and generate test cases.

    **Workflow Stages:**
    1. **ObservationAgent**: Crawls the URL and extracts UI elements
    2. **RequirementsAgent**: Generates BDD test scenarios
    3. **AnalysisAgent**: Analyzes risks, ROI, and dependencies
    4. **EvolutionAgent**: Generates executable test code

    **Returns:** workflow_id immediately (workflow runs in background)
    **Progress:** Track via SSE stream at `/api/v2/workflows/{workflow_id}/stream`
    **Status:** Check via GET `/api/v2/workflows/{workflow_id}`
    **Results:** Retrieve via GET `/api/v2/workflows/{workflow_id}/results`
    """
)
async def generate_tests(
    request: GenerateTestsRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> WorkflowStatusResponse:
    """Start 4-agent workflow in background; return workflow_id immediately."""
    workflow_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    request_dict = {
        "url": str(request.url),
        "user_instruction": request.user_instruction,
        "depth": request.depth,
        "login_credentials": request.login_credentials,
        "gmail_credentials": request.gmail_credentials,
    }

    set_state(workflow_id, {
        "workflow_id": workflow_id,
        "status": "pending",
        "current_agent": None,
        "progress": {},
        "total_progress": 0.0,
        "started_at": started_at.isoformat(),
        "error": None,
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await orchestration_service.run_workflow(workflow_id, request_dict)
        except Exception as e:
            # Workflow already stored failed state in workflow_store; log and avoid re-raising
            # so Starlette does not report "Exception in ASGI application" (client already got 202).
            import logging
            logging.getLogger(__name__).exception("Background workflow %s failed: %s", workflow_id, e)

    background_tasks.add_task(run_in_background)

    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        status="pending",
        current_agent=None,
        progress={},
        total_progress=0.0,
        started_at=started_at,
        estimated_completion=None,
        error=None,
    )

