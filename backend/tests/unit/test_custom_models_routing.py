"""
Sprint 10.20 — Custom model config resolution & routing unit tests.

TDD RED phase: defines expected behaviour BEFORE implementation.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.user_settings_service import UserSettingsService


CUSTOM_SENTINEL = "__custom__"


@pytest.fixture()
def service() -> UserSettingsService:
    return UserSettingsService()


def _make_user_settings(**kwargs):
    defaults = {
        "generation_provider": "openrouter",
        "generation_model": "google/gemini-2.0-flash-exp:free",
        "generation_temperature": 0.7,
        "generation_max_tokens": 4096,
        "execution_provider": "openrouter",
        "execution_model": "google/gemini-2.0-flash-exp:free",
        "execution_temperature": 0.7,
        "execution_max_tokens": 4096,
        "local_vllm_custom_model": None,
        "local_vllm_custom_endpoint": None,
        "local_vllm_api_key": None,
        "local_vllm_enable_thinking": False,
        "custom_models": None,
    }
    defaults.update(kwargs)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


# ---------------------------------------------------------------------------
# get_provider_config() — __custom__ sentinel resolution
# ---------------------------------------------------------------------------

class TestGetProviderConfigCustomSentinel:
    def test_openrouter_custom_sentinel_resolves_from_registry(self, service):
        registry = {"openrouter": [{"id": "my/custom:free"}]}
        user = _make_user_settings(
            generation_provider="openrouter",
            generation_model=CUSTOM_SENTINEL,
            custom_models=registry,
        )
        db = MagicMock()
        service.get_user_settings = MagicMock(return_value=user)

        config = service.get_provider_config(db, user_id=1, config_type="generation")
        assert config["model"] == "my/custom:free"
        assert config["provider"] == "openrouter"

    def test_openrouter_custom_sentinel_falls_back_to_local_vllm_custom_model(self, service):
        """Migration compat: local_vllm_custom_model used when registry empty."""
        user = _make_user_settings(
            generation_provider="openrouter",
            generation_model=CUSTOM_SENTINEL,
            local_vllm_custom_model="legacy/custom-model",
            custom_models=None,
        )
        db = MagicMock()
        service.get_user_settings = MagicMock(return_value=user)

        config = service.get_provider_config(db, user_id=1, config_type="generation")
        assert config["model"] == "legacy/custom-model"

    def test_azure_custom_includes_endpoint_override(self, service):
        registry = {
            "azure": [{
                "id": "gpt-5.3",
                "endpoint": "https://custom.openai.azure.com",
                "api_version": "2024-12-01-preview",
            }]
        }
        user = _make_user_settings(
            generation_provider="azure",
            generation_model="gpt-5.3",
            custom_models=registry,
        )
        db = MagicMock()
        service.get_user_settings = MagicMock(return_value=user)

        config = service.get_provider_config(db, user_id=1, config_type="generation")
        assert config["model"] == "gpt-5.3"
        assert config["azure_endpoint"] == "https://custom.openai.azure.com"
        assert config["azure_api_version"] == "2024-12-01-preview"

    def test_local_vllm_custom_sentinel_still_works(self, service):
        user = _make_user_settings(
            generation_provider="local_vllm",
            generation_model=CUSTOM_SENTINEL,
            local_vllm_custom_model="MyCustomModel",
            local_vllm_custom_endpoint="http://192.168.1.1:8000/v1",
        )
        db = MagicMock()
        service.get_user_settings = MagicMock(return_value=user)

        config = service.get_provider_config(db, user_id=1, config_type="generation")
        assert config["model"] == "MyCustomModel"
        assert config["local_vllm_custom_endpoint"] == "http://192.168.1.1:8000/v1"


# ---------------------------------------------------------------------------
# get_agent_config() — __custom__ sentinel resolution
# ---------------------------------------------------------------------------

class TestGetAgentConfigCustomSentinel:
    def test_agent_custom_sentinel_resolves_from_registry(self, service):
        registry = {"google": [{"id": "gemini-custom-preview"}]}
        user = _make_user_settings(
            observation_provider="google",
            observation_model=CUSTOM_SENTINEL,
            custom_models=registry,
        )
        db = MagicMock()
        service.get_user_settings = MagicMock(return_value=user)

        config = service.get_agent_config(db, user_id=1, agent_name="observation")
        assert config["provider"] == "google"
        assert config["model"] == "gemini-custom-preview"

    def test_agent_azure_custom_includes_endpoint(self, service):
        registry = {
            "azure": [{
                "id": "my-deploy",
                "endpoint": "https://eastus2.openai.azure.com",
                "api_version": "2024-12-01-preview",
            }]
        }
        user = _make_user_settings(
            analysis_provider="azure",
            analysis_model="my-deploy",
            custom_models=registry,
        )
        db = MagicMock()
        service.get_user_settings = MagicMock(return_value=user)

        config = service.get_agent_config(db, user_id=1, agent_name="analysis")
        assert config["model"] == "my-deploy"
        assert config.get("azure_endpoint") == "https://eastus2.openai.azure.com"


# ---------------------------------------------------------------------------
# resolve_custom_model() — lookup helper
# ---------------------------------------------------------------------------

class TestResolveCustomModel:
    def test_finds_model_in_registry(self, service):
        registry = {"openrouter": [{"id": "test/model:free", "display_name": "Test"}]}
        entry = service.resolve_custom_model_entry(registry, "openrouter", "test/model:free")
        assert entry is not None
        assert entry["id"] == "test/model:free"

    def test_returns_none_for_unknown_model(self, service):
        registry = {"openrouter": [{"id": "known/model:free"}]}
        entry = service.resolve_custom_model_entry(registry, "openrouter", "unknown/model")
        assert entry is None

    def test_unknown_custom_without_registry_raises(self, service):
        with pytest.raises(ValueError, match="custom model"):
            service.resolve_custom_model_for_provider(
                custom_models={},
                provider="openrouter",
                model=CUSTOM_SENTINEL,
                fallback_custom_name=None,
            )


# ---------------------------------------------------------------------------
# UniversalLLM — azure endpoint override from user config (Sprint 10.20-B5)
# ---------------------------------------------------------------------------

class TestUniversalLlmAzureCustomEndpoint:
    @pytest.mark.asyncio
    async def test_chat_completion_forwards_azure_endpoint_override(self, monkeypatch):
        from app.services.universal_llm import UniversalLLMService

        captured: dict = {}

        async def fake_call_azure(self, messages, model=None, temperature=0.7, max_tokens=None, endpoint_override=None, api_version_override=None):
            captured["endpoint_override"] = endpoint_override
            captured["api_version_override"] = api_version_override
            return {"choices": [{"message": {"content": "ok"}}]}

        monkeypatch.setattr(UniversalLLMService, "_call_azure", fake_call_azure)

        service = UniversalLLMService()
        await service.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            provider="azure",
            model="gpt-5.3",
            azure_endpoint="https://custom.openai.azure.com",
            azure_api_version="2024-12-01-preview",
        )

        assert captured["endpoint_override"] == "https://custom.openai.azure.com"
        assert captured["api_version_override"] == "2024-12-01-preview"
