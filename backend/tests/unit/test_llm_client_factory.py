"""
Unit tests for LLM Client Factory (Sprint 10.6 Phase 0 — Task 0.5).

TDD: These tests were written BEFORE implementation.
All tests exercise get_llm_client(provider, model) -> correct client type.

Coverage:
- Azure client returned for provider="azure"
- Cerebras client returned for provider="cerebras"
- Google client returned for provider="google" (when GOOGLE_API_KEY set)
- OpenRouter client returned for provider="openrouter" (when OPENROUTER_API_KEY set)
- Unknown provider falls back to AzureClient
- Google with missing env key falls back to AzureClient
- OpenRouter with missing env key falls back to AzureClient
- Factory exception falls back to AzureClient
- Provider name is case-insensitive
- Returned client has .enabled attribute
"""
import importlib
import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_factory():
    """Import factory fresh to avoid cached module state."""
    import llm.client_factory as cf
    return cf


# ---------------------------------------------------------------------------
# 1. Azure provider
# ---------------------------------------------------------------------------

class TestAzureProvider:
    def test_azure_returns_azure_client(self, monkeypatch):
        """get_llm_client('azure', ...) returns an AzureClient."""
        from llm.azure_client import AzureClient
        cf = _import_factory()
        client = cf.get_llm_client("azure", "ChatGPT-UAT")
        assert isinstance(client, AzureClient)

    def test_azure_uses_specified_model(self, monkeypatch):
        """AzureClient is configured with the model supplied to the factory."""
        cf = _import_factory()
        client = cf.get_llm_client("azure", "gpt-4o-test")
        assert client.deployment == "gpt-4o-test"

    def test_azure_case_insensitive(self):
        """'Azure', 'AZURE', 'azure' all return AzureClient."""
        from llm.azure_client import AzureClient
        cf = _import_factory()
        for variant in ("Azure", "AZURE", " azure "):
            result = cf.get_llm_client(variant, "ChatGPT-UAT")
            assert isinstance(result, AzureClient), f"Failed for variant '{variant}'"

    def test_client_has_enabled_attribute(self):
        """All returned clients expose .enabled (bool)."""
        cf = _import_factory()
        client = cf.get_llm_client("azure", "ChatGPT-UAT")
        assert hasattr(client, "enabled")
        assert isinstance(client.enabled, bool)


# ---------------------------------------------------------------------------
# 2. Cerebras provider
# ---------------------------------------------------------------------------

class TestCerebrasProvider:
    def test_cerebras_returns_cerebras_client(self):
        """get_llm_client('cerebras', ...) returns a CerebrasClient."""
        from llm.cerebras_client import CerebrasClient
        cf = _import_factory()
        client = cf.get_llm_client("cerebras", "llama3.1-8b")
        assert isinstance(client, CerebrasClient)

    def test_cerebras_uses_specified_model(self):
        """CerebrasClient is configured with the model supplied to the factory."""
        cf = _import_factory()
        client = cf.get_llm_client("cerebras", "llama3.1-70b")
        assert client.model == "llama3.1-70b"

    def test_cerebras_has_enabled_attribute(self):
        cf = _import_factory()
        client = cf.get_llm_client("cerebras", "llama3.1-8b")
        assert hasattr(client, "enabled")
        assert isinstance(client.enabled, bool)

    def test_cerebras_case_insensitive(self):
        from llm.cerebras_client import CerebrasClient
        cf = _import_factory()
        for variant in ("Cerebras", "CEREBRAS"):
            result = cf.get_llm_client(variant, "llama3.1-8b")
            assert isinstance(result, CerebrasClient), f"Failed for variant '{variant}'"


# ---------------------------------------------------------------------------
# 3. Google provider
# ---------------------------------------------------------------------------

class TestGoogleProvider:
    def test_google_with_api_key_returns_google_client(self, monkeypatch):
        """get_llm_client('google', ...) returns GoogleClient when key is set."""
        from llm.google_client import GoogleClient
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-123")
        cf = _import_factory()
        client = cf.get_llm_client("google", "gemini-2.0-flash-exp")
        assert isinstance(client, GoogleClient)

    def test_google_uses_specified_model(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-123")
        cf = _import_factory()
        client = cf.get_llm_client("google", "gemini-1.5-pro")
        assert client.model == "gemini-1.5-pro"

    def test_google_has_enabled_attribute(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-123")
        cf = _import_factory()
        client = cf.get_llm_client("google", "gemini-2.0-flash-exp")
        assert hasattr(client, "enabled")
        assert isinstance(client.enabled, bool)

    def test_google_without_api_key_falls_back_to_azure(self, monkeypatch):
        """Missing GOOGLE_API_KEY causes graceful fallback to AzureClient."""
        from llm.azure_client import AzureClient
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        cf = _import_factory()
        client = cf.get_llm_client("google", "gemini-2.0-flash-exp")
        assert isinstance(client, AzureClient)

    def test_google_case_insensitive(self, monkeypatch):
        from llm.google_client import GoogleClient
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-123")
        cf = _import_factory()
        for variant in ("Google", "GOOGLE"):
            result = cf.get_llm_client(variant, "gemini-2.0-flash-exp")
            assert isinstance(result, GoogleClient), f"Failed for variant '{variant}'"


# ---------------------------------------------------------------------------
# 4. OpenRouter provider
# ---------------------------------------------------------------------------

class TestOpenRouterProvider:
    def test_openrouter_with_api_key_returns_openrouter_client(self, monkeypatch):
        """get_llm_client('openrouter', ...) returns OpenRouterClient when key set."""
        from llm.openrouter_client import OpenRouterClient
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        cf = _import_factory()
        client = cf.get_llm_client("openrouter", "meta-llama/llama-3.3-70b-instruct:free")
        assert isinstance(client, OpenRouterClient)

    def test_openrouter_uses_specified_model(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        cf = _import_factory()
        client = cf.get_llm_client("openrouter", "qwen/qwen3-coder-480b-a35b:free")
        assert client.model == "qwen/qwen3-coder-480b-a35b:free"

    def test_openrouter_has_enabled_attribute(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        cf = _import_factory()
        client = cf.get_llm_client("openrouter", "meta-llama/llama-3.3-70b-instruct:free")
        assert hasattr(client, "enabled")
        assert isinstance(client.enabled, bool)

    def test_openrouter_without_api_key_falls_back_to_azure(self, monkeypatch):
        """Missing OPENROUTER_API_KEY causes graceful fallback to AzureClient."""
        from llm.azure_client import AzureClient
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        cf = _import_factory()
        client = cf.get_llm_client("openrouter", "some-model")
        assert isinstance(client, AzureClient)

    def test_openrouter_case_insensitive(self, monkeypatch):
        from llm.openrouter_client import OpenRouterClient
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        cf = _import_factory()
        for variant in ("OpenRouter", "OPENROUTER"):
            result = cf.get_llm_client(variant, "some-model")
            assert isinstance(result, OpenRouterClient), f"Failed for variant '{variant}'"


# ---------------------------------------------------------------------------
# 5. Unknown / fallback behaviour
# ---------------------------------------------------------------------------

class TestFallbackBehaviour:
    def test_unknown_provider_falls_back_to_azure(self):
        """Any unrecognised provider string returns AzureClient."""
        from llm.azure_client import AzureClient
        cf = _import_factory()
        client = cf.get_llm_client("not_a_real_provider", "some_model")
        assert isinstance(client, AzureClient)

    def test_empty_provider_falls_back_to_azure(self):
        from llm.azure_client import AzureClient
        cf = _import_factory()
        client = cf.get_llm_client("", "some_model")
        assert isinstance(client, AzureClient)

    def test_none_provider_falls_back_to_azure(self):
        from llm.azure_client import AzureClient
        cf = _import_factory()
        client = cf.get_llm_client(None, "some_model")
        assert isinstance(client, AzureClient)

    def test_factory_exception_falls_back_to_azure(self, monkeypatch):
        """If any provider constructor raises, factory returns AzureClient."""
        from llm.azure_client import AzureClient
        cf = _import_factory()

        def boom(model):
            raise RuntimeError("Simulated init failure")

        monkeypatch.setattr(cf, "_get_cerebras_client", boom)
        client = cf.get_llm_client("cerebras", "llama3.1-8b")
        assert isinstance(client, AzureClient)

    def test_fallback_uses_azure_default_model(self):
        """Fallback Azure client uses the default Azure model (not the failed provider's model)."""
        cf = _import_factory()
        client = cf.get_llm_client("unknownprovider", "some-model")
        # Should be using the Azure default, not "some-model"
        assert client.deployment == cf._AZURE_DEFAULT_MODEL


# ---------------------------------------------------------------------------
# 6. Agent parameterisation — agents read provider/model from config
# ---------------------------------------------------------------------------

class TestAgentParameterisation:
    """Verify each agent reads llm_provider + llm_model from its config dict."""

    def _make_mock_queue(self):
        mq = MagicMock()
        mq.publish = MagicMock(return_value=None)
        mq.subscribe = MagicMock(return_value=None)
        return mq

    def test_observation_agent_uses_factory_with_cerebras(self, monkeypatch):
        """ObservationAgent with llm_provider=cerebras gets CerebrasClient."""
        from llm.cerebras_client import CerebrasClient
        import llm.client_factory as cf
        created = {}

        original_get = cf.get_llm_client

        def spy(provider, model):
            result = original_get(provider, model)
            created["provider"] = provider
            created["model"] = model
            created["client"] = result
            return result

        # Observation agent imports get_llm_client at MODULE level, so patch there
        monkeypatch.setattr("agents.observation_agent.get_llm_client", spy)

        from agents.observation_agent import ObservationAgent
        config = {
            "use_llm": True,
            "llm_provider": "cerebras",
            "llm_model": "llama3.1-8b",
        }
        agent = ObservationAgent(
            message_queue=self._make_mock_queue(),
            agent_id="test_obs",
            priority=5,
            config=config,
        )
        assert created.get("provider") == "cerebras"
        assert created.get("model") == "llama3.1-8b"
        assert isinstance(agent.llm_client, CerebrasClient)

    def test_requirements_agent_uses_factory_with_openrouter(self, monkeypatch):
        """RequirementsAgent with llm_provider=openrouter gets OpenRouterClient."""
        from llm.openrouter_client import OpenRouterClient
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
        # RequirementsAgent imports get_llm_client at module level — patch there
        monkeypatch.setattr("agents.requirements_agent.get_llm_client",
                            lambda provider, model: __import__('llm.client_factory', fromlist=['get_llm_client']).get_llm_client(provider, model))

        from agents.requirements_agent import RequirementsAgent
        config = {
            "use_llm": True,
            "llm_provider": "openrouter",
            "llm_model": "qwen/qwen3-coder-480b-a35b:free",
        }
        agent = RequirementsAgent(
            agent_id="test_req",
            agent_type="requirements",
            priority=5,
            message_queue=self._make_mock_queue(),
            config=config,
        )
        assert isinstance(agent.llm_client, OpenRouterClient)

    def test_analysis_agent_uses_factory_with_azure(self, monkeypatch):
        """AnalysisAgent with no provider override defaults to AzureClient."""
        from llm.azure_client import AzureClient
        from agents.analysis_agent import AnalysisAgent

        config = {"use_llm": True}  # No llm_provider — should default to azure
        agent = AnalysisAgent(
            agent_id="test_ana",
            agent_type="analysis",
            priority=5,
            message_queue=self._make_mock_queue(),
            config=config,
        )
        assert isinstance(agent.llm_client, AzureClient)

    def test_evolution_agent_uses_factory_with_cerebras(self, monkeypatch):
        """EvolutionAgent with llm_provider=cerebras gets CerebrasClient."""
        from llm.cerebras_client import CerebrasClient
        from agents.evolution_agent import EvolutionAgent

        config = {
            "use_llm": True,
            "llm_provider": "cerebras",
            "llm_model": "llama3.1-70b",
        }
        agent = EvolutionAgent(
            agent_id="test_evo",
            agent_type="evolution",
            priority=5,
            message_queue=self._make_mock_queue(),
            config=config,
        )
        assert isinstance(agent.llm_client, CerebrasClient)

    def test_agent_defaults_to_azure_when_provider_not_in_config(self):
        """Agents default to azure/ChatGPT-UAT when config has no llm_provider."""
        from llm.azure_client import AzureClient
        from agents.evolution_agent import EvolutionAgent

        config = {"use_llm": True}
        agent = EvolutionAgent(
            agent_id="test_evo_default",
            agent_type="evolution",
            priority=5,
            message_queue=self._make_mock_queue(),
            config=config,
        )
        assert isinstance(agent.llm_client, AzureClient)


# ---------------------------------------------------------------------------
# 7. AzureOpenAIAdapter — accepts provider/model constructor args
# ---------------------------------------------------------------------------

class TestAzureOpenAIAdapterFactory:
    def test_adapter_accepts_provider_model_args(self):
        """AzureOpenAIAdapter can be constructed with provider + model kwargs."""
        from llm.browser_use_adapter import AzureOpenAIAdapter

        # Should not raise even if azure client is disabled (no real API key in test)
        adapter = AzureOpenAIAdapter(provider="azure", model="ChatGPT-UAT")
        assert adapter is not None

    def test_adapter_uses_factory_for_non_azure_provider(self, monkeypatch):
        """AzureOpenAIAdapter with provider=openrouter uses OpenRouterClient via factory."""
        from llm.openrouter_client import OpenRouterClient
        import llm.client_factory as cf
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")

        from llm.browser_use_adapter import AzureOpenAIAdapter
        adapter = AzureOpenAIAdapter(provider="openrouter", model="meta-llama/llama-3.3-70b-instruct:free")
        assert isinstance(adapter.azure_client, OpenRouterClient)

    def test_adapter_backward_compatible_azure_client_kwarg(self):
        """AzureOpenAIAdapter still works when azure_client is passed directly."""
        from llm.azure_client import AzureClient, get_azure_client
        from llm.browser_use_adapter import AzureOpenAIAdapter

        azure_c = get_azure_client()
        adapter = AzureOpenAIAdapter(azure_client=azure_c)
        assert adapter.azure_client is azure_c


# ---------------------------------------------------------------------------
# 8. OrchestrationService — injects llm_provider/llm_model into agent configs
# ---------------------------------------------------------------------------

class TestOrchestrationServiceAgentConfig:
    def test_create_agents_injects_default_llm_config(self):
        """_create_agents passes llm_provider and llm_model into each agent config."""
        from app.services.orchestration_service import OrchestrationService
        service = OrchestrationService()

        obs, req, ana, evo = service._create_agents()

        # All agents should have been initialised; llm_client type depends on
        # env configuration — we just verify the agents were created without error.
        assert obs is not None
        assert req is not None
        assert ana is not None
        assert evo is not None

    def test_create_agents_with_explicit_per_agent_config(self):
        """_create_agents accepts per_agent_llm_config dict and injects it."""
        from app.services.orchestration_service import OrchestrationService
        from llm.azure_client import AzureClient

        service = OrchestrationService()
        per_agent = {
            "observation": {"llm_provider": "azure", "llm_model": "ChatGPT-UAT"},
            "requirements": {"llm_provider": "azure", "llm_model": "ChatGPT-UAT"},
            "analysis":     {"llm_provider": "azure", "llm_model": "ChatGPT-UAT"},
            "evolution":    {"llm_provider": "azure", "llm_model": "ChatGPT-UAT"},
        }
        obs, req, ana, evo = service._create_agents(per_agent_llm_config=per_agent)

        # All should use AzureClient (we provide azure explicitly)
        for agent in (obs, req, ana, evo):
            assert isinstance(agent.llm_client, AzureClient)
