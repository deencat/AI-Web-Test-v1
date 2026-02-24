"""
API v2: Improve existing tests entry point.

POST /api/v2/improve-tests
Runs iterative improvement workflow on existing test case IDs (evolution + analysis loop).
"""
from fastapi import APIRouter, BackgroundTasks, Depends, status
from app.schemas.workflow import ImproveTestsRequest, WorkflowStatusResponse, WorkflowErrorResponse
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state
import uuid
from datetime import datetime

router = APIRouter()


@router.post(
    "/improve-tests",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={400: {"model": WorkflowErrorResponse, "description": "Invalid request"}},
    summary="Improve existing tests (iterative)",
    description="""
    Runs **iterative improvement** workflow on existing test cases: evolution + analysis loop
    (up to `max_iterations`). Use when you want to refine tests by ID rather than generate from a URL.

    **Input:** `test_case_ids`, optional `user_instruction`, `max_iterations`.
    **Returns:** workflow_id (runs in background). **Status:** Implementation may be stub;
    full loop is defined in OrchestrationService.run_iterative_workflow.
    """,
)
async def improve_tests(
    request: ImproveTestsRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> WorkflowStatusResponse:
    """Start improve-tests workflow in background."""
    workflow_id = str(uuid.uuid4())
    started_at = datetime.utcnow()
    request_dict = {
        "test_case_ids": request.test_case_ids,
        "user_instruction": request.user_instruction,
        "max_iterations": request.max_iterations,
    }
    set_state(workflow_id, {
        "workflow_id": workflow_id,
        "status": "pending",
        "current_agent": None,
        "progress": {},
        "total_progress": 0.0,
        "started_at": started_at.isoformat(),
        "error": None,
        "workflow_type": "improve",
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await orchestration_service.run_iterative_workflow(
                workflow_id,
                request_dict,
                max_iterations=request.max_iterations,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Background improve-tests %s failed: %s", workflow_id, e)

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
