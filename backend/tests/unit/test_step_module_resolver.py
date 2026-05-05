"""
Unit tests for step_module_resolver — Sprint 10.11.

TDD RED phase: validates @module: reference parsing, parameter substitution,
missing module errors, and nested step expansion.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helper: build mock DB session
# ---------------------------------------------------------------------------

def _make_db_with_modules(modules: dict):
    """
    Return a mock SQLAlchemy Session that returns StepLibraryModule-like objects
    when queried by name.
    modules: {name: {"steps": [...], "parameters": [...]}}
    """
    from types import SimpleNamespace

    db_mock = MagicMock()

    def _filter_side_effect(*args, **kwargs):
        query_mock = MagicMock()
        # Store which name was queried via filter args
        query_mock._modules = modules
        query_mock._filter_args = args

        def _first():
            # Inspect the filter for a match
            for arg in args:
                # SQLAlchemy BinaryExpression — check right side (the value)
                try:
                    val = arg.right.value
                    if val in modules:
                        mod_data = modules[val]
                        return SimpleNamespace(
                            name=val,
                            steps=mod_data.get("steps", []),
                            parameters=mod_data.get("parameters", []),
                        )
                except AttributeError:
                    pass
            return None

        query_mock.first = _first
        return query_mock

    db_mock.query.return_value.filter.side_effect = _filter_side_effect
    return db_mock


# ---------------------------------------------------------------------------
# Basic resolution
# ---------------------------------------------------------------------------

class TestResolveStepsNoModules:
    """Steps without @module: references pass through unchanged."""

    def test_plain_steps_unchanged(self):
        from app.services.step_module_resolver import resolve_steps
        db = MagicMock()
        steps = ["Navigate to https://example.com", "Click Login button"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result == steps

    def test_empty_steps_returns_empty(self):
        from app.services.step_module_resolver import resolve_steps
        db = MagicMock()
        result = resolve_steps([], db=db, user_id=1)
        assert result == []

    def test_dict_steps_pass_through(self):
        from app.services.step_module_resolver import resolve_steps
        db = MagicMock()
        steps = [{"action": "navigate", "value": "https://example.com"}]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result == steps


class TestModuleReferenceExpansion:
    """@module: references are expanded to concrete steps."""

    def test_module_ref_expands_to_steps(self):
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        mod = MagicMock(spec=StepLibraryModule)
        mod.steps = ["Navigate to https://login.com", "Click Login"]
        mod.parameters = []

        db.query.return_value.filter.return_value.first.return_value = mod

        steps = ["@module:login_flow()"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result == ["Navigate to https://login.com", "Click Login"]

    def test_module_ref_mixed_with_plain_steps(self):
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        mod = MagicMock(spec=StepLibraryModule)
        mod.steps = ["Step A", "Step B"]
        mod.parameters = []
        db.query.return_value.filter.return_value.first.return_value = mod

        steps = ["Before module", "@module:my_module()", "After module"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result == ["Before module", "Step A", "Step B", "After module"]


class TestParameterSubstitution:
    """Parameters in @module: refs are substituted into step text."""

    def test_single_param_substituted(self):
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        mod = MagicMock(spec=StepLibraryModule)
        mod.steps = ["Enter username: {username}"]
        mod.parameters = ["username"]
        db.query.return_value.filter.return_value.first.return_value = mod

        steps = ["@module:login_flow(username=admin@test.com)"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result == ["Enter username: admin@test.com"]

    def test_multiple_params_substituted(self):
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        mod = MagicMock(spec=StepLibraryModule)
        mod.steps = ["Enter username: {username}", "Enter password: {password}"]
        mod.parameters = ["username", "password"]
        db.query.return_value.filter.return_value.first.return_value = mod

        steps = ["@module:login_flow(username=admin,password=secret)"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result == ["Enter username: admin", "Enter password: secret"]

    def test_undeclared_param_placeholder_left_as_is(self):
        """If a step has {placeholder} with no matching param, leave it unchanged."""
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        mod = MagicMock(spec=StepLibraryModule)
        mod.steps = ["Enter username: {username}", "Click Submit"]
        mod.parameters = ["username"]
        db.query.return_value.filter.return_value.first.return_value = mod

        steps = ["@module:login_flow(username=alice)"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result[0] == "Enter username: alice"
        assert result[1] == "Click Submit"


class TestMissingModuleError:
    """Missing module references produce an error step — never crash execution."""

    def test_missing_module_produces_error_step(self):
        from app.services.step_module_resolver import resolve_steps

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        steps = ["@module:nonexistent_module()"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert len(result) == 1
        assert "error" in result[0].lower() or "not found" in result[0].lower()

    def test_missing_module_does_not_affect_other_steps(self):
        from app.services.step_module_resolver import resolve_steps
        from app.models.step_library_module import StepLibraryModule

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        steps = ["Valid step before", "@module:missing()", "Valid step after"]
        result = resolve_steps(steps, db=db, user_id=1)
        assert result[0] == "Valid step before"
        assert result[2] == "Valid step after"
        # Middle is an error step
        assert "error" in result[1].lower() or "not found" in result[1].lower()


# ---------------------------------------------------------------------------
# parse_module_ref utility
# ---------------------------------------------------------------------------

class TestParseModuleRef:
    """parse_module_ref correctly extracts module name and params."""

    def test_parse_no_params(self):
        from app.services.step_module_resolver import parse_module_ref
        name, params = parse_module_ref("@module:login_flow()")
        assert name == "login_flow"
        assert params == {}

    def test_parse_single_param(self):
        from app.services.step_module_resolver import parse_module_ref
        name, params = parse_module_ref("@module:login(username=admin)")
        assert name == "login"
        assert params == {"username": "admin"}

    def test_parse_multiple_params(self):
        from app.services.step_module_resolver import parse_module_ref
        name, params = parse_module_ref("@module:login(username=admin,password=pass123)")
        assert name == "login"
        assert params == {"username": "admin", "password": "pass123"}

    def test_parse_no_parens(self):
        """@module:name without () is also valid shorthand."""
        from app.services.step_module_resolver import parse_module_ref
        name, params = parse_module_ref("@module:login_flow")
        assert name == "login_flow"
        assert params == {}

    def test_non_module_ref_returns_none(self):
        from app.services.step_module_resolver import parse_module_ref
        result = parse_module_ref("Navigate to https://example.com")
        assert result is None


# ---------------------------------------------------------------------------
# is_module_ref utility
# ---------------------------------------------------------------------------

class TestIsModuleRef:
    """is_module_ref correctly identifies @module: references."""

    def test_module_ref_detected(self):
        from app.services.step_module_resolver import is_module_ref
        assert is_module_ref("@module:login_flow()") is True
        assert is_module_ref("@module:checkout(param=val)") is True
        assert is_module_ref("@module:my_module") is True

    def test_plain_step_not_detected(self):
        from app.services.step_module_resolver import is_module_ref
        assert is_module_ref("Click Login button") is False
        assert is_module_ref("") is False
        assert is_module_ref("module:login") is False  # missing @
