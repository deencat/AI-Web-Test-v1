"""Tests for Tier 1 click wait behavior."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.tier1_playwright import Tier1PlaywrightExecutor


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
