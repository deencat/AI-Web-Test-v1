"""
Unit/API tests for Feature 3: requires_runtime_credentials sanitizer round-trip.

Ensures sanitize_test_case_for_response includes the flag so GET/PUT/list/clone
responses do not collapse True to the Pydantic default False.
"""
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.api import deps
from app.api.v1.endpoints import tests as tests_module
from app.api.v1.endpoints.tests import sanitize_test_case_for_response
from app.db.base import Base
from app.models.test_case import TestCase, TestType, Priority, TestStatus
from app.models.user import User
from app.schemas.test_case import TestCaseUpdate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
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


def _make_test_case(
    db: Session,
    user_id: int,
    *,
    title: str = "CRM Flag Test",
    requires_runtime_credentials: bool = False,
) -> TestCase:
    tc = TestCase(
        title=title,
        description="Desc",
        test_type=TestType.E2E,
        priority=Priority.MEDIUM,
        status=TestStatus.PENDING,
        steps=["Navigate to page"],
        expected_result="OK",
        preconditions=None,
        test_data=None,
        tags=["crm"],
        test_metadata=None,
        requires_runtime_credentials=requires_runtime_credentials,
        user_id=user_id,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def _minimal_orm(
    *,
    requires_runtime_credentials: bool,
) -> MagicMock:
    """Lightweight ORM-like object for direct sanitizer unit tests."""
    tc = MagicMock()
    tc.id = 1
    tc.title = "Sanitize Unit"
    tc.description = "Has description"
    tc.test_type = TestType.E2E
    tc.priority = Priority.MEDIUM
    tc.status = TestStatus.PENDING
    tc.steps = ["step"]
    tc.expected_result = "done"
    tc.preconditions = None
    tc.test_data = None
    tc.category_id = None
    tc.test_category_id = None
    tc.tags = None
    tc.test_metadata = None
    tc.created_at = datetime.utcnow()
    tc.updated_at = datetime.utcnow()
    tc.user_id = 1
    tc.scenario_id = None
    tc.template_id = None
    tc.test_category = None
    tc.requires_runtime_credentials = requires_runtime_credentials
    return tc


# ---------------------------------------------------------------------------
# Direct sanitizer unit tests
# ---------------------------------------------------------------------------

class TestSanitizeIncludesRequiresRuntimeCredentials:
    def test_sanitize_includes_requires_runtime_credentials_true(self):
        response = sanitize_test_case_for_response(
            _minimal_orm(requires_runtime_credentials=True)
        )
        assert response.requires_runtime_credentials is True

    def test_sanitize_includes_requires_runtime_credentials_false(self):
        response = sanitize_test_case_for_response(
            _minimal_orm(requires_runtime_credentials=False)
        )
        assert response.requires_runtime_credentials is False

    def test_sanitize_response_has_no_credential_fields(self):
        response = sanitize_test_case_for_response(
            _minimal_orm(requires_runtime_credentials=True)
        )
        payload = response.model_dump()
        assert "login_credentials" not in payload
        assert "password" not in payload
        assert "username" not in payload or payload.get("username") is None


# ---------------------------------------------------------------------------
# API round-trip tests (PUT → GET / list / clone via sanitizer)
# ---------------------------------------------------------------------------

class TestRequiresRuntimeCredentialsApiRoundTrip:
    def test_update_then_get_preserves_true(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(db, user_a.id, requires_runtime_credentials=False)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        put_resp = client.put(
            f"/tests/{tc.id}",
            json={"requires_runtime_credentials": True},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["requires_runtime_credentials"] is True

        get_resp = client.get(f"/tests/{tc.id}")
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["requires_runtime_credentials"] is True
        assert "login_credentials" not in body
        assert "password" not in body

        tests_app.dependency_overrides.clear()

    def test_update_then_get_preserves_false(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(db, user_a.id, requires_runtime_credentials=True)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        put_resp = client.put(
            f"/tests/{tc.id}",
            json={"requires_runtime_credentials": False},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["requires_runtime_credentials"] is False

        get_resp = client.get(f"/tests/{tc.id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["requires_runtime_credentials"] is False

        tests_app.dependency_overrides.clear()

    def test_list_includes_flag(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(
            db, user_a.id, title="List Flag True", requires_runtime_credentials=True
        )
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        list_resp = client.get("/tests")
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        match = next(item for item in items if item["id"] == tc.id)
        assert match["requires_runtime_credentials"] is True

        tests_app.dependency_overrides.clear()

    def test_clone_of_true_source_returns_true(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(
            db, user_a.id, title="Clone Source True", requires_runtime_credentials=True
        )
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        clone_resp = client.post(f"/tests/{tc.id}/clone")
        assert clone_resp.status_code == 201
        assert clone_resp.json()["requires_runtime_credentials"] is True

        tests_app.dependency_overrides.clear()

    def test_crud_update_persists_flag_without_credentials(
        self, db: Session, user_a: User
    ):
        """DB store holds only the boolean — no credential payload."""
        from app.crud import test_case as test_crud

        tc = _make_test_case(db, user_a.id, requires_runtime_credentials=False)
        updated = test_crud.update_test_case(
            db,
            tc.id,
            TestCaseUpdate(requires_runtime_credentials=True),
        )
        assert updated is not None
        assert updated.requires_runtime_credentials is True
        assert not hasattr(updated, "login_credentials") or getattr(updated, "login_credentials", None) is None
        # ORM columns do not include password/username
        column_names = {c.name for c in TestCase.__table__.columns}
        assert "password" not in column_names
        assert "username" not in column_names
        assert "login_credentials" not in column_names
