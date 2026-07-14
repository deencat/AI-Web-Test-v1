"""Tests for Tier 1 click wait behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.tier1_playwright import Tier1PlaywrightExecutor


def test_to_playwright_selector_prefixes_absolute_xpath():
    executor = Tier1PlaywrightExecutor()
    xpath = "/html/body/div/div[1]/div[3]"
    assert executor._to_playwright_selector(xpath) == f"xpath={xpath}"


def test_to_playwright_selector_leaves_css_unchanged():
    executor = Tier1PlaywrightExecutor()
    assert executor._to_playwright_selector("#login-btn") == "#login-btn"
    assert executor._to_playwright_selector("button[type='submit']") == "button[type='submit']"


def test_to_playwright_selector_preserves_existing_xpath_prefix():
    executor = Tier1PlaywrightExecutor()
    selector = "xpath=/html/body/div"
    assert executor._to_playwright_selector(selector) == selector


@pytest.mark.asyncio
async def test_execute_click_uses_xpath_prefix_for_absolute_xpath():
    executor = Tier1PlaywrightExecutor(timeout_ms=30000)

    page = MagicMock()
    page.url = "https://example.com/account"
    page.wait_for_load_state = AsyncMock(return_value=None)

    clicked_element = AsyncMock()
    clicked_element.wait_for = AsyncMock(return_value=None)
    clicked_element.text_content = AsyncMock(return_value="View bill")
    clicked_element.click = AsyncMock(return_value=None)

    clicked_locator = MagicMock()
    clicked_locator.first = clicked_element
    page.locator = MagicMock(return_value=clicked_locator)

    absolute_xpath = "/html/body/div/div[1]/div[3]/div/div/div[2]/div/div/div[2]/div[2]/div[1]/div"
    await executor._execute_click(page, absolute_xpath)

    page.locator.assert_called_once_with(f"xpath={absolute_xpath}")


@pytest.mark.asyncio
async def test_execute_click_waits_for_popup_login_loading_to_clear():
    executor = Tier1PlaywrightExecutor(timeout_ms=30000)

    page = MagicMock()
    page.url = "https://example.com/account"
    page.wait_for_load_state = AsyncMock(return_value=None)

    clicked_element = AsyncMock()
    clicked_element.wait_for = AsyncMock(return_value=None)
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
        if selector == "button[type='submit']":
            return clicked_locator
        return loading_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    await executor._execute_click(page, "button[type='submit']")

    assert loading_element.wait_for.await_count > 0
    assert any(
        call.kwargs == {"state": "hidden", "timeout": 8000}
        for call in loading_element.wait_for.await_args_list
    )
