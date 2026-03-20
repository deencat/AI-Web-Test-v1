"""Logging tests for explicit per-agent provider/model visibility.

These tests ensure the runtime logs clearly show which configured provider/model
`RequirementsAgent` and `EvolutionAgent` are using, so workflow runs can be
verified from server logs.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from agents.base_agent import TaskContext
from agents.evolution_agent import EvolutionAgent
from agents.requirements_agent import RequirementsAgent


def _mock_llm_response_json(payload: str):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = payload
    response.usage.total_tokens = 123
    return response


@pytest.mark.asyncio
async def test_requirements_agent_logs_provider_model_for_scenario_generation(caplog):
    mock_llm_client = MagicMock()
    mock_llm_client.enabled = True
    mock_llm_client.deployment = "nvidia/nemotron-nano-9b-v2:free"
    mock_llm_client.client.chat.completions.create.return_value = _mock_llm_response_json(
        '{"scenarios": [{"scenario_id": "REQ-LLM-001", "title": "Login flow", "given": "User is on page", "when": "User clicks login", "then": "User logs in", "priority": "high", "scenario_type": "functional", "confidence": 0.91}]}'
    )

    with patch("agents.requirements_agent.get_llm_client", return_value=mock_llm_client):
        agent = RequirementsAgent(
            agent_id="req-1",
            agent_type="requirements",
            priority=5,
            message_queue=Mock(),
            config={
                "use_llm": True,
                "llm_provider": "openrouter",
                "llm_model": "nvidia/nemotron-nano-9b-v2:free",
            },
        )

    with caplog.at_level("INFO"):
        scenarios = await agent._generate_scenarios_with_llm(
            ui_elements=[{"type": "button", "text": "Login"}],
            page_structure={"url": "https://example.com/login"},
            page_context={"page_type": "login"},
            user_instruction="test login flow",
        )

    assert scenarios
    assert "RequirementsAgent: Using LLM provider/model for scenario generation: openrouter/nvidia/nemotron-nano-9b-v2:free" in caplog.text


@pytest.mark.asyncio
async def test_evolution_agent_logs_provider_model_for_step_generation(caplog):
    mock_llm_client = MagicMock()
    mock_llm_client.enabled = True
    mock_llm_client.deployment = "llama3.1-8b"
    mock_llm_client.client.chat.completions.create.return_value = _mock_llm_response_json(
        '{"steps": ["Navigate to https://example.com/login", "Click Login", "Verify: Journey completes successfully"]}'
    )

    with patch("llm.client_factory.get_llm_client", return_value=mock_llm_client):
        agent = EvolutionAgent(
            agent_id="evo-1",
            agent_type="evolution",
            priority=5,
            message_queue=Mock(),
            config={
                "use_llm": True,
                "cache_enabled": False,
                "llm_provider": "cerebras",
                "llm_model": "llama3.1-8b",
            },
        )

    task = TaskContext(
        task_id="task-1",
        task_type="test_generation",
        payload={
            "scenarios": [{
                "scenario_id": "REQ-P-001",
                "title": "Page Navigation",
                "given": "User is on the page",
                "when": "User navigates",
                "then": "Journey completes successfully",
                "priority": "high",
                "scenario_type": "functional",
            }],
            "risk_scores": [{"scenario_id": "REQ-P-001", "rpn": 42}],
            "final_prioritization": [{"scenario_id": "REQ-P-001", "composite_score": 0.91}],
            "page_context": {"url": "https://example.com/login", "page_type": "login"},
            "test_data": [],
        },
        conversation_id="conv-1",
    )

    with caplog.at_level("INFO"):
        result = await agent.execute_task(task)

    assert result.success is True
    assert "EvolutionAgent: Using LLM provider/model for step generation: cerebras/llama3.1-8b" in caplog.text
