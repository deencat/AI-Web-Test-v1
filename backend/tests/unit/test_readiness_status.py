"""
Unit/API tests for Feature 4: Test Readiness Status.

Covers default on create, PUT round-trip, invalid enum → 422, list filter,
sanitizer inclusion, clone copies readiness, and execution status untouched.
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
from app.crud import test_case as test_crud
from app.db.base import Base
from app.models.test_case import (
    TestCase,
    TestType,
    Priority,
    TestStatus,
    ReadinessStatus,
)
from app.models.user import User
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate


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
    title: str = "Readiness Test",
    readiness_status: ReadinessStatus = ReadinessStatus.DRAFT,
    status: TestStatus = TestStatus.PENDING,
) -> TestCase:
    tc = TestCase(
        title=title,
        description="Desc",
        test_type=TestType.E2E,
        priority=Priority.MEDIUM,
        status=status,
        readiness_status=readiness_status,
        steps=["Navigate to page"],
        expected_result="OK",
        preconditions=None,
        test_data=None,
        tags=None,
        test_metadata=None,
        user_id=user_id,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def _minimal_orm(*, readiness_status: ReadinessStatus) -> MagicMock:
    tc = MagicMock()
    tc.id = 1
    tc.title = "Sanitize Unit"
    tc.description = "Has description"
    tc.test_type = TestType.E2E
    tc.priority = Priority.MEDIUM
    tc.status = TestStatus.PENDING
    tc.readiness_status = readiness_status
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
    tc.requires_runtime_credentials = False
    return tc


class TestSanitizeIncludesReadinessStatus:
    def test_sanitize_includes_readiness_status(self):
        response = sanitize_test_case_for_response(
            _minimal_orm(readiness_status=ReadinessStatus.READY_TO_TEST)
        )
        assert response.readiness_status == ReadinessStatus.READY_TO_TEST

    def test_sanitize_includes_blocked(self):
        response = sanitize_test_case_for_response(
            _minimal_orm(readiness_status=ReadinessStatus.BLOCKED)
        )
        assert response.readiness_status == ReadinessStatus.BLOCKED
        assert response.status == TestStatus.PENDING


class TestReadinessCrudDefaults:
    def test_create_defaults_to_draft(self, db: Session, user_a: User):
        created = test_crud.create_test_case(
            db=db,
            test_case=TestCaseCreate(
                title="New Draft",
                description="Desc",
                test_type=TestType.E2E,
                steps=["step"],
                expected_result="ok",
            ),
            user_id=user_a.id,
        )
        assert created.readiness_status == ReadinessStatus.DRAFT
        assert created.status == TestStatus.PENDING

    def test_update_readiness_does_not_change_execution_status(
        self, db: Session, user_a: User
    ):
        tc = _make_test_case(
            db, user_a.id, status=TestStatus.PASSED, readiness_status=ReadinessStatus.DRAFT
        )
        updated = test_crud.update_test_case(
            db=db,
            test_case_id=tc.id,
            updates=TestCaseUpdate(readiness_status=ReadinessStatus.BLOCKED),
        )
        assert updated is not None
        assert updated.readiness_status == ReadinessStatus.BLOCKED
        assert updated.status == TestStatus.PASSED

    def test_list_filter_by_readiness(self, db: Session, user_a: User):
        _make_test_case(db, user_a.id, title="Draft", readiness_status=ReadinessStatus.DRAFT)
        blocked = _make_test_case(
            db, user_a.id, title="Blocked", readiness_status=ReadinessStatus.BLOCKED
        )
        items, total = test_crud.get_test_cases(
            db=db, user_id=user_a.id, readiness_status=ReadinessStatus.BLOCKED
        )
        assert total == 1
        assert items[0].id == blocked.id

    def test_clone_copies_readiness(self, db: Session, user_a: User):
        original = _make_test_case(
            db,
            user_a.id,
            readiness_status=ReadinessStatus.BLOCKED,
            status=TestStatus.PASSED,
        )
        cloned = test_crud.clone_test_case(
            db, original, user_id=user_a.id, new_title="Blocked (Copy)"
        )
        assert cloned.readiness_status == ReadinessStatus.BLOCKED
        assert cloned.status == TestStatus.PENDING


class TestReadinessApi:
    def test_put_then_get_round_trip(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(db, user_a.id)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        put_resp = client.put(
            f"/tests/{tc.id}",
            json={"readiness_status": "ready_to_test"},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["readiness_status"] == "ready_to_test"
        assert put_resp.json()["status"] == "pending"

        get_resp = client.get(f"/tests/{tc.id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["readiness_status"] == "ready_to_test"
        assert get_resp.json()["status"] == "pending"

    def test_invalid_readiness_returns_422(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(db, user_a.id)
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        resp = client.put(f"/tests/{tc.id}", json={"readiness_status": "not_a_status"})
        assert resp.status_code == 422

    def test_list_filter_query_param(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        _make_test_case(db, user_a.id, title="A", readiness_status=ReadinessStatus.DRAFT)
        _make_test_case(
            db, user_a.id, title="B", readiness_status=ReadinessStatus.READY_TO_TEST
        )
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)

        resp = client.get("/tests", params={"readiness_status": "ready_to_test"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["readiness_status"] == "ready_to_test"

    def test_create_api_defaults_draft(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)
        resp = client.post(
            "/tests",
            json={
                "title": "API Created",
                "description": "Desc",
                "test_type": "e2e",
                "steps": ["step 1"],
                "expected_result": "ok",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["readiness_status"] == "draft"

    def test_clone_api_copies_readiness(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tc = _make_test_case(
            db, user_a.id, readiness_status=ReadinessStatus.BLOCKED
        )
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)
        resp = client.post(f"/tests/{tc.id}/clone", json={})
        assert resp.status_code == 201
        assert resp.json()["readiness_status"] == "blocked"
        assert resp.json()["status"] == "pending"

    def test_batch_assign_readiness(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        t1 = _make_test_case(db, user_a.id, title="One")
        t2 = _make_test_case(db, user_a.id, title="Two")
        tests_app.dependency_overrides[deps.get_current_user] = lambda: _mock_user(user_a.id)
        client = TestClient(tests_app)
        resp = client.patch(
            "/tests/batch/readiness",
            json={"test_ids": [t1.id, t2.id], "readiness_status": "ready_to_test"},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2
        db.refresh(t1)
        db.refresh(t2)
        assert t1.readiness_status == ReadinessStatus.READY_TO_TEST
        assert t2.readiness_status == ReadinessStatus.READY_TO_TEST
