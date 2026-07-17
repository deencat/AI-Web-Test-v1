"""
Shared signature-pad locate / stroke / ink-verify helpers.

Feature 5 / Sprint 11–13: programmatic stroke is the source of truth for
``draw_signature`` / ``sign``. Prefer pointer/mouse/touch events (SignaturePad-
compatible); optional canvas ctx paint is a visual supplement only — never the
sole basis for PASS when the library stays empty.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Optional, Sequence

logger = logging.getLogger(__name__)

# Soft act() methods that must NEVER imply the pad was signed.
SOFT_ACT_METHODS = frozenset(
    {
        "scrollintoview",
        "scroll",
        "scrollinto",
        "locator",
        "highlight",
        "focus",
        "hover",
    }
)

_SIGNATURE_SELECTORS: Sequence[str] = (
    "canvas.signature-pad",
    "canvas[id*='signature' i]",
    "canvas[class*='signature' i]",
    "canvas[data-testid*='signature' i]",
)

_NEAR_LABEL_TEXTS: Sequence[str] = (
    "Please sign here",
    "please sign here",
    "Sign here",
    "sign here",
    "Signature",
    "signature",
)

# Click/open/tap a Signature *control* (modal opener) → click, not draw.
_SIGNATURE_CONTROL_CLICK_RE = re.compile(
    r"\b(click|open|tap)\b.{0,80}\bsignature\b",
    re.IGNORECASE | re.DOTALL,
)
_SIGN_BUTTON_CLICK_RE = re.compile(
    r"\b(click|open|tap)\b.{0,80}\bsign\b.{0,40}\bbutton\b",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class SignResult:
    success: bool
    error: Optional[str] = None
    ink_verified: bool = False
    xpath: Optional[str] = None


def is_soft_act_method(method: Optional[str]) -> bool:
    """Return True if an act() method is locate/scroll-only (not a real stroke)."""
    if not method:
        return False
    normalized = re.sub(r"[\s_-]+", "", str(method).lower())
    return normalized in SOFT_ACT_METHODS or "scrollinto" in normalized


def infer_signature_step_action(instruction: str) -> Optional[str]:
    """
    Map NL instruction to click vs draw_signature when signature-related.

    Returns:
        ``\"click\"`` for opening a Signature control,
        ``\"draw_signature\"`` for true sign/draw-on-pad phrasing,
        ``None`` when the instruction is not signature-related.
    """
    if not instruction or not str(instruction).strip():
        return None
    text = str(instruction).strip()
    lower = text.lower()

    if _SIGNATURE_CONTROL_CLICK_RE.search(text) or _SIGN_BUTTON_CLICK_RE.search(text):
        return "click"

    # True sign / draw-on-pad
    if re.search(r"\bdraw\s+signature\b", lower):
        return "draw_signature"
    if re.search(r"\bsign\s+(it|here|under|on|the)\b", lower):
        return "draw_signature"
    if re.search(r"\bsignature\b", lower) and not re.search(
        r"\b(click|open|tap)\b", lower
    ):
        return "draw_signature"
    if re.search(r"\bsign\b", lower) and not re.search(r"\b(click|open|tap)\b", lower):
        return "draw_signature"
    # e.g. "Click and sign" — has click + sign but is not a Signature *button* opener
    if "sign" in lower or "signature" in lower:
        return "draw_signature"
    return None


async def locate_signature_canvas(
    page: Any,
    instruction: Optional[str] = None,
    *,
    xpath: Optional[str] = None,
):
    """
    Locate a signature ``<canvas>`` using xpath, named selectors, near-label
    heuristics, then largest visible canvas.
    """
    if xpath:
        locator = page.locator(f"xpath={xpath}").first
        if await locator.count() > 0:
            logger.info("[signature_pad] Located canvas via xpath")
            return locator

    for selector in _SIGNATURE_SELECTORS:
        try:
            locator = page.locator(selector).first
            if await locator.count() > 0 and await _is_visible_enough(locator):
                logger.info("[signature_pad] Located canvas via selector: %s", selector)
                return locator
        except Exception:
            continue

    # Near-label heuristics (instruction + common phrases)
    labels = list(_NEAR_LABEL_TEXTS)
    if instruction:
        for phrase in _extract_quoted_phrases(instruction):
            if phrase and phrase not in labels:
                labels.insert(0, phrase)
        # Also try raw instruction snippets containing "sign"
        if "sign" in instruction.lower() and instruction not in labels:
            labels.append(instruction.strip()[:80])

    for label in labels:
        try:
            handle = await page.evaluate_handle(
                """
                (labelText) => {
                    const normalize = (s) => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                    const target = normalize(labelText);
                    if (!target) return null;

                    const candidates = Array.from(
                        document.querySelectorAll('label, p, span, div, h1, h2, h3, h4, legend, strong')
                    );
                    for (const el of candidates) {
                        const text = normalize(el.textContent);
                        if (!text || text.length > 200) continue;
                        if (!text.includes(target) && !target.includes(text)) continue;

                        // Prefer canvas inside shared ancestor / following sibling
                        let node = el;
                        for (let depth = 0; depth < 6 && node; depth++) {
                            const canvas = node.querySelector && node.querySelector('canvas');
                            if (canvas) {
                                const rect = canvas.getBoundingClientRect();
                                if (rect.width > 20 && rect.height > 20) return canvas;
                            }
                            node = node.parentElement;
                        }
                        // Next siblings
                        let sib = el.nextElementSibling;
                        for (let i = 0; i < 5 && sib; i++) {
                            const canvas = sib.tagName === 'CANVAS'
                                ? sib
                                : (sib.querySelector && sib.querySelector('canvas'));
                            if (canvas) {
                                const rect = canvas.getBoundingClientRect();
                                if (rect.width > 20 && rect.height > 20) return canvas;
                            }
                            sib = sib.nextElementSibling;
                        }
                    }
                    return null;
                }
                """,
                label,
            )
            element = handle.as_element() if handle else None
            if element:
                locator = page.locator("canvas").nth(
                    await _index_of_element(page, element)
                )
                # Prefer wrapping the element handle as a locator when possible
                try:
                    from playwright.async_api import ElementHandle

                    if isinstance(element, ElementHandle) or hasattr(element, "evaluate"):
                        # Build locator from evaluated element via unique mark
                        marked = await page.evaluate(
                            """
                            (el) => {
                                if (!el) return -1;
                                const all = Array.from(document.querySelectorAll('canvas'));
                                return all.indexOf(el);
                            }
                            """,
                            element,
                        )
                        if isinstance(marked, int) and marked >= 0:
                            locator = page.locator("canvas").nth(marked)
                            if await locator.count() > 0:
                                logger.info(
                                    "[signature_pad] Located canvas near label: %r",
                                    label,
                                )
                                return locator
                except Exception:
                    pass
        except Exception as exc:
            logger.debug("[signature_pad] Near-label locate failed for %r: %s", label, exc)

    # Largest visible canvas in viewport
    try:
        index = await page.evaluate(
            """
            () => {
                const canvases = Array.from(document.querySelectorAll('canvas'));
                let bestIdx = -1;
                let bestArea = 0;
                const vw = window.innerWidth || 0;
                const vh = window.innerHeight || 0;
                canvases.forEach((c, i) => {
                    const r = c.getBoundingClientRect();
                    if (r.width < 20 || r.height < 20) return;
                    const visible =
                        r.bottom > 0 && r.right > 0 && r.top < vh && r.left < vw;
                    if (!visible) return;
                    const area = r.width * r.height;
                    if (area > bestArea) {
                        bestArea = area;
                        bestIdx = i;
                    }
                });
                return bestIdx;
            }
            """
        )
        if isinstance(index, int) and index >= 0:
            locator = page.locator("canvas").nth(index)
            if await locator.count() > 0:
                logger.info(
                    "[signature_pad] Located largest visible canvas (index=%s)", index
                )
                return locator
    except Exception as exc:
        logger.debug("[signature_pad] Largest-canvas locate failed: %s", exc)

    raise ValueError("No signature canvas found")


async def _is_visible_enough(locator) -> bool:
    try:
        if hasattr(locator, "is_visible"):
            return bool(await locator.is_visible())
    except Exception:
        pass
    try:
        return (await locator.count()) > 0
    except Exception:
        return False


async def _index_of_element(page, element) -> int:
    try:
        idx = await page.evaluate(
            """
            (el) => {
                const all = Array.from(document.querySelectorAll('canvas'));
                return all.indexOf(el);
            }
            """,
            element,
        )
        return int(idx) if isinstance(idx, int) and idx >= 0 else 0
    except Exception:
        return 0


def _extract_quoted_phrases(instruction: str) -> list[str]:
    return [m.strip() for m in re.findall(r'["\']([^"\']+)["\']', instruction or "")]


async def draw_signature_stroke(
    page: Any,
    canvas,
    *,
    include_ctx_paint: bool = True,
) -> None:
    """
    Draw a multi-strategy stroke on ``canvas``.

    Order (events preferred for SignaturePad ``isEmpty``):
    1. Playwright mouse drag across bbox
    2. pointer / mouse / touch dispatch
    3. Optional ctx 2d stroke as visual supplement only
    """
    await canvas.scroll_into_view_if_needed()
    try:
        await canvas.focus()
    except Exception:
        pass
    await asyncio.sleep(0.05)

    bbox = await canvas.bounding_box()
    if not bbox:
        raise ValueError("Cannot get bounding box for signature canvas")

    canvas_x = bbox["x"]
    canvas_y = bbox["y"]
    canvas_width = bbox["width"]
    canvas_height = bbox["height"]

    # 1) Mouse drag (cursive-ish path)
    points = [
        (canvas_x + canvas_width * 0.1, canvas_y + canvas_height * 0.5),
        (canvas_x + canvas_width * 0.25, canvas_y + canvas_height * 0.35),
        (canvas_x + canvas_width * 0.4, canvas_y + canvas_height * 0.6),
        (canvas_x + canvas_width * 0.55, canvas_y + canvas_height * 0.4),
        (canvas_x + canvas_width * 0.75, canvas_y + canvas_height * 0.55),
        (canvas_x + canvas_width * 0.85, canvas_y + canvas_height * 0.45),
    ]
    await page.mouse.move(points[0][0], points[0][1])
    await page.mouse.down()
    for x, y in points[1:]:
        await page.mouse.move(x, y, steps=5)
        await asyncio.sleep(0.01)
    await page.mouse.up()
    await asyncio.sleep(0.05)

    # 2) Pointer / mouse / touch events (SignaturePad listeners)
    drag_start_x = canvas_x + canvas_width * 0.25
    drag_start_y = canvas_y + canvas_height * 0.5
    drag_end_x = canvas_x + canvas_width * 0.65
    drag_end_y = canvas_y + canvas_height * 0.5

    await canvas.dispatch_event(
        "pointerdown",
        {
            "clientX": drag_start_x,
            "clientY": drag_start_y,
            "buttons": 1,
            "pointerType": "pen",
            "pressure": 0.5,
            "bubbles": True,
        },
    )
    await canvas.dispatch_event(
        "pointermove",
        {
            "clientX": drag_end_x,
            "clientY": drag_end_y,
            "buttons": 1,
            "pointerType": "pen",
            "pressure": 0.5,
            "bubbles": True,
        },
    )
    await canvas.dispatch_event(
        "pointerup",
        {
            "clientX": drag_end_x,
            "clientY": drag_end_y,
            "buttons": 0,
            "pointerType": "pen",
            "pressure": 0,
            "bubbles": True,
        },
    )

    await canvas.dispatch_event(
        "mousedown",
        {"clientX": drag_start_x, "clientY": drag_start_y, "buttons": 1, "bubbles": True},
    )
    await canvas.dispatch_event(
        "mousemove",
        {"clientX": drag_end_x, "clientY": drag_end_y, "buttons": 1, "bubbles": True},
    )
    await canvas.dispatch_event(
        "mouseup",
        {"clientX": drag_end_x, "clientY": drag_end_y, "buttons": 0, "bubbles": True},
    )

    await canvas.evaluate(
        """
        (canvas) => {
            try {
                const rect = canvas.getBoundingClientRect();
                const x = rect.left + rect.width * 0.3;
                const y = rect.top + rect.height * 0.5;
                const touch = new Touch({
                    identifier: Date.now(),
                    target: canvas,
                    clientX: x,
                    clientY: y,
                    radiusX: 2,
                    radiusY: 2,
                    rotationAngle: 0,
                    force: 0.5,
                });
                canvas.dispatchEvent(new TouchEvent('touchstart', {
                    touches: [touch], bubbles: true, cancelable: true
                }));
                canvas.dispatchEvent(new TouchEvent('touchmove', {
                    touches: [touch], bubbles: true, cancelable: true
                }));
                canvas.dispatchEvent(new TouchEvent('touchend', {
                    changedTouches: [touch], bubbles: true, cancelable: true
                }));
            } catch (err) {
                // TouchEvent may be unsupported
            }
        }
        """
    )

    await canvas.dispatch_event("input", {"bubbles": True})
    await canvas.dispatch_event("change", {"bubbles": True})

    # 3) Optional ctx paint — supplement only (after events)
    if include_ctx_paint:
        await canvas.evaluate(
            """
            (canvas) => {
                const width = canvas.clientWidth || 300;
                const height = canvas.clientHeight || 150;
                if (!canvas.width || !canvas.height) {
                    canvas.width = width;
                    canvas.height = height;
                }
                const ctx = canvas.getContext('2d');
                if (!ctx) return false;
                ctx.save();
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.lineCap = 'round';
                ctx.beginPath();
                ctx.moveTo(width * 0.2, height * 0.5);
                ctx.lineTo(width * 0.8, height * 0.5);
                ctx.stroke();
                ctx.restore();
                return true;
            }
            """
        )

    logger.info("[signature_pad] Stroke strategies applied (mouse + pointer/touch + optional ctx)")


async def verify_signature_ink(page: Any, canvas) -> bool:
    """
    Return True when the pad has ink.

    Prefer SignaturePad ``isEmpty === false`` when the library is present;
    otherwise sample canvas pixels for non-blank content.
    """
    try:
        result = await canvas.evaluate(
            """
            (canvas) => {
                // SignaturePad instance on element or nearby
                const pad =
                    canvas.signaturePad ||
                    canvas._signaturePad ||
                    (canvas.__signaturePad) ||
                    (window.signaturePad && window.signaturePad.canvas === canvas
                        ? window.signaturePad : null);

                if (pad && typeof pad.isEmpty === 'function') {
                    return { source: 'signaturepad', empty: pad.isEmpty() };
                }
                if (pad && typeof pad.isEmpty === 'boolean') {
                    return { source: 'signaturepad', empty: pad.isEmpty };
                }

                // Common data attribute / sibling hooks
                try {
                    const parent = canvas.parentElement;
                    if (parent) {
                        const keys = Object.keys(parent);
                        for (const k of keys) {
                            const v = parent[k];
                            if (v && typeof v.isEmpty === 'function') {
                                return { source: 'signaturepad', empty: v.isEmpty() };
                            }
                        }
                    }
                } catch (e) {}

                const ctx = canvas.getContext('2d');
                if (!ctx) return { source: 'pixels', empty: true };
                const w = canvas.width || 0;
                const h = canvas.height || 0;
                if (w < 2 || h < 2) return { source: 'pixels', empty: true };

                const sample = ctx.getImageData(0, 0, w, h).data;
                // Look for non-near-white / non-transparent pixels
                let ink = 0;
                const step = 16; // sample every 4th pixel (RGBA stride * 4)
                for (let i = 0; i < sample.length; i += step) {
                    const r = sample[i];
                    const g = sample[i + 1];
                    const b = sample[i + 2];
                    const a = sample[i + 3];
                    if (a > 10 && (r < 250 || g < 250 || b < 250)) {
                        ink++;
                        if (ink > 5) {
                            return { source: 'pixels', empty: false };
                        }
                    }
                }
                return { source: 'pixels', empty: ink === 0 };
            }
            """
        )
    except Exception as exc:
        logger.warning("[signature_pad] Ink verification evaluate failed: %s", exc)
        return False

    if not isinstance(result, dict):
        return bool(result)

    empty = result.get("empty", True)
    source = result.get("source", "unknown")
    has_ink = empty is False
    logger.info(
        "[signature_pad] Ink verify source=%s empty=%s has_ink=%s",
        source,
        empty,
        has_ink,
    )
    return has_ink


async def sign_canvas(
    page: Any,
    *,
    instruction: Optional[str] = None,
    xpath: Optional[str] = None,
    include_ctx_paint: bool = True,
) -> SignResult:
    """
    Locate canvas, draw multi-strategy stroke, verify ink.

    Returns ``SignResult`` with ``success=False`` and a clear error when no
    canvas is found or ink verification fails (fail closed — never silent PASS).
    """
    try:
        canvas = await locate_signature_canvas(
            page, instruction=instruction, xpath=xpath
        )
    except Exception as exc:
        msg = str(exc) or "No signature canvas found"
        logger.warning("[signature_pad] Locate failed: %s", msg)
        return SignResult(success=False, error=msg, ink_verified=False)

    try:
        await draw_signature_stroke(
            page, canvas, include_ctx_paint=include_ctx_paint
        )
    except Exception as exc:
        msg = f"Signature stroke failed: {exc}"
        logger.warning("[signature_pad] %s", msg)
        return SignResult(success=False, error=msg, ink_verified=False)

    has_ink = await verify_signature_ink(page, canvas)
    if not has_ink:
        msg = "Signature pad appears empty after stroke (ink verification failed)"
        logger.warning("[signature_pad] %s", msg)
        return SignResult(success=False, error=msg, ink_verified=False)

    resolved_xpath = xpath
    if not resolved_xpath:
        try:
            resolved_xpath = await canvas.evaluate(
                """
                (el) => {
                    if (!el || !el.getRootNode) return null;
                    // Best-effort absolute xpath
                    function xpathFor(node) {
                        if (node.id) return '//*[@id=\"' + node.id + '\"]';
                        if (node === document.body) return '/html/body';
                        let ix = 0;
                        const siblings = node.parentNode ? node.parentNode.childNodes : [];
                        for (let i = 0; i < siblings.length; i++) {
                            const sib = siblings[i];
                            if (sib === node) {
                                const tag = node.tagName.toLowerCase();
                                const parentPath = xpathFor(node.parentNode);
                                return parentPath + '/' + tag + '[' + (ix + 1) + ']';
                            }
                            if (sib.nodeType === 1 && sib.tagName === node.tagName) ix++;
                        }
                        return null;
                    }
                    return xpathFor(el);
                }
                """
            )
        except Exception:
            resolved_xpath = None

    logger.info("[signature_pad] Sign succeeded with ink verified")
    return SignResult(
        success=True,
        error=None,
        ink_verified=True,
        xpath=resolved_xpath if isinstance(resolved_xpath, str) else xpath,
    )
