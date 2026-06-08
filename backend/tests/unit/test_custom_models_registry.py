"""
Sprint 10.20 — User-Configurable Custom AI Models: registry unit tests.

TDD RED phase: defines expected behaviour BEFORE implementation.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from app.services.user_settings_service import UserSettingsService
from app.schemas.user_settings import CustomModelEntry, validate_model_id


CUSTOM_SENTINEL = "__custom__"


@pytest.fixture()
def service() -> UserSettingsService:
    return UserSettingsService()


# ---------------------------------------------------------------------------
# validate_model_id()
# ---------------------------------------------------------------------------

class TestValidateModelId:
    def test_accepts_valid_openrouter_id(self):
        assert validate_model_id("my/vendor-model:free") == "my/vendor-model:free"

    def test_accepts_valid_azure_id(self):
        assert validate_model_id("gpt-5.3") == "gpt-5.3"

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="empty"):
            validate_model_id("")

    def test_rejects_too_long_id(self):
        with pytest.raises(ValueError, match="200"):
            validate_model_id("a" * 201)

    def test_rejects_invalid_characters(self):
        with pytest.raises(ValueError, match="invalid"):
            validate_model_id("model with spaces")


# ---------------------------------------------------------------------------
# CustomModelEntry schema
# ---------------------------------------------------------------------------

class TestCustomModelEntrySchema:
    def test_minimal_entry(self):
        entry = CustomModelEntry(id="my-model")
        assert entry.id == "my-model"
        assert entry.display_name is None

    def test_azure_entry_with_endpoint(self):
        entry = CustomModelEntry(
            id="gpt-5.3",
            endpoint="https://myresource.openai.azure.com",
            api_version="2024-12-01-preview",
        )
        assert entry.endpoint == "https://myresource.openai.azure.com"
        assert entry.api_version == "2024-12-01-preview"


# ---------------------------------------------------------------------------
# get_available_providers() — custom_models merge
# ---------------------------------------------------------------------------

class TestGetAvailableProvidersCustomModelsMerge:
    @pytest.fixture()
    def mock_settings(self):
        with patch("app.services.user_settings_service.settings") as mock:
            mock.GOOGLE_API_KEY = "key"
            mock.CEREBRAS_API_KEY = "key"
            mock.OPENROUTER_API_KEY = "key"
            mock.AZURE_OPENAI_API_KEY = "key"
            yield mock

    def test_empty_registry_backward_compat(self, service, mock_settings):
        providers = service.get_available_providers(custom_models=None)
        openrouter = next(p for p in providers if p.name == "openrouter")
        assert all(not getattr(o, "is_custom", False) for o in openrouter.model_options)

    def test_custom_models_appended_with_is_custom_flag(self, service, mock_settings):
        registry = {
            "openrouter": [{"id": "my/custom-model:free", "display_name": "My Custom"}],
        }
        providers = service.get_available_providers(custom_models=registry)
        openrouter = next(p for p in providers if p.name == "openrouter")
        custom_opts = [o for o in openrouter.model_options if o.is_custom]
        assert len(custom_opts) == 1
        assert custom_opts[0].id == "my/custom-model:free"
        assert custom_opts[0].display_name == "My Custom"

    def test_curated_wins_on_collision(self, service, mock_settings):
        """When custom model ID collides with curated list, curated entry wins (no duplicate)."""
        curated_id = service.PROVIDER_CONFIGS["openrouter"]["models"][0]
        registry = {"openrouter": [{"id": curated_id}]}
        providers = service.get_available_providers(custom_models=registry)
        openrouter = next(p for p in providers if p.name == "openrouter")
        ids = [o.id for o in openrouter.model_options]
        assert ids.count(curated_id) == 1
        curated_opt = next(o for o in openrouter.model_options if o.id == curated_id)
        assert curated_opt.is_custom is False

    def test_custom_model_in_flat_models_list(self, service, mock_settings):
        registry = {"azure": [{"id": "my-azure-deploy"}]}
        providers = service.get_available_providers(custom_models=registry)
        azure = next(p for p in providers if p.name == "azure")
        assert "my-azure-deploy" in azure.models


# ---------------------------------------------------------------------------
# Registry CRUD helpers
# ---------------------------------------------------------------------------

class TestRegistryCrudHelpers:
    def test_add_custom_model_appends_to_provider(self, service):
        registry = {}
        updated = service.add_custom_model(
            registry, "openrouter", CustomModelEntry(id="new/model:free")
        )
        assert len(updated["openrouter"]) == 1
        assert updated["openrouter"][0]["id"] == "new/model:free"

    def test_add_custom_model_dedupes_by_id(self, service):
        registry = {"openrouter": [{"id": "existing/model:free"}]}
        updated = service.add_custom_model(
            registry, "openrouter", CustomModelEntry(id="existing/model:free")
        )
        assert len(updated["openrouter"]) == 1

    def test_remove_custom_model(self, service):
        registry = {
            "openrouter": [
                {"id": "keep/model:free"},
                {"id": "remove/me:free"},
            ]
        }
        updated = service.remove_custom_model(registry, "openrouter", "remove/me:free")
        ids = [e["id"] for e in updated["openrouter"]]
        assert "remove/me:free" not in ids
        assert "keep/model:free" in ids

    def test_remove_nonexistent_is_noop(self, service):
        registry = {"openrouter": [{"id": "a/model:free"}]}
        updated = service.remove_custom_model(registry, "openrouter", "missing")
        assert updated == registry

    def test_parse_custom_models_from_db_none(self, service):
        assert service.parse_custom_models(None) == {}

    def test_parse_custom_models_from_db_json_string(self, service):
        raw = json.dumps({"azure": [{"id": "gpt-5.3"}]})
        result = service.parse_custom_models(raw)
        assert result["azure"][0]["id"] == "gpt-5.3"
