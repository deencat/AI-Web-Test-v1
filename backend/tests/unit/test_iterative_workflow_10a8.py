"""
Unit tests for 10A.8 iterative improvement workflow (run_iterative_workflow).
Tests: validation (empty test_case_ids, missing test case), cancel, and one full iteration with mocks.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.workflow_store import set_state, request_cancel, delete_state, get_state
from app.services.orchestration_service import OrchestrationService
from app.services.progress_tracker import ProgressTracker


@pytest.fixture(autouse=True)
def clear_workflow():
    wfid = "wf-iter-10a8"
    delete_state(wfid)
    yield wfid
    delete_state(wfid)


@pytest.mark.asyncio
async def test_run_iterative_workflow_requires_test_case_ids():
    """run_iterative_workflow raises ValueError when test_case_ids is missing or empty."""
    service = OrchestrationService(progress_tracker=ProgressTracker())
    with pytest.raises(ValueError, match="test_case_ids"):
        await service.run_iterative_workflow("wf-any", {"user_instruction": "x"}, max_iterations=1)
    with pytest.raises(ValueError, match="test_case_ids"):
        await service.run_iterative_workflow("wf-any", {"test_case_ids": []}, max_iterations=1)


@pytest.mark.asyncio
async def test_run_iterative_workflow_exits_when_cancel_requested(clear_workflow):
    """If cancel is requested before the loop, run_iterative_workflow returns cancelled."""
    workflow_id = clear_workflow
    set_state(workflow_id, {"workflow_id": workflow_id, "status": "pending"})
    request_cancel(workflow_id)

    # Mock DB and get_test_case to return one test case so we enter the loop, then cancel
    fake_tc = MagicMock()
    fake_tc.id = 1
    fake_tc.title = "Test"
    fake_tc.description = "Desc"
    fake_tc.steps = ["step1"]
    fake_tc.expected_result = "OK"

    with patch("app.db.session.SessionLocal") as mock_session:
        with patch("app.crud.test_case.get_test_case", return_value=fake_tc):
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            service = OrchestrationService(progress_tracker=ProgressTracker())
            # Cancel is already requested; first _check_cancelled() in loop should trigger
            result = await service.run_iterative_workflow(
                workflow_id,
                {"test_case_ids": [1], "user_instruction": ""},
                max_iterations=2,
            )
    assert result.get("status") == "cancelled"
    state = get_state(workflow_id)
    assert state and state.get("status") == "cancelled"


@pytest.mark.asyncio
async def test_run_iterative_workflow_one_iteration_with_mocked_agents(clear_workflow):
    """Full one iteration: load test cases -> evolution -> analysis -> completed (mocked agents)."""
    workflow_id = clear_workflow
    fake_tc = MagicMock()
    fake_tc.id = 101
    fake_tc.title = "Login test"
    fake_tc.description = "Given login page"
    fake_tc.steps = ["open url", "enter credentials"]
    fake_tc.expected_result = "User is logged in"

    evolution_result = MagicMock()
    evolution_result.success = True
    evolution_result.result = {"test_case_ids": [201, 202], "test_count": 2}

    analysis_result = MagicMock()
    analysis_result.success = True
    analysis_result.result = {
        "risk_scores": [{"scenario_id": "101", "rpn": 20}],
        "final_prioritization": [],
    }

    fake_tc_2 = MagicMock()
    fake_tc_2.id = 201
    fake_tc_2.title = "Evolved"
    fake_tc_2.description = "Desc"
    fake_tc_2.steps = ["step1"]
    fake_tc_2.expected_result = "OK"

    def get_test_case_side_effect(db, tid):
        if tid in (101,):
            return fake_tc
        if tid in (201, 202):
            return fake_tc_2
        return None

    with patch("app.db.session.SessionLocal") as mock_session:
        with patch("app.crud.test_case.get_test_case", side_effect=get_test_case_side_effect):
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            with patch.object(OrchestrationService, "_create_agents") as mock_create:
                mock_obs, mock_req, mock_ana, mock_evo = MagicMock(), MagicMock(), MagicMock(), MagicMock()
                mock_evo.execute_task = AsyncMock(return_value=evolution_result)
                mock_ana.execute_task = AsyncMock(return_value=analysis_result)
                mock_create.return_value = (mock_obs, mock_req, mock_ana, mock_evo)
                service = OrchestrationService(progress_tracker=ProgressTracker())
                result = await service.run_iterative_workflow(
                    workflow_id,
                    {"test_case_ids": [101], "user_instruction": "Improve", "max_iterations": 1},
                    max_iterations=1,
                )
    assert result.get("status") == "completed"
    assert result.get("workflow_id") == workflow_id
    assert "iteration_history" in result
    assert len(result["iteration_history"]) == 1
    assert result["iteration_history"][0]["iteration"] == 1
    assert result.get("test_case_ids") == [201, 202]
    state = get_state(workflow_id)
    assert state and state.get("status") == "completed"
    assert state.get("result", {}).get("iterations_completed") == 1
