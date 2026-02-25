"""
API v2: Workflow Management Endpoints

Endpoints for managing workflow state and retrieving results.
"""
from fastapi import APIRouter, HTTPException, status, Path
from app.schemas.workflow import WorkflowStatusResponse, WorkflowResultsResponse, WorkflowErrorResponse
from app.services.workflow_store import get_state, request_cancel
from typing import Optional
from datetime import datetime, timezone

router = APIRouter()


def _parse_datetime(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


@router.get(
    "/{workflow_id}",
    response_model=WorkflowStatusResponse,
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Get workflow status",
    description="Retrieve the current status of a workflow.",
)
async def get_workflow_status(
    workflow_id: str = Path(..., description="Workflow identifier")
) -> WorkflowStatusResponse:
    """Get workflow status by ID."""
    state = get_state(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow not found",
                "code": "NOT_FOUND",
                "workflow_id": workflow_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )
    started_at = _parse_datetime(state.get("started_at")) or datetime.now(timezone.utc)
    return WorkflowStatusResponse(
        workflow_id=state.get("workflow_id", workflow_id),
        status=state.get("status", "pending"),
        current_agent=state.get("current_agent"),
        progress=state.get("progress") or {},
        total_progress=state.get("total_progress", 0.0),
        started_at=started_at,
        estimated_completion=None,
        error=state.get("error"),
    )


@router.get(
    "/{workflow_id}/results",
    response_model=WorkflowResultsResponse,
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Get workflow results",
    description="Retrieve the generated test cases from a completed workflow.",
)
async def get_workflow_results(
    workflow_id: str = Path(..., description="Workflow identifier")
) -> WorkflowResultsResponse:
    """Get workflow results (generated tests)."""
    state = get_state(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow not found",
                "code": "NOT_FOUND",
                "workflow_id": workflow_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )
    result = state.get("result")
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow results not ready (still running or failed)",
                "code": "NOT_READY",
                "workflow_id": workflow_id,
                "status": state.get("status"),
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )
    completed_at = _parse_datetime(state.get("completed_at")) or datetime.now(timezone.utc)
    return WorkflowResultsResponse(
        workflow_id=workflow_id,
        status=state.get("status", "completed"),
        test_case_ids=result.get("test_case_ids") or [],
        test_count=result.get("test_count", 0),
        observation_result=result.get("observation_result"),
        requirements_result=result.get("requirements_result"),
        analysis_result=result.get("analysis_result"),
        evolution_result=result.get("evolution_result"),
        completed_at=completed_at,
        total_duration_seconds=result.get("total_duration_seconds", 0.0),
    )


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Cancel workflow",
    description="""
    Cancel a running workflow. Sets a cancellation flag; the orchestration checks it
    between stages and stops cleanly. GET /workflows/{id} will show status `cancelled` once stopped.
    Returns 204 No Content on success, 404 if the workflow does not exist.
    """,
)
async def cancel_workflow(
    workflow_id: str = Path(..., description="Workflow identifier")
):
    """Cancel a running workflow. Returns 204 on success, 404 if not found."""
    state = get_state(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow not found",
                "code": "NOT_FOUND",
                "workflow_id": workflow_id,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )
    request_cancel(workflow_id)
    return None  # 204 No Content

