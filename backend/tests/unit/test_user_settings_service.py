"""
Unit tests for UserSettingsService — Sprint 10.5 Feature 1: OpenRouter Free Models.

TDD RED phase: these tests define the expected behaviour BEFORE implementation.
"""
import pytest
from unittest.mock import patch

from app.services.user_settings_service import UserSettingsService


FREE_MODEL_SUFFIX = ":free"
RECOMMENDED_FREE_MODEL = "qwen/qwen3-coder-480b-a35b:free"
MIN_FREE_OPENROUTER_MODELS = 18  # 19 rows in spec, 18 unique (one duplicate deduped)
MAX_PAID_OPENROUTER_MODELS = 0   # paid models must be removed from list


@pytest.fixture()
def service() -> UserSettingsService:
    return UserSettingsService()


# ---------------------------------------------------------------------------
# PROVIDER_CONFIGS static shape tests
# ---------------------------------------------------------------------------

class TestProviderConfigsStaticShape:
    """Verify static PROVIDER_CONFIGS has the expected structure."""

    def test_openrouter_config_exists(self, service: UserSettingsService):
        assert "openrouter" in service.PROVIDER_CONFIGS

    def test_openrouter_has_required_keys(self, service: UserSettingsService):
        config = service.PROVIDER_CONFIGS["openrouter"]
        assert "display_name" in config
        assert "models" in config
        assert "recommended" in config
        assert "api_key_env" in config

    def test_openrouter_has_enough_free_models(self, service: UserSettingsService):
        """At least MIN_FREE_OPENROUTER_MODELS models with :free suffix must be present."""
        models = service.PROVIDER_CONFIGS["openrouter"]["models"]
        free_models = [m for m in models if m.endswith(FREE_MODEL_SUFFIX)]
        assert len(free_models) >= MIN_FREE_OPENROUTER_MODELS, (
            f"Expected >= {MIN_FREE_OPENROUTER_MODELS} free models, got {len(free_models)}: {free_models}"
        )

    def test_openrouter_no_paid_legacy_models(self, service: UserSettingsService):
        """Stale paid models (gpt-4o, claude-3-*) must be removed."""
        models = service.PROVIDER_CONFIGS["openrouter"]["models"]
        forbidden = [m for m in models if m in ("gpt-4o", "claude-3-opus-20240229", "claude-3-sonnet-20240229")]
        assert forbidden == [], f"Paid models still present: {forbidden}"

    def test_openrouter_no_stale_free_models(self, service: UserSettingsService):
        """Stale/inactive models must be removed."""
        models = service.PROVIDER_CONFIGS["openrouter"]["models"]
        stale = [m for m in models if m in ("qwen/qwen-2-7b-instruct:free", "microsoft/phi-3-mini-128k-instruct:free")]
        assert stale == [], f"Stale free models still present: {stale}"

    def test_recommended_model_is_free_coder_model(self, service: UserSettingsService):
        """Recommended model must be the coder :free model."""
        recommended = service.PROVIDER_CONFIGS["openrouter"]["recommended"]
        assert recommended == RECOMMENDED_FREE_MODEL

    def test_recommended_model_is_in_models_list(self, service: UserSettingsService):
        config = service.PROVIDER_CONFIGS["openrouter"]
        assert config["recommended"] in config["models"]

    def test_no_duplicate_models_in_openrouter(self, service: UserSettingsService):
        models = service.PROVIDER_CONFIGS["openrouter"]["models"]
        assert len(models) == len(set(models)), f"Duplicate models found in list"


# ---------------------------------------------------------------------------
# get_available_providers() — ModelOption / is_free flag tests
# ---------------------------------------------------------------------------

class TestGetAvailableProvidersModelOptions:
    """Each AvailableProvider returned by get_available_providers() must expose
    a `model_options` list where every :free model has is_free=True."""

    @pytest.fixture()
    def openrouter_provider(self, service: UserSettingsService):
        """Run get_available_providers() with a mocked settings object."""
        with patch("app.services.user_settings_service.settings") as mock_settings:
            # Simulate all keys being truthy so all providers show as configured
            mock_settings.GOOGLE_API_KEY = "key"
            mock_settings.CEREBRAS_API_KEY = "key"
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.AZURE_OPENAI_API_KEY = "key"
            providers = service.get_available_providers()
        return next(p for p in providers if p.name == "openrouter")

    def test_openrouter_provider_has_model_options(self, openrouter_provider):
        assert hasattr(openrouter_provider, "model_options"), (
            "AvailableProvider must expose 'model_options' field"
        )

    def test_model_options_is_list(self, openrouter_provider):
        assert isinstance(openrouter_provider.model_options, list)

    def test_model_options_not_empty(self, openrouter_provider):
        assert len(openrouter_provider.model_options) >= MIN_FREE_OPENROUTER_MODELS

    def test_free_models_have_is_free_true(self, openrouter_provider):
        for opt in openrouter_provider.model_options:
            if opt.id.endswith(FREE_MODEL_SUFFIX):
                assert opt.is_free is True, f"Model {opt.id!r} should have is_free=True"

    def test_non_free_models_have_is_free_false(self, openrouter_provider):
        for opt in openrouter_provider.model_options:
            if not opt.id.endswith(FREE_MODEL_SUFFIX):
                assert opt.is_free is False, f"Model {opt.id!r} should have is_free=False"

    def test_model_options_have_id_field(self, openrouter_provider):
        for opt in openrouter_provider.model_options:
            assert hasattr(opt, "id") and opt.id, f"ModelOption missing 'id'"

    def test_model_options_have_display_name_field(self, openrouter_provider):
        for opt in openrouter_provider.model_options:
            assert hasattr(opt, "display_name") and opt.display_name, (
                f"ModelOption {opt.id!r} missing 'display_name'"
            )

    def test_recommended_is_first_in_model_options(self, openrouter_provider):
        """The recommended coder model should appear first in model_options."""
        assert openrouter_provider.model_options[0].id == RECOMMENDED_FREE_MODEL

    def test_backward_compat_models_still_populated(self, openrouter_provider):
        """Legacy `models: list[str]` field must still be populated for old clients."""
        assert len(openrouter_provider.models) >= MIN_FREE_OPENROUTER_MODELS

    def test_models_and_model_options_are_consistent(self, openrouter_provider):
        """Every id in model_options must appear in models (and vice versa)."""
        opt_ids = {opt.id for opt in openrouter_provider.model_options}
        model_ids = set(openrouter_provider.models)
        assert opt_ids == model_ids, (
            f"model_options ids and models must be identical sets.\n"
            f"Only in model_options: {opt_ids - model_ids}\n"
            f"Only in models: {model_ids - opt_ids}"
        )


# ---------------------------------------------------------------------------
# ModelOption schema tests (via AvailableProvider)
# ---------------------------------------------------------------------------

class TestModelOptionSchema:
    """Direct validation of ModelOption Pydantic schema."""

    def test_model_option_can_be_constructed(self):
        from app.schemas.user_settings import ModelOption
        opt = ModelOption(id="google/gemini-2.0-flash-exp:free", display_name="Gemini 2.0 Flash (Exp)", is_free=True)
        assert opt.id == "google/gemini-2.0-flash-exp:free"
        assert opt.display_name == "Gemini 2.0 Flash (Exp)"
        assert opt.is_free is True

    def test_model_option_paid_is_false(self):
        from app.schemas.user_settings import ModelOption
        opt = ModelOption(id="gpt-4o", display_name="GPT-4o", is_free=False)
        assert opt.is_free is False

    def test_model_option_missing_id_raises(self):
        from app.schemas.user_settings import ModelOption
        with pytest.raises(Exception):
            ModelOption(display_name="No ID", is_free=True)  # type: ignore[call-arg]

    def test_available_provider_has_model_options_field(self):
        from app.schemas.user_settings import AvailableProvider
        import inspect
        fields = AvailableProvider.model_fields if hasattr(AvailableProvider, "model_fields") else AvailableProvider.__fields__
        assert "model_options" in fields, "AvailableProvider must have a 'model_options' field"


# ---------------------------------------------------------------------------
# Azure gpt-5.2 model — Sprint 10.8 Developer B
# ---------------------------------------------------------------------------

class TestAzureGpt52Model:
    """gpt-5.2 must appear in the Azure provider model list."""

    def test_gpt52_in_azure_models(self, service: UserSettingsService):
        models = service.PROVIDER_CONFIGS["azure"]["models"]
        assert "gpt-5.2" in models, "gpt-5.2 must be listed in Azure models"

    def test_azure_provider_has_more_than_one_model(self, service: UserSettingsService):
        models = service.PROVIDER_CONFIGS["azure"]["models"]
        assert len(models) >= 2, "Azure provider must have ChatGPT-UAT and gpt-5.2"

    def test_gpt52_in_available_providers_azure_models(self, service: UserSettingsService):
        with patch("app.services.user_settings_service.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = "key"
            mock_settings.CEREBRAS_API_KEY = "key"
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.AZURE_OPENAI_API_KEY = "key"
            providers = service.get_available_providers()
        azure = next(p for p in providers if p.name == "azure")
        assert "gpt-5.2" in azure.models, "gpt-5.2 must appear in the azure provider models list"

    def test_gpt52_model_option_is_not_free(self, service: UserSettingsService):
        with patch("app.services.user_settings_service.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = "key"
            mock_settings.CEREBRAS_API_KEY = "key"
            mock_settings.OPENROUTER_API_KEY = "key"
            mock_settings.AZURE_OPENAI_API_KEY = "key"
            providers = service.get_available_providers()
        azure = next(p for p in providers if p.name == "azure")
        gpt52_opt = next(o for o in azure.model_options if o.id == "gpt-5.2")
        assert gpt52_opt.is_free is False
