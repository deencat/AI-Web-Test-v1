"""
Unit tests for OrchestrationService cancellation (API v2).
When cancel is requested, run_workflow should stop cleanly and return status cancelled.
"""
import pytest
from app.services.workflow_store import set_state, request_cancel, delete_state, get_state
from app.services.orchestration_service import OrchestrationService
from app.services.progress_tracker import ProgressTracker


@pytest.fixture(autouse=True)
def clear_workflow():
    wfid = "wf-orch-cancel-test"
    delete_state(wfid)
    yield wfid
    delete_state(wfid)


@pytest.mark.asyncio
async def test_run_workflow_exits_early_when_cancel_requested(clear_workflow):
    """If request_cancel is called before run_workflow, it should return cancelled without running agents."""
    workflow_id = clear_workflow
    set_state(workflow_id, {
        "workflow_id": workflow_id,
        "status": "pending",
        "current_agent": None,
        "progress": {},
        "total_progress": 0.0,
        "started_at": "2026-02-23T10:00:00",
        "error": None,
    })
    request_cancel(workflow_id)

    service = OrchestrationService(progress_tracker=ProgressTracker())
    result = await service.run_workflow(workflow_id, {"url": "https://example.com"})

    assert result["workflow_id"] == workflow_id
    assert result["status"] == "cancelled"
    state = get_state(workflow_id)
    assert state is not None
    assert state.get("status") == "cancelled"
    assert "Cancelled by user" in (state.get("error") or "")
