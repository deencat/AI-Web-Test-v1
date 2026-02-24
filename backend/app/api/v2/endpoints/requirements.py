"""
API v2: Requirements-only entry point.

POST /api/v2/requirements
Runs RequirementsAgent. Input: workflow_id from a prior observation run, or inline observation_result.
Chain with POST /analysis next.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.schemas.workflow import RequirementsRequest, WorkflowStatusResponse, WorkflowErrorResponse
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state, get_state
import uuid
from datetime import datetime

router = APIRouter()


@router.post(
    "/requirements",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": WorkflowErrorResponse, "description": "Invalid request (missing observation data)"},
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Run requirements only",
    description="""
    Runs **RequirementsAgent** only: generates BDD scenarios from observation data.

    **Input:** Either `workflow_id` (from a completed observation workflow) or inline `observation_result`.
    **Returns:** workflow_id (runs in background).
    **Chain:** Pass this or the same workflow_id to POST `/api/v2/analysis` next.
    """,
)
async def run_requirements(
    request: RequirementsRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> WorkflowStatusResponse:
    """Start requirements-only workflow in background."""
    if not request.workflow_id and not request.observation_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Provide workflow_id or observation_result", "code": "MISSING_INPUT"},
        )
    if request.workflow_id and not get_state(request.workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Workflow not found", "code": "NOT_FOUND", "workflow_id": request.workflow_id},
        )
    workflow_id = str(uuid.uuid4())
    started_at = datetime.utcnow()
    request_dict = {
        "workflow_id": request.workflow_id,
        "observation_result": request.observation_result,
        "user_instruction": request.user_instruction,
    }
    set_state(workflow_id, {
        "workflow_id": workflow_id,
        "status": "pending",
        "current_agent": None,
        "progress": {},
        "total_progress": 0.0,
        "started_at": started_at.isoformat(),
        "error": None,
        "workflow_type": "requirements",
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await orchestration_service.run_requirements_after_observation(workflow_id, request_dict)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Background requirements %s failed: %s", workflow_id, e)

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
