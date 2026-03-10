"""
Unit tests for test_generation.py — Sprint 10.5 truncation fix.

Problem:  When user saves max_tokens=1200, generation requests 1200 tokens
          from the LLM. For 5 complex test cases this causes mid-JSON
          truncation → JSONDecodeError.

Fix scope:
  1. Enforce MIN_GENERATION_TOKENS (4096) — user max_tokens setting is
     respected for *execution* but never allowed to starve generation.
  2. _try_recover_truncated_json() — attempt to salvage whatever complete
     test_case objects are present before the cutoff.

TDD: RED first, then implement.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.test_generation import TestGenerationService


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_service() -> TestGenerationService:
    return TestGenerationService()


def _truncated_json(num_complete: int = 1) -> str:
    """Build a syntactically broken JSON string: `num_complete` full test
    cases followed by the beginning of an unterminated one."""
    cases = []
    for i in range(num_complete):
        cases.append({
            "title": f"Test case {i + 1}",
            "description": f"Description {i + 1}",
            "test_type": "e2e",
            "priority": "high",
            "steps": ["Step 1", "Step 2"],
            "test_data": {},
            "expected_result": "Pass",
        })
    base = json.dumps({"test_cases": cases})
    # Remove closing braces and add truncated entry
    chopped = base.rstrip("}")  # remove outer }
    chopped = chopped.rstrip("]")  # remove ]
    if num_complete > 0:
        chopped += ','
    chopped += '\n    {\n      "title": "Truncated test case",\n      "description": "This got cut o'
    return chopped


# ---------------------------------------------------------------------------
# Test MIN_GENERATION_TOKENS constant
# ---------------------------------------------------------------------------

class TestMinGenerationTokensConstant:
    def test_service_has_min_generation_tokens(self):
        """TestGenerationService must expose MIN_GENERATION_TOKENS."""
        svc = _make_service()
        assert hasattr(svc, "MIN_GENERATION_TOKENS"), (
            "TestGenerationService must define MIN_GENERATION_TOKENS"
        )

    def test_min_generation_tokens_is_at_least_4096(self):
        svc = _make_service()
        assert svc.MIN_GENERATION_TOKENS >= 4096, (
            f"MIN_GENERATION_TOKENS should be >= 4096, got {svc.MIN_GENERATION_TOKENS}"
        )


# ---------------------------------------------------------------------------
# _try_recover_truncated_json
# ---------------------------------------------------------------------------

class TestTryRecoverTruncatedJson:
    """Unit tests for the JSON truncation recovery helper."""

    def test_method_exists(self):
        svc = _make_service()
        assert hasattr(svc, "_try_recover_truncated_json"), (
            "TestGenerationService must implement _try_recover_truncated_json()"
        )

    def test_valid_json_returned_unchanged(self):
        svc = _make_service()
        valid = json.dumps({"test_cases": [{"title": "A", "steps": []}]})
        result = svc._try_recover_truncated_json(valid)
        assert result is not None
        assert json.loads(result)["test_cases"][0]["title"] == "A"

    def test_recovers_complete_test_cases_from_truncated_json(self):
        svc = _make_service()
        truncated = _truncated_json(num_complete=2)
        result = svc._try_recover_truncated_json(truncated)
        assert result is not None, "Should recover 2 complete test cases"
        parsed = json.loads(result)
        assert "test_cases" in parsed
        assert len(parsed["test_cases"]) == 2

    def test_recovers_single_complete_test_case(self):
        svc = _make_service()
        truncated = _truncated_json(num_complete=1)
        result = svc._try_recover_truncated_json(truncated)
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed["test_cases"]) == 1

    def test_returns_none_when_no_complete_case_present(self):
        """If nothing is recoverable (truncated before first complete case), return None."""
        svc = _make_service()
        garbage = '{"test_cases": [{"title": "Cut off immediately'
        result = svc._try_recover_truncated_json(garbage)
        # Should return None (no usable cases) or valid empty JSON — but must NOT raise
        if result is not None:
            parsed = json.loads(result)
            assert parsed.get("test_cases", []) == []

    def test_recovery_produces_valid_json(self):
        """Recovered output must always be parseable by json.loads."""
        svc = _make_service()
        truncated = _truncated_json(num_complete=3)
        result = svc._try_recover_truncated_json(truncated)
        assert result is not None
        json.loads(result)  # Must not raise

    def test_non_truncated_empty_valid_json_passes_through(self):
        svc = _make_service()
        valid = json.dumps({"test_cases": []})
        result = svc._try_recover_truncated_json(valid)
        assert result is not None
        assert json.loads(result) == {"test_cases": []}


# ---------------------------------------------------------------------------
# _effective_max_tokens: enforce minimum generation token budget
# ---------------------------------------------------------------------------

class TestEffectiveMaxTokens:
    """Unit tests for _effective_max_tokens() helper."""

    def test_method_exists(self):
        svc = _make_service()
        assert hasattr(svc, "_effective_max_tokens"), (
            "TestGenerationService must implement _effective_max_tokens()"
        )

    def test_1200_is_raised_to_minimum(self):
        svc = _make_service()
        result = svc._effective_max_tokens(1200)
        assert result >= svc.MIN_GENERATION_TOKENS, (
            f"1200 must be raised to MIN_GENERATION_TOKENS={svc.MIN_GENERATION_TOKENS}"
        )

    def test_2048_is_raised_to_minimum(self):
        svc = _make_service()
        result = svc._effective_max_tokens(2048)
        assert result >= svc.MIN_GENERATION_TOKENS

    def test_4096_at_boundary_is_accepted(self):
        svc = _make_service()
        result = svc._effective_max_tokens(4096)
        assert result == 4096

    def test_8192_above_minimum_is_respected(self):
        svc = _make_service()
        result = svc._effective_max_tokens(8192)
        assert result == 8192

    def test_16000_large_value_unchanged(self):
        svc = _make_service()
        result = svc._effective_max_tokens(16000)
        assert result == 16000


# ---------------------------------------------------------------------------
# min-token enforcement inside generate_tests()
# ---------------------------------------------------------------------------

class TestGenerateTestsMinTokenEnforcement:
    """Ensure generate_tests() never sends fewer than MIN_GENERATION_TOKENS to LLM."""

    @pytest.fixture()
    def service(self):
        return _make_service()

    def _make_llm_response(self, n: int = 2) -> dict:
        cases = [
            {
                "title": f"Test {i}",
                "description": "desc",
                "test_type": "e2e",
                "priority": "high",
                "steps": ["Open URL"],
                "test_data": {},
                "expected_result": "Pass",
            }
            for i in range(n)
        ]
        return {
            "choices": [{"message": {"content": json.dumps({"test_cases": cases})}}],
            "model": "openai/gpt-oss-120b:free",
            "usage": {"total_tokens": 800},
        }

    @pytest.mark.asyncio
    async def test_user_max_tokens_1200_is_raised_to_minimum(self, service):
        """When user has saved max_tokens=1200, LLM must be called with MIN_GENERATION_TOKENS."""
        captured_kwargs = {}

        async def fake_chat_completion(**kwargs):
            captured_kwargs.update(kwargs)
            return self._make_llm_response()

        service.llm.chat_completion = fake_chat_completion

        user_config = {
            "provider": "openrouter",
            "model": "openai/gpt-oss-120b:free",
            "temperature": 0.7,
            "max_tokens": 1200,  # ← too low; must be raised
        }

        with patch(
            "app.services.user_settings_service.user_settings_service.get_provider_config",
            return_value=user_config,
        ):
            with patch("app.services.test_generation.Session"):
                mock_db = MagicMock()
                await service.generate_tests(
                    requirement="test login",
                    num_tests=3,
                    db=mock_db,
                    user_id=42,
                    use_kb_context=False,
                )

        assert "max_tokens" in captured_kwargs, "max_tokens must be passed to LLM"
        assert captured_kwargs["max_tokens"] >= service.MIN_GENERATION_TOKENS, (
            f"LLM max_tokens {captured_kwargs['max_tokens']} < MIN_GENERATION_TOKENS "
            f"{service.MIN_GENERATION_TOKENS}"
        )

    @pytest.mark.asyncio
    async def test_user_max_tokens_8192_is_respected(self, service):
        """When user has a value above minimum, their value is used as-is."""
        captured_kwargs = {}

        async def fake_chat_completion(**kwargs):
            captured_kwargs.update(kwargs)
            return self._make_llm_response()

        service.llm.chat_completion = fake_chat_completion

        user_config = {
            "provider": "openrouter",
            "model": "openai/gpt-oss-120b:free",
            "temperature": 0.7,
            "max_tokens": 8192,
        }

        with patch(
            "app.services.user_settings_service.user_settings_service.get_provider_config",
            return_value=user_config,
        ):
            with patch("app.services.test_generation.Session"):
                mock_db = MagicMock()
                await service.generate_tests(
                    requirement="test login",
                    num_tests=3,
                    db=mock_db,
                    user_id=42,
                    use_kb_context=False,
                )

        assert captured_kwargs["max_tokens"] == 8192


# ---------------------------------------------------------------------------
# Truncated response end-to-end recovery in generate_tests()
# ---------------------------------------------------------------------------

class TestGenerateTestsTruncationRecovery:
    """generate_tests() must recover partial JSON instead of raising 500."""

    @pytest.fixture()
    def service(self):
        return _make_service()

    @pytest.mark.asyncio
    async def test_truncated_json_recovers_complete_cases(self, service):
        """If the LLM returns truncated JSON, generate_tests returns the
        complete test cases that were fully serialised before the cutoff."""
        truncated_content = _truncated_json(num_complete=2)

        async def fake_chat(**kwargs):
            return {
                "choices": [{"message": {"content": truncated_content}}],
                "model": "openai/gpt-oss-120b:free",
                "usage": {"total_tokens": 1200},
            }

        service.llm.chat_completion = fake_chat
        result = await service.generate_tests(requirement="test login", num_tests=5)

        assert "test_cases" in result
        assert len(result["test_cases"]) == 2, (
            "Should recover 2 complete test cases from truncated response"
        )
        assert result["metadata"].get("truncation_recovered") is True

    @pytest.mark.asyncio
    async def test_fully_unrecoverable_json_still_raises(self, service):
        """If recovery also fails (e.g. garbage response), an exception must be raised."""
        async def fake_chat(**kwargs):
            return {
                "choices": [{"message": {"content": "not json at all {{{"}}],
                "model": "openai/gpt-oss-120b:free",
                "usage": {"total_tokens": 50},
            }

        service.llm.chat_completion = fake_chat

        with pytest.raises(Exception, match="Failed to parse LLM response"):
            await service.generate_tests(requirement="test login", num_tests=3)
