"""Shared helpers for stabilizing the page after click actions."""

import asyncio
import inspect
from typing import Dict

from playwright.async_api import TimeoutError as PlaywrightTimeout

LOADING_SELECTORS = [
    "div[role='status'].spinner-border",
    "[role='status'].spinner-border",
    "[class*='loading']",
    "[class*='spinner']",
    "[class*='skeleton']",
    "[class*='shimmer']",
    "[class*='overlay']",
    "[aria-busy='true']",
    ".loading",
    ".spinner",
    ".skeleton",
    ".shimmer",
    ".overlay",
    "iframe[class*='load']",
    "[id*='loading']",
    "[id*='spinner']",
    "[id*='skeleton']",
]

NAVIGATION_KEYWORDS = [
    "next",
    "continue",
    "submit",
    "proceed",
    "upload",
    "confirm",
    "checkout",
    "payment",
    "pay",
    "login",
    "log in",
    "log-in",
    "sign in",
    "sign-in",
    "signin",
]

PAYMENT_KEYWORDS = ["checkout", "payment", "pay"]
AUTH_KEYWORDS = ["login", "log in", "log-in", "sign in", "sign-in", "signin", "authenticate"]
STEP_BOUNDARY_LOADING_TIMEOUT_MS = 15000

# Modal/dialog container selectors checked in order for auto-dismissal.
MODAL_CONTAINER_SELECTORS = [
    ".modal.show",
    "[role='dialog']",
    "[aria-modal='true']",
]

# Button label texts tried in order when dismissing a detected modal.
# Matching is case-insensitive via Playwright's get_by_role name= parameter.
SAFE_MODAL_DISMISS_BUTTON_TEXTS = [
    "I understand",
    "I Understand",
    "OK",
    "Ok",
    "Close",
    "Dismiss",
    "Got it",
    "Accept",
    "Agree",
]

CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS = [
    "Confirm",
    "Continue",
    "Done",
]

NUISANCE_MODAL_TEXT_TOKENS = (
    "reminder",
    "notice",
    "informational",
    "information",
    "session expired",
    "session timeout",
    "timed out",
    "maintenance",
    "security reminder",
    "i understand",
    "got it",
)

GENERIC_OVERLAY_SELECTORS = {"[class*='overlay']", ".overlay"}
LOADING_SIGNAL_TOKENS = ("loading", "spinner", "skeleton", "shimmer")
INTERACTABLE_MODAL_CHILD_SELECTOR = (
    "input, button, textarea, select, [contenteditable='true'], [role='button']"
)


def _combined_click_text(instruction: str, element_text: str) -> str:
    return " ".join(part for part in [instruction or "", element_text or ""] if part).lower()


async def _locator_attribute(locator, name: str) -> str:
    try:
        raw_value = await locator.get_attribute(name)
    except Exception:
        return ""

    return raw_value.lower() if isinstance(raw_value, str) else ""


async def _locator_text(locator) -> str:
    for method_name in ("inner_text", "text_content"):
        method = getattr(locator, method_name, None)
        if not callable(method):
            continue

        try:
            value = await method()
        except Exception:
            continue

        if isinstance(value, str) and value.strip():
            return " ".join(value.split()).strip().lower()

    return ""


def _call_sync_locator_method(locator, method_name: str, *args, **kwargs):
    method = getattr(locator, method_name, None)
    if not callable(method) or inspect.iscoroutinefunction(method):
        return None

    try:
        return method(*args, **kwargs)
    except Exception:
        return None


async def _overlay_has_loading_signal(locator) -> bool:
    """Treat generic overlays as blockers only when they resemble real loading UI."""
    if await _locator_attribute(locator, "aria-busy") == "true":
        return True

    class_hints = " ".join([
        await _locator_attribute(locator, "class"),
        await _locator_attribute(locator, "id"),
    ])
    if any(token in class_hints for token in LOADING_SIGNAL_TOKENS):
        return True

    signal_selectors = [
        "[role='status']",
        "[aria-busy='true']",
        "[class*='spinner']",
        "[class*='loading']",
        ".spinner",
        ".loading",
    ]

    for selector in signal_selectors:
        try:
            signal_locator = _call_sync_locator_method(locator, "locator", selector)
            if signal_locator is None:
                continue

            signal = signal_locator.first
            if await signal.count() > 0:
                return True
        except Exception:
            continue

    return False


async def _visible_interactable_modal_present(page) -> bool:
    """Return True when a modal/dialog is still open and ready for the next auth action."""
    for container_sel in MODAL_CONTAINER_SELECTORS:
        try:
            modal = page.locator(container_sel).first
            if await modal.count() == 0 or not await modal.is_visible():
                continue

            interactive_locator = _call_sync_locator_method(
                modal,
                "locator",
                INTERACTABLE_MODAL_CHILD_SELECTOR,
            )
            if interactive_locator is None:
                continue

            interactive = interactive_locator.first
            if await interactive.count() > 0:
                return True
        except Exception:
            continue

    return False


async def _modal_allows_business_autodismiss(modal) -> bool:
    """Return True when a modal looks like a nuisance/info blocker, not business flow UI."""
    modal_text = await _locator_text(modal)
    return any(token in modal_text for token in NUISANCE_MODAL_TEXT_TOKENS)


def classify_click_transition(instruction: str, element_text: str) -> Dict[str, bool]:
    """Classify whether a click is likely to trigger a page or modal transition."""
    combined_text = _combined_click_text(instruction, element_text)

    is_payment_click = any(keyword in combined_text for keyword in PAYMENT_KEYWORDS)
    is_auth_click = any(keyword in combined_text for keyword in AUTH_KEYWORDS)
    is_navigation_click = any(keyword in combined_text for keyword in NAVIGATION_KEYWORDS)

    return {
        "is_auth_click": is_auth_click,
        "is_navigation_click": is_navigation_click or is_auth_click or is_payment_click,
        "is_payment_click": is_payment_click,
    }


async def auto_dismiss_blocking_modals(page, logger) -> bool:
    """
    Detect visible modal/dialog overlays and auto-click their dismiss button.

    Called after page navigation to clear mandatory modals (e.g. Three HK preprod
    "I understand" reminder) before the next test step executes.  This is the
    deterministic equivalent of the ObservationAgent LLM instruction:
    "If a reminder, confirmation, or informational modal appears, click the
    close, confirm, or I understand button" (ADR-004-5 / ADR-002-19-C).

    Returns True if at least one modal was dismissed, False if no modal was present.
    """
    for container_sel in MODAL_CONTAINER_SELECTORS:
        try:
            modal = page.locator(container_sel).first
            if await modal.count() == 0:
                continue
            if not await modal.is_visible():
                continue

            logger.info("[Modal] Visible overlay detected via '%s' — attempting auto-dismiss", container_sel)

            button_texts = list(SAFE_MODAL_DISMISS_BUTTON_TEXTS)
            if await _modal_allows_business_autodismiss(modal):
                button_texts.extend(CONDITIONAL_MODAL_DISMISS_BUTTON_TEXTS)

            for btn_text in button_texts:
                try:
                    btn = _call_sync_locator_method(
                        modal,
                        "get_by_role",
                        "button",
                        name=btn_text,
                        exact=False,
                    )
                    if btn is None:
                        continue

                    if await btn.count() == 0:
                        continue
                    await btn.first.click(timeout=3000)
                    logger.info("[Modal] Auto-dismissed with button '%s'", btn_text)
                    await asyncio.sleep(0.5)
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


async def wait_for_loading_indicators_to_clear(page, logger, timeout_ms: int) -> None:
    """Wait for common loading indicators to disappear."""
    for selector in LOADING_SELECTORS:
        try:
            loading_element = page.locator(selector).first
            if await loading_element.count() > 0:
                if selector in GENERIC_OVERLAY_SELECTORS and not await _overlay_has_loading_signal(loading_element):
                    logger.debug("Ignoring non-loading overlay while checking readiness: %s", selector)
                    continue

                logger.info("Waiting for loading indicator to clear: %s", selector)
                await loading_element.wait_for(state="hidden", timeout=timeout_ms)
                logger.info("Loading indicator cleared: %s", selector)
        except Exception:
            continue


async def wait_for_step_boundary_readiness(page, logger, timeout_ms: int) -> None:
    """Wait for active loading indicators to clear before starting the next step."""
    wait_timeout = min(timeout_ms, STEP_BOUNDARY_LOADING_TIMEOUT_MS)
    await wait_for_loading_indicators_to_clear(page, logger, wait_timeout)
    await asyncio.sleep(0.2)


async def wait_for_post_click_readiness(
    page,
    clicked_element,
    instruction: str,
    element_text: str,
    current_url: str,
    timeout_ms: int,
    logger,
) -> Dict[str, bool]:
    """Apply bounded readiness waits after a click before the next step executes."""
    classification = classify_click_transition(instruction, element_text)
    wait_timeout = min(timeout_ms, 10000)

    await asyncio.sleep(0.2)

    url_changed = page.url != current_url
    if url_changed:
        logger.info("URL changed from %s to %s after click", current_url, page.url)
        # URL already changed → treat as navigation regardless of keyword classification.
        # Covers "Select plan" buttons on SPAs (e.g. Three HK preprod) where the button
        # text never matches NAVIGATION_KEYWORDS but a full page transition occurs.
        classification["is_navigation_click"] = True
        try:
            await page.wait_for_load_state("load", timeout=wait_timeout)
        except PlaywrightTimeout:
            logger.warning("Timed out waiting for page load after click")

    if not classification["is_navigation_click"]:
        try:
            await page.wait_for_load_state("networkidle", timeout=wait_timeout)
        except PlaywrightTimeout:
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            except PlaywrightTimeout:
                await asyncio.sleep(1)
        return classification

    if classification["is_auth_click"] and not url_changed:
        if await _visible_interactable_modal_present(page):
            logger.info("Auth modal remained interactable after click; skipping hidden/networkidle waits")
            return classification

    if classification["is_auth_click"]:
        auth_timeout = min(timeout_ms, 5000)
        try:
            await clicked_element.wait_for(state="hidden", timeout=auth_timeout)
        except Exception:
            logger.debug("Auth click target remained visible while waiting for popup to close")

        try:
            await page.wait_for_load_state("networkidle", timeout=auth_timeout)
        except PlaywrightTimeout:
            logger.debug("Auth click did not reach networkidle within %sms", auth_timeout)

    loading_timeout = 15000 if classification["is_payment_click"] else min(timeout_ms, 8000)
    await wait_for_loading_indicators_to_clear(page, logger, loading_timeout)
    await asyncio.sleep(0.4)

    # After a navigation click (including plan-selection redirects), auto-dismiss any
    # modal that appeared on the landing page.  This mirrors the ObservationAgent LLM
    # instruction "If a reminder/modal appears, click I understand" (ADR-002-19-C).
    if classification["is_navigation_click"]:
        await auto_dismiss_blocking_modals(page, logger)

    return classification
