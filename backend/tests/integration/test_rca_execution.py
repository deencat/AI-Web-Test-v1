"""
Integration tests for AI-Powered Failure Root Cause Analysis — Sprint 10.12.

TDD RED phase: validates that:
- _capture_execution_feedback stores root_cause_analysis on all_tiers_exhausted failures
- generate_root_cause_analysis is called only for all_tiers_exhausted error type
- root_cause_analysis persisted in the DB via ExecutionFeedback record
- Feedback records with null root_cause_analysis are still created for other failure types
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exhausted_tier_info():
    return [
        {"tier": 1, "success": False, "error": "Selector not found"},
        {"tier": 2, "success": False, "error": "XPath extraction failed"},
        {"tier": 3, "success": False, "error": "Stagehand observe returned []"},
    ]


def _partial_tier_info():
    return [
        {"tier": 1, "success": False, "error": "Timeout"},
    ]


def _mock_page(url="https://example.com/test"):
    page = AsyncMock()
    page.url = url
    page.inner_html = AsyncMock(return_value="<body><button disabled>Pay</button></body>")
    page.content = AsyncMock(return_value="<html><body></body></html>")
    page.viewport_size = {"width": 1280, "height": 720}
    return page


# ---------------------------------------------------------------------------
# 1. _capture_execution_feedback: RCA stored on all_tiers_exhausted
# ---------------------------------------------------------------------------


class TestCaptureExecutionFeedbackRCA:
    """When error_type is all_tiers_exhausted, root_cause_analysis is populated."""

    @pytest.mark.asyncio
    async def test_rca_stored_on_all_tiers_exhausted(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc.config = MagicMock(browser="chromium")
        svc._classify_failure_type = MagicMock(return_value="all_tiers_exhausted")
        svc._extract_selector_from_error = MagicMock(return_value=(None, None))
        svc.three_tier_service = MagicMock(user_ai_config={"provider": "azure", "model": "ChatGPT-UAT"})

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        page = _mock_page()

        rca_text = "The Pay Now button remained disabled because T&C was unchecked."

        with patch(
            "app.services.execution_service.generate_root_cause_analysis",
            new=AsyncMock(return_value=rca_text),
        ) as mock_rca, patch(
            "app.crud.execution_feedback.create_feedback"
        ) as mock_create:
            mock_create.return_value = MagicMock(id=42)

            await svc._capture_execution_feedback(
                db=db,
                execution_id=10,
                step_index=5,
                step_description="Click the Pay Now button",
                error_message="All tiers exhausted",
                page=page,
                screenshot_path="/tmp/shot.png",
                duration_ms=4500,
                tier_info=_exhausted_tier_info(),
                strategy_used="option_c",
                error_type="all_tiers_exhausted",
            )

        # generate_root_cause_analysis should have been called
        mock_rca.assert_called_once()

        # create_feedback should have been called with root_cause_analysis set
        call_kwargs = mock_create.call_args
        feedback_obj = call_kwargs[1]["feedback"] if "feedback" in call_kwargs[1] else call_kwargs[0][1]
        assert feedback_obj.root_cause_analysis == rca_text

    @pytest.mark.asyncio
    async def test_rca_not_called_for_partial_failure(self):
        """RCA must NOT fire when error_type is not all_tiers_exhausted."""
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc.config = MagicMock(browser="chromium")
        svc._classify_failure_type = MagicMock(return_value="timeout")
        svc._extract_selector_from_error = MagicMock(return_value=(None, None))
        svc.three_tier_service = None

        db = MagicMock()
        page = _mock_page()

        with patch(
            "app.services.execution_service.generate_root_cause_analysis",
            new=AsyncMock(return_value="should not be called"),
        ) as mock_rca, patch(
            "app.crud.execution_feedback.create_feedback"
        ) as mock_create:
            mock_create.return_value = MagicMock(id=1)

            await svc._capture_execution_feedback(
                db=db,
                execution_id=10,
                step_index=3,
                step_description="Click button",
                error_message="Timeout after 30s",
                page=page,
                screenshot_path=None,
                duration_ms=30000,
                tier_info=_partial_tier_info(),
                # no error_type, or error_type != "all_tiers_exhausted"
            )

        mock_rca.assert_not_called()

    @pytest.mark.asyncio
    async def test_rca_none_when_llm_fails(self):
        """If RCA generation raises or returns None, feedback is still created."""
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc.config = MagicMock(browser="chromium")
        svc._classify_failure_type = MagicMock(return_value="all_tiers_exhausted")
        svc._extract_selector_from_error = MagicMock(return_value=(None, None))
        svc.three_tier_service = MagicMock(user_ai_config={"provider": "azure", "model": "ChatGPT-UAT"})

        db = MagicMock()
        page = _mock_page()

        with patch(
            "app.services.execution_service.generate_root_cause_analysis",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.crud.execution_feedback.create_feedback"
        ) as mock_create:
            mock_create.return_value = MagicMock(id=1)

            # Should not raise
            await svc._capture_execution_feedback(
                db=db,
                execution_id=10,
                step_index=3,
                step_description="Click button",
                error_message="All tiers exhausted",
                page=page,
                screenshot_path=None,
                duration_ms=5000,
                tier_info=_exhausted_tier_info(),
                error_type="all_tiers_exhausted",
            )

        # Feedback was still created despite None RCA
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args
        feedback_obj = call_kwargs[1]["feedback"] if "feedback" in call_kwargs[1] else call_kwargs[0][1]
        assert feedback_obj.root_cause_analysis is None


# ---------------------------------------------------------------------------
# 2. OTP step detection: RCA skipped for otp_step failure type
# ---------------------------------------------------------------------------


class TestRcaSkippedForOtpStep:
    """OTP digit steps should not trigger RCA even if all tiers exhausted."""

    @pytest.mark.asyncio
    async def test_rca_not_called_for_otp_step(self):
        from app.services.execution_service import ExecutionService

        svc = ExecutionService.__new__(ExecutionService)
        svc.config = MagicMock(browser="chromium")
        svc._classify_failure_type = MagicMock(return_value="otp_step_failed")
        svc._extract_selector_from_error = MagicMock(return_value=(None, None))
        svc.three_tier_service = None

        db = MagicMock()
        page = _mock_page()

        with patch(
            "app.services.execution_service.generate_root_cause_analysis",
            new=AsyncMock(return_value="should not be called"),
        ) as mock_rca, patch(
            "app.crud.execution_feedback.create_feedback"
        ) as mock_create:
            mock_create.return_value = MagicMock(id=1)

            await svc._capture_execution_feedback(
                db=db,
                execution_id=10,
                step_index=7,
                step_description="Input the first number of OTP '4' to the first box",
                error_message="failed",
                page=page,
                screenshot_path=None,
                duration_ms=1000,
                tier_info=_exhausted_tier_info(),
                error_type="all_tiers_exhausted",
            )

        # OTP steps never trigger RCA
        mock_rca.assert_not_called()


# ---------------------------------------------------------------------------
# 3. DB round-trip: root_cause_analysis persisted via crud
# ---------------------------------------------------------------------------


class TestRcaDbPersistence:
    """ExecutionFeedback can be created with root_cause_analysis via CRUD."""

    def test_create_feedback_with_rca(self):
        from app.schemas.execution_feedback import ExecutionFeedbackCreate
        from app.crud.execution_feedback import create_feedback

        feedback_schema = ExecutionFeedbackCreate(
            execution_id=5,
            step_index=3,
            error_message="All tiers exhausted",
            root_cause_analysis="T&C checkbox was not ticked before clicking Pay.",
        )

        # Mock the DB session
        fake_record = MagicMock()
        fake_record.root_cause_analysis = "T&C checkbox was not ticked before clicking Pay."

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock(side_effect=lambda obj: None)

        with patch(
            "app.models.execution_feedback.ExecutionFeedback",
            return_value=fake_record,
        ):
            # Should not raise
            result = create_feedback(db=db, feedback=feedback_schema)

        db.add.assert_called_once()
        db.commit.assert_called_once()
