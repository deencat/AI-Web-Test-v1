"""
Unit tests for Feature 4: Timed Wait Step (cancel-aware short-circuit).
"""
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.timed_wait import (
    MAX_TIMED_WAIT_MS,
    parse_timed_wait_ms,
    sleep_cancel_aware,
)
from app.services.execution_service import ExecutionService


# ---------------------------------------------------------------------------
# parse_timed_wait_ms
# ---------------------------------------------------------------------------


class TestParseTimedWaitMs:
    def test_parse_wait_10_seconds(self):
        assert parse_timed_wait_ms("Wait 10 seconds") == 10_000

    def test_parse_wait_canonical(self):
        assert parse_timed_wait_ms("wait: 10s") == 10_000
        assert parse_timed_wait_ms("wait:10s") == 10_000

    def test_parse_wait_ms(self):
        assert parse_timed_wait_ms("WAIT 5000ms") == 5_000
        assert parse_timed_wait_ms("wait 10000 ms") == 10_000

    def test_parse_sleep_and_delay(self):
        assert parse_timed_wait_ms("sleep 3") == 3_000
        assert parse_timed_wait_ms("delay 3 seconds") == 3_000

    def test_parse_minutes(self):
        assert parse_timed_wait_ms("Wait 1 minute") == 60_000
        assert parse_timed_wait_ms("wait 2 minutes") == 120_000

    def test_parse_structured_timeout_ms(self):
        assert (
            parse_timed_wait_ms(
                "Wait 10 seconds",
                {"action": "wait", "timeout_ms": 3000},
            )
            == 3_000
        )

    def test_parse_structured_timeout_alias(self):
        assert (
            parse_timed_wait_ms(
                "",
                {"action": "wait", "timeout": 3000},
            )
            == 3_000
        )

    def test_parse_structured_kind_timed(self):
        assert (
            parse_timed_wait_ms(
                "",
                {"kind": "timed", "timeout_ms": 2500},
            )
            == 2_500
        )

    def test_reject_wait_for_message(self):
        assert parse_timed_wait_ms("Wait for the success message") is None
        assert parse_timed_wait_ms("Wait for the success message to appear") is None

    def test_reject_wait_until(self):
        assert parse_timed_wait_ms("Wait until spinner disappears") is None
        assert parse_timed_wait_ms("Wait until the spinner disappears") is None

    def test_reject_wait_for_with_number(self):
        # Ambiguous — prefer non-timed when "for" present
        assert parse_timed_wait_ms("wait 10 seconds for the modal") is None

    def test_clamp_above_120s(self):
        assert parse_timed_wait_ms("Wait 999 seconds") == MAX_TIMED_WAIT_MS
        assert (
            parse_timed_wait_ms("", {"action": "wait", "timeout_ms": 999_000})
            == MAX_TIMED_WAIT_MS
        )

    def test_non_wait_instruction(self):
        assert parse_timed_wait_ms("Click Login") is None
        assert parse_timed_wait_ms("Please wait while we process") is None

    def test_clamp_below_min_ms(self):
        # Structured tiny timeout clamps up to MIN_TIMED_WAIT_MS (100)
        assert (
            parse_timed_wait_ms("", {"action": "wait", "timeout_ms": 1}) == 100
        )

    def test_parse_duration_from_text_via_structured_value(self):
        assert (
            parse_timed_wait_ms(
                "",
                {"action": "wait", "value": "10s"},
            )
            == 10_000
        )
        assert (
            parse_timed_wait_ms(
                "",
                {"action": "wait", "value": "5000"},
            )
            == 5_000
        )

    def test_structured_timeout_string_with_unit(self):
        assert (
            parse_timed_wait_ms(
                "",
                {"action": "wait", "timeout_ms": "2.5s"},
            )
            == 2_500
        )

    def test_structured_timeout_invalid_falls_through_to_value(self):
        assert (
            parse_timed_wait_ms(
                "",
                {"action": "wait", "timeout_ms": "nope", "value": "1500"},
            )
            == 1_500
        )

    def test_structured_wait_instruction_as_bare_duration(self):
        assert (
            parse_timed_wait_ms(
                "2500ms",
                {"action": "wait"},
            )
            == 2_500
        )

    def test_empty_instruction_no_structured(self):
        assert parse_timed_wait_ms("") is None
        assert parse_timed_wait_ms(None) is None
        assert parse_timed_wait_ms("   ") is None

    def test_structured_wait_empty_fields_returns_none(self):
        assert parse_timed_wait_ms("", {"action": "wait"}) is None
        assert parse_timed_wait_ms("", {"action": "wait", "value": ""}) is None

    def test_parse_duration_helpers_edge_cases(self):
        from app.services.timed_wait import _parse_duration_from_text

        assert _parse_duration_from_text(None) is None
        assert _parse_duration_from_text("") is None
        assert _parse_duration_from_text("   ") is None
        assert _parse_duration_from_text("not-a-duration") is None
        assert _parse_duration_from_text("10s") == 10_000
        assert _parse_duration_from_text("2 minutes") == 120_000
        assert _parse_duration_from_text("100") == 100  # pure int → ms (then min clamp)


# ---------------------------------------------------------------------------
# sleep_cancel_aware
# ---------------------------------------------------------------------------


class TestSleepCancelAware:
    @pytest.mark.asyncio
    async def test_sleep_duration_approx(self):
        start = time.monotonic()
        cancelled = await sleep_cancel_aware(500, chunk_ms=100)
        elapsed = (time.monotonic() - start) * 1000
        assert cancelled is False
        assert 250 <= elapsed <= 900

    @pytest.mark.asyncio
    async def test_cancel_mid_wait(self):
        cancelled_flag = {"v": False}

        def cancel_check():
            return cancelled_flag["v"]

        async def flip_soon():
            await asyncio.sleep(0.2)
            cancelled_flag["v"] = True

        start = time.monotonic()
        flip_task = asyncio.create_task(flip_soon())
        cancelled = await sleep_cancel_aware(10_000, cancel_check, chunk_ms=100)
        await flip_task
        elapsed = (time.monotonic() - start) * 1000

        assert cancelled is True
        assert elapsed < 1500

    @pytest.mark.asyncio
    async def test_cancel_already_true_before_first_chunk(self):
        cancelled = await sleep_cancel_aware(5_000, lambda: True, chunk_ms=100)
        assert cancelled is True


# ---------------------------------------------------------------------------
# ExecutionService short-circuit
# ---------------------------------------------------------------------------


class TestExecutionServiceTimedWaitShortCircuit:
    @pytest.mark.asyncio
    async def test_short_circuit_does_not_call_three_tier(self):
        service = ExecutionService.__new__(ExecutionService)
        service.three_tier_service = MagicMock()
        service.three_tier_service.execute_step = AsyncMock(
            return_value={"success": True, "tier": 1}
        )

        with patch(
            "app.services.execution_service.sleep_cancel_aware",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_sleep:
            result = await service._execute_step(
                page=MagicMock(),
                step_description="Wait 10 seconds",
                step_number=1,
                base_url="https://example.com",
                detailed_step=None,
                execution_id=None,
                cancel_check=None,
            )

        mock_sleep.assert_awaited_once()
        args, kwargs = mock_sleep.await_args
        assert args[0] == 10_000
        service.three_tier_service.execute_step.assert_not_called()
        assert result["success"] is True
        assert result["tier_used"] == "timed_wait"
        assert result["action"] == "wait"

    @pytest.mark.asyncio
    async def test_short_circuit_canonical_form(self):
        service = ExecutionService.__new__(ExecutionService)
        service.three_tier_service = MagicMock()
        service.three_tier_service.execute_step = AsyncMock()

        with patch(
            "app.services.execution_service.sleep_cancel_aware",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_sleep:
            result = await service._execute_step(
                page=MagicMock(),
                step_description="wait: 5s",
                step_number=2,
                base_url="https://example.com",
            )

        assert mock_sleep.await_args.args[0] == 5_000
        service.three_tier_service.execute_step.assert_not_called()
        assert result["tier_used"] == "timed_wait"

    @pytest.mark.asyncio
    async def test_short_circuit_structured_timeout_ms(self):
        service = ExecutionService.__new__(ExecutionService)
        service.three_tier_service = MagicMock()
        service.three_tier_service.execute_step = AsyncMock()

        with patch(
            "app.services.execution_service.sleep_cancel_aware",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_sleep:
            result = await service._execute_step(
                page=MagicMock(),
                step_description="pause",
                step_number=1,
                base_url="https://example.com",
                detailed_step={"action": "wait", "timeout_ms": 3000},
            )

        assert mock_sleep.await_args.args[0] == 3_000
        service.three_tier_service.execute_step.assert_not_called()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_cancel_mid_wait_returns_cancelled(self):
        service = ExecutionService.__new__(ExecutionService)
        service.three_tier_service = MagicMock()
        service.three_tier_service.execute_step = AsyncMock()

        with patch(
            "app.services.execution_service.sleep_cancel_aware",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await service._execute_step(
                page=MagicMock(),
                step_description="wait: 30s",
                step_number=1,
                base_url="https://example.com",
            )

        assert result["cancelled"] is True
        assert result["success"] is False
        service.three_tier_service.execute_step.assert_not_called()

    @pytest.mark.asyncio
    async def test_wait_for_does_not_short_circuit(self):
        service = ExecutionService.__new__(ExecutionService)
        service.three_tier_service = MagicMock()
        service.three_tier_service.execute_step = AsyncMock(
            return_value={
                "success": True,
                "tier": 1,
                "execution_time_ms": 10,
            }
        )

        result = await service._execute_step(
            page=MagicMock(),
            step_description="Wait for the success message",
            step_number=1,
            base_url="https://example.com",
        )

        service.three_tier_service.execute_step.assert_called_once()
        assert result["success"] is True
        assert result.get("tier_used") != "timed_wait"


# ---------------------------------------------------------------------------
# Tier 2 wait not a silent no-op
# ---------------------------------------------------------------------------


class TestTier2WaitNotNoop:
    @pytest.mark.asyncio
    async def test_tier2_wait_sleeps_with_duration(self):
        from app.services.tier2_hybrid import Tier2HybridExecutor

        executor = Tier2HybridExecutor.__new__(Tier2HybridExecutor)
        executor.timeout_ms = 30000
        executor.cache_service = MagicMock()
        executor.payment_direct_enabled = False
        executor._verify_and_clear_pending_tab_check = AsyncMock()

        page = MagicMock()
        step = {
            "action": "wait",
            "instruction": "wait: 1s",
            "timeout_ms": 200,
        }

        with patch(
            "app.services.tier2_hybrid.sleep_cancel_aware",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_sleep:
            result = await executor.execute_step(page, step)

        mock_sleep.assert_awaited_once()
        assert mock_sleep.await_args.args[0] == 200  # structured timeout_ms wins
        assert result["success"] is True
        assert result["tier"] == 2

    @pytest.mark.asyncio
    async def test_tier2_wait_without_duration_fails(self):
        from app.services.tier2_hybrid import Tier2HybridExecutor

        executor = Tier2HybridExecutor.__new__(Tier2HybridExecutor)
        executor.timeout_ms = 30000
        executor.cache_service = MagicMock()
        executor.payment_direct_enabled = False
        executor._verify_and_clear_pending_tab_check = AsyncMock()

        page = MagicMock()
        step = {
            "action": "wait",
            "instruction": "Wait for the success message",
        }

        result = await executor.execute_step(page, step)
        assert result["success"] is False
        err = result.get("error") or ""
        assert (
            "timeout" in err.lower()
            or "duration" in err.lower()
            or "Timed wait" in err
        )
