"""Regression tests: ThreeTierExecutionService must apply spinner-settle and
tab-state verification after Tier 3 succeeds on a Three HK plan-tab click step.

Root cause identified in Execution #714 (Test Case 1079):
Tier 2 could not find the 'Greater China Pro Monthly Plan' tab locator because
the cross-category navigation had not yet hydrated the 4.5G tab row.  Tier 3
(Stagehand act()) took over and clicked the tab, but:
  1. No _wait_for_spa_spinner_settle was called.
  2. No _is_three_hk_plan_tab_selected check was performed.
  3. _pending_three_hk_tab_key was never set for the RC2 cross-step guard.
The SPA spinner reset the active tab to the default and the step was silently marked PASS.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.three_tier_execution_service import ThreeTierExecutionService
from app.services.tier2_hybrid import Tier2HybridExecutor

THREE_HK_UAT_URL = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"


def _make_service() -> ThreeTierExecutionService:
    page = MagicMock()
    page.url = THREE_HK_UAT_URL
    svc = ThreeTierExecutionService(
        db=MagicMock(),
        page=page,
    )
    return svc


def _make_tier2_executor() -> Tier2HybridExecutor:
    return Tier2HybridExecutor(
        db=MagicMock(),
        xpath_extractor=MagicMock(),
        timeout_ms=30_000,
    )


class TestApplyTabVerificationAfterTier3:
    """_apply_tab_verification_after_tier3 must run spinner-settle and tab-state
    check after Tier 3 succeeds on a Three HK plan-tab step."""

    def setup_method(self):
        self.svc = _make_service()
        executor = _make_tier2_executor()
        self.svc.tier2_executor = executor

    @pytest.mark.asyncio
    async def test_noop_for_non_tab_step(self):
        """Non-tab steps must not trigger spinner-settle or tab-state check."""
        self.svc.tier2_executor._wait_for_spa_spinner_settle = AsyncMock()
        tier3_result = {"success": True, "tier": 3}

        await self.svc._apply_tab_verification_after_tier3(
            step={"action": "click", "instruction": "Click the Next button"},
            tier3_result=tier3_result,
        )

        self.svc.tier2_executor._wait_for_spa_spinner_settle.assert_not_awaited()
        assert tier3_result["success"] is True

    @pytest.mark.asyncio
    async def test_spinner_settle_called_for_tab_step(self):
        """Spinner-settle must be called after Tier 3 succeeds on a tab step."""
        self.svc.tier2_executor._wait_for_spa_spinner_settle = AsyncMock()
        self.svc.tier2_executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=True)
        tier3_result = {"success": True, "tier": 3}

        await self.svc._apply_tab_verification_after_tier3(
            step={"action": "click", "instruction": "Click 'Greater China Pro Monthly Plan' tab"},
            tier3_result=tier3_result,
        )

        self.svc.tier2_executor._wait_for_spa_spinner_settle.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sets_pending_tab_key_when_tab_confirmed_selected(self):
        """_pending_three_hk_tab_key must be set for RC2 guard when tab is selected."""
        self.svc.tier2_executor._wait_for_spa_spinner_settle = AsyncMock()
        self.svc.tier2_executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=True)
        tier3_result = {"success": True, "tier": 3}

        await self.svc._apply_tab_verification_after_tier3(
            step={"action": "click", "instruction": "Click 'Greater China Pro Monthly Plan' tab"},
            tier3_result=tier3_result,
        )

        assert self.svc.tier2_executor._pending_three_hk_tab_key == "greater china pro monthly plan"
        assert tier3_result["success"] is True

    @pytest.mark.asyncio
    async def test_attempts_recovery_reclick_when_tab_not_selected(self):
        """If tab not selected after spinner-settle, recovery re-click must be attempted."""
        self.svc.tier2_executor._wait_for_spa_spinner_settle = AsyncMock()
        self.svc.tier2_executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)
        self.svc.tier2_executor._recovery_click_three_hk_tab = AsyncMock(return_value=True)
        tier3_result = {"success": True, "tier": 3}

        await self.svc._apply_tab_verification_after_tier3(
            step={"action": "click", "instruction": "Click 'Greater China Pro Monthly Plan' tab"},
            tier3_result=tier3_result,
        )

        self.svc.tier2_executor._recovery_click_three_hk_tab.assert_awaited_once_with(
            self.svc.page, "greater china pro monthly plan"
        )
        assert self.svc.tier2_executor._pending_three_hk_tab_key == "greater china pro monthly plan"
        assert tier3_result["success"] is True

    @pytest.mark.asyncio
    async def test_downgrades_tier3_result_when_recovery_also_fails(self):
        """If recovery re-click also fails, tier3_result must be downgraded to success=False."""
        self.svc.tier2_executor._wait_for_spa_spinner_settle = AsyncMock()
        self.svc.tier2_executor._is_three_hk_plan_tab_selected = AsyncMock(return_value=False)
        self.svc.tier2_executor._recovery_click_three_hk_tab = AsyncMock(return_value=False)
        tier3_result = {"success": True, "tier": 3}

        await self.svc._apply_tab_verification_after_tier3(
            step={"action": "click", "instruction": "Click 'Greater China Pro Monthly Plan' tab"},
            tier3_result=tier3_result,
        )

        assert tier3_result["success"] is False
        assert "tab_state_verification_failed" in tier3_result.get("error_type", "")

    @pytest.mark.asyncio
    async def test_noop_when_tier2_executor_not_initialized(self):
        """If tier2_executor is None, verification silently skips without error."""
        self.svc.tier2_executor = None
        tier3_result = {"success": True, "tier": 3}

        # Must not raise
        await self.svc._apply_tab_verification_after_tier3(
            step={"action": "click", "instruction": "Click 'Greater China Pro Monthly Plan' tab"},
            tier3_result=tier3_result,
        )

        assert tier3_result["success"] is True


class TestOptionCAppliesTabVerificationAfterTier3:
    """_execute_option_c must call _apply_tab_verification_after_tier3 when Tier 3
    is used as the last resort for a Three HK plan-tab step."""

    def setup_method(self):
        self.svc = _make_service()

    @pytest.mark.asyncio
    async def test_tab_verification_called_after_tier3_success_in_option_c(self):
        """When Tier 2 fails and Tier 3 succeeds, _apply_tab_verification_after_tier3 is called."""
        tier2_fail = {"success": False, "tier": 2, "error": "tab locator not found"}
        tier3_success = {"success": True, "tier": 3}

        self.svc._ensure_tier2_initialized = AsyncMock()
        self.svc._ensure_tier3_initialized = AsyncMock()
        self.svc.tier2_executor = MagicMock()
        self.svc.tier2_executor.execute_step = AsyncMock(return_value=tier2_fail)
        self.svc.tier3_executor = MagicMock()
        self.svc.tier3_executor.execute_step = AsyncMock(return_value=tier3_success)
        self.svc._apply_tab_verification_after_tier3 = AsyncMock()

        step = {"action": "click", "instruction": "Click 'Greater China Pro Monthly Plan' tab"}
        await self.svc._execute_option_c(step=step, execution_history=[])

        self.svc._apply_tab_verification_after_tier3.assert_awaited_once_with(
            step=step, tier3_result=tier3_success
        )
