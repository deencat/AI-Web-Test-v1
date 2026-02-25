"""
API v2: Observation-only entry point.

POST /api/v2/observation
Runs ObservationAgent only (crawl URL, extract UI elements). Use returned workflow_id
to chain into POST /requirements, or GET /workflows/{id}/results for observation_result.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, status
from app.schemas.workflow import ObservationRequest, WorkflowStatusResponse, WorkflowErrorResponse
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state
import uuid
from datetime import datetime

router = APIRouter()


@router.post(
    "/observation",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={400: {"model": WorkflowErrorResponse, "description": "Invalid request"}},
    summary="Run observation only",
    description="""
    Runs **ObservationAgent** only: crawls the URL and extracts UI elements.

    **Returns:** workflow_id immediately (runs in background).
    **Results:** GET `/api/v2/workflows/{workflow_id}/results` for `observation_result`.
    **Chain:** Pass this `workflow_id` to POST `/api/v2/requirements` to run the next stage.
    """,
)
async def run_observation(
    request: ObservationRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> WorkflowStatusResponse:
    """Start observation-only workflow in background."""
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
        "workflow_type": "observation",
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await orchestration_service.run_observation_only(workflow_id, request_dict)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Background observation %s failed: %s", workflow_id, e)

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
