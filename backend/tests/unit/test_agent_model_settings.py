"""
Unit tests for Sprint 10.6 Phase 1: Per-Agent Model Provider & Model Selection
— Database & Backend Schema

TDD RED phase: these tests define expected behaviour BEFORE implementation.

Covers:
- UserSettingBase / UserSettingUpdate / UserSettingInDB have 8 new optional fields
- get_agent_config(db, user_id, agent_name) falls back to Azure default when no override
- get_agent_config returns override when set
- unknown provider name raises ValueError
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.user_settings_service import UserSettingsService


AGENT_NAMES = ["observation", "requirements", "analysis", "evolution"]
AGENT_PROVIDER_FIELDS = [f"{a}_provider" for a in AGENT_NAMES]
AGENT_MODEL_FIELDS = [f"{a}_model" for a in AGENT_NAMES]
ALL_AGENT_FIELDS = AGENT_PROVIDER_FIELDS + AGENT_MODEL_FIELDS

DEFAULT_PROVIDER = "azure"
DEFAULT_MODEL = "ChatGPT-UAT"


@pytest.fixture()
def service() -> UserSettingsService:
    return UserSettingsService()


# ---------------------------------------------------------------------------
# Pydantic schema field tests
# ---------------------------------------------------------------------------

class TestAgentFieldsInSchemas:
    """All 8 per-agent fields must appear in the relevant Pydantic schemas
    as Optional[str] (i.e. they can be None / omitted)."""

    def test_user_setting_base_has_all_agent_fields(self):
        from app.schemas.user_settings import UserSettingBase
        fields = (
            UserSettingBase.model_fields
            if hasattr(UserSettingBase, "model_fields")
            else UserSettingBase.__fields__
        )
        for field in ALL_AGENT_FIELDS:
            assert field in fields, f"UserSettingBase missing field: {field!r}"

    def test_user_setting_update_has_all_agent_fields(self):
        from app.schemas.user_settings import UserSettingUpdate
        fields = (
            UserSettingUpdate.model_fields
            if hasattr(UserSettingUpdate, "model_fields")
            else UserSettingUpdate.__fields__
        )
        for field in ALL_AGENT_FIELDS:
            assert field in fields, f"UserSettingUpdate missing field: {field!r}"

    def test_user_setting_in_db_has_all_agent_fields(self):
        from app.schemas.user_settings import UserSettingInDB
        fields = (
            UserSettingInDB.model_fields
            if hasattr(UserSettingInDB, "model_fields")
            else UserSettingInDB.__fields__
        )
        for field in ALL_AGENT_FIELDS:
            assert field in fields, f"UserSettingInDB missing field: {field!r}"

    def test_agent_provider_fields_are_optional_in_base(self):
        """Agent provider/model fields in UserSettingBase must be Optional (default None)."""
        from app.schemas.user_settings import UserSettingBase
        # Construct with only the required non-agent fields; agent fields must default to None
        instance = UserSettingBase(
            generation_provider="google",
            generation_model="gemini-2.0-flash",
            execution_provider="google",
            execution_model="gemini-2.0-flash",
        )
        for field in ALL_AGENT_FIELDS:
            assert getattr(instance, field) is None, (
                f"UserSettingBase.{field} should default to None, got {getattr(instance, field)!r}"
            )

    def test_agent_provider_fields_are_optional_in_update(self):
        """Empty UserSettingUpdate must not raise; all agent fields default None."""
        from app.schemas.user_settings import UserSettingUpdate
        instance = UserSettingUpdate()
        for field in ALL_AGENT_FIELDS:
            assert getattr(instance, field) is None, (
                f"UserSettingUpdate.{field} should default to None"
            )

    def test_agent_provider_accepts_valid_value_in_update(self):
        """Setting a valid provider in UserSettingUpdate must not raise."""
        from app.schemas.user_settings import UserSettingUpdate
        instance = UserSettingUpdate(observation_provider="google", observation_model="gemini-2.0-flash")
        assert instance.observation_provider == "google"
        assert instance.observation_model == "gemini-2.0-flash"

    def test_agent_provider_rejects_invalid_value_in_update(self):
        """Setting an unknown provider in UserSettingUpdate must raise ValueError."""
        from app.schemas.user_settings import UserSettingUpdate
        with pytest.raises(Exception):
            UserSettingUpdate(observation_provider="unknown-provider-xyz")


# ---------------------------------------------------------------------------
# get_agent_config() — fallback behaviour
# ---------------------------------------------------------------------------

class TestGetAgentConfigFallback:
    """When no per-agent override is stored, get_agent_config must return
    Azure defaults ("azure", "ChatGPT-UAT")."""

    def _make_db_with_settings(self, **kwargs):
        """Build a mock DB session returning a UserSetting-like object."""
        mock_settings = MagicMock()
        # default all agent fields to None
        for field in ALL_AGENT_FIELDS:
            setattr(mock_settings, field, None)
        # override any provided kwargs
        for k, v in kwargs.items():
            setattr(mock_settings, k, v)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
        return mock_db

    def test_no_override_returns_azure_provider(self, service: UserSettingsService):
        db = self._make_db_with_settings()
        result = service.get_agent_config(db, user_id=1, agent_name="observation")
        assert result["provider"] == DEFAULT_PROVIDER

    def test_no_override_returns_azure_model(self, service: UserSettingsService):
        db = self._make_db_with_settings()
        result = service.get_agent_config(db, user_id=1, agent_name="observation")
        assert result["model"] == DEFAULT_MODEL

    def test_fallback_applies_to_all_agent_names(self, service: UserSettingsService):
        for agent in AGENT_NAMES:
            db = self._make_db_with_settings()
            result = service.get_agent_config(db, user_id=1, agent_name=agent)
            assert result["provider"] == DEFAULT_PROVIDER, f"Agent {agent!r} failed"
            assert result["model"] == DEFAULT_MODEL, f"Agent {agent!r} failed"

    def test_no_user_settings_row_returns_azure_default(self, service: UserSettingsService):
        """When the user has no settings row at all, still return Azure default."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.get_agent_config(mock_db, user_id=99, agent_name="analysis")
        assert result["provider"] == DEFAULT_PROVIDER
        assert result["model"] == DEFAULT_MODEL

    def test_none_db_returns_azure_default(self, service: UserSettingsService):
        """get_agent_config with db=None must return Azure default (background task safe)."""
        result = service.get_agent_config(None, user_id=1, agent_name="evolution")
        assert result["provider"] == DEFAULT_PROVIDER
        assert result["model"] == DEFAULT_MODEL


# ---------------------------------------------------------------------------
# get_agent_config() — override behaviour
# ---------------------------------------------------------------------------

class TestGetAgentConfigOverride:
    """When a per-agent override is stored, get_agent_config must return it."""

    def _make_db_with_override(self, agent: str, provider: str, model: str):
        mock_settings = MagicMock()
        for field in ALL_AGENT_FIELDS:
            setattr(mock_settings, field, None)
        setattr(mock_settings, f"{agent}_provider", provider)
        setattr(mock_settings, f"{agent}_model", model)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
        return mock_db

    def test_override_provider_is_returned(self, service: UserSettingsService):
        db = self._make_db_with_override("observation", "google", "gemini-2.0-flash")
        result = service.get_agent_config(db, user_id=1, agent_name="observation")
        assert result["provider"] == "google"

    def test_override_model_is_returned(self, service: UserSettingsService):
        db = self._make_db_with_override("observation", "google", "gemini-2.0-flash")
        result = service.get_agent_config(db, user_id=1, agent_name="observation")
        assert result["model"] == "gemini-2.0-flash"

    def test_override_for_requirements_agent(self, service: UserSettingsService):
        db = self._make_db_with_override("requirements", "cerebras", "llama3.3-70b")
        result = service.get_agent_config(db, user_id=1, agent_name="requirements")
        assert result["provider"] == "cerebras"
        assert result["model"] == "llama3.3-70b"

    def test_override_for_analysis_agent(self, service: UserSettingsService):
        db = self._make_db_with_override("analysis", "openrouter", "qwen/qwen3-coder-480b-a35b:free")
        result = service.get_agent_config(db, user_id=1, agent_name="analysis")
        assert result["provider"] == "openrouter"
        assert result["model"] == "qwen/qwen3-coder-480b-a35b:free"

    def test_override_for_evolution_agent(self, service: UserSettingsService):
        db = self._make_db_with_override("evolution", "azure", "ChatGPT-UAT")
        result = service.get_agent_config(db, user_id=1, agent_name="evolution")
        assert result["provider"] == "azure"
        assert result["model"] == "ChatGPT-UAT"

    def test_override_agent_does_not_affect_other_agents(self, service: UserSettingsService):
        """Override on observation must not leak into requirements."""
        mock_settings = MagicMock()
        for field in ALL_AGENT_FIELDS:
            setattr(mock_settings, field, None)
        mock_settings.observation_provider = "google"
        mock_settings.observation_model = "gemini-2.0-flash"
        # requirements stays None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings

        req_result = service.get_agent_config(mock_db, user_id=1, agent_name="requirements")
        assert req_result["provider"] == DEFAULT_PROVIDER
        assert req_result["model"] == DEFAULT_MODEL

    def test_provider_only_override_without_model_falls_back_model(self, service: UserSettingsService):
        """If only provider is set but model is None, model must fall back to default for that provider."""
        mock_settings = MagicMock()
        for field in ALL_AGENT_FIELDS:
            setattr(mock_settings, field, None)
        mock_settings.observation_provider = "google"
        mock_settings.observation_model = None  # model not set

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings

        result = service.get_agent_config(mock_db, user_id=1, agent_name="observation")
        # provider override applied, model falls back to recommended for google
        assert result["provider"] == "google"
        assert result["model"] is not None


# ---------------------------------------------------------------------------
# get_agent_config() — unknown agent name
# ---------------------------------------------------------------------------

class TestGetAgentConfigUnknownAgent:
    """Passing an unrecognised agent_name must raise ValueError."""

    def test_unknown_agent_name_raises(self, service: UserSettingsService):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="Unknown agent"):
            service.get_agent_config(mock_db, user_id=1, agent_name="flying-unicorn")

    def test_empty_agent_name_raises(self, service: UserSettingsService):
        mock_db = MagicMock()
        with pytest.raises(ValueError):
            service.get_agent_config(mock_db, user_id=1, agent_name="")


# ---------------------------------------------------------------------------
# validate_provider validator in UserSettingUpdate
# ---------------------------------------------------------------------------

class TestAgentProviderValidation:
    """The validate_provider validator must also reject invalid values for
    the per-agent provider fields."""

    @pytest.mark.parametrize("field", AGENT_PROVIDER_FIELDS)
    def test_valid_providers_accepted(self, field: str):
        from app.schemas.user_settings import UserSettingUpdate
        for provider in ("google", "cerebras", "openrouter", "azure"):
            instance = UserSettingUpdate(**{field: provider})
            assert getattr(instance, field) == provider

    @pytest.mark.parametrize("field", AGENT_PROVIDER_FIELDS)
    def test_invalid_provider_rejected(self, field: str):
        from app.schemas.user_settings import UserSettingUpdate
        with pytest.raises(Exception):
            UserSettingUpdate(**{field: "gpt-evil-provider"})

    @pytest.mark.parametrize("field", AGENT_PROVIDER_FIELDS)
    def test_none_is_accepted(self, field: str):
        from app.schemas.user_settings import UserSettingUpdate
        instance = UserSettingUpdate(**{field: None})
        assert getattr(instance, field) is None
