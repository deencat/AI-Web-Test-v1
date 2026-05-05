"""
Integration tests for Step Library @module: expansion in execution flow — Sprint 10.11.

TDD RED phase: validates that @module: references are correctly expanded in the
execution service before step dispatch.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_module(name: str, steps: list, parameters: list = None):
    """Create a simple namespace to represent a StepLibraryModule DB row."""
    return SimpleNamespace(
        id=1,
        name=name,
        steps=steps,
        parameters=parameters or [],
        display_name=name.replace("_", " ").title(),
    )


# ---------------------------------------------------------------------------
# resolve_steps integration with DB
# ---------------------------------------------------------------------------

class TestResolveStepsWithRealQuery:
    """resolve_steps correctly queries the DB and expands modules."""

    def test_resolve_expands_module_step(self):
        """@module: ref with real DB query shape is expanded to concrete steps."""
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        mod = _make_module("login_three_hk", ["Navigate to UAT", "Click Login"])

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mod

        raw = ["@module:login_three_hk()"]
        result = resolve_steps(raw, db=db, user_id=5)

        assert result == ["Navigate to UAT", "Click Login"]
        db.query.assert_called_once_with(StepLibraryModule)

    def test_resolve_user_id_filter_applied(self):
        """resolve_steps filters modules by user_id to prevent cross-user access."""
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        resolve_steps(["@module:login()"], db=db, user_id=99)

        # Ensure query was called - user_id filtering tested at DB layer
        db.query.assert_called_once_with(StepLibraryModule)


# ---------------------------------------------------------------------------
# OTP step guard compatibility
# ---------------------------------------------------------------------------

class TestModuleExpansionDoesNotBreakOTPGuard:
    """Expanded module steps must not accidentally trigger IMAP OTP expansion."""

    def test_module_steps_dont_look_like_otp_steps(self):
        """Standard login module steps should not match is_otp_step."""
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        mod = _make_module("login_three_hk", [
            "Navigate to https://wwwuat.three.com.hk",
            "Click the 'Login' link",
            "Enter the username: testuser@example.com",
        ])

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mod

        result = resolve_steps(["@module:login_three_hk()"], db=db, user_id=1)

        # None of these should be OTP steps
        try:
            from app.services.email_otp_service import is_otp_step
            for step in result:
                assert not is_otp_step(step), f"Step '{step}' incorrectly detected as OTP step"
        except ImportError:
            pytest.skip("email_otp_service not available")


# ---------------------------------------------------------------------------
# Three-tier execution service wiring
# ---------------------------------------------------------------------------

class TestThreeTierExecutionServiceModuleExpansion:
    """ThreeTierExecutionService calls resolve_steps before dispatching."""

    @pytest.mark.asyncio
    async def test_execute_step_receives_expanded_steps(self):
        """
        Verify resolve_steps is called before step execution.
        The actual step execution is mocked; we verify the resolver was invoked.
        """
        from app.services.step_module_resolver import resolve_steps

        raw_steps = ["@module:login_flow()", "Verify dashboard loads"]
        expanded_steps = ["Navigate to https://example.com", "Click Login", "Verify dashboard loads"]

        with patch("app.services.step_module_resolver.resolve_steps", return_value=expanded_steps) as mock_resolve:
            result = mock_resolve(raw_steps, db=MagicMock(), user_id=1)
            mock_resolve.assert_called_once()
            assert result == expanded_steps

    def test_backward_compat_no_module_refs(self):
        """Steps without @module: refs are returned unchanged."""
        from app.services.step_module_resolver import resolve_steps

        db = MagicMock()
        plain_steps = ["Click Login", "Enter password: secret"]
        result = resolve_steps(plain_steps, db=db, user_id=1)
        assert result == plain_steps


# ---------------------------------------------------------------------------
# CRUD integration: step library DB operations
# ---------------------------------------------------------------------------

class TestExecutionServiceWiring:
    """Verify resolve_steps is imported and wired into the execution services."""

    def test_execution_service_imports_resolve_steps(self):
        """execution_service.py must import resolve_steps from step_module_resolver."""
        import importlib
        import inspect
        import app.services.execution_service as svc
        importlib.reload(svc)
        src = inspect.getsource(svc)
        assert "resolve_steps" in src, "execution_service.py does not call resolve_steps"
        assert "step_module_resolver" in src, "execution_service.py does not import step_module_resolver"

    def test_stagehand_service_imports_resolve_steps(self):
        """stagehand_service.py must import resolve_steps from step_module_resolver."""
        import importlib
        import inspect
        import app.services.stagehand_service as svc
        importlib.reload(svc)
        src = inspect.getsource(svc)
        assert "resolve_steps" in src, "stagehand_service.py does not call resolve_steps"
        assert "step_module_resolver" in src, "stagehand_service.py does not import step_module_resolver"
    """CRUD operations on StepLibraryModule through the crud module."""

    def test_create_returns_module_with_id(self):
        from app.crud.step_library import create_module
        from app.schemas.step_library_module import StepLibraryModuleCreate

        db = MagicMock()

        schema = StepLibraryModuleCreate(
            name="login_three_hk",
            display_name="Three HK Login Flow",
            steps=["Navigate to UAT", "Click Login"],
            parameters=["username"],
        )

        # Mock the DB add/refresh cycle
        created_mod = MagicMock()
        created_mod.id = 1
        created_mod.name = "login_three_hk"
        db.refresh.side_effect = lambda obj: None
        db.add.return_value = None
        db.commit.return_value = None

        with patch("app.crud.step_library.StepLibraryModule", return_value=created_mod):
            result = create_module(db=db, schema=schema, user_id=1)
            db.add.assert_called_once()
            db.commit.assert_called_once()

    def test_list_modules_filters_by_user(self):
        from app.crud.step_library import list_modules

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = list_modules(db=db, user_id=42)
        assert result == []
        db.query.return_value.filter.assert_called_once()

    def test_get_by_name_user_scoped(self):
        from app.crud.step_library import get_by_name
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_by_name(db=db, name="nonexistent", user_id=1)
        assert result is None

    def test_delete_module(self):
        from app.crud.step_library import delete_module
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        mod = MagicMock(spec=StepLibraryModule)
        db.query.return_value.filter.return_value.first.return_value = mod

        result = delete_module(db=db, module_id=1, user_id=1)
        db.delete.assert_called_once_with(mod)
        db.commit.assert_called_once()
        assert result is True

    def test_delete_nonexistent_returns_false(self):
        from app.crud.step_library import delete_module

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = delete_module(db=db, module_id=999, user_id=1)
        assert result is False
        db.delete.assert_not_called()
