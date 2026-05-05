"""
Unit tests for StepLibraryModule ORM model and Pydantic schemas — Sprint 10.11.

TDD RED phase: validates model fields, schema validation, and name uniqueness constraints.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# ORM model field validation
# ---------------------------------------------------------------------------

class TestStepLibraryModuleModelFields:
    """Verify the SQLAlchemy model has the expected columns."""

    def test_model_has_expected_columns(self):
        from app.models.step_library_module import StepLibraryModule
        columns = {col.key for col in StepLibraryModule.__table__.columns}
        assert "id" in columns
        assert "user_id" in columns
        assert "name" in columns
        assert "display_name" in columns
        assert "description" in columns
        assert "steps" in columns
        assert "parameters" in columns
        assert "tags" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_tablename(self):
        from app.models.step_library_module import StepLibraryModule
        assert StepLibraryModule.__tablename__ == "step_library_modules"

    def test_user_id_is_foreign_key(self):
        from app.models.step_library_module import StepLibraryModule
        fks = {fk.target_fullname for fk in StepLibraryModule.__table__.foreign_keys}
        assert "users.id" in fks

    def test_name_not_nullable(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["name"]
        assert not col.nullable

    def test_name_has_unique_constraint(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["name"]
        assert col.unique

    def test_display_name_not_nullable(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["display_name"]
        assert not col.nullable

    def test_steps_not_nullable(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["steps"]
        assert not col.nullable

    def test_description_nullable(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["description"]
        assert col.nullable

    def test_parameters_nullable(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["parameters"]
        assert col.nullable

    def test_tags_nullable(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["tags"]
        assert col.nullable

    def test_name_has_index(self):
        from app.models.step_library_module import StepLibraryModule
        col = StepLibraryModule.__table__.columns["name"]
        assert col.index


# ---------------------------------------------------------------------------
# Pydantic schema validation
# ---------------------------------------------------------------------------

class TestStepLibraryModuleCreateSchema:
    """Validate StepLibraryModuleCreate schema."""

    def test_valid_minimal_create(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        schema = StepLibraryModuleCreate(
            name="login_three_hk",
            display_name="Three HK Login Flow",
            steps=["Navigate to https://three.com.hk", "Click Login"],
        )
        assert schema.name == "login_three_hk"
        assert len(schema.steps) == 2

    def test_name_too_short_raises(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        with pytest.raises(Exception):
            StepLibraryModuleCreate(
                name="",
                display_name="Some Display",
                steps=["step 1"],
            )

    def test_name_too_long_raises(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        with pytest.raises(Exception):
            StepLibraryModuleCreate(
                name="a" * 101,
                display_name="Some Display",
                steps=["step 1"],
            )

    def test_empty_steps_raises(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        with pytest.raises(Exception):
            StepLibraryModuleCreate(
                name="my_module",
                display_name="My Module",
                steps=[],
            )

    def test_with_parameters(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        schema = StepLibraryModuleCreate(
            name="login_flow",
            display_name="Login Flow",
            steps=["Enter username: {username}", "Enter password: {password}"],
            parameters=["username", "password"],
        )
        assert schema.parameters == ["username", "password"]

    def test_with_tags(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        schema = StepLibraryModuleCreate(
            name="checkout_flow",
            display_name="Checkout Flow",
            steps=["Click checkout"],
            tags=["e2e", "checkout"],
        )
        assert schema.tags == ["e2e", "checkout"]

    def test_with_description(self):
        from app.schemas.step_library_module import StepLibraryModuleCreate
        schema = StepLibraryModuleCreate(
            name="otp_flow",
            display_name="OTP Flow",
            steps=["Click OTP button"],
            description="Enter OTP steps for Two-factor auth",
        )
        assert schema.description == "Enter OTP steps for Two-factor auth"


class TestStepLibraryModuleUpdateSchema:
    """Validate StepLibraryModuleUpdate schema — all fields optional."""

    def test_empty_update_is_valid(self):
        from app.schemas.step_library_module import StepLibraryModuleUpdate
        schema = StepLibraryModuleUpdate()
        assert schema.name is None
        assert schema.steps is None

    def test_partial_update_only_display_name(self):
        from app.schemas.step_library_module import StepLibraryModuleUpdate
        schema = StepLibraryModuleUpdate(display_name="Updated Display")
        assert schema.display_name == "Updated Display"
        assert schema.steps is None

    def test_partial_update_only_steps(self):
        from app.schemas.step_library_module import StepLibraryModuleUpdate
        schema = StepLibraryModuleUpdate(steps=["new step 1", "new step 2"])
        assert len(schema.steps) == 2


class TestStepLibraryModuleResponseSchema:
    """Validate StepLibraryModuleResponse schema."""

    def test_response_schema_has_required_fields(self):
        from app.schemas.step_library_module import StepLibraryModuleResponse
        data = {
            "id": 1,
            "user_id": 42,
            "name": "login_three_hk",
            "display_name": "Three HK Login Flow",
            "steps": ["step 1", "step 2"],
            "parameters": None,
            "tags": None,
            "description": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        schema = StepLibraryModuleResponse(**data)
        assert schema.id == 1
        assert schema.name == "login_three_hk"

    def test_response_includes_usage_count_when_provided(self):
        from app.schemas.step_library_module import StepLibraryModuleResponse
        data = {
            "id": 1,
            "user_id": 42,
            "name": "login_flow",
            "display_name": "Login Flow",
            "steps": ["step 1"],
            "parameters": None,
            "tags": None,
            "description": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "usage_count": 7,
        }
        schema = StepLibraryModuleResponse(**data)
        assert schema.usage_count == 7
