"""Tests for Tier 3 payment field verification after Stagehand act()."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.tier3_stagehand import Tier3StagehandExecutor


class TestTier3PaymentVerification:
    def setup_method(self):
        self.stagehand = MagicMock()
        self.stagehand.page = MagicMock()
        self.executor = Tier3StagehandExecutor(stagehand=self.stagehand, timeout_ms=30000)

    @pytest.mark.asyncio
    async def test_fill_reports_failure_when_gw_proxy_field_stays_empty(self):
        self.stagehand.page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"
        self.stagehand.page.act = AsyncMock(return_value=None)

        absent_locator = MagicMock()
        absent_locator.count = AsyncMock(return_value=0)
        self.stagehand.page.locator = MagicMock(return_value=absent_locator)

        step = {
            "action": "fill",
            "instruction": "Step 42: Input credit card number 4111111111111111",
            "value": "4111111111111111",
        }

        result = await self.executor.execute_step(step)

        assert result["success"] is False
        assert "did not populate payment field" in result["error"]

    @pytest.mark.asyncio
    async def test_fill_succeeds_when_gw_proxy_field_is_populated(self):
        self.stagehand.page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"
        self.stagehand.page.act = AsyncMock(return_value=None)

        present_locator = MagicMock()
        present_locator.count = AsyncMock(return_value=1)
        absent_locator = MagicMock()
        absent_locator.count = AsyncMock(return_value=0)

        mock_inner = AsyncMock()
        mock_inner.wait_for = AsyncMock(return_value=None)
        mock_inner.input_value = AsyncMock(return_value="4111111111111111")
        mock_inner_locator = MagicMock()
        mock_inner_locator.first = mock_inner

        mock_frame = MagicMock()
        mock_frame.locator = MagicMock(return_value=mock_inner_locator)

        def locator_side_effect(selector):
            if selector == "iframe.gw-proxy-number":
                return present_locator
            return absent_locator

        self.stagehand.page.locator = MagicMock(side_effect=locator_side_effect)
        self.stagehand.page.frame_locator = MagicMock(return_value=mock_frame)

        step = {
            "action": "fill",
            "instruction": "Step 42: Input credit card number 4111111111111111",
            "value": "4111111111111111",
        }

        result = await self.executor.execute_step(step)

        assert result["success"] is True
