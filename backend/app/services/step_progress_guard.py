"""Helpers for detecting visible progress across repeated confirm steps."""

from dataclasses import dataclass

from app.services.post_click_readiness import MODAL_CONTAINER_SELECTORS

BODY_SELECTOR = "body"
MAX_SIGNATURE_CHARS = 400


@dataclass(frozen=True)
class StepProgressSnapshot:
    """Compact snapshot of the visible UI state around a step."""

    url: str
    modal_signature: str
    body_signature: str


def should_enforce_confirm_progress(step: dict) -> bool:
    """Return True for repeated business-confirm clicks that must visibly advance."""
    action = (step.get("action") or "").lower()
    instruction = (step.get("instruction") or "").lower()
    return action == "click" and "confirm" in instruction


def has_confirm_step_progress(
    before: StepProgressSnapshot,
    after: StepProgressSnapshot,
    instruction: str,
) -> bool:
    """Return True when a confirm step caused a visible UI transition."""
    if "confirm" not in (instruction or "").lower():
        return True

    if before.url != after.url:
        return True

    if before.modal_signature != after.modal_signature:
        return True

    if not before.modal_signature and before.body_signature != after.body_signature:
        return True

    return False


async def capture_step_progress_snapshot(page) -> StepProgressSnapshot:
    """Capture a small, normalized snapshot of the current page or modal state."""
    modal_signature = await _capture_visible_modal_signature(page)
    body_signature = ""
    if not modal_signature:
        body_signature = await _capture_body_signature(page)

    return StepProgressSnapshot(
        url=(getattr(page, "url", "") or ""),
        modal_signature=modal_signature,
        body_signature=body_signature,
    )


async def _capture_visible_modal_signature(page) -> str:
    for selector in MODAL_CONTAINER_SELECTORS:
        try:
            modal = page.locator(selector).first
            if await modal.count() == 0 or not await modal.is_visible():
                continue
            return await _normalized_locator_text(modal)
        except Exception:
            continue

    return ""


async def _capture_body_signature(page) -> str:
    try:
        body = page.locator(BODY_SELECTOR).first
        if await body.count() == 0:
            return ""
        return await _normalized_locator_text(body)
    except Exception:
        return ""


async def _normalized_locator_text(locator) -> str:
    raw_text = ""

    try:
        raw_text = await locator.inner_text()
    except Exception:
        raw_text = ""

    if not raw_text:
        try:
            raw_text = await locator.text_content()
        except Exception:
            raw_text = ""

    collapsed = " ".join((raw_text or "").split()).strip().lower()
    return collapsed[:MAX_SIGNATURE_CHARS]