"""
Unit tests for AI-Powered Failure Root Cause Analysis — Sprint 10.12.

TDD RED phase: validates prompt construction, DOM token capping,
LLM mock interaction, and the ExecutionFeedbackCreate schema field.
All tests should FAIL until the implementation is in place.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_execution_history(
    t1_error="Element not found",
    t2_error="XPath timeout",
    t3_error="Stagehand observe returned empty",
):
    return [
        {"tier": 1, "success": False, "error": t1_error},
        {"tier": 2, "success": False, "error": t2_error},
        {"tier": 3, "success": False, "error": t3_error},
    ]


def _make_step_data(instruction="Click the Pay Now button"):
    return {
        "action": "click",
        "instruction": instruction,
        "selector": "#pay-now-btn",
    }


# ---------------------------------------------------------------------------
# 1. ExecutionFeedbackCreate schema: root_cause_analysis field
# ---------------------------------------------------------------------------


class TestExecutionFeedbackSchema:
    """root_cause_analysis is an optional str on ExecutionFeedbackCreate and response."""

    def test_create_schema_accepts_root_cause_analysis(self):
        from app.schemas.execution_feedback import ExecutionFeedbackCreate

        fb = ExecutionFeedbackCreate(
            execution_id=1,
            root_cause_analysis="The button was disabled due to unchecked T&C.",
        )
        assert fb.root_cause_analysis == "The button was disabled due to unchecked T&C."

    def test_create_schema_defaults_to_none(self):
        from app.schemas.execution_feedback import ExecutionFeedbackCreate

        fb = ExecutionFeedbackCreate(execution_id=1)
        assert fb.root_cause_analysis is None

    def test_response_schema_includes_root_cause_analysis(self):
        from app.schemas.execution_feedback import ExecutionFeedbackResponse
        from datetime import datetime

        resp = ExecutionFeedbackResponse(
            id=1,
            execution_id=1,
            is_anomaly=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            root_cause_analysis="DOM changed between runs.",
        )
        assert resp.root_cause_analysis == "DOM changed between runs."

    def test_response_schema_root_cause_analysis_defaults_to_none(self):
        from app.schemas.execution_feedback import ExecutionFeedbackResponse
        from datetime import datetime

        resp = ExecutionFeedbackResponse(
            id=1,
            execution_id=1,
            is_anomaly=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert resp.root_cause_analysis is None


# ---------------------------------------------------------------------------
# 2. ExecutionFeedback ORM model: root_cause_analysis column
# ---------------------------------------------------------------------------


class TestExecutionFeedbackModel:
    """ORM model has a root_cause_analysis TEXT column."""

    def test_model_has_root_cause_analysis_attribute(self):
        from app.models.execution_feedback import ExecutionFeedback

        fb = ExecutionFeedback()
        # Column exists and is None by default
        assert hasattr(fb, "root_cause_analysis")
        assert fb.root_cause_analysis is None

    def test_model_column_is_text_nullable(self):
        from app.models.execution_feedback import ExecutionFeedback
        import sqlalchemy as sa

        col = ExecutionFeedback.__table__.c.root_cause_analysis
        assert isinstance(col.type, sa.Text)
        assert col.nullable is True


# ---------------------------------------------------------------------------
# 3. RCA service: _build_rca_prompt
# ---------------------------------------------------------------------------


class TestBuildRcaPrompt:
    """_build_rca_prompt assembles the LLM prompt correctly."""

    def _get_fn(self):
        from app.services.root_cause_analysis_service import _build_rca_prompt
        return _build_rca_prompt

    def test_prompt_contains_instruction(self):
        fn = self._get_fn()
        prompt = fn(
            instruction="Click the Pay Now button",
            page_url="https://example.com/checkout",
            execution_history=_make_execution_history(),
            dom_snapshot="<html><button id='pay-now' disabled>Pay Now</button></html>",
        )
        assert "Click the Pay Now button" in prompt

    def test_prompt_contains_page_url(self):
        fn = self._get_fn()
        prompt = fn(
            instruction="Click button",
            page_url="https://example.com/checkout",
            execution_history=_make_execution_history(),
            dom_snapshot="",
        )
        assert "https://example.com/checkout" in prompt

    def test_prompt_contains_tier_errors(self):
        fn = self._get_fn()
        history = _make_execution_history(
            t1_error="Timeout after 30000ms",
            t2_error="XPath //button[@id='pay'] not found",
            t3_error="Observe returned no elements",
        )
        prompt = fn(
            instruction="Click button",
            page_url="https://example.com",
            execution_history=history,
            dom_snapshot="",
        )
        assert "Timeout after 30000ms" in prompt
        assert "XPath //button[@id='pay'] not found" in prompt
        assert "Observe returned no elements" in prompt

    def test_prompt_contains_dom_snapshot(self):
        fn = self._get_fn()
        snapshot = "<button class='btn-primary'>Submit</button>"
        prompt = fn(
            instruction="Click Submit",
            page_url="https://example.com",
            execution_history=_make_execution_history(),
            dom_snapshot=snapshot,
        )
        assert snapshot in prompt

    def test_prompt_handles_partial_execution_history(self):
        """Only Tier 1 failed — Tier 2/3 not present."""
        fn = self._get_fn()
        history = [{"tier": 1, "success": False, "error": "Element not visible"}]
        prompt = fn(
            instruction="Click button",
            page_url="https://example.com",
            execution_history=history,
            dom_snapshot="",
        )
        assert "Element not visible" in prompt
        # Should handle missing Tier 2/3 gracefully
        assert "Tier 1" in prompt or "tier 1" in prompt or "1" in prompt

    def test_prompt_handles_empty_execution_history(self):
        fn = self._get_fn()
        prompt = fn(
            instruction="Click button",
            page_url="https://example.com",
            execution_history=[],
            dom_snapshot="",
        )
        assert "Click button" in prompt


# ---------------------------------------------------------------------------
# 4. RCA service: _cap_dom_snapshot
# ---------------------------------------------------------------------------


class TestCapDomSnapshot:
    """DOM snapshot is capped server-side to ~4000 tokens before being sent to LLM."""

    def _get_fn(self):
        from app.services.root_cause_analysis_service import _cap_dom_snapshot
        return _cap_dom_snapshot

    def test_short_snapshot_unchanged(self):
        fn = self._get_fn()
        short = "<html><body><p>Hello</p></body></html>"
        assert fn(short) == short

    def test_long_snapshot_is_truncated(self):
        fn = self._get_fn()
        # ~16000 chars ≈ 4000 tokens (rough 4 chars/token estimate)
        long_html = "x" * 20000
        result = fn(long_html)
        assert len(result) < len(long_html)

    def test_truncated_snapshot_has_marker(self):
        fn = self._get_fn()
        long_html = "a" * 20000
        result = fn(long_html)
        assert "[truncated]" in result

    def test_none_returns_empty_string(self):
        fn = self._get_fn()
        assert fn(None) == ""

    def test_empty_string_returns_empty_string(self):
        fn = self._get_fn()
        assert fn("") == ""


# ---------------------------------------------------------------------------
# 5. RCA service: generate_root_cause_analysis (async, LLM mocked)
# ---------------------------------------------------------------------------


class TestGenerateRootCauseAnalysis:
    """generate_root_cause_analysis calls LLM and returns plain-text analysis."""

    @pytest.mark.asyncio
    async def test_returns_llm_response_text(self):
        from app.services.root_cause_analysis_service import generate_root_cause_analysis

        mock_page = AsyncMock()
        mock_page.url = "https://example.com/checkout"
        mock_page.inner_html = AsyncMock(return_value="<button disabled>Pay</button>")

        llm_response = {
            "choices": [{"message": {"content": "The Pay button was disabled."}}]
        }

        with patch(
            "app.services.root_cause_analysis_service.UniversalLLMService"
        ) as MockLLM:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.chat_completion = AsyncMock(return_value=llm_response)
            MockLLM.return_value = mock_llm_instance

            result = await generate_root_cause_analysis(
                page=mock_page,
                step_data=_make_step_data("Click the Pay Now button"),
                execution_history=_make_execution_history(),
            )

        assert result == "The Pay button was disabled."

    @pytest.mark.asyncio
    async def test_returns_none_when_not_all_tiers_exhausted(self):
        """RCA must NOT fire for partial failures — only all_tiers_exhausted."""
        from app.services.root_cause_analysis_service import generate_root_cause_analysis

        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.inner_html = AsyncMock(return_value="<body></body>")

        # Only Tier 1 tried
        history = [{"tier": 1, "success": False, "error": "timeout"}]

        with patch(
            "app.services.root_cause_analysis_service.UniversalLLMService"
        ) as MockLLM:
            mock_llm_instance = AsyncMock()
            MockLLM.return_value = mock_llm_instance

            result = await generate_root_cause_analysis(
                page=mock_page,
                step_data=_make_step_data(),
                execution_history=history,
                error_type="tier1_failed",
            )

        # LLM must NOT be called
        mock_llm_instance.chat_completion.assert_not_called()
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_llm_exception(self):
        """LLM failure must not crash execution — return None gracefully."""
        from app.services.root_cause_analysis_service import generate_root_cause_analysis

        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.inner_html = AsyncMock(return_value="<body></body>")

        with patch(
            "app.services.root_cause_analysis_service.UniversalLLMService"
        ) as MockLLM:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.chat_completion = AsyncMock(
                side_effect=Exception("LLM API unreachable")
            )
            MockLLM.return_value = mock_llm_instance

            result = await generate_root_cause_analysis(
                page=mock_page,
                step_data=_make_step_data(),
                execution_history=_make_execution_history(),
                error_type="all_tiers_exhausted",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_inner_html_failure_handled_gracefully(self):
        """If page.inner_html raises, RCA proceeds with empty DOM snapshot."""
        from app.services.root_cause_analysis_service import generate_root_cause_analysis

        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.inner_html = AsyncMock(side_effect=Exception("context destroyed"))

        llm_response = {
            "choices": [{"message": {"content": "Button was stale."}}]
        }

        with patch(
            "app.services.root_cause_analysis_service.UniversalLLMService"
        ) as MockLLM:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.chat_completion = AsyncMock(return_value=llm_response)
            MockLLM.return_value = mock_llm_instance

            result = await generate_root_cause_analysis(
                page=mock_page,
                step_data=_make_step_data(),
                execution_history=_make_execution_history(),
                error_type="all_tiers_exhausted",
            )

        assert result == "Button was stale."

    @pytest.mark.asyncio
    async def test_llm_prompt_references_all_info(self):
        """Verify the prompt sent to LLM includes step instruction and page URL."""
        from app.services.root_cause_analysis_service import generate_root_cause_analysis

        mock_page = AsyncMock()
        mock_page.url = "https://checkout.example.com/pay"
        mock_page.inner_html = AsyncMock(return_value="<body></body>")

        llm_response = {
            "choices": [{"message": {"content": "Root cause found."}}]
        }
        captured_messages = []

        async def capture_chat(*args, **kwargs):
            captured_messages.extend(kwargs.get("messages", args[0] if args else []))
            return llm_response

        with patch(
            "app.services.root_cause_analysis_service.UniversalLLMService"
        ) as MockLLM:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.chat_completion = AsyncMock(side_effect=capture_chat)
            MockLLM.return_value = mock_llm_instance

            await generate_root_cause_analysis(
                page=mock_page,
                step_data=_make_step_data("Click the Pay Now button"),
                execution_history=_make_execution_history(
                    t1_error="Element not visible"
                ),
                error_type="all_tiers_exhausted",
            )

        assert captured_messages, "LLM was never called"
        full_prompt = " ".join(
            m.get("content", "") for m in captured_messages if isinstance(m, dict)
        )
        assert "Click the Pay Now button" in full_prompt
        assert "https://checkout.example.com/pay" in full_prompt
        assert "Element not visible" in full_prompt
