"""Tests for shared post-click readiness helpers."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.post_click_readiness import (
    wait_for_loading_indicators_to_clear,
    wait_for_post_click_readiness,
    wait_for_step_boundary_readiness,
)


def _make_locator(
    count: int = 0,
    visible: bool = False,
    attributes=None,
    interactive_child_count: int = 0,
):
    locator = AsyncMock()
    locator.count = AsyncMock(return_value=count)
    locator.is_visible = AsyncMock(return_value=visible)
    locator.wait_for = AsyncMock(return_value=None)
    locator.first = locator

    attrs = attributes or {}
    locator.get_attribute = AsyncMock(side_effect=lambda name: attrs.get(name))

    interactive_locator = AsyncMock()
    interactive_locator.count = AsyncMock(return_value=interactive_child_count)
    interactive_locator.first = interactive_locator
    locator.locator = MagicMock(return_value=interactive_locator)

    return locator


@pytest.mark.asyncio
async def test_wait_for_loading_indicators_uses_bootstrap_spinner_selector():
    page = MagicMock()
    logger = MagicMock()

    matched_element = AsyncMock()
    matched_element.count = AsyncMock(return_value=1)
    matched_element.wait_for = AsyncMock(return_value=None)
    matched_locator = MagicMock()
    matched_locator.first = matched_element

    default_element = AsyncMock()
    default_element.count = AsyncMock(return_value=0)
    default_element.wait_for = AsyncMock(return_value=None)
    default_locator = MagicMock()
    default_locator.first = default_element

    def locator_side_effect(selector):
        if selector == "div[role='status'].spinner-border":
            return matched_locator
        return default_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    await wait_for_loading_indicators_to_clear(page, logger, timeout_ms=4000)

    matched_element.wait_for.assert_awaited_once_with(state="hidden", timeout=4000)


@pytest.mark.asyncio
async def test_wait_for_step_boundary_readiness_waits_for_bootstrap_spinner_before_next_step():
    page = MagicMock()
    logger = MagicMock()

    matched_element = AsyncMock()
    matched_element.count = AsyncMock(return_value=1)
    matched_element.wait_for = AsyncMock(return_value=None)
    matched_locator = MagicMock()
    matched_locator.first = matched_element

    default_element = AsyncMock()
    default_element.count = AsyncMock(return_value=0)
    default_element.wait_for = AsyncMock(return_value=None)
    default_locator = MagicMock()
    default_locator.first = default_element

    def locator_side_effect(selector):
        if selector == "div[role='status'].spinner-border":
            return matched_locator
        return default_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    with patch("app.services.post_click_readiness.asyncio.sleep", AsyncMock(return_value=None)) as sleep_mock:
        await wait_for_step_boundary_readiness(page, logger, timeout_ms=30000)

    matched_element.wait_for.assert_awaited_once_with(state="hidden", timeout=15000)
    sleep_mock.assert_awaited_once_with(0.2)


@pytest.mark.asyncio
async def test_wait_for_step_boundary_readiness_ignores_modal_backdrop_overlays():
    page = MagicMock()
    logger = MagicMock()

    overlay_element = _make_locator(
        count=1,
        visible=True,
        attributes={
            "class": "modal-backdrop overlay show",
            "aria-busy": "false",
        },
    )
    default_locator = _make_locator(count=0, visible=False)

    def locator_side_effect(selector):
        if selector == "[class*='overlay']":
            return overlay_element
        return default_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    with patch("app.services.post_click_readiness.asyncio.sleep", AsyncMock(return_value=None)):
        await wait_for_step_boundary_readiness(page, logger, timeout_ms=30000)

    overlay_element.wait_for.assert_not_awaited()


@pytest.mark.asyncio
async def test_wait_for_loading_indicators_waits_for_busy_overlay():
    page = MagicMock()
    logger = MagicMock()

    overlay_element = _make_locator(
        count=1,
        visible=True,
        attributes={
            "class": "loading overlay",
            "aria-busy": "true",
        },
    )
    default_locator = _make_locator(count=0, visible=False)

    def locator_side_effect(selector):
        if selector == "[class*='overlay']":
            return overlay_element
        return default_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    await wait_for_loading_indicators_to_clear(page, logger, timeout_ms=4000)

    overlay_element.wait_for.assert_awaited_once_with(state="hidden", timeout=4000)


@pytest.mark.asyncio
async def test_wait_for_post_click_readiness_skips_auth_wait_for_interactable_modal_transition():
    page = MagicMock()
    logger = MagicMock()
    current_url = "https://example.com/login"
    page.url = current_url
    page.wait_for_load_state = AsyncMock(return_value=None)

    clicked_element = AsyncMock()
    clicked_element.wait_for = AsyncMock(return_value=None)

    modal_locator = _make_locator(count=1, visible=True, interactive_child_count=2)
    default_locator = _make_locator(count=0, visible=False)

    def locator_side_effect(selector):
        if selector == ".modal.show":
            return modal_locator
        return default_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    with patch("app.services.post_click_readiness.asyncio.sleep", AsyncMock(return_value=None)):
        classification = await wait_for_post_click_readiness(
            page=page,
            clicked_element=clicked_element,
            instruction="Click the 'Login' button on popup to proceed to the password input page",
            element_text="Login",
            current_url=current_url,
            timeout_ms=30000,
            logger=logger,
        )

    assert classification["is_auth_click"] is True
    clicked_element.wait_for.assert_not_awaited()
    page.wait_for_load_state.assert_not_awaited()
