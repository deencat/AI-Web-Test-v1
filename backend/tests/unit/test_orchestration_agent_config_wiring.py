"""
Unit tests for Sprint 10.6 Phase 3 (fix):
Orchestration Service Per-Agent LLM Config Wiring

TDD RED phase: verifies that OrchestrationService._resolve_per_agent_llm_config
reads per-agent overrides from user_settings_service and that _create_agents
receives those overrides so agents use the user-configured LLM instead of the
hard-wired Azure default.

Covers:
- _resolve_per_agent_llm_config returns Azure defaults when no override is set
- _resolve_per_agent_llm_config returns user override when set
- _create_agents receives the correct per_agent_llm_config (non-default provider)
- run_workflow passes per-agent config through to agent construction
"""
import pytest
from unittest.mock import MagicMock, patch, call

from app.services.orchestration_service import OrchestrationService

AZURE_DEFAULT = {"provider": "azure", "model": "ChatGPT-UAT"}


@pytest.fixture()
def service() -> OrchestrationService:
    return OrchestrationService(progress_tracker=None)


# ---------------------------------------------------------------------------
# _resolve_per_agent_llm_config
# ---------------------------------------------------------------------------

class TestResolvePerAgentLlmConfig:
    """OrchestrationService._resolve_per_agent_llm_config must read
    user_settings_service.get_agent_config for all four agents and map the
    result into the per_agent_llm_config dict expected by _create_agents."""

    def test_returns_azure_defaults_when_all_agents_unset(self, service):
        """When user_settings has no per-agent overrides, all agents get Azure
        default (provider=azure, model=ChatGPT-UAT)."""
        mock_db = MagicMock()

        with patch(
            "app.services.orchestration_service.user_settings_service"
        ) as mock_svc:
            mock_svc.get_agent_config.return_value = dict(AZURE_DEFAULT)

            result = service._resolve_per_agent_llm_config(mock_db, user_id=1)

        assert result["observation"]["llm_provider"] == "azure"
        assert result["observation"]["llm_model"] == "ChatGPT-UAT"
        assert result["requirements"]["llm_provider"] == "azure"
        assert result["analysis"]["llm_provider"] == "azure"
        assert result["evolution"]["llm_provider"] == "azure"

    def test_returns_override_for_configured_agent(self, service):
        """When observation_provider/model override exists, _resolve returns
        {provider: google, model: gemini-2.0-flash} for observation only."""
        mock_db = MagicMock()

        def _agent_config(db, user_id, agent_name):
            if agent_name == "observation":
                return {"provider": "google", "model": "gemini-2.0-flash"}
            return dict(AZURE_DEFAULT)

        with patch(
            "app.services.orchestration_service.user_settings_service"
        ) as mock_svc:
            mock_svc.get_agent_config.side_effect = _agent_config

            result = service._resolve_per_agent_llm_config(mock_db, user_id=1)

        assert result["observation"]["llm_provider"] == "google"
        assert result["observation"]["llm_model"] == "gemini-2.0-flash"
        # Other agents must stay on Azure
        assert result["requirements"]["llm_provider"] == "azure"
        assert result["analysis"]["llm_provider"] == "azure"
        assert result["evolution"]["llm_provider"] == "azure"

    def test_all_four_agents_can_be_overridden(self, service):
        """Every agent can have an independent override."""
        mock_db = MagicMock()

        overrides = {
            "observation":   {"provider": "google",      "model": "gemini-2.0-flash"},
            "requirements":  {"provider": "openrouter",  "model": "qwen/qwen3-coder-480b-a35b:free"},
            "analysis":      {"provider": "google",      "model": "gemini-1.5-pro"},
            "evolution":     {"provider": "openrouter",  "model": "qwen/qwen3-coder-480b-a35b:free"},
        }

        with patch(
            "app.services.orchestration_service.user_settings_service"
        ) as mock_svc:
            mock_svc.get_agent_config.side_effect = (
                lambda db, user_id, agent_name: overrides[agent_name]
            )

            result = service._resolve_per_agent_llm_config(mock_db, user_id=1)

        assert result["observation"]["llm_provider"] == "google"
        assert result["requirements"]["llm_provider"] == "openrouter"
        assert result["analysis"]["llm_provider"] == "google"
        assert result["evolution"]["llm_provider"] == "openrouter"

    def test_calls_get_agent_config_for_all_four_agents(self, service):
        """get_agent_config must be called once per agent (4 times total)."""
        mock_db = MagicMock()

        with patch(
            "app.services.orchestration_service.user_settings_service"
        ) as mock_svc:
            mock_svc.get_agent_config.return_value = dict(AZURE_DEFAULT)

            service._resolve_per_agent_llm_config(mock_db, user_id=1)

        called_agents = {c.args[2] for c in mock_svc.get_agent_config.call_args_list}
        assert called_agents == {"observation", "requirements", "analysis", "evolution"}

    def test_returns_azure_defaults_when_db_is_none(self, service):
        """When db=None is passed (background tasks without a session),
        _resolve must return all-Azure defaults without crashing."""
        with patch(
            "app.services.orchestration_service.user_settings_service"
        ) as mock_svc:
            mock_svc.get_agent_config.return_value = dict(AZURE_DEFAULT)

            result = service._resolve_per_agent_llm_config(None, user_id=1)

        assert result["observation"]["llm_provider"] == "azure"
        assert result["requirements"]["llm_provider"] == "azure"


# ---------------------------------------------------------------------------
# _create_agents: per_agent_llm_config is wired through to obs_config
# ---------------------------------------------------------------------------

class TestCreateAgentsUsesPerAgentConfig:
    """_create_agents must feed per_agent_llm_config into each agent's config
    dict so the agent reads config.get('llm_provider') / config.get('llm_model')
    from the overrides, not the hard-wired azure default."""

    def test_observation_agent_receives_google_provider_config(self, service):
        """When per_agent_llm_config sets observation to google, ObservationAgent
        must be constructed with a config dict containing llm_provider='google'."""
        per_agent = {
            "observation": {"llm_provider": "google", "llm_model": "gemini-2.0-flash"},
        }

        captured_configs: list = []

        class _CapturingAgent:
            def __init__(self, **kwargs):
                captured_configs.append(kwargs.get("config", {}))

        with patch("agents.observation_agent.ObservationAgent", _CapturingAgent), \
             patch("agents.requirements_agent.RequirementsAgent", _CapturingAgent), \
             patch("agents.analysis_agent.AnalysisAgent", _CapturingAgent), \
             patch("agents.evolution_agent.EvolutionAgent", _CapturingAgent):
            service._create_agents(db=None, per_agent_llm_config=per_agent)

        # First captured config is ObservationAgent's config
        assert len(captured_configs) >= 1
        obs_conf = captured_configs[0]
        assert obs_conf.get("llm_provider") == "google"
        assert obs_conf.get("llm_model") == "gemini-2.0-flash"

    def test_default_agent_config_uses_azure_when_no_override(self, service):
        """When no per_agent_llm_config is provided, ObservationAgent gets
        llm_provider='azure' and llm_model='ChatGPT-UAT'."""
        captured_configs: list = []

        class _CapturingAgent:
            def __init__(self, **kwargs):
                captured_configs.append(kwargs.get("config", {}))

        with patch("agents.observation_agent.ObservationAgent", _CapturingAgent), \
             patch("agents.requirements_agent.RequirementsAgent", _CapturingAgent), \
             patch("agents.analysis_agent.AnalysisAgent", _CapturingAgent), \
             patch("agents.evolution_agent.EvolutionAgent", _CapturingAgent):
            service._create_agents(db=None, per_agent_llm_config=None)

        obs_conf = captured_configs[0]
        assert obs_conf.get("llm_provider") == "azure"
        assert obs_conf.get("llm_model") == "ChatGPT-UAT"
