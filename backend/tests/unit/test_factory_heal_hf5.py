"""Unit tests for HF-5 self-healing service."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.factory_heal_service import (
    classify_failure_strategy,
    clear_xpath_cache_for_feedback,
)


class TestClassifyFailureStrategy:
    def test_xpath_from_failure_type(self):
        fb = SimpleNamespace(
            failure_type="selector_not_found",
            error_message="",
            selector_type=None,
        )
        assert classify_failure_strategy([fb]) == "xpath"

    def test_xpath_from_error_message(self):
        fb = SimpleNamespace(
            failure_type="timeout",
            error_message="Element not found for selector #buy",
            selector_type=None,
        )
        assert classify_failure_strategy([fb]) == "xpath"

    def test_flow_default(self):
        fb = SimpleNamespace(
            failure_type="assertion_failed",
            error_message="Expected title Plans",
            selector_type=None,
        )
        assert classify_failure_strategy([fb]) == "flow"


class TestClearXpathCache:
    def test_clear_by_page_url(self):
        db = MagicMock()
        row = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [row]
        fb = SimpleNamespace(page_url="https://example.com/plan", failed_selector=None)
        deleted = clear_xpath_cache_for_feedback(db, [fb])
        assert deleted == 1
        db.delete.assert_called_with(row)
        db.commit.assert_called_once()


class TestHealAttemptEscalation:
    @patch("app.services.factory_heal_service.crud_heal.create_heal_review_item")
    @patch("app.services.factory_heal_service.crud_heal.get_heal_attempt")
    @patch("app.services.factory_heal_service.crud_feedback.get_feedback_by_execution")
    @patch("app.services.factory_heal_service.crud_executions.create_execution")
    def test_max_attempts_escalates_without_heal(
        self,
        mock_create_exec,
        mock_get_feedback,
        mock_get_attempt,
        mock_create_review,
    ):
        from app.models.test_execution import ExecutionResult, ExecutionStatus
        from app.services.factory_heal_service import heal_from_feedback

        db = MagicMock()
        execution = SimpleNamespace(
            id=99,
            status=ExecutionStatus.COMPLETED,
            result=ExecutionResult.FAIL,
            test_case_id=5,
            base_url="https://example.com",
            browser="chromium",
            environment="dev",
        )
        test_case = SimpleNamespace(
            id=5,
            title="Plan test",
            description="desc",
            tags=["regression"],
            priority=SimpleNamespace(value="medium"),
            test_metadata={},
        )

        attempt = SimpleNamespace(attempt_count=2, last_action="recrawl", last_error="prior fail")
        mock_get_attempt.return_value = attempt
        review = SimpleNamespace(id=7)
        mock_create_review.return_value = review

        db.query.return_value.filter.return_value.first.side_effect = [execution, test_case]

        result = heal_from_feedback(db, 99, user_id=1)

        assert result["action"] == "escalated"
        assert result["heal_review_id"] == 7
        mock_create_review.assert_called_once()
