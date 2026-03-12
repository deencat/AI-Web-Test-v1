"""Tests for shared post-click readiness helpers."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.post_click_readiness import wait_for_loading_indicators_to_clear


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
