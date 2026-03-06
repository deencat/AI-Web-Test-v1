"""
Unit tests for OrchestrationService intra-stage progress callbacks and cancellation hooks.

TDD RED tests for Sprint 10 enhancements:
- pass progress_callback into long-running stage payloads
- pass cancel_check into long-running stage payloads
- emit agent_progress events from callback payloads
"""

import asyncio
import pytest

from app.services.orchestration_service import OrchestrationService
from app.services.workflow_store import delete_state, request_cancel


class _Result:
    def __init__(self, task_id: str, success: bool, result=None, error=None, confidence: float = 0.0):
        self.task_id = task_id
        self.success = success
        self.result = result or {}
        self.error = error
        self.confidence = confidence
        self.execution_time_seconds = 0.0


class _Tracker:
    def __init__(self):
        self.events = []

    async def emit(self, workflow_id: str, event: str, data: dict):
        self.events.append((workflow_id, event, data))


class _ObsAgent:
    def __init__(self, should_cancel=False):
        self.should_cancel = should_cancel

    async def execute_task(self, task):
        progress_callback = task.payload.get("progress_callback")
        cancel_check = task.payload.get("cancel_check")

        assert callable(progress_callback), "progress_callback must be provided in observation payload"
        assert callable(cancel_check), "cancel_check must be provided in observation payload"

        progress_callback(
            {
                "progress": 0.25,
                "message": "Analyzing page 1/4",
                "pages_analyzed": 1,
                "pages_total": 4,
            }
        )

        if self.should_cancel:
            request_cancel(task.conversation_id)
            # Agent checks cancel hook during stage work
            _ = cancel_check()
            return _Result(
                task_id=task.task_id,
                success=True,
                result={
                    "ui_elements": [],
                    "page_structure": {},
                    "page_context": {"url": task.payload.get("url", "")},
                },
                confidence=0.7,
            )

        progress_callback(
            {
                "progress": 0.75,
                "message": "Analyzing page 3/4",
                "pages_analyzed": 3,
                "pages_total": 4,
            }
        )

        return _Result(
            task_id=task.task_id,
            success=True,
            result={
                "ui_elements": [{"type": "input"}, {"type": "button"}],
                "page_structure": {},
                "page_context": {"url": task.payload.get("url", "")},
            },
            confidence=0.9,
        )


class _ReqAgent:
    async def execute_task(self, task):
        progress_callback = task.payload.get("progress_callback")
        cancel_check = task.payload.get("cancel_check")
        assert callable(progress_callback), "progress_callback must be provided in requirements payload"
        assert callable(cancel_check), "cancel_check must be provided in requirements payload"

        progress_callback(
            {
                "progress": 0.40,
                "message": "Generating scenarios 1/2",
                "scenarios_generated": 1,
                "scenarios_total": 2,
            }
        )

        return _Result(
            task_id=task.task_id,
            success=True,
            result={"scenarios": [{"id": 1}, {"id": 2}], "test_data": [], "coverage_metrics": {}},
            confidence=0.9,
        )


class _AnalysisAgent:
    async def execute_task(self, task):
        progress_callback = task.payload.get("progress_callback")
        cancel_check = task.payload.get("cancel_check")
        assert callable(progress_callback), "progress_callback must be provided in analysis payload"
        assert callable(cancel_check), "cancel_check must be provided in analysis payload"

        progress_callback(
            {
                "progress": 0.55,
                "message": "Analyzing risk for scenario 1/2",
                "scenarios_analyzed": 1,
                "scenarios_total": 2,
            }
        )

        return _Result(
            task_id=task.task_id,
            success=True,
            result={"risk_scores": [], "final_prioritization": []},
            confidence=0.9,
        )


class _EvolutionAgent:
    async def execute_task(self, task):
        return _Result(
            task_id=task.task_id,
            success=True,
            result={"test_case_ids": [101, 102], "test_count": 2},
            confidence=0.9,
        )


@pytest.mark.asyncio
async def test_run_workflow_emits_intra_stage_agent_progress_events():
    workflow_id = "wf-intra-stage-progress"
    delete_state(workflow_id)

    tracker = _Tracker()
    service = OrchestrationService(progress_tracker=tracker)

    service._create_agents = lambda db=None: (_ObsAgent(False), _ReqAgent(), _AnalysisAgent(), _EvolutionAgent())

    result = await service.run_workflow(workflow_id, {"url": "https://example.com"})
    assert result["status"] == "completed"

    await asyncio.sleep(0.02)

    progress_events = [e for e in tracker.events if e[1] == "agent_progress"]
    assert progress_events, "Expected at least one agent_progress event"
    assert any(e[2].get("agent") == "observation" for e in progress_events)
    assert any(e[2].get("pages_total") == 4 for e in progress_events)

    delete_state(workflow_id)


@pytest.mark.asyncio
async def test_run_workflow_can_cancel_during_observation_stage_work():
    workflow_id = "wf-cancel-mid-observation"
    delete_state(workflow_id)

    tracker = _Tracker()
    service = OrchestrationService(progress_tracker=tracker)

    service._create_agents = lambda db=None: (_ObsAgent(True), _ReqAgent(), _AnalysisAgent(), _EvolutionAgent())

    result = await service.run_workflow(workflow_id, {"url": "https://example.com"})
    assert result["status"] == "cancelled"

    await asyncio.sleep(0.02)
    started_agents = [e[2].get("agent") for e in tracker.events if e[1] == "agent_started"]
    assert started_agents == ["observation"], "Workflow should not proceed to requirements after cancel"

    delete_state(workflow_id)
