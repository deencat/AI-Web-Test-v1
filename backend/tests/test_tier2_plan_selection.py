"""Tests for Three HK preprod plan-selection recovery in Tier 2."""

import sys
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.tier2_hybrid import Tier2HybridExecutor


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
