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


def _make_locator(count=0, visible=False, text=""):
    """Return a minimal Playwright-like locator mock."""
    loc = AsyncMock()
    loc.count = AsyncMock(return_value=count)
    loc.is_visible = AsyncMock(return_value=visible)
    loc.click = AsyncMock()
    loc.inner_text = AsyncMock(return_value=text)
    loc.text_content = AsyncMock(return_value=text)
    loc.first = loc  # .first returns self
    return loc


def _make_page(
    modal_visible=False,
    modal_selector=".modal.show",
    button_text_matched=None,
    modal_text="",
):
    """
    Build a mock page whose locator() returns modals/buttons according to params.

    modal_visible   – True  → locator returns count=1 + is_visible=True for the modal
    button_text_matched – str or None; if str, button with that label returns count=1+visible
    """
    page = MagicMock()

    no_result = _make_locator(count=0, visible=False)
    modal_loc = _make_locator(
        count=1 if modal_visible else 0,
        visible=modal_visible,
        text=modal_text,
    )

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
# Test 2 — .modal.show visible with "I understand" on a NUISANCE modal → clicks it
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_modal_show_i_understand_clicked_for_nuisance_reminder():
    """Visible .modal.show nuisance reminder with 'I understand' button → clicked, returns True.

    'I understand' is conditional: it should only be clicked when the modal text
    contains a nuisance/informational token (e.g. 'reminder'), not on every modal.
    """
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="i understand",
        modal_text="this is a reminder about the uat preprod environment",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is True
    btn.click.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 2b — T&C business modal with "I understand" → must NOT be auto-dismissed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tnc_business_modal_i_understand_not_auto_dismissed():
    """Business T&C modal with 'I understand' button must NOT be auto-dismissed.

    Root cause fix for execution #689 / Test Case 101, Step 9:
    When Step 8 ('Click Next') navigates to T&C page, auto_dismiss_blocking_modals
    must not pre-emptively click 'I understand' because Step 9 is explicitly
    designated to do that as a business action.
    """
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="i understand",
        modal_text="please read the terms and conditions carefully before proceeding",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is False
    btn.click.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 2c — Nuisance token 'i understand' removed from NUISANCE_MODAL_TEXT_TOKENS
# ---------------------------------------------------------------------------

def test_nuisance_modal_text_tokens_does_not_contain_i_understand():
    """'i understand' must NOT be in NUISANCE_MODAL_TEXT_TOKENS.

    Root cause: a modal's own button label is not evidence of being a nuisance
    modal.  Including it caused any modal with an 'I understand' button to pass
    _modal_allows_business_autodismiss, defeating the business-flow guard.
    """
    from app.services.post_click_readiness import NUISANCE_MODAL_TEXT_TOKENS

    assert "i understand" not in NUISANCE_MODAL_TEXT_TOKENS, (
        "'i understand' must not be in NUISANCE_MODAL_TEXT_TOKENS — it is a button "
        "label, not a modal-purpose indicator; its presence defeats the business-flow guard"
    )


def test_nuisance_modal_text_tokens_does_not_contain_got_it():
    """'got it' must NOT be in NUISANCE_MODAL_TEXT_TOKENS for the same reason."""
    from app.services.post_click_readiness import NUISANCE_MODAL_TEXT_TOKENS

    assert "got it" not in NUISANCE_MODAL_TEXT_TOKENS, (
        "'got it' must not be in NUISANCE_MODAL_TEXT_TOKENS — it is a button label, "
        "not a modal-purpose indicator"
    )


# ---------------------------------------------------------------------------
# Test 2d — 'I understand' must be in CONDITIONAL, not SAFE list
# ---------------------------------------------------------------------------

def test_i_understand_is_in_conditional_not_safe_list():
    """'I understand' must live in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS, not SAFE.

    Being in SAFE means it is tried on every visible modal unconditionally,
    which causes it to be clicked even on business-flow T&C modals before the
    designated test step can interact with them.
    """
    from app.services.post_click_readiness import (
        SAFE_MODAL_DISMISS_BUTTON_TEXTS,
        CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS,
    )

    assert "I understand" not in SAFE_MODAL_DISMISS_BUTTON_TEXTS, (
        "'I understand' must not be in SAFE_MODAL_DISMISS_BUTTON_TEXTS; "
        "move it to CONDITIONAL so it is only clicked on confirmed nuisance modals"
    )
    assert "I understand" in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS, (
        "'I understand' must be in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS"
    )
    assert "I Understand" not in SAFE_MODAL_DISMISS_BUTTON_TEXTS
    assert "I Understand" in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS


# ---------------------------------------------------------------------------
# Test 2e — 'Close' must be in CONDITIONAL, not SAFE list
# ---------------------------------------------------------------------------

def test_close_is_in_conditional_not_safe_list():
    """'Close' must live in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS, not SAFE.

    Root cause fix for execution #692 / Test Case 101, Step 9 (second failure):
    After 'I understand' was moved to CONDITIONAL, the T&C (purchase) modal was
    still auto-dismissed via its Bootstrap 'Close' (X) button, which was in SAFE
    and fired unconditionally on any visible modal — consuming the modal before
    Step 9 could interact with it.
    """
    from app.services.post_click_readiness import (
        SAFE_MODAL_DISMISS_BUTTON_TEXTS,
        CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS,
    )

    assert "Close" not in SAFE_MODAL_DISMISS_BUTTON_TEXTS, (
        "'Close' must not be in SAFE_MODAL_DISMISS_BUTTON_TEXTS; "
        "move it to CONDITIONAL so it is only clicked on confirmed nuisance modals. "
        "On the Three HK T&C modal (account/purchase page), 'Close' is the X button "
        "that dismisses the whole dialog — clicking it auto-dismisses the business modal "
        "before Step 9 ('Click I understand') can execute."
    )
    assert "Close" in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS, (
        "'Close' must be in CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS"
    )


@pytest.mark.asyncio
async def test_tnc_modal_close_button_not_auto_dismissed():
    """Purchase-page T&C modal with 'Close' button must NOT be auto-dismissed.

    Root cause for execution #692: After the Next button click, the T&C Bootstrap
    modal appeared on the purchase page. auto_dismiss found the 'Close' (X) button
    in the SAFE list and clicked it, consuming the modal before Step 9 could run.
    """
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="close",
        modal_text="please agree to the terms and conditions before proceeding with your purchase",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is False
    btn.click.assert_not_awaited()


@pytest.mark.asyncio
async def test_session_expired_modal_close_button_is_auto_dismissed():
    """Session-expired nuisance modal with 'Close' button IS auto-dismissed.

    'Close' in CONDITIONAL means it fires when the modal is confirmed nuisance.
    A session-expired dialog is a true blocker with no business-flow value.
    The modal text must contain a NUISANCE_MODAL_TEXT_TOKENS token ('session expired')
    for _modal_allows_business_autodismiss to return True.
    """
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="close",
        modal_text="session expired please log in again",
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


@pytest.mark.asyncio
async def test_business_confirm_modal_is_not_auto_dismissed():
    """Business dialogs with Confirm should not be auto-dismissed."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="confirm",
        modal_text="Select Mobile Number Confirm the subscription details before proceeding",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is False
    btn.click.assert_not_awaited()


@pytest.mark.asyncio
async def test_reminder_confirm_modal_can_still_be_auto_dismissed():
    """Reminder dialogs may still auto-dismiss via Confirm when they are non-business blockers."""
    from app.services.post_click_readiness import auto_dismiss_blocking_modals

    page, btn = _make_page(
        modal_visible=True,
        modal_selector=".modal.show",
        button_text_matched="confirm",
        modal_text="Reminder Please confirm you understand this informational notice",
    )

    result = await auto_dismiss_blocking_modals(page, logger)

    assert result is True
    btn.click.assert_awaited_once()
