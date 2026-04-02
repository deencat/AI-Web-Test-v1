"""Tests for Tier2 payment helper methods."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

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

    def test_iframe_button_keywords_does_not_expand_submit_to_pay_without_payment_context(self):
        assert self.executor._iframe_button_keywords("Step 48: Click the submit button") == ["submit"]

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
        self.executor._try_click_inside_iframe.assert_awaited_once_with(
            page,
            "click submit button",
            "/html/body[1]/div[1]/iframe[1]",
        )
        self.executor._execute_action_with_xpath.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_step_click_fails_when_iframe_fallback_cannot_verify_click(self):
        page = MagicMock()
        page.url = "https://example.com/checkout"

        self.executor.cache_service.get_cached_xpath = MagicMock(return_value=None)
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor._try_click_inside_iframe = AsyncMock(return_value=False)

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

        assert result["success"] is False
        assert result["error_type"] == "ValueError"
        assert "iframe" in result["error"].lower()
        self.executor._try_click_inside_iframe.assert_awaited_once_with(
            page,
            "click submit button",
            "/html/body[1]/div[1]/iframe[1]",
        )
        self.executor._execute_action_with_xpath.assert_not_called()

    @pytest.mark.asyncio
    async def test_try_click_inside_iframe_targets_observed_frame_and_waits_for_readiness(self):
        page = MagicMock()
        page.url = "https://example.com/checkout"

        main_frame = MagicMock()
        other_frame = MagicMock()
        target_frame = MagicMock()
        page.main_frame = main_frame
        page.frames = [main_frame, other_frame, target_frame]

        iframe_handle = MagicMock()
        iframe_handle.content_frame = AsyncMock(return_value=target_frame)

        iframe_locator_first = MagicMock()
        iframe_locator_first.element_handle = AsyncMock(return_value=iframe_handle)
        iframe_locator = MagicMock()
        iframe_locator.first = iframe_locator_first

        clicked_element = AsyncMock()
        clicked_element.wait_for = AsyncMock(return_value=None)
        clicked_element.is_enabled = AsyncMock(return_value=True)
        clicked_element.text_content = AsyncMock(return_value="Submit")
        clicked_element.click = AsyncMock(return_value=None)

        clicked_locator = MagicMock()
        clicked_locator.first = clicked_element

        page.locator = MagicMock(return_value=iframe_locator)
        target_frame.locator = MagicMock(return_value=clicked_locator)
        other_frame.locator = MagicMock()

        self.executor._wait_for_element_enabled_before_click = AsyncMock(return_value=None)

        with patch(
            "app.services.tier2_hybrid.wait_for_post_click_readiness",
            AsyncMock(return_value={"is_payment_click": False}),
        ) as readiness_mock:
            result = await self.executor._try_click_inside_iframe(
                page,
                "click submit button",
                "/html/body[1]/div[1]/iframe[1]",
            )

        assert result is True
        page.locator.assert_called_once_with("xpath=/html/body[1]/div[1]/iframe[1]")
        other_frame.locator.assert_not_called()
        target_frame.locator.assert_called()
        readiness_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_try_click_inside_iframe_returns_false_when_post_click_readiness_fails(self):
        page = MagicMock()
        page.url = "https://example.com/checkout"

        main_frame = MagicMock()
        target_frame = MagicMock()
        page.main_frame = main_frame
        page.frames = [main_frame, target_frame]

        iframe_handle = MagicMock()
        iframe_handle.content_frame = AsyncMock(return_value=target_frame)

        iframe_locator_first = MagicMock()
        iframe_locator_first.element_handle = AsyncMock(return_value=iframe_handle)
        iframe_locator = MagicMock()
        iframe_locator.first = iframe_locator_first

        clicked_element = AsyncMock()
        clicked_element.wait_for = AsyncMock(return_value=None)
        clicked_element.is_enabled = AsyncMock(return_value=True)
        clicked_element.text_content = AsyncMock(return_value="Submit")
        clicked_element.click = AsyncMock(return_value=None)

        clicked_locator = MagicMock()
        clicked_locator.first = clicked_element

        page.locator = MagicMock(return_value=iframe_locator)
        target_frame.locator = MagicMock(return_value=clicked_locator)

        self.executor._wait_for_element_enabled_before_click = AsyncMock(return_value=None)

        with patch(
            "app.services.tier2_hybrid.wait_for_post_click_readiness",
            AsyncMock(side_effect=RuntimeError("no verified transition")),
        ):
            result = await self.executor._try_click_inside_iframe(
                page,
                "click submit button",
                "/html/body[1]/div[1]/iframe[1]",
            )

        assert result is False
        clicked_element.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_try_click_inside_iframe_skips_visible_button_with_wrong_label(self):
        page = MagicMock()
        page.url = "https://example.com/checkout"

        main_frame = MagicMock()
        target_frame = MagicMock()
        page.main_frame = main_frame
        page.frames = [main_frame, target_frame]

        iframe_handle = MagicMock()
        iframe_handle.content_frame = AsyncMock(return_value=target_frame)

        iframe_locator_first = MagicMock()
        iframe_locator_first.element_handle = AsyncMock(return_value=iframe_handle)
        iframe_locator = MagicMock()
        iframe_locator.first = iframe_locator_first

        cancel_button = AsyncMock()
        cancel_button.wait_for = AsyncMock(return_value=None)
        cancel_button.is_enabled = AsyncMock(return_value=True)
        cancel_button.text_content = AsyncMock(return_value="Cancel")
        cancel_button.click = AsyncMock(return_value=None)

        async def _cancel_attr(name):
            attrs = {
                "value": "Cancel",
                "aria-label": "Cancel",
                "title": "",
                "name": "cancel",
                "id": "cancel-button",
                "type": "submit",
            }
            return attrs.get(name)

        cancel_button.get_attribute = AsyncMock(side_effect=_cancel_attr)
        cancel_locator = MagicMock()
        cancel_locator.first = cancel_button

        submit_button = AsyncMock()
        submit_button.wait_for = AsyncMock(return_value=None)
        submit_button.is_enabled = AsyncMock(return_value=True)
        submit_button.text_content = AsyncMock(return_value="")
        submit_button.click = AsyncMock(return_value=None)

        async def _submit_attr(name):
            attrs = {
                "value": "Submit",
                "aria-label": "Submit",
                "title": "",
                "name": "submit",
                "id": "submit-button",
                "type": "submit",
            }
            return attrs.get(name)

        submit_button.get_attribute = AsyncMock(side_effect=_submit_attr)
        submit_locator = MagicMock()
        submit_locator.first = submit_button

        missing_button = AsyncMock()
        missing_button.wait_for = AsyncMock(side_effect=Exception("not found"))
        missing_button.text_content = AsyncMock(return_value="")
        missing_button.click = AsyncMock(return_value=None)
        missing_button.get_attribute = AsyncMock(return_value=None)
        missing_locator = MagicMock()
        missing_locator.first = missing_button

        def _locator_side_effect(selector):
            if selector == "button[type='submit']":
                return cancel_locator
            if selector == "input[type='submit']":
                return submit_locator
            return missing_locator

        def _role_side_effect(role, name=None, exact=False):
            if role == "button" and name == "submit":
                return submit_locator
            return missing_locator

        page.locator = MagicMock(return_value=iframe_locator)
        target_frame.locator = MagicMock(side_effect=_locator_side_effect)
        target_frame.get_by_role = MagicMock(side_effect=_role_side_effect)

        self.executor._wait_for_element_enabled_before_click = AsyncMock(return_value=None)

        with patch(
            "app.services.tier2_hybrid.wait_for_post_click_readiness",
            AsyncMock(return_value={"is_payment_click": False, "is_navigation_click": False}),
        ):
            result = await self.executor._try_click_inside_iframe(
                page,
                "Step 48: Click the submit button",
                "/html/body[1]/div[1]/iframe[1]",
            )

        assert result is True
        cancel_button.click.assert_not_awaited()
        submit_button.click.assert_awaited_once()

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

    @pytest.mark.asyncio
    async def test_execute_step_prefers_cached_xpath_before_payment_probes(self):
        page = MagicMock()
        page.url = "https://three.com.hk/postpaid/en/checkout/checkout?promotionId=HPPRM0000000187&step=autopay"

        self.executor.cache_service.get_cached_xpath = MagicMock(return_value={"xpath": "/html/body/form/input[1]"})
        self.executor.cache_service.invalidate_cache = MagicMock()
        self.executor.cache_service.cache_xpath = MagicMock()
        self.executor.cache_service.validate_and_update = MagicMock()

        self.executor._validate_cached_xpath_for_step = AsyncMock(return_value=True)
        self.executor._execute_action_with_xpath = AsyncMock(return_value=None)
        self.executor._maybe_wait_for_payment_gateway = AsyncMock(return_value=None)
        self.executor._try_payment_field_action = AsyncMock(return_value=None)
        self.executor.xpath_extractor.extract_xpath_with_page = AsyncMock()

        result = await self.executor.execute_step(
            page,
            {
                "action": "fill",
                "instruction": "Step 32: Input card holder name test",
                "value": "test",
            },
        )

        assert result["success"] is True
        self.executor._maybe_wait_for_payment_gateway.assert_not_awaited()
        self.executor._try_payment_field_action.assert_not_awaited()
        self.executor.xpath_extractor.extract_xpath_with_page.assert_not_awaited()
        self.executor._execute_action_with_xpath.assert_awaited_once_with(
            page,
            "fill",
            "/html/body/form/input[1]",
            "test",
            "Step 32: Input card holder name test",
        )

    @pytest.mark.asyncio
    async def test_execute_action_with_xpath_waits_for_popup_login_loading_to_clear(self):
        page = MagicMock()
        page.url = "https://example.com/account"
        page.wait_for_load_state = AsyncMock(return_value=None)

        clicked_element = AsyncMock()
        clicked_element.wait_for = AsyncMock(return_value=None)
        clicked_element.is_enabled = AsyncMock(return_value=True)
        clicked_element.text_content = AsyncMock(return_value="Login")
        clicked_element.click = AsyncMock(return_value=None)

        clicked_locator = MagicMock()
        clicked_locator.first = clicked_element

        loading_element = AsyncMock()
        loading_element.count = AsyncMock(return_value=1)
        loading_element.wait_for = AsyncMock(return_value=None)

        loading_locator = MagicMock()
        loading_locator.first = loading_element

        def locator_side_effect(selector):
            if selector == "xpath=/html/body/form/button[1]":
                return clicked_locator
            return loading_locator

        page.locator = MagicMock(side_effect=locator_side_effect)

        await self.executor._execute_action_with_xpath(
            page=page,
            action="click",
            xpath="/html/body/form/button[1]",
            value=None,
            instruction="Step 6: Click the 'Login' button on popup to log in to the account",
        )

        assert loading_element.wait_for.await_count > 0
        assert any(
            call.kwargs == {"state": "hidden", "timeout": 8000}
            for call in loading_element.wait_for.await_args_list
        )


# ---------------------------------------------------------------------------
# Bug fixes: exp. date keyword + payment_direct default — Sprint 10.9
# ---------------------------------------------------------------------------

class TestPaymentInstructionKeywords:
    """_is_payment_instruction must recognise 'exp.' / 'exp date' shorthand."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.parametrize("instruction", [
        "Step 33: Input exp. date '01/39'",
        "Input exp date '01/39'",
        "Fill in exp. date 01/39",
        "Enter exp date 12/28",
    ])
    def test_exp_date_shorthand_recognised_as_payment(self, instruction):
        assert self.executor._is_payment_instruction(instruction, "fill") is True, (
            f"Expected '{instruction}' to be recognised as payment instruction"
        )

    def test_exp_date_not_recognised_for_click_action(self):
        """Non fill/type/select actions must still return False."""
        assert self.executor._is_payment_instruction("exp. date field", "click") is False


class TestPaymentDirectDefault:
    """ENABLE_PAYMENT_DIRECT_HANDLING must default to True (opt-out, not opt-in)."""

    def test_payment_direct_enabled_by_default(self, monkeypatch):
        monkeypatch.delenv("ENABLE_PAYMENT_DIRECT_HANDLING", raising=False)
        executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)
        assert executor.payment_direct_enabled is True

    def test_payment_direct_can_be_disabled_via_env(self, monkeypatch):
        monkeypatch.setenv("ENABLE_PAYMENT_DIRECT_HANDLING", "false")
        executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)
        assert executor.payment_direct_enabled is False

    def test_payment_direct_enabled_via_env(self, monkeypatch):
        monkeypatch.setenv("ENABLE_PAYMENT_DIRECT_HANDLING", "true")
        executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)
        assert executor.payment_direct_enabled is True


class TestCombinedExpiryFill:
    """_try_payment_field_action must handle combined MM/YY expiry fill (not just select)."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.asyncio
    async def test_combined_expiry_fill_succeeds_via_direct_selector(self):
        page = MagicMock()
        page.url = "https://paygwuat.hthk.com/pay"

        mock_element = AsyncMock()
        mock_element.wait_for = AsyncMock(return_value=None)
        mock_element.fill = AsyncMock(return_value=None)

        mock_locator = MagicMock()
        mock_locator.first = mock_element
        page.locator = MagicMock(return_value=mock_locator)
        page.frame_locator = MagicMock(return_value=MagicMock())

        result = await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 33: Input exp. date '01/39'",
            value="01/39",
            start_time=__import__("time").time(),
        )

        assert result is not None
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_combined_expiry_returns_none_when_no_selector_matches(self):
        """Returns None (not a crash) when no combined expiry selector is visible."""
        page = MagicMock()
        page.url = "https://example.com"

        mock_element = AsyncMock()
        mock_element.wait_for = AsyncMock(side_effect=Exception("not found"))

        mock_locator = MagicMock()
        mock_locator.first = mock_element

        mock_frame = MagicMock()
        mock_frame.locator = MagicMock(return_value=mock_locator)
        page.locator = MagicMock(return_value=mock_locator)
        page.frame_locator = MagicMock(return_value=mock_frame)

        result = await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 33: Input exp. date '01/39'",
            value="01/39",
            start_time=__import__("time").time(),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_combined_expiry_fill_uses_page_label_fallback_before_iframe_probes(self):
        page = MagicMock()
        page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"

        self.executor.payment_gateway_ready = True
        self.executor.payment_gateway_url = page.url

        mock_fail_element = AsyncMock()
        mock_fail_element.wait_for = AsyncMock(side_effect=Exception("not found"))
        mock_fail_locator = MagicMock()
        mock_fail_locator.first = mock_fail_element

        tried_labels = []

        mock_success_element = AsyncMock()
        mock_success_element.wait_for = AsyncMock(return_value=None)
        mock_success_element.fill = AsyncMock(return_value=None)

        def get_by_label_side_effect(label, exact=False):
            tried_labels.append(label)
            if label == "Exp. Date (MM/YY)":
                return mock_success_element
            fail = AsyncMock()
            fail.wait_for = AsyncMock(side_effect=Exception("not found"))
            return fail

        page.locator = MagicMock(return_value=mock_fail_locator)
        page.get_by_label = MagicMock(side_effect=get_by_label_side_effect)
        page.frame_locator = MagicMock(side_effect=AssertionError("iframe probes should not run before page labels"))

        result = await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 33: Input exp. Date. 01/39",
            value="01/39",
            start_time=__import__("time").time(),
        )

        assert result is not None and result["success"] is True
        assert "Exp. Date (MM/YY)" in tried_labels
        page.frame_locator.assert_not_called()


class TestPaymentFieldProbeOrdering:
    """Payment helpers should prefer page-local matches before iframe fan-out."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.asyncio
    async def test_page_labels_are_tried_before_iframe_probes(self):
        page = MagicMock()
        page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"

        self.executor.payment_gateway_ready = True
        self.executor.payment_gateway_url = page.url

        mock_fail_element = AsyncMock()
        mock_fail_element.wait_for = AsyncMock(side_effect=Exception("not found"))
        mock_fail_locator = MagicMock()
        mock_fail_locator.first = mock_fail_element

        tried_labels = []

        mock_success_element = AsyncMock()
        mock_success_element.wait_for = AsyncMock(return_value=None)
        mock_success_element.fill = AsyncMock(return_value=None)

        def get_by_label_side_effect(label, exact=False):
            tried_labels.append(label)
            if label == "Cardholder name":
                return mock_success_element
            fail = AsyncMock()
            fail.wait_for = AsyncMock(side_effect=Exception("not found"))
            return fail

        page.locator = MagicMock(return_value=mock_fail_locator)
        page.get_by_label = MagicMock(side_effect=get_by_label_side_effect)
        page.frame_locator = MagicMock(side_effect=AssertionError("iframe probes should not run before page labels"))

        result = await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 45: Input card holder name test",
            value="test input",
            start_time=__import__("time").time(),
        )

        assert result is not None and result["success"] is True
        assert "Cardholder name" in tried_labels
        page.frame_locator.assert_not_called()

    @pytest.mark.asyncio
    async def test_iframe_probes_are_skipped_when_no_payment_iframe_exists(self):
        page = MagicMock()
        page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"

        self.executor.payment_gateway_ready = True
        self.executor.payment_gateway_url = page.url

        mock_fail_element = AsyncMock()
        mock_fail_element.wait_for = AsyncMock(side_effect=Exception("not found"))
        mock_fail_locator = MagicMock()
        mock_fail_locator.first = mock_fail_element

        absent_iframe_first = AsyncMock()
        absent_iframe_first.count = AsyncMock(return_value=0)
        absent_iframe_locator = MagicMock()
        absent_iframe_locator.count = AsyncMock(return_value=0)
        absent_iframe_locator.first = absent_iframe_first

        def locator_side_effect(selector):
            if selector.startswith("iframe"):
                return absent_iframe_locator
            return mock_fail_locator

        label_fail = AsyncMock()
        label_fail.wait_for = AsyncMock(side_effect=Exception("not found"))

        page.locator = MagicMock(side_effect=locator_side_effect)
        page.get_by_label = MagicMock(return_value=label_fail)
        page.frame_locator = MagicMock(side_effect=AssertionError("iframe fan-out should be skipped when no matching iframe exists"))

        result = await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 45: Input card holder name test",
            value="test input",
            start_time=__import__("time").time(),
        )

        assert result is None
        page.frame_locator.assert_not_called()


# ---------------------------------------------------------------------------
# Bug fix: autopay page URL path detection — Sprint 10.9
# ---------------------------------------------------------------------------

class TestAutopayUrlDetection:
    """_is_external_payment_gateway_url must also detect autopay pages via URL path/query."""

    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.parametrize("url", [
        "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/checkout/checkout?promotionId=HPPRM0000000879&step=autopay",
        "https://example.com/checkout?step=autopay",
        "https://shop.example.com/payment/auto-pay",
        "https://wwwuat.three.com.hk/en/checkout?step=auto-pay",
    ])
    def test_autopay_url_detected_as_payment_page(self, url):
        assert self.executor._is_external_payment_gateway_url(url) is True, (
            f"Expected '{url}' to be detected as a payment page requiring 8s wait"
        )

    def test_non_autopay_checkout_url_not_detected(self):
        """A regular checkout page without autopay in path/query uses 1500ms timeout."""
        url = "https://wwwuat.three.com.hk/en/checkout?step=review"
        assert self.executor._is_external_payment_gateway_url(url) is False

    def test_existing_external_gateway_hostname_still_detected(self):
        url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"
        assert self.executor._is_external_payment_gateway_url(url) is True

    def test_empty_url_returns_false(self):
        assert self.executor._is_external_payment_gateway_url("") is False

    @pytest.mark.asyncio
    async def test_autopay_page_uses_8000ms_wait_timeout(self):
        """_maybe_wait_for_payment_gateway must use 8000ms for autopay pages."""
        page = MagicMock()
        page.url = "https://wwwuat.three.com.hk/en/checkout?step=autopay"
        page.wait_for_selector = AsyncMock(side_effect=Exception("not ready"))

        await self.executor._maybe_wait_for_payment_gateway(page)

        page.wait_for_selector.assert_called_once_with(
            self.executor._payment_input_css_selector(),
            state="visible",
            timeout=8000,
        )


# ---------------------------------------------------------------------------
# Bug fix: same-origin autopay page must NOT stall 10s per selector
# when payment_gateway_ready=False — Sprint 10.9 / ADR-002-16 gap
# ---------------------------------------------------------------------------

class TestAutopayDirectHandlerTimeout:
    """
    _try_payment_field_action must use a short probe timeout (<=2000ms) for
    same-origin autopay pages even when payment_gateway_ready is False.

    Gap identified: if _maybe_wait_for_payment_gateway cannot match the page's
    actual CSS selectors (e.g. Three HK autopay uses non-standard field attrs),
    payment_gateway_ready stays False and the fallback wait_timeout becomes 10000ms
    per selector — causing a ~50s stall before observe() is called.
    """

    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.asyncio
    async def test_same_origin_autopay_uses_short_probe_timeout_when_readiness_failed(self):
        """
        For a same-origin ?step=autopay URL where payment_gateway_ready=False,
        _try_payment_field_action must wait no more than 2000ms per selector,
        not the 10000ms that was used for external gateways.
        """
        page = MagicMock()
        page.url = "https://three.com.hk/postpaid/en/checkout/checkout?promotionId=HPPRM0000000187&step=autopay"

        # Readiness check failed — gateway_ready stays False
        self.executor.payment_gateway_ready = False
        self.executor.payment_gateway_url = None

        wait_calls = []

        mock_element = AsyncMock()

        async def track_wait_for(**kwargs):
            wait_calls.append(kwargs)
            raise Exception("not found")  # all selectors fail

        mock_element.wait_for = track_wait_for
        mock_element.fill = AsyncMock(return_value=None)

        mock_locator = MagicMock()
        mock_locator.first = mock_element

        mock_frame = MagicMock()
        mock_frame.locator = MagicMock(return_value=mock_locator)

        page.locator = MagicMock(return_value=mock_locator)
        page.frame_locator = MagicMock(return_value=mock_frame)

        # get_by_label also fails
        mock_label_locator = AsyncMock()
        mock_label_locator.wait_for = AsyncMock(side_effect=Exception("not found"))
        page.get_by_label = MagicMock(return_value=mock_label_locator)

        await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 31: Input credit card number 4111111111111111",
            value="4111111111111111",
            start_time=__import__("time").time(),
        )

        # All wait_for calls must use <=2000ms — NOT the 10000ms external-gateway value
        assert wait_calls, "Expected at least one wait_for call on selectors"
        for call_kwargs in wait_calls:
            timeout = call_kwargs.get("timeout", 0)
            assert timeout <= 2000, (
                f"Same-origin autopay page must not stall {timeout}ms per selector "
                f"(expected <=2000ms). This causes ~50s stall when all selectors fail."
            )

    @pytest.mark.asyncio
    async def test_external_gateway_keeps_generous_timeout_when_readiness_failed(self):
        """
        External cross-origin gateways (e.g. mastercard) MAY use a longer probe
        timeout because iframe content loads slowly.
        """
        page = MagicMock()
        page.url = "https://gphk.gateway.mastercard.com/checkout/pay/SESSION123"

        self.executor.payment_gateway_ready = False
        self.executor.payment_gateway_url = None

        wait_calls = []

        mock_element = AsyncMock()

        async def track_wait_for(**kwargs):
            wait_calls.append(kwargs)
            raise Exception("not found")

        mock_element.wait_for = track_wait_for
        mock_locator = MagicMock()
        mock_locator.first = mock_element

        mock_frame = MagicMock()
        mock_frame.locator = MagicMock(return_value=mock_locator)

        page.locator = MagicMock(return_value=mock_locator)
        page.frame_locator = MagicMock(return_value=mock_frame)

        mock_label_locator = AsyncMock()
        mock_label_locator.wait_for = AsyncMock(side_effect=Exception("not found"))
        page.get_by_label = MagicMock(return_value=mock_label_locator)

        await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 31: Input credit card number 4111111111111111",
            value="4111111111111111",
            start_time=__import__("time").time(),
        )

        # External gateway must use >2000ms to tolerate slow iframe loading
        if wait_calls:
            any_generous = any(kw.get("timeout", 0) > 2000 for kw in wait_calls)
            assert any_generous, (
                "External gateway should use a generous per-selector timeout to tolerate slow iframes"
            )


class TestCreditCardLabelCandidates:
    """
    _try_payment_field_action must include 'Credit Card No.' in label_candidates
    for credit card steps, covering Three HK autopay form which uses that exact label.
    """

    def setup_method(self):
        self.executor = Tier2HybridExecutor(db=MagicMock(), xpath_extractor=MagicMock(), timeout_ms=30000)

    @pytest.mark.asyncio
    async def test_credit_card_no_label_tried_on_autopay_page(self):
        """
        When CSS selector probing fails, get_by_label("Credit Card No.") must be
        attempted for a 'credit card number' instruction (Three HK autopay form).
        """
        page = MagicMock()
        page.url = "https://three.com.hk/postpaid/en/checkout/checkout?promotionId=HPPRM0000000187&step=autopay"

        self.executor.payment_gateway_ready = False
        self.executor.payment_gateway_url = None

        # All CSS selector probes fail
        mock_fail_element = AsyncMock()
        mock_fail_element.wait_for = AsyncMock(side_effect=Exception("not found"))
        mock_fail_locator = MagicMock()
        mock_fail_locator.first = mock_fail_element

        mock_frame = MagicMock()
        mock_frame.locator = MagicMock(return_value=mock_fail_locator)

        page.locator = MagicMock(return_value=mock_fail_locator)
        page.frame_locator = MagicMock(return_value=mock_frame)

        # Only "Credit Card No." label resolves successfully
        tried_labels = []

        mock_success_element = AsyncMock()
        mock_success_element.wait_for = AsyncMock(return_value=None)
        mock_success_element.fill = AsyncMock(return_value=None)

        def get_by_label_side_effect(label, exact=False):
            tried_labels.append(label)
            if label == "Credit Card No.":
                return mock_success_element
            fail = AsyncMock()
            fail.wait_for = AsyncMock(side_effect=Exception("not found"))
            return fail

        page.get_by_label = MagicMock(side_effect=get_by_label_side_effect)

        result = await self.executor._try_payment_field_action(
            page=page,
            action="fill",
            instruction="Step 31: Input credit card number 4111111111111111",
            value="4111111111111111",
            start_time=__import__("time").time(),
        )

        assert "Credit Card No." in tried_labels, (
            f"Expected 'Credit Card No.' in label candidates, got: {tried_labels}"
        )
        assert result is not None and result["success"] is True
