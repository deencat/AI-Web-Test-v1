"""Tests for Tier2 payment helper methods."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

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

    def test_should_retry_observe_extraction_for_payment_fill_no_results(self):
        extraction_result = {
            "success": False,
            "error": "ValueError: observe() returned no results for: credit card number"
        }

        should_retry = self.executor._should_retry_observe_extraction(
            extraction_result=extraction_result,
            action="fill",
            selector=None,
            instruction="Step 19: Input card number",
        )

        assert should_retry is True

    def test_select_xpath_from_option_xpath(self):
        option_xpath = "/html/body/div/form/select[1]/option[16]"
        assert self.executor._select_xpath_from_option_xpath(option_xpath) == "/html/body/div/form/select[1]"

    def test_xpath_targets_iframe(self):
        assert self.executor._xpath_targets_iframe("/html/body/div/iframe[1]") is True
        assert self.executor._xpath_targets_iframe("/html/body/div/button[1]") is False

    @pytest.mark.asyncio
    async def test_maybe_wait_for_payment_gateway_skips_when_ready(self):
        page = MagicMock()
        page.url = "https://example.com/payment"

        self.executor.payment_gateway_ready = True
        self.executor.payment_gateway_url = page.url

        await self.executor._maybe_wait_for_payment_gateway(page)
        page.locator.assert_not_called()

    @pytest.mark.asyncio
    async def test_maybe_wait_for_payment_gateway_uses_quick_timeout_on_non_gateway_url(self):
        page = MagicMock()
        page.url = "https://three.com.hk/postpaid/en/checkout"
        page.wait_for_selector = AsyncMock(side_effect=Exception("not ready"))

        await self.executor._maybe_wait_for_payment_gateway(page)

        page.wait_for_selector.assert_called_once_with(
            self.executor._payment_input_css_selector(),
            state="visible",
            timeout=1500,
        )
        assert self.executor.payment_gateway_ready is False

    @pytest.mark.asyncio
    async def test_maybe_wait_for_payment_gateway_uses_extended_timeout_on_gateway_url(self):
        page = MagicMock()
        page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"
        page.wait_for_selector = AsyncMock(return_value=MagicMock())

        await self.executor._maybe_wait_for_payment_gateway(page)

        page.wait_for_selector.assert_called_once_with(
            self.executor._payment_input_css_selector(),
            state="visible",
            timeout=8000,
        )
        assert self.executor.payment_gateway_ready is True
        assert self.executor.payment_gateway_url == page.url

    @pytest.mark.asyncio
    async def test_execute_step_retries_observe_once_after_wait_when_no_results(self):
        page = MagicMock()
        page.url = "https://www.three.com.hk/postpaid/en/account/purchase"

        self.executor.cache_service.get_cached_xpath = MagicMock(return_value=None)
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor._wait_for_page_interactable_for_observe = AsyncMock(return_value=None)

        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock(side_effect=[
            {
                "success": False,
                "error": "ValueError: observe() returned no results for: select plan",
                "error_type": "ValueError",
            },
            {
                "success": True,
                "xpath": "//button[contains(., '$288/month')]",
                "page_title": "Purchase",
                "element_text": "$288/month",
            },
        ])

        step = {
            "action": "click",
            "selector": None,
            "instruction": "Step 7: Select the '$288/month' plan from the available plans",
            "value": None,
        }

        result = await self.executor.execute_step(page, step)

        assert result["success"] is True
        assert self.executor.xpath_extractor.extract_xpath_with_page.await_count == 2
        self.executor._wait_for_page_interactable_for_observe.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_step_retries_observe_once_after_navigation_context_destroyed(self):
        page = MagicMock()
        page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION456"

        self.executor.cache_service.get_cached_xpath = MagicMock(return_value=None)
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor._wait_for_page_interactable_for_observe = AsyncMock(return_value=None)
        self.executor._maybe_wait_for_payment_gateway = AsyncMock(return_value=None)

        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock(side_effect=[
            {
                "success": False,
                "error": "Error: Page.title: Execution context was destroyed, most likely because of a navigation",
                "error_type": "Error",
            },
            {
                "success": True,
                "xpath": "//input[@name='cardNumber']",
                "page_title": "Payment",
                "element_text": "",
            },
        ])

        step = {
            "action": "fill",
            "selector": None,
            "instruction": "Step 19: Input '4111111111111111' as the credit card number",
            "value": "4111111111111111",
        }

        result = await self.executor.execute_step(page, step)

        assert result["success"] is True
        assert self.executor.xpath_extractor.extract_xpath_with_page.await_count == 2
        self.executor._wait_for_page_interactable_for_observe.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_step_click_uses_iframe_fallback_when_xpath_is_iframe(self):
        page = MagicMock()
        page.url = "https://example.com/checkout"

        self.executor.cache_service.get_cached_xpath = MagicMock(return_value=None)
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor._try_click_inside_iframe = AsyncMock(return_value=True)

        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock(return_value={
            "success": True,
            "xpath": "/html/body[1]/div[1]/iframe[1]",
            "page_title": "Checkout",
            "element_text": "",
        })

        step = {
            "action": "click",
            "selector": None,
            "instruction": "click submit button",
            "value": None,
        }

        result = await self.executor.execute_step(page, step)

        assert result["success"] is True
        self.executor._try_click_inside_iframe.assert_awaited_once_with(page, "click submit button")
        self.executor._execute_action_with_xpath.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_cached_xpath_for_step_rejects_email_field_for_password_instruction(self):
        page = MagicMock()
        element = AsyncMock()
        element.wait_for = AsyncMock()

        attrs = {
            "type": "email",
            "name": "email",
            "id": "loginEmail",
            "placeholder": "Email address",
            "aria-label": "Email",
            "autocomplete": "email",
        }

        async def _get_attr(name):
            return attrs.get(name)

        element.get_attribute = AsyncMock(side_effect=_get_attr)
        locator = MagicMock()
        locator.first = element
        page.locator.return_value = locator

        is_valid = await self.executor._validate_cached_xpath_for_step(
            page=page,
            xpath="/html/body/input[1]",
            action="fill",
            instruction="Step 5: Input password in the password field",
            value="DEE57vTo!",
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_execute_step_reextracts_when_cached_xpath_semantically_mismatched(self):
        page = MagicMock()
        page.url = "https://example.com/login"

        self.executor.cache_service.get_cached_xpath = MagicMock(return_value={"xpath": "/html/body/input[1]"})
        self.executor.cache_service.invalidate_cache = MagicMock()
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor.cache_service.validate_and_update = MagicMock()

        self.executor._validate_cached_xpath_for_step = AsyncMock(return_value=False)
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock(return_value={
            "success": True,
            "xpath": "/html/body/form/input[2]",
            "page_title": "Login",
            "element_text": "Password",
        })

        result = await self.executor.execute_step(
            page,
            {
                "action": "fill",
                "instruction": "Step 5: Input password in the password field",
                "value": "DEE57vTo!",
            },
        )

        assert result["success"] is True
        self.executor.cache_service.invalidate_cache.assert_called_once()
        self.executor.xpath_extractor.extract_xpath_with_page.assert_awaited_once()
        self.executor._execute_action_with_xpath.assert_awaited_once()
