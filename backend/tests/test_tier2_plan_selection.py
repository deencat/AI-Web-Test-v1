"""Tests for Three HK preprod plan-selection recovery and performance in Tier 2."""

import sys
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.tier2_hybrid import Tier2HybridExecutor


class TestTier2NavigatePerformance:
    """Regression guards for navigate-step performance (RC-PERF-1)."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    @pytest.mark.asyncio
    async def test_navigate_uses_domcontentloaded_not_networkidle(self):
        """navigate action must use wait_until='domcontentloaded', not 'networkidle'.

        Regression guard: Three HK UAT never reaches networkidle.  Using
        'networkidle' caused every navigate step to time out at 30 s per tier
        (90 s total for 3-tier fallback).  'domcontentloaded' resolves in ~1-3 s.
        """
        page = MagicMock()
        page.goto = AsyncMock(return_value=None)
        page.url = "about:blank"

        with patch.object(self.executor, "_verify_and_clear_pending_tab_check", AsyncMock()):
            result = await self.executor.execute_step(
                page=page,
                step={
                    "instruction": "Step 1: Navigate to the Three HK plan page",
                    "action": "navigate",
                    "value": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
                    "element_text": "",
                },
            )

        assert result["success"] is True
        page.goto.assert_awaited_once()
        _, call_kwargs = page.goto.await_args
        assert call_kwargs.get("wait_until") == "domcontentloaded", (
            f"navigate called page.goto with wait_until={call_kwargs.get('wait_until')!r}; "
            "must use 'domcontentloaded' to avoid 30 s networkidle timeout on Three HK UAT"
        )


class TestThreeHkPlanSelectionRecovery:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    def test_is_three_hk_plan_selection_click_true_for_uat_plan_step(self):
        assert self.executor._is_three_hk_plan_selection_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Step 7: Select a $338 plan from the available plans",
            action="click",
        ) is True

    def test_is_three_hk_plan_selection_click_false_for_non_plan_click(self):
        assert self.executor._is_three_hk_plan_selection_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Step 8: Click the continue button",
            action="click",
        ) is False

    @pytest.mark.asyncio
    async def test_ensure_plan_click_progressed_returns_when_transition_confirms(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._wait_for_three_hk_plan_transition = AsyncMock(return_value=True)
        self.executor._retry_three_hk_plan_click = AsyncMock(return_value=False)

        with patch("app.services.tier2_hybrid.auto_dismiss_blocking_modals", AsyncMock(return_value=False)) as dismiss_mock:
            await self.executor._ensure_three_hk_plan_click_progressed(
                page=page,
                instruction="Step 7: Select a $338 plan from the available plans",
                current_url=page.url,
            )

        dismiss_mock.assert_not_awaited()
        self.executor._retry_three_hk_plan_click.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ensure_plan_click_progressed_retries_once_after_bounce(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._wait_for_three_hk_plan_transition = AsyncMock(side_effect=[False, False, True])
        self.executor._retry_three_hk_plan_click = AsyncMock(return_value=True)

        with patch("app.services.tier2_hybrid.auto_dismiss_blocking_modals", AsyncMock(return_value=True)) as dismiss_mock:
            await self.executor._ensure_three_hk_plan_click_progressed(
                page=page,
                instruction="Step 7: Select a $338 plan from the available plans",
                current_url=page.url,
            )

        dismiss_mock.assert_awaited_once()
        self.executor._retry_three_hk_plan_click.assert_awaited_once_with(
            page,
            "Step 7: Select a $338 plan from the available plans",
        )

    @pytest.mark.asyncio
    async def test_ensure_plan_click_progressed_raises_when_still_on_plan_page(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._wait_for_three_hk_plan_transition = AsyncMock(side_effect=[False, False])
        self.executor._retry_three_hk_plan_click = AsyncMock(return_value=False)

        with patch("app.services.tier2_hybrid.auto_dismiss_blocking_modals", AsyncMock(return_value=False)):
            with pytest.raises(ValueError, match="plan selection did not advance"):
                await self.executor._ensure_three_hk_plan_click_progressed(
                    page=page,
                    instruction="Step 7: Select a $338 plan from the available plans",
                    current_url=page.url,
                )

    @pytest.mark.asyncio
    async def test_execute_action_with_xpath_calls_plan_progress_guard(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        element = AsyncMock()
        element.wait_for = AsyncMock(return_value=None)
        element.text_content = AsyncMock(return_value="Select")
        element.click = AsyncMock(return_value=None)

        locator = MagicMock()
        locator.first = element
        page.locator = MagicMock(return_value=locator)

        self.executor._wait_for_element_enabled_before_click = AsyncMock(return_value=None)
        self.executor._ensure_three_hk_plan_click_progressed = AsyncMock(return_value=None)

        with patch(
            "app.services.tier2_hybrid.wait_for_post_click_readiness",
            AsyncMock(return_value={"is_payment_click": False}),
        ):
            await self.executor._execute_action_with_xpath(
                page=page,
                action="click",
                xpath="/html/body/div/button[1]",
                instruction="Step 7: Select a $338 plan from the available plans",
            )

        self.executor._ensure_three_hk_plan_click_progressed.assert_awaited_once_with(
            page,
            "Step 7: Select a $338 plan from the available plans",
            "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
        )


class TestThreeHkPlanTabRecovery:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    def test_is_three_hk_plan_tab_click_true_for_voucher_tab_step(self):
        assert self.executor._is_three_hk_plan_tab_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Click voucher monthly plan tab.",
            action="click",
        ) is True

    def test_is_three_hk_plan_tab_click_false_for_plan_selection_step(self):
        assert self.executor._is_three_hk_plan_tab_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Step 7: Select the '$288/month' plan from the available plans",
            action="click",
        ) is False

    @pytest.mark.asyncio
    async def test_ensure_plan_tab_click_progressed_retries_once_after_unverified_tab_switch(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._wait_for_three_hk_plan_tab_transition = AsyncMock(side_effect=[False, False, True])
        self.executor._retry_three_hk_plan_tab_click = AsyncMock(return_value=True)

        with patch("app.services.tier2_hybrid.auto_dismiss_blocking_modals", AsyncMock(return_value=False)) as dismiss_mock:
            await self.executor._ensure_three_hk_plan_tab_click_progressed(
                page=page,
                instruction="Click voucher monthly plan tab.",
                current_url=page.url,
            )

        dismiss_mock.assert_awaited_once()
        self.executor._retry_three_hk_plan_tab_click.assert_awaited_once_with(
            page,
            "Click voucher monthly plan tab.",
        )

    @pytest.mark.asyncio
    async def test_execute_step_uses_direct_tab_helper_before_xpath_cache(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._try_three_hk_plan_tab_click = AsyncMock(
            return_value={
                "success": True,
                "tier": 2,
                "execution_time_ms": 123.0,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }
        )
        self.executor.cache_service.get_cached_xpath = MagicMock(side_effect=AssertionError("cache should be bypassed"))

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": "Click voucher monthly plan tab.",
            },
        )

        assert result["success"] is True
        self.executor._try_three_hk_plan_tab_click.assert_awaited_once_with(
            page,
            "Click voucher monthly plan tab.",
            ANY,
        )


class TestThreeHkPlanTabSpinnerSettle:
    """RC1 + RC2: tab state must be verified AFTER the SPA spinner cycle completes."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    @pytest.mark.asyncio
    async def test_try_tab_click_waits_for_spinner_before_progress_check(self):
        """spinner-settle must fire BEFORE _ensure_three_hk_plan_tab_click_progressed."""
        call_order = []

        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        locator = AsyncMock()
        locator.wait_for = AsyncMock()
        locator.click = AsyncMock()

        self.executor._capture_three_hk_plan_tab_snapshot = AsyncMock(return_value={"tab_key": "voucher", "signature": ("url", False, ())})
        self.executor._find_three_hk_plan_tab_locator = AsyncMock(return_value=(locator, "Voucher Monthly Plan", "text"))

        async def mock_spinner_settle(p):
            call_order.append("spinner")

        async def mock_ensure(p, instr, url, before):
            call_order.append("ensure")

        self.executor._wait_for_spa_spinner_settle = mock_spinner_settle
        self.executor._ensure_three_hk_plan_tab_click_progressed = mock_ensure

        with patch("app.services.tier2_hybrid.wait_for_post_click_readiness", AsyncMock(return_value={})):
            await self.executor._try_three_hk_plan_tab_click(page, "Click voucher monthly plan tab.")

        assert call_order == ["spinner", "ensure"], (
            f"Expected spinner before ensure, got: {call_order}"
        )

    @pytest.mark.asyncio
    async def test_spinner_settle_waits_for_spinner_appear_then_hide(self):
        """_wait_for_spa_spinner_settle probes for spinner then waits for it to be hidden."""
        page = MagicMock()

        spinner_locator = AsyncMock()
        spinner_locator.count = AsyncMock(return_value=1)   # spinner IS visible
        spinner_locator.wait_for = AsyncMock(return_value=None)  # hidden successfully

        page.locator = MagicMock(return_value=spinner_locator)

        await self.executor._wait_for_spa_spinner_settle(page)

        # Should have checked for spinner presence
        page.locator.assert_called_with("div[role='status'].spinner-border, [role='status'].spinner-border")
        # Should have waited for it to become hidden
        spinner_locator.wait_for.assert_awaited_once_with(state="hidden", timeout=ANY)

    @pytest.mark.asyncio
    async def test_spinner_settle_is_noop_when_no_spinner_present(self):
        """_wait_for_spa_spinner_settle returns quickly when spinner never mounts."""
        page = MagicMock()

        spinner_locator = AsyncMock()
        spinner_locator.count = AsyncMock(return_value=0)   # no spinner
        spinner_locator.wait_for = AsyncMock()

        page.locator = MagicMock(return_value=spinner_locator)

        await self.executor._wait_for_spa_spinner_settle(page)

        spinner_locator.wait_for.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_spinner_settle_in_retry_path(self):
        """_ensure_three_hk_plan_tab_click_progressed calls spinner settle before each retry check."""
        call_order = []

        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        # First transition check fails → spinner → retry → second check passes
        self.executor._wait_for_three_hk_plan_tab_transition = AsyncMock(side_effect=[False, True])
        self.executor._retry_three_hk_plan_tab_click = AsyncMock(return_value=True)

        async def mock_spinner(p):
            call_order.append("spinner")

        self.executor._wait_for_spa_spinner_settle = mock_spinner

        with patch("app.services.tier2_hybrid.auto_dismiss_blocking_modals", AsyncMock(return_value=False)):
            await self.executor._ensure_three_hk_plan_tab_click_progressed(
                page=page,
                instruction="Click voucher monthly plan tab.",
                current_url=page.url,
            )

        # Spinner settle must have been called before the retry verification
        assert "spinner" in call_order


class TestPostSettleTabRecheck:
    """RC2: after ADR-002-23 step-boundary spinner clears, execute_step must re-verify
    that the previously-clicked Three HK tab is still selected (not silently reverted)."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    # ------------------------------------------------------------------ #
    # _pending_three_hk_tab_key state management                         #
    # ------------------------------------------------------------------ #

    def test_executor_initialises_with_no_pending_tab_key(self):
        """_pending_three_hk_tab_key must be None on a fresh executor."""
        assert self.executor._pending_three_hk_tab_key is None

    @pytest.mark.asyncio
    async def test_try_tab_click_sets_pending_key_on_success(self):
        """_try_three_hk_plan_tab_click must set _pending_three_hk_tab_key after success."""
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        locator = AsyncMock()
        locator.wait_for = AsyncMock()
        locator.click = AsyncMock()

        self.executor._capture_three_hk_plan_tab_snapshot = AsyncMock(
            return_value={"tab_key": "voucher", "signature": ("url", False, ())}
        )
        self.executor._find_three_hk_plan_tab_locator = AsyncMock(
            return_value=(locator, "Voucher Monthly Plan", "text")
        )
        self.executor._wait_for_spa_spinner_settle = AsyncMock()
        self.executor._ensure_three_hk_plan_tab_click_progressed = AsyncMock()

        with patch("app.services.tier2_hybrid.wait_for_post_click_readiness", AsyncMock(return_value={})):
            await self.executor._try_three_hk_plan_tab_click(
                page, "Click voucher monthly plan tab."
            )

        # _extract_three_hk_plan_tab_key("Click voucher monthly plan tab.") returns
        # the full key string (e.g. "voucher monthly plan"), not just "voucher".
        assert self.executor._pending_three_hk_tab_key is not None
        assert "voucher" in self.executor._pending_three_hk_tab_key

    # ------------------------------------------------------------------ #
    # _verify_and_clear_pending_tab_check                                 #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_verify_and_clear_pending_tab_check_is_noop_when_no_pending_key(self):
        """No pending key → method returns without raising or calling any locator."""
        page = MagicMock()
        self.executor._pending_three_hk_tab_key = None
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)

        # Should not raise and should not touch is_three_hk_plan_tab_selected
        await self.executor._verify_and_clear_pending_tab_check(page)

        self.executor._is_three_hk_plan_tab_selected.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_verify_and_clear_passes_and_clears_when_tab_still_selected(self):
        """Tab is still selected after spinner-settle → method clears key, no error."""
        page = MagicMock()
        self.executor._pending_three_hk_tab_key = "voucher"
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=True)

        await self.executor._verify_and_clear_pending_tab_check(page)

        assert self.executor._pending_three_hk_tab_key is None

    @pytest.mark.asyncio
    async def test_verify_and_clear_raises_when_tab_has_reverted(self):
        """Tab reverted after spinner-settle AND recovery locator not found → ValueError raised."""
        page = MagicMock()
        self.executor._pending_three_hk_tab_key = "voucher"
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)
        # Explicit: recovery re-click also cannot find the locator
        self.executor._recovery_click_three_hk_tab = AsyncMock(return_value=False)

        with pytest.raises(ValueError, match="reverted"):
            await self.executor._verify_and_clear_pending_tab_check(page)

        assert self.executor._pending_three_hk_tab_key is None

    # ------------------------------------------------------------------ #
    # execute_step integration                                            #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_execute_step_calls_pending_tab_check_before_processing_step(self):
        """execute_step must call _verify_and_clear_pending_tab_check before any tier logic."""
        call_order = []

        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._pending_three_hk_tab_key = "voucher"

        async def mock_verify(p):
            call_order.append("tab_recheck")
            self.executor._pending_three_hk_tab_key = None

        self.executor._verify_and_clear_pending_tab_check = mock_verify
        self.executor._is_three_hk_plan_tab_click = MagicMock(return_value=False)
        # Cache miss so execution falls through; side_effect records the call
        self.executor.cache_service.get_cached_xpath = MagicMock(
            side_effect=lambda *a, **kw: call_order.append("cache") or None
        )

        # execute_step catches all exceptions and returns {"success": False} —
        # it never re-raises. Just call it and inspect call_order.
        await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": "Step 7: Select the '$288/month' plan from the available plans",
            },
        )

        assert "tab_recheck" in call_order, (
            f"tab_recheck must have run, got order: {call_order}"
        )
        # tab_recheck must precede cache lookup when both occurred
        if "cache" in call_order:
            assert call_order.index("tab_recheck") < call_order.index("cache"), (
                f"tab_recheck must precede cache lookup, got order: {call_order}"
            )

class TestPostSettleTabRecheckRecovery:
    """RC3: when _verify_and_clear_pending_tab_check detects a revert it must
    attempt a recovery re-click via _recovery_click_three_hk_tab before failing.
    """

    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30_000,
        )

    # ------------------------------------------------------------------ #
    # _recovery_click_three_hk_tab                                       #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_recovery_returns_true_when_tab_selected_after_reclick(self):
        """Locator found, click succeeds, post-click check returns True → True."""
        page = MagicMock()
        locator = AsyncMock()
        locator.click = AsyncMock()

        self.executor._find_three_hk_plan_tab_locator = AsyncMock(
            return_value=(locator, "Voucher Monthly Plan", "text")
        )
        self.executor._wait_for_spa_spinner_settle = AsyncMock()
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=True)

        result = await self.executor._recovery_click_three_hk_tab(page, "voucher monthly plan")

        assert result is True
        locator.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_recovery_returns_false_when_tab_still_not_selected_after_reclick(self):
        """Locator found, click succeeds, but tab still not selected → False."""
        page = MagicMock()
        locator = AsyncMock()
        locator.click = AsyncMock()

        self.executor._find_three_hk_plan_tab_locator = AsyncMock(
            return_value=(locator, "Voucher Monthly Plan", "text")
        )
        self.executor._wait_for_spa_spinner_settle = AsyncMock()
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)

        result = await self.executor._recovery_click_three_hk_tab(page, "voucher monthly plan")

        assert result is False

    @pytest.mark.asyncio
    async def test_recovery_returns_false_when_locator_not_found(self):
        """When the tab locator cannot be found, return False without clicking."""
        page = MagicMock()
        self.executor._find_three_hk_plan_tab_locator = AsyncMock(
            return_value=(None, "Voucher Monthly Plan", None)
        )
        self.executor._wait_for_spa_spinner_settle = AsyncMock()
        self.executor._is_three_hk_plan_tab_selected = AsyncMock()

        result = await self.executor._recovery_click_three_hk_tab(page, "voucher monthly plan")

        assert result is False
        self.executor._is_three_hk_plan_tab_selected.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_recovery_returns_false_when_click_raises(self):
        """If click() throws, swallow exception and return False."""
        page = MagicMock()
        locator = AsyncMock()
        locator.click = AsyncMock(side_effect=RuntimeError("timeout"))

        self.executor._find_three_hk_plan_tab_locator = AsyncMock(
            return_value=(locator, "Voucher Monthly Plan", "text")
        )
        self.executor._wait_for_spa_spinner_settle = AsyncMock()
        self.executor._is_three_hk_plan_tab_selected = AsyncMock()

        result = await self.executor._recovery_click_three_hk_tab(page, "voucher monthly plan")

        assert result is False
        self.executor._is_three_hk_plan_tab_selected.assert_not_awaited()

    # ------------------------------------------------------------------ #
    # _verify_and_clear_pending_tab_check with recovery                  #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_verify_calls_recovery_reclick_when_tab_reverted_and_succeeds(self):
        """Tab reverted but recovery re-click succeeds → no ValueError, key cleared."""
        page = MagicMock()
        self.executor._pending_three_hk_tab_key = "voucher monthly plan"
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)
        self.executor._recovery_click_three_hk_tab = AsyncMock(return_value=True)

        # Must NOT raise
        await self.executor._verify_and_clear_pending_tab_check(page)

        assert self.executor._pending_three_hk_tab_key is None
        self.executor._recovery_click_three_hk_tab.assert_awaited_once_with(
            page, "voucher monthly plan"
        )

    @pytest.mark.asyncio
    async def test_verify_raises_when_recovery_reclick_also_fails(self):
        """Tab reverted AND recovery re-click returns False → ValueError raised."""
        page = MagicMock()
        self.executor._pending_three_hk_tab_key = "voucher monthly plan"
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)
        self.executor._recovery_click_three_hk_tab = AsyncMock(return_value=False)

        with pytest.raises(ValueError, match="reverted"):
            await self.executor._verify_and_clear_pending_tab_check(page)

        assert self.executor._pending_three_hk_tab_key is None

    @pytest.mark.asyncio
    async def test_verify_does_not_call_recovery_when_tab_still_selected(self):
        """Tab is still selected → recovery re-click must NOT be called."""
        page = MagicMock()
        self.executor._pending_three_hk_tab_key = "voucher monthly plan"
        self.executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=True)
        self.executor._recovery_click_three_hk_tab = AsyncMock(return_value=True)

        await self.executor._verify_and_clear_pending_tab_check(page)

        self.executor._recovery_click_three_hk_tab.assert_not_awaited()


# ======================================================================== #
# Checkbox state verification and Subscribe Now disabled-button fast-fail  #
# ======================================================================== #

class TestCheckboxStateVerification:
    """Tests for RC1 (observe retry for check), RC2 (post-check is_checked),
    and RC3 (Subscribe Now disabled fast-fail) from execution #683."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    # ------------------------------------------------------------------ #
    # RC1: observe() retry for check action                               #
    # ------------------------------------------------------------------ #

    def test_should_retry_observe_for_check_action_with_no_results(self):
        """observe() returning no results for a check action should trigger retry."""
        result = self.executor._should_retry_observe_extraction(
            extraction_result={"success": False, "error": "observe() returned no results for: Check the T&C checkbox"},
            action="check",
            selector=None,
            instruction="Check the 'T&C' checkbox to agree to the terms and conditions",
        )
        assert result is True

    def test_should_not_retry_observe_for_check_action_when_success(self):
        """No retry when extraction already succeeded for a check action."""
        result = self.executor._should_retry_observe_extraction(
            extraction_result={"success": True, "xpath": "//input[@type='checkbox']"},
            action="check",
            selector=None,
            instruction="Check the 'T&C' checkbox",
        )
        assert result is False

    def test_should_not_retry_observe_for_check_action_with_selector(self):
        """No retry when a selector is already provided (selector bypasses observe)."""
        result = self.executor._should_retry_observe_extraction(
            extraction_result={"success": False, "error": "observe() returned no results"},
            action="check",
            selector="//input[@type='checkbox']",
            instruction="Check the 'T&C' checkbox",
        )
        assert result is False

    def test_should_not_retry_observe_for_uncheck_action_with_no_results(self):
        """Uncheck action does NOT get the observe retry (only check does)."""
        result = self.executor._should_retry_observe_extraction(
            extraction_result={"success": False, "error": "observe() returned no results"},
            action="uncheck",
            selector=None,
            instruction="Uncheck the newsletter checkbox",
        )
        assert result is False

    # ------------------------------------------------------------------ #
    # RC2: post-check is_checked() validation                             #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_check_action_raises_when_still_unchecked_after_element_check(self):
        """After element.check() succeeds, if is_checked() is False, raise ValueError."""
        page = MagicMock()
        element = AsyncMock()
        element.wait_for = AsyncMock()
        element.is_checked = AsyncMock(side_effect=[False, False])  # before + after check()
        element.check = AsyncMock()
        page.locator.return_value.first = element

        with pytest.raises(ValueError, match="still unchecked"):
            await self.executor._execute_action_with_xpath(
                page=page,
                xpath="//input[@type='checkbox']",
                action="check",
                value=None,
                instruction="Check the T&C checkbox",
            )

    @pytest.mark.asyncio
    async def test_check_action_passes_when_is_checked_after_element_check(self):
        """After element.check(), is_checked() returns True → no exception."""
        page = MagicMock()
        element = AsyncMock()
        element.wait_for = AsyncMock()
        element.is_checked = AsyncMock(side_effect=[False, True])  # not checked, then checked
        element.check = AsyncMock()
        page.locator.return_value.first = element

        # Should complete without exception
        await self.executor._execute_action_with_xpath(
            page=page,
            xpath="//input[@type='checkbox']",
            action="check",
            value=None,
            instruction="Check the T&C checkbox",
        )
        element.check.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_action_skips_element_check_when_already_checked(self):
        """If element.is_checked() is True initially, element.check() is never called."""
        page = MagicMock()
        element = AsyncMock()
        element.wait_for = AsyncMock()
        element.is_checked = AsyncMock(return_value=True)
        element.check = AsyncMock()
        page.locator.return_value.first = element

        await self.executor._execute_action_with_xpath(
            page=page,
            xpath="//input[@type='checkbox']",
            action="check",
            value=None,
            instruction="Check the T&C checkbox",
        )
        element.check.assert_not_awaited()

    # ------------------------------------------------------------------ #
    # RC3: Subscribe Now disabled-button fast-fail                        #
    # ------------------------------------------------------------------ #

    @pytest.mark.asyncio
    async def test_subscribe_now_button_disabled_raises_value_error(self):
        """When 'Subscribe Now' button stays disabled, raise ValueError immediately."""
        element = AsyncMock()
        element.is_enabled = AsyncMock(return_value=False)

        with pytest.raises(ValueError, match="Subscribe Now"):
            await self.executor._wait_for_element_enabled_before_click(
                element=element,
                instruction="Step 12: Click the 'Subscribe Now' button to initiate the subscription process",
            )

    @pytest.mark.asyncio
    async def test_subscribe_now_button_enabled_no_raise(self):
        """When 'Subscribe Now' button is enabled from the start, no exception."""
        element = AsyncMock()
        element.is_enabled = AsyncMock(return_value=True)

        # Should not raise
        await self.executor._wait_for_element_enabled_before_click(
            element=element,
            instruction="Step 12: Click the 'Subscribe Now' button",
        )

    @pytest.mark.asyncio
    async def test_other_button_disabled_only_logs_warning_not_raises(self):
        """Other disabled buttons (not Subscribe Now) still just log warning, not raise."""
        element = AsyncMock()
        element.is_enabled = AsyncMock(return_value=False)

        # Should NOT raise — legacy behaviour preserved for non-Subscribe-Now buttons
        await self.executor._wait_for_element_enabled_before_click(
            element=element,
            instruction="Click the Next button to continue",
        )


class TestThreeHkObserveReadiness:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    def test_extract_hpprm_code_from_plan_instruction(self):
        assert self.executor._extract_hpprm_code(
            'Click "HPPRM0000002896" with $238/30 month plan'
        ) == "HPPRM0000002896"

    def test_should_wait_for_three_hk_observe_readiness_for_hpprm_click(self):
        assert self.executor._should_wait_for_three_hk_observe_readiness(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
            action="click",
        ) is True

    def test_should_wait_for_three_hk_observe_readiness_for_moneyback_panel(self):
        assert self.executor._should_wait_for_three_hk_observe_readiness(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction='Click "Moneyback point" panel',
            action="click",
        ) is True

    def test_should_not_wait_for_three_hk_observe_readiness_on_non_uat_url(self):
        assert self.executor._should_wait_for_three_hk_observe_readiness(
            page_url="https://example.com/plans",
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
            action="click",
        ) is False

    def test_should_wait_for_three_hk_observe_readiness_when_page_identity_matches(self):
        assert self.executor._should_wait_for_three_hk_observe_readiness(
            page_url="https://example.com/plans",
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
            action="click",
            looks_like_three_hk_promotion_page=True,
        ) is True

    @pytest.mark.asyncio
    async def test_looks_like_three_hk_promotion_page_true_for_footer_marker_on_non_uat_host(self):
        page = MagicMock()
        page.url = "https://example.com/embedded-checkout"
        page.title = AsyncMock(return_value="Embedded Checkout")

        footer_locator = MagicMock()
        footer_locator.count = AsyncMock(return_value=1)

        hpprm_locator = MagicMock()
        hpprm_locator.count = AsyncMock(return_value=0)

        empty_text_locator = MagicMock()
        empty_text_locator.count = AsyncMock(return_value=0)

        def locator_side_effect(selector):
            if selector == "app-new-card-footer":
                return footer_locator
            if selector == "text=/HPPRM\\d+/i":
                return hpprm_locator
            raise AssertionError(f"Unexpected locator selector: {selector}")

        page.locator = MagicMock(side_effect=locator_side_effect)
        page.get_by_text = MagicMock(return_value=empty_text_locator)

        assert await self.executor._looks_like_three_hk_promotion_page(
            page,
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
        ) is True

    @pytest.mark.asyncio
    async def test_wait_for_three_hk_promotion_catalog_ready_waits_for_hpprm(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        loading_locator = MagicMock()
        loading_locator.count = AsyncMock(return_value=0)

        hpprm_locator = MagicMock()
        hpprm_locator.first = MagicMock()
        hpprm_locator.first.wait_for = AsyncMock()

        def get_by_text_side_effect(text, exact=False):
            if "Loading promotions" in text:
                return loading_locator
            if text == "HPPRM0000002896":
                return hpprm_locator
            return MagicMock()

        page.get_by_text = MagicMock(side_effect=get_by_text_side_effect)

        await self.executor._wait_for_three_hk_promotion_catalog_ready(
            page,
            'Click "HPPRM0000002896" with $238/30 month plan',
        )

        hpprm_locator.first.wait_for.assert_awaited_once_with(
            state="visible",
            timeout=15000,
        )

    @pytest.mark.asyncio
    async def test_wait_for_page_interactable_for_observe_calls_catalog_wait(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"
        page.wait_for_load_state = AsyncMock()

        self.executor._wait_for_three_hk_promotion_catalog_ready = AsyncMock()

        await self.executor._wait_for_page_interactable_for_observe(
            page,
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
        )

        self.executor._wait_for_three_hk_promotion_catalog_ready.assert_awaited_once_with(
            page,
            'Click "HPPRM0000002896" with $238/30 month plan',
        )

    @pytest.mark.asyncio
    async def test_wait_for_page_interactable_for_observe_calls_catalog_wait_when_dom_identified(self):
        page = MagicMock()
        page.url = "https://example.com/embedded-checkout"
        page.wait_for_load_state = AsyncMock()

        self.executor._looks_like_three_hk_promotion_page = AsyncMock(return_value=True)
        self.executor._wait_for_three_hk_promotion_catalog_ready = AsyncMock()

        await self.executor._wait_for_page_interactable_for_observe(
            page,
            instruction='Click "Moneyback point" panel',
        )

        self.executor._wait_for_three_hk_promotion_catalog_ready.assert_awaited_once_with(
            page,
            'Click "Moneyback point" panel',
        )


class TestThreeHkPromotionCardDirectClick:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    def test_is_three_hk_promotion_card_click_true_for_hpprm_step(self):
        assert self.executor._is_three_hk_promotion_card_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
            action="click",
        ) is True

    def test_is_three_hk_promotion_card_click_true_for_wifi7_price_step(self):
        assert self.executor._is_three_hk_promotion_card_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Click wifi7 plan $238/30 month plan",
            action="click",
        ) is True

    def test_is_three_hk_promotion_card_click_true_for_wifi6_price_step(self):
        assert self.executor._is_three_hk_promotion_card_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Click wi-fi6 plan $198/30 month plan",
            action="click",
        ) is True

    def test_is_three_hk_promotion_card_click_true_for_price_only_plan_step(self):
        """Regression: price-only steps must not be blocked by empty text-variant extraction."""
        assert self.executor._is_three_hk_promotion_card_click(
            page_url="https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en",
            instruction="Click $228 / 36 month plan",
            action="click",
        ) is True

    def test_three_hk_footer_shows_empty_cart(self):
        assert self.executor._three_hk_footer_shows_empty_cart("$ 0") is True
        assert self.executor._three_hk_footer_shows_empty_cart("$0") is True
        assert self.executor._three_hk_footer_shows_empty_cart("$ 238") is False

    @pytest.mark.asyncio
    async def test_verify_promotion_card_rejects_stale_pagewide_success_on_plan_switch(self):
        page = MagicMock()
        card_locator = AsyncMock()
        card_locator.evaluate = AsyncMock(
            return_value={
                "selected": False,
                "snippet": "HPPRM0000002896 5G Broadband Wi-Fi 7 Service Plan",
            }
        )

        moneyback_locator = MagicMock()
        moneyback_locator.count = AsyncMock(return_value=1)
        moneyback_locator.first = AsyncMock()
        moneyback_locator.first.is_visible = AsyncMock(return_value=True)

        promotion_error = MagicMock()
        promotion_error.count = AsyncMock(return_value=0)

        def get_by_text_side_effect(text, exact=False):
            if text == "Moneyback":
                return moneyback_locator
            if text == "Please select a promotion":
                return promotion_error
            raise AssertionError(f"Unexpected text lookup: {text}")

        page.get_by_text = MagicMock(side_effect=get_by_text_side_effect)
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")

        assert not await self.executor._verify_three_hk_promotion_card_selected(
            page,
            'Click "HPPRM0000002896" with $238/30 month plan',
            card_locator=card_locator,
            before_footer_text="$ 238",
        )

    @pytest.mark.asyncio
    async def test_verify_promotion_card_accepts_local_selected_state_for_same_price_switch(self):
        page = MagicMock()
        card_locator = AsyncMock()
        card_locator.evaluate = AsyncMock(
            return_value={
                "selected": True,
                "snippet": "HPPRM0000002896 5G Broadband Wi-Fi 7 Service Plan active",
            }
        )

        page.get_by_text = MagicMock(side_effect=AssertionError("page-wide fallback should not run"))
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")

        assert await self.executor._verify_three_hk_promotion_card_selected(
            page,
            'Click "HPPRM0000002896" with $238/30 month plan',
            card_locator=card_locator,
            before_footer_text="$ 238",
        )

    @pytest.mark.asyncio
    async def test_verify_promotion_card_accepts_wifi7_local_selected_state_without_hpprm(self):
        page = MagicMock()
        card_locator = AsyncMock()
        card_locator.evaluate = AsyncMock(
            return_value={
                "selected": True,
                "snippet": "5G Broadband Wi-Fi 7 Service Plan active $238/30 month",
            }
        )

        page.get_by_text = MagicMock(side_effect=AssertionError("page-wide fallback should not run"))
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")

        assert await self.executor._verify_three_hk_promotion_card_selected(
            page,
            "Click wifi7 plan $238/30 month plan",
            card_locator=card_locator,
            before_footer_text="$ 238",
        )

    @pytest.mark.asyncio
    async def test_verify_promotion_card_accepts_wifi6_local_selected_state_without_hpprm(self):
        page = MagicMock()
        card_locator = AsyncMock()
        card_locator.evaluate = AsyncMock(
            return_value={
                "selected": True,
                "snippet": "5G Broadband Wi-Fi 6 Service Plan active $198/30 month",
            }
        )

        page.get_by_text = MagicMock(side_effect=AssertionError("page-wide fallback should not run"))
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 198")

        assert await self.executor._verify_three_hk_promotion_card_selected(
            page,
            "Click wi-fi6 plan $198/30 month plan",
            card_locator=card_locator,
            before_footer_text="$ 198",
        )

    @pytest.mark.asyncio
    async def test_verify_promotion_card_accepts_first_selection_when_cart_changes_from_empty(self):
        page = MagicMock()
        card_locator = AsyncMock()
        card_locator.evaluate = AsyncMock(
            return_value={
                "selected": False,
                "snippet": "HPPRM0000002896 5G Broadband Wi-Fi 7 Service Plan",
            }
        )

        moneyback_locator = MagicMock()
        moneyback_locator.count = AsyncMock(return_value=0)

        promotion_error = MagicMock()
        promotion_error.count = AsyncMock(return_value=0)

        def get_by_text_side_effect(text, exact=False):
            if text == "Moneyback":
                return moneyback_locator
            if text == "Please select a promotion":
                return promotion_error
            raise AssertionError(f"Unexpected text lookup: {text}")

        page.get_by_text = MagicMock(side_effect=get_by_text_side_effect)
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")

        assert await self.executor._verify_three_hk_promotion_card_selected(
            page,
            'Click "HPPRM0000002896" with $238/30 month plan',
            card_locator=card_locator,
            before_footer_text="$ 0",
        )

    @pytest.mark.asyncio
    async def test_execute_step_uses_direct_promotion_helper_before_xpath_cache(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._try_three_hk_promotion_card_click = AsyncMock(
            return_value={
                "success": True,
                "tier": 2,
                "execution_time_ms": 150.0,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }
        )
        self.executor.cache_service.get_cached_xpath = MagicMock(
            side_effect=AssertionError("cache should be bypassed")
        )

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": 'Click "HPPRM0000002896" with $238/30 month plan',
            },
        )

        assert result["success"] is True
        self.executor._try_three_hk_promotion_card_click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_try_promotion_card_click_returns_success_when_first_verification_passes(self):
        page = MagicMock()
        page.url = "https://example.com/embedded-checkout"

        locator = AsyncMock()
        locator.click = AsyncMock(return_value=None)

        self.executor._find_three_hk_promotion_card_locator = AsyncMock(
            return_value=(locator, "text=HPPRM0000002896")
        )
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")
        self.executor._wait_for_spa_spinner_settle = AsyncMock(return_value=None)
        self.executor._verify_three_hk_promotion_card_selected = AsyncMock(return_value=True)

        with patch(
            "app.services.tier2_hybrid.wait_for_post_click_readiness",
            AsyncMock(return_value={}),
        ), patch(
            "app.services.tier2_hybrid.auto_dismiss_blocking_modals",
            AsyncMock(return_value=False),
        ) as dismiss_mock:
            result = await self.executor._try_three_hk_promotion_card_click(
                page,
                'Click "HPPRM0000002896" with $238/30 month plan',
            )

        assert result["success"] is True
        locator.click.assert_awaited_once()
        dismiss_mock.assert_not_awaited()
        self.executor._verify_three_hk_promotion_card_selected.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_find_promotion_card_locator_matches_wifi7_price_without_hpprm(self):
        page = MagicMock()

        wifi7_locator = AsyncMock()
        wifi7_locator.wait_for = AsyncMock(return_value=None)
        wifi7_locator.evaluate = AsyncMock(
            return_value="5G Broadband Wi-Fi 7 Service Plan $238/30 month"
        )
        wifi7_locator.locator = MagicMock(
            return_value=MagicMock(first=MagicMock(count=AsyncMock(return_value=0)))
        )

        matches = MagicMock()
        matches.count = AsyncMock(return_value=1)
        matches.nth = MagicMock(return_value=wifi7_locator)

        empty_locator = AsyncMock()
        empty_locator.wait_for = AsyncMock(side_effect=TimeoutError("not visible"))

        def locator_side_effect(selector):
            if "wi-fi 7" in selector and "$238" in selector:
                return matches
            match = MagicMock()
            match.first = empty_locator
            return match

        page.locator = MagicMock(side_effect=locator_side_effect)
        page.get_by_text = MagicMock(side_effect=AssertionError("xpath lookup should succeed first"))

        self.executor._wait_for_three_hk_promotion_catalog_ready = AsyncMock(return_value=None)
        self.executor._wait_for_spa_spinner_settle = AsyncMock(return_value=None)

        locator, strategy = await self.executor._find_three_hk_promotion_card_locator(
            page,
            "Click wifi7 plan $238/30 month plan",
        )

        assert locator is wifi7_locator
        assert "wi-fi 7" in strategy
        assert "$238" in strategy

    @pytest.mark.asyncio
    async def test_find_promotion_card_locator_matches_wifi6_price_without_hpprm(self):
        page = MagicMock()

        wifi6_locator = AsyncMock()
        wifi6_locator.wait_for = AsyncMock(return_value=None)
        wifi6_locator.evaluate = AsyncMock(
            return_value="5G Broadband Wi-Fi 6 Service Plan $198/30 month"
        )
        wifi6_locator.locator = MagicMock(
            return_value=MagicMock(first=MagicMock(count=AsyncMock(return_value=0)))
        )

        matches = MagicMock()
        matches.count = AsyncMock(return_value=1)
        matches.nth = MagicMock(return_value=wifi6_locator)

        empty_locator = AsyncMock()
        empty_locator.wait_for = AsyncMock(side_effect=TimeoutError("not visible"))

        def locator_side_effect(selector):
            if "wi-fi 6" in selector and "$198" in selector:
                return matches
            match = MagicMock()
            match.first = empty_locator
            return match

        page.locator = MagicMock(side_effect=locator_side_effect)
        page.get_by_text = MagicMock(side_effect=AssertionError("xpath lookup should succeed first"))

        self.executor._wait_for_three_hk_promotion_catalog_ready = AsyncMock(return_value=None)
        self.executor._wait_for_spa_spinner_settle = AsyncMock(return_value=None)

        locator, strategy = await self.executor._find_three_hk_promotion_card_locator(
            page,
            "Click wi-fi6 plan $198/30 month plan",
        )

        assert locator is wifi6_locator
        assert "wi-fi 6" in strategy
        assert "$198" in strategy

    @pytest.mark.asyncio
    async def test_find_promotion_card_locator_rejects_shared_parent_with_wifi7_for_wifi6(self):
        page = MagicMock()

        shared_parent_locator = AsyncMock()
        shared_parent_locator.wait_for = AsyncMock(return_value=None)
        shared_parent_locator.evaluate = AsyncMock(
            return_value=(
                "Featured Monthly Plans Wi-Fi 6 $198/30 month "
                "Wi-Fi 7 $238/30 month"
            )
        )
        shared_parent_locator.locator = MagicMock(
            return_value=MagicMock(first=MagicMock(count=AsyncMock(return_value=0)))
        )

        wifi6_card_locator = AsyncMock()
        wifi6_card_locator.wait_for = AsyncMock(return_value=None)
        wifi6_card_locator.evaluate = AsyncMock(
            return_value="5G Broadband Wi-Fi 6 Service Plan $198/30 month"
        )
        wifi6_card_locator.locator = MagicMock(
            return_value=MagicMock(first=MagicMock(count=AsyncMock(return_value=0)))
        )

        matches = MagicMock()
        matches.count = AsyncMock(return_value=2)
        matches.nth = MagicMock(side_effect=[shared_parent_locator, wifi6_card_locator])

        def locator_side_effect(selector):
            if "wi-fi 6" in selector and "$198" in selector:
                return matches
            return MagicMock(first=AsyncMock(wait_for=AsyncMock(side_effect=TimeoutError())))

        page.locator = MagicMock(side_effect=locator_side_effect)
        page.get_by_text = MagicMock(side_effect=AssertionError("xpath lookup should succeed first"))

        self.executor._wait_for_three_hk_promotion_catalog_ready = AsyncMock(return_value=None)
        self.executor._wait_for_spa_spinner_settle = AsyncMock(return_value=None)

        locator, strategy = await self.executor._find_three_hk_promotion_card_locator(
            page,
            "Click wi-fi6 plan $198/30 month plan",
        )

        assert locator is wifi6_card_locator
        assert "wi-fi 6" in strategy

    @pytest.mark.asyncio
    async def test_verify_promotion_card_rejects_wifi7_snippet_for_wifi6_with_empty_cart_signals(self):
        page = MagicMock()
        card_locator = AsyncMock()
        card_locator.evaluate = AsyncMock(
            return_value={
                "selected": False,
                "snippet": "5G Broadband Wi-Fi 7 Service Plan $238/30 month",
            }
        )

        moneyback_locator = MagicMock()
        moneyback_locator.count = AsyncMock(return_value=1)
        moneyback_locator.first = AsyncMock()
        moneyback_locator.first.is_visible = AsyncMock(return_value=True)

        promotion_error = MagicMock()
        promotion_error.count = AsyncMock(return_value=0)

        def get_by_text_side_effect(text, exact=False):
            if text == "Moneyback":
                return moneyback_locator
            if text == "Please select a promotion":
                return promotion_error
            raise AssertionError(f"Unexpected text lookup: {text}")

        page.get_by_text = MagicMock(side_effect=get_by_text_side_effect)
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")

        assert not await self.executor._verify_three_hk_promotion_card_selected(
            page,
            "Click wi-fi6 plan $198/30 month plan",
            card_locator=card_locator,
            before_footer_text="$ 0",
        )

    def test_instruction_matches_rejects_snippet_with_both_wifi_families_for_wifi6(self):
        assert not self.executor._instruction_matches_three_hk_promotion_snippet(
            "Click wi-fi6 plan $198/30 month plan",
            "Featured Plans Wi-Fi 6 $198 Wi-Fi 7 $238",
        )

    def test_snippet_has_contradictory_wifi_family_detects_wifi7_for_wifi6_step(self):
        assert self.executor._snippet_has_contradictory_wifi_family(
            "Click wi-fi6 plan $198/30 month plan",
            "5G Broadband Wi-Fi 7 Service Plan",
        )

    @pytest.mark.asyncio
    async def test_validate_cached_xpath_rejects_wifi7_element_for_wifi6_instruction(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        locator = AsyncMock()
        locator.wait_for = AsyncMock(return_value=None)
        locator.inner_text = AsyncMock(
            return_value="5G Broadband Wi-Fi 7 Service Plan $238/30 month"
        )
        page.locator = MagicMock(return_value=MagicMock(first=locator))

        is_valid = await self.executor._validate_cached_xpath_for_step(
            page=page,
            xpath="//div[contains(., 'Wi-Fi 7')]",
            action="click",
            instruction="Click wi-fi6 plan $198/30 month plan",
            value=None,
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_cached_xpath_accepts_wifi6_element_for_wifi6_instruction(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        locator = AsyncMock()
        locator.wait_for = AsyncMock(return_value=None)
        locator.inner_text = AsyncMock(
            return_value="5G Broadband Wi-Fi 6 Service Plan $198/30 month"
        )
        page.locator = MagicMock(return_value=MagicMock(first=locator))

        is_valid = await self.executor._validate_cached_xpath_for_step(
            page=page,
            xpath="//div[contains(., 'Wi-Fi 6')]",
            action="click",
            instruction="Click wi-fi6 plan $198/30 month plan",
            value=None,
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_execute_step_uses_direct_promotion_helper_on_dom_identified_non_uat_host(self):
        page = MagicMock()
        page.url = "https://example.com/embedded-checkout"

        self.executor._looks_like_three_hk_promotion_page = AsyncMock(return_value=True)
        self.executor._try_three_hk_promotion_card_click = AsyncMock(
            return_value={
                "success": True,
                "tier": 2,
                "execution_time_ms": 150.0,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }
        )
        self.executor.cache_service.get_cached_xpath = MagicMock(
            side_effect=AssertionError("cache should be bypassed")
        )

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": 'Click "HPPRM0000002896" with $238/30 month plan',
            },
        )

        assert result["success"] is True
        self.executor._looks_like_three_hk_promotion_page.assert_awaited_once_with(
            page,
            instruction='Click "HPPRM0000002896" with $238/30 month plan',
        )
        self.executor._try_three_hk_promotion_card_click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_step_uses_direct_promotion_helper_for_wifi7_price_step(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._try_three_hk_promotion_card_click = AsyncMock(
            return_value={
                "success": True,
                "tier": 2,
                "execution_time_ms": 150.0,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }
        )
        self.executor.cache_service.get_cached_xpath = MagicMock(
            side_effect=AssertionError("cache should be bypassed")
        )

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": "Click wifi7 plan $238/30 month plan",
            },
        )

        assert result["success"] is True
        self.executor._try_three_hk_promotion_card_click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_step_uses_direct_promotion_helper_for_wifi6_price_step(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"

        self.executor._try_three_hk_promotion_card_click = AsyncMock(
            return_value={
                "success": True,
                "tier": 2,
                "execution_time_ms": 150.0,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }
        )
        self.executor.cache_service.get_cached_xpath = MagicMock(
            side_effect=AssertionError("cache should be bypassed")
        )
        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock(
            side_effect=AssertionError("generic xpath extraction should be bypassed")
        )

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": "Click wi-fi6 plan $198/30 month plan",
            },
        )

        assert result["success"] is True
        self.executor._try_three_hk_promotion_card_click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_step_uses_direct_moneyback_helper_on_dom_identified_non_uat_host(self):
        page = MagicMock()
        page.url = "https://example.com/embedded-checkout"

        self.executor._looks_like_three_hk_promotion_page = AsyncMock(return_value=True)
        self.executor._try_three_hk_moneyback_panel_click = AsyncMock(
            return_value={
                "success": True,
                "tier": 2,
                "execution_time_ms": 120.0,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }
        )
        self.executor.cache_service.get_cached_xpath = MagicMock(
            side_effect=AssertionError("cache should be bypassed")
        )

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": 'Click "Moneyback point" panel',
            },
        )

        assert result["success"] is True
        self.executor._try_three_hk_moneyback_panel_click.assert_awaited_once()


class TestThreeHkMoneybackSectionScopedSelection:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(
            db=MagicMock(),
            xpath_extractor=MagicMock(),
            timeout_ms=30000,
        )

    def test_extract_three_hk_section_qualifier(self):
        assert (
            self.executor._extract_three_hk_section_qualifier(
                'Click "Moneyback point" panel under "Exclusion Promotion"'
            )
            == "Exclusion Promotion"
        )

    @pytest.mark.asyncio
    async def test_find_moneyback_locator_scopes_lookup_to_section(self):
        page = MagicMock()

        section_container = AsyncMock()
        section_container.wait_for = AsyncMock(return_value=None)
        section_container.inner_text = AsyncMock(
            return_value="Exclusion Promotion Moneyback point"
        )

        scoped_locator = AsyncMock()
        scoped_locator.wait_for = AsyncMock(return_value=None)

        scoped_text_match = MagicMock()
        scoped_text_match.first = scoped_locator
        section_container.get_by_text = MagicMock(return_value=scoped_text_match)

        section_match = MagicMock()
        section_match.first = section_container
        page.locator = MagicMock(return_value=section_match)
        page.get_by_text = MagicMock(
            side_effect=AssertionError("global lookup should not run")
        )

        self.executor._wait_for_spa_spinner_settle = AsyncMock(return_value=None)

        locator, label, strategy, section_label, container_snippet = (
            await self.executor._find_three_hk_moneyback_panel_locator(
                page,
                'Click "Moneyback point" panel under "Exclusion Promotion"',
            )
        )

        assert locator is scoped_locator
        assert label == "Moneyback point"
        assert strategy == "section-scoped"
        assert section_label == "Exclusion Promotion"
        assert container_snippet == "Exclusion Promotion Moneyback point"
        section_container.get_by_text.assert_called_with("Moneyback point", exact=False)
        page.get_by_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_moneyback_locator_refuses_global_fallback_when_scoped_lookup_fails(self):
        page = MagicMock()

        section_container = AsyncMock()
        section_container.wait_for = AsyncMock(return_value=None)
        section_container.inner_text = AsyncMock(return_value="Exclusion Promotion")

        missing_locator = AsyncMock()
        missing_locator.wait_for = AsyncMock(side_effect=RuntimeError("not visible"))

        scoped_text_match = MagicMock()
        scoped_text_match.first = missing_locator
        section_container.get_by_text = MagicMock(return_value=scoped_text_match)

        section_match = MagicMock()
        section_match.first = section_container
        page.locator = MagicMock(return_value=section_match)
        page.get_by_text = MagicMock(
            side_effect=AssertionError("global fallback should not run")
        )

        self.executor._wait_for_spa_spinner_settle = AsyncMock(return_value=None)

        locator, label, strategy, section_label, container_snippet = (
            await self.executor._find_three_hk_moneyback_panel_locator(
                page,
                'Click "Moneyback point" panel under "Exclusion Promotion"',
            )
        )

        assert locator is None
        assert label is None
        assert strategy == "section-scoped"
        assert section_label == "Exclusion Promotion"
        assert container_snippet == "Exclusion Promotion"
        page.get_by_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_moneyback_section_selection_requires_local_selected_state(self):
        page = MagicMock()

        panel_locator = AsyncMock()
        panel_locator.evaluate = AsyncMock(
            return_value={
                "selected": False,
                "snippet": "Exclusion Promotion Moneyback point",
            }
        )

        promotion_error = MagicMock()
        promotion_error.count = AsyncMock(return_value=0)
        page.get_by_text = MagicMock(return_value=promotion_error)

        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 238")

        assert not await self.executor._verify_three_hk_moneyback_panel_selected(
            page,
            panel_locator=panel_locator,
            section_label="Exclusion Promotion",
        )

    @pytest.mark.asyncio
    async def test_execute_step_blocks_checkout_when_cart_still_empty(self):
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 0")

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": "Click 'checkout' button",
            },
        )

        assert result["success"] is False
        assert "cart is still $0" in (result.get("error") or "")

    @pytest.mark.asyncio
    async def test_execute_step_blocks_checkout_when_cart_still_empty_on_dom_identified_non_uat_host(self):
        page = MagicMock()
        page.url = "https://example.com/embedded-checkout"

        self.executor._looks_like_three_hk_promotion_page = AsyncMock(return_value=True)
        self.executor._read_three_hk_footer_cart_text = AsyncMock(return_value="$ 0")

        result = await self.executor.execute_step(
            page=page,
            step={
                "action": "click",
                "instruction": "Click 'checkout' button",
            },
        )

        assert result["success"] is False
        assert "cart is still $0" in (result.get("error") or "")
