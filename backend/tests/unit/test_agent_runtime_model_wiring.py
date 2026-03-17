"""Runtime wiring tests for Sprint 10.6 per-agent model selection.

These tests cover the last-mile runtime paths that were still ignoring per-agent
settings even after orchestration injected `llm_provider` / `llm_model`:

1. ObservationAgent browser-use adapter selection
   - non-Azure providers must NOT go through browser-use ChatAzureOpenAI
   - they must use the provider-aware custom adapter instead

2. AnalysisAgent real-time execution
   - StagehandExecutionService.initialize() must receive the AnalysisAgent's
     configured provider/model instead of falling back to .env defaults
"""

from unittest.mock import Mock

import pytest


class _DummyEnabledClient:
    def __init__(self, deployment: str = "dummy-model"):
        self.enabled = True
        self.deployment = deployment
        self.client = object()
        self.api_key = "test-key"


def test_observation_agent_uses_custom_browser_use_adapter_for_non_azure_provider(monkeypatch):
    """ObservationAgent with `llm_provider=openrouter` must bypass the built-in
    ChatAzureOpenAI adapter path and use the provider-aware custom adapter.
    """
    from agents.observation_agent import ObservationAgent

    dummy_client = _DummyEnabledClient("meta-llama/llama-3.3-70b-instruct:free")
    monkeypatch.setattr("agents.observation_agent.get_llm_client", lambda provider, model: dummy_client)

    captured = {}

    class _FakeAdapter:
        def __init__(self, azure_client=None, provider=None, model=None):
            captured["azure_client"] = azure_client
            captured["provider"] = provider
            captured["model"] = model

    monkeypatch.setattr("llm.browser_use_adapter.AzureOpenAIAdapter", _FakeAdapter)

    agent = ObservationAgent(
        message_queue=Mock(),
        config={
            "use_llm": True,
            "llm_provider": "openrouter",
            "llm_model": "meta-llama/llama-3.3-70b-instruct:free",
        },
    )

    adapter = agent._create_browser_use_llm_adapter()

    assert isinstance(adapter, _FakeAdapter)
    assert captured["azure_client"] is dummy_client


@pytest.mark.asyncio
async def test_analysis_agent_passes_agent_model_to_stagehand_initialize(monkeypatch):
    """AnalysisAgent real-time execution must initialize Stagehand with the
    agent's configured provider/model, not the .env execution default.
    """
    from agents.analysis_agent import AnalysisAgent

    captured = {"initialize_user_config": None}

    class _FakeStagehandExecutionService:
        def __init__(self, headless=True):
            self.stagehand = None

        async def initialize(self, user_config=None):
            captured["initialize_user_config"] = user_config
            self.stagehand = object()

        async def _execute_step_hybrid(self, step_desc, idx):
            return {"success": True, "action_method": "stagehand_ai"}

        async def cleanup(self):
            return None

    monkeypatch.setattr(
        "app.services.stagehand_service.StagehandExecutionService",
        _FakeStagehandExecutionService,
    )

    agent = AnalysisAgent(
        agent_id="analysis-test",
        agent_type="analysis",
        priority=5,
        message_queue=Mock(),
        config={
            "use_llm": False,
            "db": None,
            "llm_provider": "openrouter",
            "llm_model": "mistralai/mistral-small-3.1-24b-instruct:free",
        },
    )

    scenario = {
        "scenario_id": "REQ-P-001",
        "title": "Login journey",
        "given": "User is on the homepage",
        "when": "User interacts with the login flow",
        "then": "Journey completes successfully",
    }
    page_context = {"url": "https://www.three.com.hk/postpaid/en"}

    result = await agent._execute_scenario_real_time(scenario, page_context)

    assert result is not None
    assert captured["initialize_user_config"] == {
        "provider": "openrouter",
        "model": "mistralai/mistral-small-3.1-24b-instruct:free",
    }
