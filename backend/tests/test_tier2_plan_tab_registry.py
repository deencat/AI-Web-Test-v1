"""Regression tests: 4.5G Monthly Plans and 5G Broadband tab labels must be registered
in THREE_HK_PLAN_TAB_LABELS so Tier 2 routes them through the specialist
spinner-settle + tab-state verification path instead of the generic XPath click
that blindly marks them PASS while the SPA resets the active tab.

Root cause identified in Executions #705 (5G Broadband) and #707 (4.5G Monthly Plans):
'Wi-Fi 6 Monthly Plan' and 'HK-UK Pro Sharing Monthly Plan' were absent from the
registry, so _is_three_hk_plan_tab_click returned False and no spinner-settle or
tab-state check was performed.
"""

import sys
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.tier2_hybrid import Tier2HybridExecutor

THREE_HK_UAT_URL = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en"


def _make_executor() -> Tier2HybridExecutor:
    return Tier2HybridExecutor(
        db=MagicMock(),
        xpath_extractor=MagicMock(),
        timeout_ms=30_000,
    )


class TestTabLabelRegistry:
    """_extract_three_hk_plan_tab_key must recognise every tab visible on the
    4.5G Monthly Plans and 5G Broadband categories."""

    def setup_method(self):
        self.executor = _make_executor()

    # ── 4.5G Monthly Plans ────────────────────────────────────────────── #

    def test_hk_uk_pro_sharing_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click 'HK-UK Pro Sharing Monthly Plan' tab"
        )
        assert key is not None, (
            "'hk-uk pro sharing monthly plan' must be registered in THREE_HK_PLAN_TAB_LABELS"
        )

    def test_greater_china_pro_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click 'Greater China Pro Monthly Plan' tab"
        )
        assert key is not None, (
            "'greater china pro monthly plan' must be registered"
        )

    def test_4_5g_sim_monthly_plan_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click '4.5G SIM Monthly Plan' tab"
        )
        assert key is not None, (
            "'4.5g sim monthly plan' must be registered"
        )

    # ── 5G Broadband ──────────────────────────────────────────────────── #

    def test_wifi6_monthly_plan_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click 'Wi-Fi 6 Monthly Plan' tab"
        )
        assert key is not None, (
            "'wi-fi 6 monthly plan' must be registered in THREE_HK_PLAN_TAB_LABELS"
        )

    def test_wifi7_monthly_plan_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click 'Wi-Fi 7 Monthly Plan' tab"
        )
        assert key is not None, (
            "'wi-fi 7 monthly plan' must be registered"
        )

    def test_hsbc_credit_card_offer_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click 'HSBC credit card offer' tab"
        )
        assert key is not None, (
            "'hsbc credit card offer' must be registered"
        )

    def test_tertiary_students_tab_matched(self):
        key = self.executor._extract_three_hk_plan_tab_key(
            "Click 'Tertiary students and staff offer' tab"
        )
        assert key is not None, (
            "'tertiary students and staff offer' must be registered"
        )

    # ── Existing labels must not regress ──────────────────────────────── #

    def test_voucher_monthly_plan_still_matched(self):
        assert self.executor._extract_three_hk_plan_tab_key(
            "Click voucher monthly plan tab."
        ) == "voucher monthly plan"

    def test_5g_monthly_sim_plan_still_matched(self):
        assert self.executor._extract_three_hk_plan_tab_key(
            "Click '5G Monthly SIM Plan' tab"
        ) == "5g monthly sim plan"


class TestIsThreeHkPlanTabClickRouting:
    """_is_three_hk_plan_tab_click must return True for all 4.5G Monthly Plans
    and 5G Broadband tab instructions on the Three HK UAT domain."""

    def setup_method(self):
        self.executor = _make_executor()

    @pytest.mark.parametrize("instruction", [
        "Click 'HK-UK Pro Sharing Monthly Plan' tab",
        "Click 'Greater China Pro Monthly Plan' tab",
        "Click '4.5G SIM Monthly Plan' tab",
        "Click 'Wi-Fi 6 Monthly Plan' tab",
        "Click 'Wi-Fi 7 Monthly Plan' tab",
        "Click 'HSBC credit card offer' tab",
        "Click 'Tertiary students and staff offer' tab",
    ])
    def test_new_tab_instructions_route_to_specialist_path(self, instruction):
        result = self.executor._is_three_hk_plan_tab_click(
            page_url=THREE_HK_UAT_URL,
            instruction=instruction,
            action="click",
        )
        assert result is True, (
            f"{instruction!r} must route through _try_three_hk_plan_tab_click "
            "so spinner-settle and tab-state verification are applied"
        )

    def test_non_tab_instruction_is_not_routed(self):
        assert self.executor._is_three_hk_plan_tab_click(
            page_url=THREE_HK_UAT_URL,
            instruction="Click $120/month plan",
            action="click",
        ) is False


class TestExecuteStepRoutesNewTabsToSpecialistPath:
    """execute_step must invoke _try_three_hk_plan_tab_click (not the cache/XPath
    path) for 4.5G Monthly Plans and 5G Broadband tab instructions."""

    def setup_method(self):
        self.executor = _make_executor()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("instruction", [
        "Click 'Wi-Fi 6 Monthly Plan' tab",
        "Click 'HK-UK Pro Sharing Monthly Plan' tab",
    ])
    async def test_execute_step_uses_tab_helper_not_cache(self, instruction):
        page = MagicMock()
        page.url = THREE_HK_UAT_URL

        self.executor._try_three_hk_plan_tab_click = AsyncMock(
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
            side_effect=AssertionError("cache lookup must be bypassed for tab clicks")
        )

        result = await self.executor.execute_step(
            page=page,
            step={"action": "click", "instruction": instruction},
        )

        assert result["success"] is True
        self.executor._try_three_hk_plan_tab_click.assert_awaited_once_with(
            page, instruction, ANY
        )
