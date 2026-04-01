"""
Unit tests for post_click_readiness.auto_dismiss_blocking_modals.

Sprint 10.9 — preprod modal auto-dismissal (ADR-002-19-C):
The execution engine must detect visible modal/dialog overlays and click their
dismiss button so the server's session gate is satisfied before plan-selection
clicks are processed.

Tests (TDD RED → GREEN):
  1. No modal visible → returns False, no click attempted
  2. .modal.show visible with "I understand" button → clicks it, returns True
  3. [role="dialog"] visible, no recognised button → skips, returns False
  4. Modal with "OK" button → clicks it, returns True
  5. Modal present but not visible (aria-hidden) → skips, returns False
  6. auto_dismiss exported from post_click_readiness (import smoke)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging

logger = logging.getLogger(__name__)


def _make_locator(count=0, visible=False):
    """Return a minimal Playwright-like locator mock."""
    loc = AsyncMock()
    loc.count = AsyncMock(return_value=count)
    loc.is_visible = AsyncMock(return_value=visible)
    loc.click = AsyncMock()
    loc.first = loc  # .first returns self
    return loc


def _make_page(modal_visible=False, modal_selector=".modal.show", button_text_matched=None):
    """
    Build a mock page whose locator() returns modals/buttons according to params.

    modal_visible   – True  → locator returns count=1 + is_visible=True for the modal
    button_text_matched – str or None; if str, button with that label returns count=1+visible
    """
    page = MagicMock()

    no_result = _make_locator(count=0, visible=False)
    modal_loc = _make_locator(count=1 if modal_visible else 0, visible=modal_visible)

    # btn_mock – found (count=1) and visible only when text matches button_text_matched
    btn_matched = _make_locator(count=1, visible=True)
    btn_none = _make_locator(count=0, visible=False)

    def _locator_factory(selector, **kwargs):
        # Return modal for the modal selector, nothing for others
        if selector == modal_selector:
            return modal_loc
        return no_result

    page.locator = MagicMock(side_effect=_locator_factory)

    # Implement get_by_role on the modal locator so "button" lookups work
    def _modal_get_by_role(role, name="", exact=False):
        if role == "button" and button_text_matched and name.lower() == button_text_matched.lower():
            return btn_matched
        return btn_none

    modal_loc.get_by_role = MagicMock(side_effect=_modal_get_by_role)
    return page, btn_matched


# ---------------------------------------------------------------------------
# Test 1 — No modal visible → no click, returns False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_modal_returns_false():
    """When no modal selector matches a visible element, returns False without clicking."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(modal_visible=False)

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is False
    btn.click.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 2 — .modal.show visible with "I understand" → clicks it, returns True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_modal_show_i_understand_clicked():
    """Visible .modal.show with 'I understand' button → button is clicked, returns True."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="i understand",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is True
    btn.click.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 3 — [role="dialog"] visible but no recognised button → returns False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_aria_dialog_no_button_returns_false():
    """Visible [role='dialog'] with no recognised dismiss button → returns False."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector="[role='dialog']",
        button_text_matched=None,   # No matching dismiss button
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is False
    btn.click.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 4 — Modal with "OK" button → clicks it, returns True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_modal_ok_button_clicked():
    """Visible modal with 'OK' button → button is clicked, returns True."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="ok",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is True
    btn.click.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 5 — Modal element exists (count=1) but is_visible=False → skips, returns False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_hidden_modal_not_dismissed():
    """Modal in DOM (count=1) but not visible (aria-hidden) → nothing clicked, returns False."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    # count=1 but visible=False → should be skipped
    page = MagicMock()
    no_result = _make_locator(count=0, visible=False)
    modal_hidden = _make_locator(count=1, visible=False)
    page.locator = MagicMock(side_effect=lambda s, **kw: modal_hidden if s == ".modal.show" else no_result)
    modal_hidden.get_by_role = MagicMock(return_value=no_result)

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is False


# ---------------------------------------------------------------------------
# Test 6 — Import smoke: auto_dismiss_blocking_modals is exported
# ---------------------------------------------------------------------------

def test_auto_dismiss_is_exported():
    """auto_dismiss_blocking_modals is importable from post_click_readiness."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals  # noqa: F401
    assert callable(auto_dismiss_blocking_modals)
