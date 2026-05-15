"""
Integration tests for Re-Run from Failed Step — Sprint 10.12 Feature B.

TDD RED phase: validates:
- Full resume flow with mock page (snapshot load, inject, step loop from start_from_step)
- SKIP records created for steps 1..start_from_step-1
- Stateful guard raises 422 when source execution has a failed step before resume point
- OTP guard raises 422 when resume would skip an OTP step
- Snapshot saved after every passing step
- steps_session_snapshots CRUD runs against real in-memory DB
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_page(url="https://example.com/dashboard"):
    page = AsyncMock()
    page.url = url
    page.goto = AsyncMock()
    page.context = AsyncMock()
    page.context.cookies = AsyncMock(return_value=[])
    page.evaluate = AsyncMock(return_value={})
    page.inner_html = AsyncMock(return_value="<body></body>")
    page.content = AsyncMock(return_value="<html></html>")
    page.viewport_size = {"width": 1280, "height": 720}
    page.screenshot = AsyncMock(return_value=b"png-data")
    return page


def _make_snapshot(execution_id=5, step_number=3, page_url="https://example.com/step3"):
    from app.models.test_execution import StepSessionSnapshot
    snap = MagicMock(spec=StepSessionSnapshot)
    snap.execution_id = execution_id
    snap.step_number = step_number
    snap.page_url = page_url
    snap.session_data = json.dumps({
        "cookies": [{"name": "auth", "value": "token"}],
        "localStorage": {"userId": "42"},
        "sessionStorage": {},
    })
    return snap


# ---------------------------------------------------------------------------
# 1. CRUD integration: save and retrieve from in-memory SQLite
# ---------------------------------------------------------------------------


class TestStepSessionSnapshotCRUDIntegration:
    """save_step_session_snapshot / get_step_session_snapshot with real DB."""

    @pytest.fixture()
    def db_session(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.base import Base
        from app.models import test_execution  # registers StepSessionSnapshot

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_save_and_retrieve_snapshot(self, db_session):
        from app.crud.step_session_snapshot import (
            save_step_session_snapshot,
            get_step_session_snapshot,
        )

        # We need a parent execution row; use minimal insert
        from app.models.test_execution import TestExecution, ExecutionStatus
        exec_row = TestExecution(
            id=101,
            test_case_id=1,
            user_id=1,
            status=ExecutionStatus.RUNNING,
        )
        db_session.add(exec_row)
        db_session.commit()

        snap_data = {"cookies": [{"name": "s", "value": "v"}], "localStorage": {}, "sessionStorage": {}}

        saved = save_step_session_snapshot(
            db=db_session,
            execution_id=101,
            step_number=3,
            page_url="https://example.com/step3",
            session_data=snap_data,
        )
        assert saved.id is not None
        assert saved.step_number == 3

        fetched = get_step_session_snapshot(db=db_session, execution_id=101, step_number=3)
        assert fetched is not None
        assert fetched.page_url == "https://example.com/step3"
        assert json.loads(fetched.session_data) == snap_data

    def test_get_snapshot_returns_none_for_missing(self, db_session):
        from app.crud.step_session_snapshot import get_step_session_snapshot

        result = get_step_session_snapshot(db=db_session, execution_id=999, step_number=99)
        assert result is None


# ---------------------------------------------------------------------------
# 2. Snapshot saved after passing step in execution loop
# ---------------------------------------------------------------------------


class TestSnapshotSavedDuringExecution:
    """_save_step_snapshot is invoked after a passing step and not after a failing step."""

    @pytest.mark.asyncio
    async def test_snapshot_saved_on_pass(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        snap_data = {"cookies": [], "localStorage": {}, "sessionStorage": {}}
        svc.export_profile_session = AsyncMock(return_value=snap_data)

        page = _make_mock_page()
        db = MagicMock()

        with patch("app.services.execution_service.save_step_session_snapshot") as mock_save:
            await svc._save_step_snapshot(db=db, execution_id=10, step_number=2, page=page)
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_snapshot_not_saved_when_export_returns_none(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc.export_profile_session = AsyncMock(return_value=None)

        page = _make_mock_page()
        db = MagicMock()

        with patch("app.services.execution_service.save_step_session_snapshot") as mock_save:
            await svc._save_step_snapshot(db=db, execution_id=10, step_number=2, page=page)
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 3. _apply_resume_snapshot integration
# ---------------------------------------------------------------------------


class TestApplyResumeSnapshotIntegration:
    """_apply_resume_snapshot restores cookies, localStorage, sessionStorage."""

    @pytest.mark.asyncio
    async def test_full_inject_cycle(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc._apply_profile_cookies = AsyncMock()
        svc._apply_profile_storage = AsyncMock()

        page = _make_mock_page()
        snapshot = _make_snapshot(page_url="https://example.com/cart")

        await svc._apply_resume_snapshot(page=page, snapshot=snapshot)

        page.goto.assert_awaited_once()
        svc._apply_profile_cookies.assert_awaited_once()
        svc._apply_profile_storage.assert_awaited_once()


# ---------------------------------------------------------------------------
# 4. validate_resume_point guards
# ---------------------------------------------------------------------------


class TestResumeGuardsIntegration:
    """validate_resume_point raises HTTP 422 for invalid resume scenarios."""

    def test_source_execution_has_failed_step_raises_422(self):
        from app.services.resume_guard import validate_resume_point
        from fastapi import HTTPException
        from app.models.test_execution import ExecutionResult, TestExecutionStep

        fail_step = MagicMock(spec=TestExecutionStep)
        fail_step.step_number = 2
        fail_step.result = ExecutionResult.FAIL

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [fail_step]

        with pytest.raises(HTTPException) as exc_info:
            validate_resume_point(
                db=db,
                resume_from_execution_id=1,
                start_from_step=5,
                steps=["a", "b", "c", "d", "e"],
            )
        assert exc_info.value.status_code == 422

    def test_otp_step_in_skipped_range_raises_422(self):
        from app.services.resume_guard import validate_resume_point
        from fastapi import HTTPException
        from app.models.test_execution import ExecutionResult, TestExecutionStep

        steps_in_db = []
        for i in range(1, 4):
            s = MagicMock(spec=TestExecutionStep)
            s.step_number = i
            s.result = ExecutionResult.PASS
            steps_in_db.append(s)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = steps_in_db

        # step index 2 (0-based 1) is an OTP step
        steps = [
            "Navigate to login page",
            "Enter the OTP sent to your email",
            "Click verify",
            "Check dashboard",
        ]

        with pytest.raises(HTTPException) as exc_info:
            validate_resume_point(
                db=db,
                resume_from_execution_id=1,
                start_from_step=4,   # would skip steps 1-3 including OTP at step 2
                steps=steps,
            )
        assert exc_info.value.status_code == 422
        assert "otp" in exc_info.value.detail.lower()

    def test_all_pass_no_otp_no_exception(self):
        from app.services.resume_guard import validate_resume_point
        from app.models.test_execution import ExecutionResult, TestExecutionStep

        steps_in_db = []
        for i in range(1, 4):
            s = MagicMock(spec=TestExecutionStep)
            s.step_number = i
            s.result = ExecutionResult.PASS
            steps_in_db.append(s)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = steps_in_db

        steps = ["Navigate", "Click login", "Fill password", "Submit"]

        validate_resume_point(
            db=db,
            resume_from_execution_id=1,
            start_from_step=4,
            steps=steps,
        )


# ---------------------------------------------------------------------------
# 5. SKIP records created for skipped range
# ---------------------------------------------------------------------------


class TestSkipRecordsIntegration:
    """_create_skip_records produces the correct step records."""

    def test_skip_count_matches_skipped_range(self):
        from app.services.execution_service import ExecutionService
        from app.crud import test_execution as crud_execution

        svc = ExecutionService.__new__(ExecutionService)
        db = MagicMock()
        steps = ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"]

        with patch.object(crud_execution, "create_execution_step") as mock_create:
            svc._create_skip_records(
                db=db,
                execution_id=20,
                steps=steps,
                start_from_step=4,
                resumed_from_execution_id=15,
            )
            assert mock_create.call_count == 3  # steps 1, 2, 3 skipped

    def test_skip_records_use_skip_result(self):
        from app.services.execution_service import ExecutionService
        from app.models.test_execution import ExecutionResult
        from app.crud import test_execution as crud_execution

        svc = ExecutionService.__new__(ExecutionService)
        db = MagicMock()
        steps = ["Navigate", "Login"]
        captured = []

        def capture(**kwargs):
            captured.append(kwargs)
            return MagicMock()

        with patch.object(crud_execution, "create_execution_step", side_effect=capture):
            svc._create_skip_records(
                db=db,
                execution_id=21,
                steps=steps,
                start_from_step=2,
                resumed_from_execution_id=12,
            )

        assert len(captured) == 1
        assert captured[0]["result"] == ExecutionResult.SKIP
