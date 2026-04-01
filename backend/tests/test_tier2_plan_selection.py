"""Tests for Three HK preprod plan-selection recovery in Tier 2."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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