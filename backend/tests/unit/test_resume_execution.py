"""
Unit tests for Re-Run from Failed Step — Sprint 10.12 Feature B.

TDD RED phase: validates model columns, CRUD helpers, schema fields,
snapshot-save logic, SKIP-record creation, and stateful/OTP guards.
All tests should FAIL until the implementation is in place.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ---------------------------------------------------------------------------
# 1. StepSessionSnapshot ORM model
# ---------------------------------------------------------------------------


class TestStepSessionSnapshotModel:
    """StepSessionSnapshot model has the correct columns."""

    def test_model_has_id_column(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        assert hasattr(snap, "id")

    def test_model_has_execution_id_column(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        assert hasattr(snap, "execution_id")

    def test_model_has_step_number_column(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        assert hasattr(snap, "step_number")

    def test_model_has_page_url_column(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        assert hasattr(snap, "page_url")

    def test_model_has_session_data_column(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        assert hasattr(snap, "session_data")

    def test_model_has_created_at_column(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        assert hasattr(snap, "created_at")

    def test_model_tablename(self):
        from app.models.test_execution import StepSessionSnapshot

        assert StepSessionSnapshot.__tablename__ == "step_session_snapshots"

    def test_model_repr_contains_execution_and_step(self):
        from app.models.test_execution import StepSessionSnapshot

        snap = StepSessionSnapshot()
        snap.id = 1
        snap.execution_id = 10
        snap.step_number = 5
        r = repr(snap)
        assert "10" in r
        assert "5" in r


# ---------------------------------------------------------------------------
# 2. ExecutionStartRequest schema: resume params
# ---------------------------------------------------------------------------


class TestExecutionStartRequestResumeParams:
    """resume_from_execution_id and start_from_step are optional ints on ExecutionStartRequest."""

    def test_schema_accepts_resume_params(self):
        from app.schemas.test_execution import ExecutionStartRequest

        req = ExecutionStartRequest(
            browser="chromium",
            base_url="https://example.com",
            resume_from_execution_id=42,
            start_from_step=5,
        )
        assert req.resume_from_execution_id == 42
        assert req.start_from_step == 5

    def test_schema_defaults_resume_params_to_none(self):
        from app.schemas.test_execution import ExecutionStartRequest

        req = ExecutionStartRequest(
            browser="chromium",
            base_url="https://example.com",
        )
        assert req.resume_from_execution_id is None
        assert req.start_from_step is None

    def test_start_from_step_must_be_positive(self):
        """start_from_step must be >= 2 (step 1 means no skip, so resume makes no sense)."""
        from app.schemas.test_execution import ExecutionStartRequest
        import pydantic

        with pytest.raises((pydantic.ValidationError, ValueError)):
            ExecutionStartRequest(
                browser="chromium",
                base_url="https://example.com",
                resume_from_execution_id=1,
                start_from_step=1,  # must be >= 2
            )


# ---------------------------------------------------------------------------
# 3. CRUD: save_step_session_snapshot / get_step_session_snapshot
# ---------------------------------------------------------------------------


class TestStepSessionSnapshotCRUD:
    """CRUD helpers for step_session_snapshots table."""

    def test_save_snapshot_persists_to_db(self):
        from app.crud.step_session_snapshot import save_step_session_snapshot

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        snap_data = {
            "cookies": [{"name": "auth", "value": "tok"}],
            "localStorage": {"theme": "dark"},
            "sessionStorage": {},
        }

        result = save_step_session_snapshot(
            db=db,
            execution_id=10,
            step_number=3,
            page_url="https://example.com/checkout",
            session_data=snap_data,
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result is not None

    def test_get_snapshot_returns_latest_for_step(self):
        from app.crud.step_session_snapshot import get_step_session_snapshot
        from app.models.test_execution import StepSessionSnapshot

        mock_snap = MagicMock(spec=StepSessionSnapshot)
        mock_snap.execution_id = 10
        mock_snap.step_number = 3

        db = MagicMock()
        mock_query = db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_snap

        result = get_step_session_snapshot(db=db, execution_id=10, step_number=3)

        assert result == mock_snap

    def test_get_snapshot_returns_none_when_not_found(self):
        from app.crud.step_session_snapshot import get_step_session_snapshot

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_step_session_snapshot(db=db, execution_id=99, step_number=5)
        assert result is None


# ---------------------------------------------------------------------------
# 4. Resume guard: validate_resume_point
# ---------------------------------------------------------------------------


class TestValidateResumePoint:
    """validate_resume_point raises HTTP 422 for invalid resume requests."""

    def test_raises_422_when_source_step_failed(self):
        from app.services.resume_guard import validate_resume_point
        from fastapi import HTTPException
        from app.models.test_execution import ExecutionResult, TestExecutionStep

        failed_step = MagicMock(spec=TestExecutionStep)
        failed_step.step_number = 2
        failed_step.result = ExecutionResult.FAIL

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [failed_step]

        with pytest.raises(HTTPException) as exc_info:
            validate_resume_point(
                db=db,
                resume_from_execution_id=10,
                start_from_step=5,
                steps=[],
            )
        assert exc_info.value.status_code == 422
        assert "step 2 failed" in exc_info.value.detail.lower()

    def test_raises_422_when_otp_step_would_be_skipped(self):
        from app.services.resume_guard import validate_resume_point
        from fastapi import HTTPException
        from app.models.test_execution import ExecutionResult, TestExecutionStep

        pass_step = MagicMock(spec=TestExecutionStep)
        pass_step.step_number = 2
        pass_step.result = ExecutionResult.PASS

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [pass_step]

        otp_step = "Enter the OTP sent to your email"
        steps = ["Navigate to https://example.com", otp_step, "Click verify"]

        with pytest.raises(HTTPException) as exc_info:
            validate_resume_point(
                db=db,
                resume_from_execution_id=10,
                start_from_step=3,  # would skip step 2 which is OTP
                steps=steps,
            )
        assert exc_info.value.status_code == 422
        assert "otp" in exc_info.value.detail.lower()

    def test_passes_when_all_prior_steps_passed_and_no_otp(self):
        from app.services.resume_guard import validate_resume_point
        from app.models.test_execution import ExecutionResult, TestExecutionStep

        pass_steps = []
        for i in range(1, 4):
            s = MagicMock(spec=TestExecutionStep)
            s.step_number = i
            s.result = ExecutionResult.PASS
            pass_steps.append(s)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = pass_steps

        steps = [
            "Navigate to https://example.com",
            "Click login",
            "Fill username",
            "Submit",
        ]

        # Should not raise
        validate_resume_point(
            db=db,
            resume_from_execution_id=10,
            start_from_step=4,
            steps=steps,
        )


# ---------------------------------------------------------------------------
# 5. Snapshot save after passing step (execution_service integration)
# ---------------------------------------------------------------------------


class TestSnapshotSaveAfterPassingStep:
    """After a passing step, _save_step_snapshot is called with correct args."""

    @pytest.mark.asyncio
    async def test_save_snapshot_called_after_pass(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)

        page = AsyncMock()
        page.url = "https://example.com/step3"
        page.context = AsyncMock()
        page.context.cookies = AsyncMock(return_value=[{"name": "sess", "value": "abc"}])
        page.evaluate = AsyncMock(return_value={})

        db = MagicMock()

        snap_data = {
            "cookies": [{"name": "sess", "value": "abc"}],
            "localStorage": {},
            "sessionStorage": {},
            "exported_at": "2026-01-01T00:00:00",
        }
        svc.export_profile_session = AsyncMock(return_value=snap_data)

        with patch("app.services.execution_service.save_step_session_snapshot") as mock_save:
            await svc._save_step_snapshot(
                db=db,
                execution_id=10,
                step_number=3,
                page=page,
            )

            mock_save.assert_called_once_with(
                db=db,
                execution_id=10,
                step_number=3,
                page_url="https://example.com/step3",
                session_data=snap_data,
            )

    @pytest.mark.asyncio
    async def test_save_snapshot_skipped_when_export_returns_none(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc.export_profile_session = AsyncMock(return_value=None)

        db = MagicMock()
        page = AsyncMock()
        page.url = "https://example.com"

        with patch("app.services.execution_service.save_step_session_snapshot") as mock_save:
            await svc._save_step_snapshot(db=db, execution_id=10, step_number=1, page=page)
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 6. Resume injection: _apply_resume_snapshot
# ---------------------------------------------------------------------------


class TestApplyResumeSnapshot:
    """_apply_resume_snapshot navigates to page_url and injects session data."""

    @pytest.mark.asyncio
    async def test_navigates_to_snapshot_page_url(self):
        from app.services.execution_service import ExecutionService
        from app.models.test_execution import StepSessionSnapshot

        svc = ExecutionService.__new__(ExecutionService)
        svc._apply_profile_cookies = AsyncMock()
        svc._apply_profile_storage = AsyncMock()

        page = AsyncMock()
        page.goto = AsyncMock()

        snap = MagicMock(spec=StepSessionSnapshot)
        snap.page_url = "https://example.com/checkout"
        snap.session_data = '{"cookies": [], "localStorage": {}, "sessionStorage": {}}'

        await svc._apply_resume_snapshot(page=page, snapshot=snap)

        page.goto.assert_called_once_with(
            "https://example.com/checkout",
            timeout=30000,
            wait_until="domcontentloaded",
        )

    @pytest.mark.asyncio
    async def test_injects_cookies_and_storage_from_snapshot(self):
        from app.services.execution_service import ExecutionService
        from app.models.test_execution import StepSessionSnapshot

        svc = ExecutionService.__new__(ExecutionService)
        svc._apply_profile_cookies = AsyncMock()
        svc._apply_profile_storage = AsyncMock()

        page = AsyncMock()
        page.goto = AsyncMock()

        session_data = {
            "cookies": [{"name": "auth", "value": "token123"}],
            "localStorage": {"key": "value"},
            "sessionStorage": {},
        }
        import json
        snap = MagicMock(spec=StepSessionSnapshot)
        snap.page_url = "https://example.com/checkout"
        snap.session_data = json.dumps(session_data)

        await svc._apply_resume_snapshot(page=page, snapshot=snap)

        svc._apply_profile_cookies.assert_awaited_once_with(page, session_data)
        svc._apply_profile_storage.assert_awaited_once_with(page, session_data)


# ---------------------------------------------------------------------------
# 7. SKIP records for skipped steps
# ---------------------------------------------------------------------------


class TestSkipRecordsCreatedForSkippedSteps:
    """When resuming from step N, steps 1 to N-1 get SKIP records."""

    def test_create_skip_records_creates_correct_count(self):
        from app.services.execution_service import ExecutionService
        from app.models.test_execution import ExecutionResult
        from app.crud import test_execution as crud_execution

        svc = ExecutionService.__new__(ExecutionService)

        db = MagicMock()

        steps = [
            "Navigate to https://example.com",
            "Click login",
            "Fill email",
            "Click submit",
            "Verify dashboard",
        ]

        with patch.object(crud_execution, "create_execution_step") as mock_create:
            svc._create_skip_records(
                db=db,
                execution_id=10,
                steps=steps,
                start_from_step=4,  # skip steps 1, 2, 3
                resumed_from_execution_id=7,
            )

            assert mock_create.call_count == 3

    def test_skip_record_description_includes_resume_source(self):
        from app.services.execution_service import ExecutionService
        from app.models.test_execution import ExecutionResult
        from app.crud import test_execution as crud_execution

        svc = ExecutionService.__new__(ExecutionService)
        db = MagicMock()

        steps = ["Navigate", "Login", "Submit"]

        recorded_calls = []

        def capture_call(**kwargs):
            recorded_calls.append(kwargs)
            return MagicMock()

        with patch.object(crud_execution, "create_execution_step", side_effect=capture_call):
            svc._create_skip_records(
                db=db,
                execution_id=10,
                steps=steps,
                start_from_step=3,
                resumed_from_execution_id=5,
            )

        assert len(recorded_calls) == 2
        for call in recorded_calls:
            assert call["result"] == ExecutionResult.SKIP
            assert "resumed from step" in call["step_description"].lower() or \
                   "skipped" in call["step_description"].lower()
