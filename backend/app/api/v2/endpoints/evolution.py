"""
API v2: Evolution-only entry point.

POST /api/v2/evolution
Runs EvolutionAgent (test generation). Input: workflow_id from a prior analysis run, or inline analysis + requirements + observation.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.schemas.workflow import EvolutionRequest, WorkflowStatusResponse, WorkflowErrorResponse
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state, get_state
import uuid
from datetime import datetime, timezone

router = APIRouter()


@router.post(
    "/evolution",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": WorkflowErrorResponse, "description": "Invalid request (missing prior stage data)"},
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Run evolution only (test generation)",
    description="""
    Runs **EvolutionAgent** only: generates executable test cases from analysis.

    **Input:** Either `workflow_id` (workflow with analysis + requirements + observation) or inline payloads.
    **Returns:** workflow_id (runs in background). GET `/api/v2/workflows/{id}/results` for `test_case_ids`.
    """,
)
async def run_evolution(
    request: EvolutionRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> WorkflowStatusResponse:
    """Start evolution-only workflow in background."""
    if request.workflow_id and not get_state(request.workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Workflow not found", "code": "NOT_FOUND", "workflow_id": request.workflow_id},
        )
    if not request.workflow_id and not all((
        request.analysis_result,
        request.requirements_result,
        request.observation_result,
    )):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Provide workflow_id or analysis_result, requirements_result, and observation_result",
                "code": "MISSING_INPUT",
            },
        )
    workflow_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    request_dict = {
        "workflow_id": request.workflow_id,
        "analysis_result": request.analysis_result,
        "requirements_result": request.requirements_result,
        "observation_result": request.observation_result,
        "user_instruction": request.user_instruction,
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
        "workflow_type": "evolution",
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await orchestration_service.run_evolution_after_analysis(workflow_id, request_dict)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Background evolution %s failed: %s", workflow_id, e)

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
