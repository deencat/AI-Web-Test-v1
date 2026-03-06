"""
Unit tests for EvolutionAgent intra-stage progress and cooperative cancellation.
"""

import pytest
from unittest.mock import MagicMock

from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext


@pytest.fixture
def agent_no_llm():
    return EvolutionAgent(
        agent_id="evo_test",
        agent_type="evolution",
        priority=5,
        message_queue=MagicMock(),
        config={"use_llm": False, "cache_enabled": False},
    )


def _scenario(i: int) -> dict:
    return {
        "scenario_id": f"REQ-{i:03d}",
        "title": f"Scenario {i}",
        "given": "Given user is on page",
        "when": "When user performs action",
        "then": "Then expected result is shown",
        "priority": "medium",
        "scenario_type": "functional",
    }


@pytest.mark.asyncio
async def test_evolution_emits_progress_callback_for_intra_stage_updates(agent_no_llm):
    progress_events = []

    def progress_callback(payload):
        progress_events.append(payload)

    task = TaskContext(
        task_id="task-progress",
        task_type="test_generation",
        payload={
            "scenarios": [_scenario(1), _scenario(2), _scenario(3)],
            "risk_scores": [],
            "final_prioritization": [],
            "page_context": {"url": "https://example.com"},
            "test_data": [],
            "progress_callback": progress_callback,
            "cancel_check": lambda: False,
        },
        conversation_id="conv-progress",
    )

    result = await agent_no_llm.execute_task(task)

    assert result.success is True
    assert result.result.get("test_count") == 3
    assert len(progress_events) >= 3
    assert any(e.get("message", "").startswith("Processing scenario") for e in progress_events)
    assert any(e.get("progress", 0) > 0 for e in progress_events)


@pytest.mark.asyncio
async def test_evolution_stops_early_when_cancel_requested_mid_stage(agent_no_llm):
    calls = {"count": 0}

    def cancel_check():
        calls["count"] += 1
        # allow first scenario, then request cancel
        return calls["count"] > 1

    task = TaskContext(
        task_id="task-cancel",
        task_type="test_generation",
        payload={
            "scenarios": [_scenario(1), _scenario(2), _scenario(3), _scenario(4)],
            "risk_scores": [],
            "final_prioritization": [],
            "page_context": {"url": "https://example.com"},
            "test_data": [],
            "cancel_check": cancel_check,
        },
        conversation_id="conv-cancel",
    )

    result = await agent_no_llm.execute_task(task)

    assert result.success is True
    assert result.result.get("test_count", 0) < 4
    assert result.metadata.get("cancelled") is True
