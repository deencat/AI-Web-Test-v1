"""
Unit tests for POST /api/v1/tests/{id}/clone — Clone Test Case feature.

Covers happy path, 404, 403, title collision, field parity, and custom new_title.
"""
import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.api import deps
from app.api.v1.endpoints import tests as tests_module
from app.crud import test_case as test_crud
from app.crud import test_category as category_crud
from app.db.base import Base
from app.models.test_case import TestCase, TestType, Priority, TestStatus, ReadinessStatus
from app.models.user import User
from app.schemas.test_category import TestCategoryCreate


# ---------------------------------------------------------------------------
# DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """In-memory SQLite database with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_a(db: Session) -> User:
    user = User(
        email="usera@example.com",
        username="usera",
        hashed_password="hash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_b(db: Session) -> User:
    user = User(
        email="userb@example.com",
        username="userb",
        hashed_password="hash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def tests_app(db: Session) -> FastAPI:
    app = FastAPI()
    app.include_router(tests_module.router, prefix="/tests")
    app.dependency_overrides[deps.get_db] = lambda: db
    return app


def _mock_user(user_id: int = 1, role: str = "user") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = role
    return user


def _make_full_test_case(
    db: Session,
    user_id: int,
    title: str = "Original Test",
    status: TestStatus = TestStatus.PASSED,
    test_category_id: int | None = None,
) -> TestCase:
    """Create a test case with rich field data for parity checks."""
    tc = TestCase(
        title=title,
        description="Full description",
        test_type=TestType.E2E,
        priority=Priority.HIGH,
        status=status,
        readiness_status=ReadinessStatus.READY_TO_TEST,
        steps=[{"action": "click", "selector": "#submit"}],
        expected_result="Success",
        preconditions="User logged in",
        test_data={"username": "alice"},
        category_id=None,
        test_category_id=test_category_id,
        tags=["smoke", "regression"],
        test_metadata={"source": "manual"},
        requires_runtime_credentials=True,
        scenario_id=None,
        template_id=None,
        user_id=user_id,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------

class TestCloneCRUD:
    def test_clone_creates_new_row_with_pending_status(self, db: Session, user_a: User):
        original = _make_full_test_case(db, user_a.id)
        cloned = test_crud.clone_test_case(
            db,
            original,
            user_id=user_a.id,
            new_title="Original Test (Copy)",
        )
        assert cloned.id != original.id
        assert cloned.user_id == user_a.id
        assert cloned.status == TestStatus.PENDING
        assert cloned.title == "Original Test (Copy)"

    def test_generate_clone_title_suffix(self, db: Session, user_a: User):
        _make_full_test_case(db, user_a.id, title="My Test")
        title = test_crud._generate_clone_title(db, user_a.id, "My Test")
        assert title == "My Test (Copy)"

        test_crud.clone_test_case(
            db,
            _make_full_test_case(db, user_a.id, title="My Test"),
            user_id=user_a.id,
            new_title="My Test (Copy)",
        )
        title2 = test_crud._generate_clone_title(db, user_a.id, "My Test")
        assert title2 == "My Test (Copy 2)"

    def test_field_parity_deep_copy(self, db: Session, user_a: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Billing", color="#FF0000"),
            user_id=user_a.id,
        )
        original = _make_full_test_case(db, user_a.id, test_category_id=category.id)
        cloned = test_crud.clone_test_case(
            db,
            original,
            user_id=user_a.id,
            new_title="Cloned",
        )

        assert cloned.description == original.description
        assert cloned.test_type == original.test_type
        assert cloned.priority == original.priority
        assert cloned.steps == original.steps
        assert cloned.steps is not original.steps
        assert cloned.expected_result == original.expected_result
        assert cloned.preconditions == original.preconditions
        assert cloned.test_data == original.test_data
        assert cloned.test_data is not original.test_data
        assert cloned.category_id == original.category_id
        assert cloned.test_category_id == original.test_category_id
        assert cloned.tags == original.tags
        assert cloned.tags is not original.tags
        assert cloned.test_metadata == original.test_metadata
        assert cloned.requires_runtime_credentials == original.requires_runtime_credentials
        assert cloned.scenario_id == original.scenario_id
        assert cloned.template_id == original.template_id
        assert cloned.readiness_status == original.readiness_status

        # Mutating clone must not affect source JSON fields
        cloned.steps.append({"action": "extra"})
        assert len(original.steps) == 1

    def test_source_unchanged_after_clone(self, db: Session, user_a: User):
        original = _make_full_test_case(db, user_a.id, status=TestStatus.PASSED)
        original_snapshot = {
            "id": original.id,
            "title": original.title,
            "status": original.status,
            "steps": copy.deepcopy(original.steps),
        }
        test_crud.clone_test_case(
            db,
            original,
            user_id=user_a.id,
            new_title="Original Test (Copy)",
        )
        db.refresh(original)
        assert original.id == original_snapshot["id"]
        assert original.title == original_snapshot["title"]
        assert original.status == original_snapshot["status"]
        assert original.steps == original_snapshot["steps"]

    def test_title_exists_for_user(self, db: Session, user_a: User):
        assert test_crud.title_exists_for_user(db, user_a.id, "Missing Title") is False
        _make_full_test_case(db, user_a.id, title="Taken Title")
        assert test_crud.title_exists_for_user(db, user_a.id, "Taken Title") is True

    def test_generate_clone_title_copy_3(self, db: Session, user_a: User):
        base = "Triple Test"
        _make_full_test_case(db, user_a.id, title=f"{base} (Copy)")
        _make_full_test_case(db, user_a.id, title=f"{base} (Copy 2)")
        title = test_crud._generate_clone_title(db, user_a.id, base)
        assert title == f"{base} (Copy 3)"

    def test_clone_with_null_optional_fields(self, db: Session, user_a: User):
        original = _make_full_test_case(db, user_a.id, title="Sparse Source")
        original.steps = None
        original.test_data = None
        original.tags = None
        original.test_metadata = None

        cloned = test_crud.clone_test_case(
            db,
            original,
            user_id=user_a.id,
            new_title="Sparse Source (Copy)",
        )
        assert cloned.steps == []
        assert cloned.test_data is None
        assert cloned.tags is None
        assert cloned.test_metadata is None


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestCloneEndpoint:
    def test_happy_path_returns_201(self, tests_app: FastAPI, db: Session, user_a: User):
        original = _make_full_test_case(db, user_a.id)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)

        client = TestClient(tests_app)
        resp = client.post(f"/tests/{original.id}/clone")
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] != original.id
        assert data["title"] == "Original Test (Copy)"
        assert data["status"] == "pending"
        assert data["steps"] == original.steps

        tests_app.dependency_overrides.clear()

    def test_not_found_returns_404(self, tests_app: FastAPI, user_a: User):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)
        resp = client.post("/tests/99999/clone")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Test case not found"
        tests_app.dependency_overrides.clear()

    def test_wrong_user_returns_403(self, tests_app: FastAPI, db: Session, user_a: User, user_b: User):
        original = _make_full_test_case(db, user_a.id)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_b.id)

        client = TestClient(tests_app)
        resp = client.post(f"/tests/{original.id}/clone")
        assert resp.status_code == 403
        assert "permission" in resp.json()["detail"].lower()
        tests_app.dependency_overrides.clear()

    def test_custom_new_title(self, tests_app: FastAPI, db: Session, user_a: User):
        original = _make_full_test_case(db, user_a.id)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)

        client = TestClient(tests_app)
        resp = client.post(
            f"/tests/{original.id}/clone",
            json={"new_title": "Custom Clone Name"},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Custom Clone Name"
        tests_app.dependency_overrides.clear()

    def test_duplicate_new_title_returns_409(self, tests_app: FastAPI, db: Session, user_a: User):
        _make_full_test_case(db, user_a.id, title="Existing Title")
        original = _make_full_test_case(db, user_a.id, title="Source Test")
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)

        client = TestClient(tests_app)
        resp = client.post(
            f"/tests/{original.id}/clone",
            json={"new_title": "Existing Title"},
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "A test case with this title already exists"
        tests_app.dependency_overrides.clear()

    def test_auto_title_collision_increments_copy_number(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        original = _make_full_test_case(db, user_a.id, title="Repeat Test")
        test_crud.clone_test_case(
            db,
            original,
            user_id=user_a.id,
            new_title="Repeat Test (Copy)",
        )
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)

        client = TestClient(tests_app)
        resp = client.post(f"/tests/{original.id}/clone")
        assert resp.status_code == 201
        assert resp.json()["title"] == "Repeat Test (Copy 2)"
        tests_app.dependency_overrides.clear()

    def test_admin_can_clone_other_users_test(
        self, tests_app: FastAPI, db: Session, user_a: User, user_b: User
    ):
        original = _make_full_test_case(db, user_a.id)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(
            user_b.id, role="admin"
        )

        client = TestClient(tests_app)
        resp = client.post(f"/tests/{original.id}/clone")
        assert resp.status_code == 201
        assert resp.json()["title"] == "Original Test (Copy)"
        tests_app.dependency_overrides.clear()
