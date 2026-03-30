"""Generate-tests skips Observation when flow_recording_path is set."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.orchestration_service import OrchestrationService
from app.services.workflow_store import delete_state


class _Result:
    def __init__(self, task_id: str, success: bool, result=None, error=None):
        self.task_id = task_id
        self.success = success
        self.result = result or {}
        self.error = error
        self.confidence = 0.9
        self.execution_time_seconds = 0.0


class _ObsAgentMustNotRun:
    async def execute_task(self, task):
        raise AssertionError("Observation must be skipped when flow_recording_path is set")


class _ReqAgent:
    async def execute_task(self, task):
        return _Result(
            task_id=task.task_id,
            success=True,
            result={"scenarios": [{"id": 1}], "test_data": [], "coverage_metrics": {}},
        )


class _AnalysisAgent:
    async def execute_task(self, task):
        return _Result(
            task_id=task.task_id,
            success=True,
            result={"risk_scores": [], "final_prioritization": []},
        )


class _EvolutionAgent:
    async def execute_task(self, task):
        return _Result(
            task_id=task.task_id,
            success=True,
            result={"test_case_ids": [501], "test_count": 1},
        )


@pytest.mark.asyncio
async def test_run_workflow_skips_observation_when_flow_recording_path(tmp_path: Path):
    base = tmp_path / "flow_recordings"
    base.mkdir()
    rec = base / "replay_skip_obs"
    rec.mkdir()
    doc = {
        "schema_version": 1,
        "source": "browser-use-observation",
        "start_url": "https://example.com/",
        "goal_reached": True,
        "steps": [
            {
                "order": 1,
                "action": "navigate",
                "target": "https://example.com/",
                "page_url": "https://example.com/",
                "page_title": "Home",
                "element_type": "navigate",
                "locator": None,
            },
        ],
    }
    (rec / "playwright_flow_recording.json").write_text(json.dumps(doc), encoding="utf-8")

    workflow_id = "wf-generate-from-recording"
    delete_state(workflow_id)
    service = OrchestrationService(progress_tracker=None)
    service._create_agents = lambda db=None, **kwargs: (
        _ObsAgentMustNotRun(),
        _ReqAgent(),
        _AnalysisAgent(),
        _EvolutionAgent(),
    )

    with patch("app.utils.flow_recording_persistence.flow_recordings_base_dir", return_value=base):
        result = await service.run_workflow(
            workflow_id,
            {
                "url": "https://example.com/",
                "flow_recording_path": "replay_skip_obs",
            },
        )

    assert result["status"] == "completed"
    assert result["result"]["test_count"] == 1
    delete_state(workflow_id)
