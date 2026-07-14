"""
Unit tests for execution cancel API and cooperative execution hooks.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.api.v1.endpoints import executions as executions_module
from app.crud import test_execution as crud_executions
from app.db.base import Base
from app.models.test_case import TestCase, TestType, Priority, TestStatus
from app.models.test_execution import ExecutionStatus
from app.models.user import User
from app.services.execution_cancel_store import (
    register_cancel,
    request_cancel,
    is_cancel_requested,
    clear_cancel,
)
from app.services.execution_queue import ExecutionQueue


# ---------------------------------------------------------------------------
# DB fixtures
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
def owner(db: Session) -> User:
    user = User(
        email="owner@example.com",
        username="owner",
        hashed_password="hash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def other_user(db: Session) -> User:
    user = User(
        email="other@example.com",
        username="other",
        hashed_password="hash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_case(db: Session, owner: User) -> TestCase:
    tc = TestCase(
        title="Cancel test",
        description="desc",
        test_type=TestType.E2E,
        priority=Priority.MEDIUM,
        status=TestStatus.PENDING,
        steps=["Step 1"],
        expected_result="ok",
        user_id=owner.id,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def _make_execution(
    db: Session,
    test_case: TestCase,
    user_id: int,
    status: ExecutionStatus = ExecutionStatus.PENDING,
) -> int:
    execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case.id,
        user_id=user_id,
        browser="chromium",
        environment="dev",
        base_url="https://example.com",
    )
    execution.status = status
    if status == ExecutionStatus.RUNNING:
        execution.started_at = datetime.utcnow()
    if status == ExecutionStatus.COMPLETED:
        execution.started_at = datetime.utcnow()
        execution.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(execution)
    return execution.id


@pytest.fixture
def client(db: Session, owner: User):
    app = FastAPI()
    app.include_router(executions_module.router, prefix="/executions")

    def override_get_db():
        yield db

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = lambda: owner
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_cancel_store():
    for eid in range(1, 200):
        clear_cancel(eid)
    yield
    for eid in range(1, 200):
        clear_cancel(eid)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_cancel_execution_crud_sets_status(db: Session, test_case: TestCase, owner: User):
    execution_id = _make_execution(db, test_case, owner.id, ExecutionStatus.RUNNING)
    result = crud_executions.cancel_execution(
        db,
        execution_id,
        total_steps=5,
        passed_steps=2,
        failed_steps=0,
        skipped_steps=1,
    )
    assert result.status == ExecutionStatus.CANCELLED
    assert result.result is None
    assert result.total_steps == 5
    assert result.passed_steps == 2
    assert result.skipped_steps == 1
    assert result.completed_at is not None
    assert result.error_message is None


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


def test_cancel_not_found(client: TestClient):
    response = client.delete("/executions/9999/cancel")
    assert response.status_code == 404


def test_cancel_wrong_user(db: Session, test_case: TestCase, owner: User, other_user: User):
    execution_id = _make_execution(db, test_case, owner.id, ExecutionStatus.PENDING)

    app = FastAPI()
    app.include_router(executions_module.router, prefix="/executions")

    def override_get_db():
        yield db

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = lambda: other_user
    other_client = TestClient(app)

    response = other_client.delete(f"/executions/{execution_id}/cancel")
    assert response.status_code == 403


def test_cancel_pending_execution(db: Session, test_case: TestCase, owner: User, client: TestClient):
    execution_id = _make_execution(db, test_case, owner.id, ExecutionStatus.PENDING)
    queue = ExecutionQueue(max_concurrent=5)
    queue.add_to_queue(execution_id, test_case.id, owner.id, priority=5)

    with patch.object(executions_module, "get_execution_queue", return_value=queue):
        response = client.delete(f"/executions/{execution_id}/cancel")

    assert response.status_code == 204
    execution = crud_executions.get_execution(db, execution_id)
    assert execution.status == ExecutionStatus.CANCELLED
    assert queue.get_queue_status()["queued_count"] == 0


def test_cancel_running_sets_flag(db: Session, test_case: TestCase, owner: User, client: TestClient):
    execution_id = _make_execution(db, test_case, owner.id, ExecutionStatus.RUNNING)

    response = client.delete(f"/executions/{execution_id}/cancel")

    assert response.status_code == 204
    assert is_cancel_requested(execution_id) is True
    execution = crud_executions.get_execution(db, execution_id)
    assert execution.status == ExecutionStatus.RUNNING


def test_cancel_completed_idempotent(db: Session, test_case: TestCase, owner: User, client: TestClient):
    execution_id = _make_execution(db, test_case, owner.id, ExecutionStatus.COMPLETED)

    response = client.delete(f"/executions/{execution_id}/cancel")

    assert response.status_code == 204
    execution = crud_executions.get_execution(db, execution_id)
    assert execution.status == ExecutionStatus.COMPLETED


def test_delete_execution_still_works(db: Session, test_case: TestCase, owner: User, client: TestClient):
    execution_id = _make_execution(db, test_case, owner.id, ExecutionStatus.COMPLETED)

    response = client.delete(f"/executions/{execution_id}")

    assert response.status_code == 204
    assert crud_executions.get_execution(db, execution_id) is None


# ---------------------------------------------------------------------------
# Cooperative execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_test_cancel_mid_step(db: Session, test_case: TestCase, owner: User):
    from app.services.execution_service import ExecutionService, ExecutionConfig

    execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case.id,
        user_id=owner.id,
        browser="chromium",
        environment="dev",
        base_url="https://example.com",
    )
    execution_id = execution.id

    service = ExecutionService(config=ExecutionConfig(browser="chromium", headless=True))
    page_mock = MagicMock()
    page_mock.goto = AsyncMock()

    async def slow_execute_step(*args, **kwargs):
        request_cancel(execution_id)
        return {"success": False, "cancelled": True, "error": "Execution cancelled by user"}

    with patch.object(service, "initialize", new=AsyncMock()), \
         patch.object(service, "create_context", new=AsyncMock()), \
         patch.object(service, "create_page", new=AsyncMock(return_value=page_mock)), \
         patch.object(service, "cleanup", new=AsyncMock()), \
         patch("app.services.execution_service.auto_dismiss_blocking_modals", new=AsyncMock()), \
         patch.object(service, "_get_user_execution_settings", return_value=MagicMock(timeout_per_tier_seconds=30, fallback_strategy="option_a")), \
         patch("app.services.execution_service.user_settings_service.get_provider_config", return_value={"provider": "openai", "model": "gpt-4"}), \
         patch("app.services.execution_service.ThreeTierExecutionService") as mock_tier_cls, \
         patch("app.services.execution_service.resolve_steps", side_effect=lambda steps, **kwargs: steps), \
         patch.object(service, "_execute_step", side_effect=slow_execute_step):

        mock_tier_cls.return_value = MagicMock()

        result = await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=owner.id,
            base_url="https://example.com",
            execution_id=execution_id,
        )

    assert result.status == ExecutionStatus.CANCELLED
    assert is_cancel_requested(execution_id) is False
