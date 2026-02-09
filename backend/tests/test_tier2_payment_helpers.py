"""Tests for Tier2 payment helper methods."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.tier2_hybrid import Tier2HybridExecutor


class TestTier2PaymentHelpers:
    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.parametrize(
        "instruction,action,expected",
        [
            ("Input 4111111111111111 as the credit card number", "fill", True),
            ("Select 01 as the expiry month dropdown", "select", True),
            ("Select 39 as the expiry year dropdown", "select", True),
            ("Input 100 as the CVV", "fill", True),
            ("Click the Continue button", "click", False),
        ],
    )
    def test_is_payment_instruction(self, instruction, action, expected):
        assert self.executor._is_payment_instruction(instruction, action) is expected

    @pytest.mark.asyncio
    async def test_maybe_wait_for_payment_gateway_skips_when_ready(self):
        page = MagicMock()
        page.url = "https://example.com/payment"

        self.executor.payment_gateway_ready = True
        self.executor.payment_gateway_url = page.url

        await self.executor._maybe_wait_for_payment_gateway(page)
        page.locator.assert_not_called()
