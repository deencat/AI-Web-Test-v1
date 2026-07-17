"""
Shared signature-pad locate / stroke / ink-verify helpers.

Feature 5 / Sprint 11–14: programmatic stroke is the source of truth for
``draw_signature`` / ``sign``. Prefer pointer/mouse/touch events (SignaturePad-
compatible). Optional canvas ctx paint is off by default — never the sole
basis for PASS (cosmetic ink / ``source=pixels`` after ctx paint is a false PASS).
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
    verify_source: Optional[str] = None


@dataclass
class InkVerifyResult:
    """Structured ink-gate outcome (``source`` is logged as verify_source)."""

    has_ink: bool
    source: str  # signaturepad | pixels | required_cleared | fail | unknown


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


# Multi-point PointerEvent + MouseEvent + TouchEvent path (SignaturePad-compatible).
# Mirrors ObservationAgent browser_use_signature_tool: pointerId/isPrimary + real drag.
_STROKE_POINTER_JS = """
(canvas) => {
  const r = canvas.getBoundingClientRect();
  if (r.width < 10 || r.height < 10) {
    return { ok: false, error: 'canvas_too_small' };
  }

  const firePointer = (type, clientX, clientY) => {
    const opts = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      clientX,
      clientY,
      screenX: clientX,
      screenY: clientY,
      pointerId: 1,
      pointerType: 'pen',
      isPrimary: true,
      pressure: type === 'pointerup' ? 0 : 0.5,
      button: 0,
      buttons: type === 'pointerup' ? 0 : 1,
    };
    canvas.dispatchEvent(new PointerEvent(type, opts));
  };

  const fireMouse = (type, clientX, clientY) => {
    const buttons = type === 'mouseup' ? 0 : 1;
    canvas.dispatchEvent(new MouseEvent(type, {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX,
      clientY,
      button: 0,
      buttons,
    }));
  };

  const steps = 28;
  const x0 = r.left + r.width * 0.12;
  const y0 = r.top + r.height * 0.52;
  firePointer('pointerdown', x0, y0);
  fireMouse('mousedown', x0, y0);
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const clientX = r.left + r.width * (0.12 + t * 0.72);
    const clientY = r.top + r.height * (0.52 + 0.14 * Math.sin(t * Math.PI));
    firePointer('pointermove', clientX, clientY);
    fireMouse('mousemove', clientX, clientY);
  }
  const xe = r.left + r.width * 0.88;
  const ye = r.top + r.height * 0.48;
  firePointer('pointerup', xe, ye);
  fireMouse('mouseup', xe, ye);

  // Touch drag: move != start (actual drag). Prefer #touchContainer when present.
  try {
    const touchTarget =
      (canvas.closest && canvas.closest('#touchContainer')) ||
      (canvas.parentElement && canvas.parentElement.id === 'touchContainer'
        ? canvas.parentElement : null) ||
      canvas;
    const id = Date.now() % 100000;
    const mkTouch = (clientX, clientY) => new Touch({
      identifier: id,
      target: touchTarget,
      clientX,
      clientY,
      pageX: clientX,
      pageY: clientY,
      radiusX: 2,
      radiusY: 2,
      rotationAngle: 0,
      force: 0.5,
    });
    const t0 = mkTouch(x0, y0);
    touchTarget.dispatchEvent(new TouchEvent('touchstart', {
      bubbles: true, cancelable: true, touches: [t0], targetTouches: [t0], changedTouches: [t0],
    }));
    for (let i = 1; i <= 12; i++) {
      const t = i / 12;
      const tx = r.left + r.width * (0.12 + t * 0.72);
      const ty = r.top + r.height * (0.52 + 0.1 * Math.sin(t * Math.PI));
      const tm = mkTouch(tx, ty);
      touchTarget.dispatchEvent(new TouchEvent('touchmove', {
        bubbles: true, cancelable: true, touches: [tm], targetTouches: [tm], changedTouches: [tm],
      }));
    }
    const te = mkTouch(xe, ye);
    touchTarget.dispatchEvent(new TouchEvent('touchend', {
      bubbles: true, cancelable: true, touches: [], targetTouches: [], changedTouches: [te],
    }));
  } catch (err) {
    // Touch constructors may be unsupported
  }

  canvas.dispatchEvent(new Event('input', { bubbles: true }));
  canvas.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, width: r.width, height: r.height };
}
"""


async def draw_signature_stroke(
    page: Any,
    canvas,
    *,
    include_ctx_paint: bool = False,
) -> None:
    """
    Draw a multi-strategy stroke on ``canvas``.

    Order (events preferred for SignaturePad ``isEmpty``):
    1. Playwright mouse drag across bbox
    2. Real PointerEvent / MouseEvent / TouchEvent multi-point path
    3. Optional Playwright touchscreen tap-drag when available
    4. Optional ctx 2d stroke — **off by default**; cosmetic only, never a PASS signal
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

    # 2) Real PointerEvent multi-point path (+ mouse + touch drag)
    try:
        await canvas.evaluate(_STROKE_POINTER_JS)
    except Exception as exc:
        logger.debug("[signature_pad] Pointer JS stroke failed, falling back: %s", exc)
        # Fallback: Playwright dispatch_event with pointerId/isPrimary
        drag_start_x = canvas_x + canvas_width * 0.25
        drag_start_y = canvas_y + canvas_height * 0.5
        mid_x = canvas_x + canvas_width * 0.45
        mid_y = canvas_y + canvas_height * 0.4
        drag_end_x = canvas_x + canvas_width * 0.65
        drag_end_y = canvas_y + canvas_height * 0.5
        for etype, x, y, buttons in (
            ("pointerdown", drag_start_x, drag_start_y, 1),
            ("pointermove", mid_x, mid_y, 1),
            ("pointermove", drag_end_x, drag_end_y, 1),
            ("pointerup", drag_end_x, drag_end_y, 0),
        ):
            await canvas.dispatch_event(
                etype,
                {
                    "clientX": x,
                    "clientY": y,
                    "buttons": buttons,
                    "button": 0,
                    "pointerId": 1,
                    "pointerType": "pen",
                    "isPrimary": True,
                    "pressure": 0.5 if buttons else 0,
                    "bubbles": True,
                },
            )
        await canvas.dispatch_event(
            "mousedown",
            {"clientX": drag_start_x, "clientY": drag_start_y, "buttons": 1, "bubbles": True},
        )
        await canvas.dispatch_event(
            "mousemove",
            {"clientX": mid_x, "clientY": mid_y, "buttons": 1, "bubbles": True},
        )
        await canvas.dispatch_event(
            "mousemove",
            {"clientX": drag_end_x, "clientY": drag_end_y, "buttons": 1, "bubbles": True},
        )
        await canvas.dispatch_event(
            "mouseup",
            {"clientX": drag_end_x, "clientY": drag_end_y, "buttons": 0, "bubbles": True},
        )
        await canvas.dispatch_event("input", {"bubbles": True})
        await canvas.dispatch_event("change", {"bubbles": True})

    # 3) Playwright touchscreen when available (helps #touchContainer pads)
    try:
        touchscreen = getattr(page, "touchscreen", None)
        if touchscreen is not None and hasattr(touchscreen, "tap"):
            # touchscreen has no drag API in all versions — tap near pad center as hint
            await touchscreen.tap(
                canvas_x + canvas_width * 0.3,
                canvas_y + canvas_height * 0.5,
            )
    except Exception:
        pass

    # 4) If SignaturePad instance found and still empty, try library-safe nudge
    try:
        await canvas.evaluate(
            """
            (canvas) => {
              function findPad(el) {
                const direct = el.signaturePad || el._signaturePad || el.__signaturePad;
                if (direct && typeof direct.isEmpty !== 'undefined') return direct;
                let node = el;
                for (let d = 0; d < 8 && node; d++) {
                  for (const k of Object.keys(node)) {
                    try {
                      const v = node[k];
                      if (!v || typeof v !== 'object') continue;
                      if (typeof v.isEmpty === 'function' || typeof v.isEmpty === 'boolean') {
                        if (v.canvas === el || v._canvas === el || !v.canvas) return v;
                      }
                    } catch (e) {}
                  }
                  node = node.parentElement;
                }
                if (window.signaturePad && window.signaturePad.canvas === el) {
                  return window.signaturePad;
                }
                return null;
              }
              const pad = findPad(canvas);
              if (!pad) return false;
              const empty = typeof pad.isEmpty === 'function' ? pad.isEmpty() : !!pad.isEmpty;
              if (!empty) return true;
              // Safe: fire onBegin/onEnd if present — no forged data
              try { if (typeof pad.onBegin === 'function') pad.onBegin(); } catch (e) {}
              try { if (typeof pad.onEnd === 'function') pad.onEnd(); } catch (e) {}
              return false;
            }
            """
        )
    except Exception:
        pass

    # 5) Optional ctx paint — OFF by default (cosmetic ink must not drive PASS)
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
        logger.info(
            "[signature_pad] Ctx paint applied (supplement only; not a PASS signal)"
        )

    logger.info(
        "[signature_pad] Stroke strategies applied (mouse + pointer/touch; ctx=%s)",
        include_ctx_paint,
    )


async def verify_signature_ink(
    page: Any,
    canvas,
    *,
    reject_pixel_only: bool = False,
) -> InkVerifyResult:
    """
    Gate whether the pad has real ink / form state.

    Rules:
    - SignaturePad (or equivalent) found → require ``isEmpty === false``;
      pixels alone must NOT override.
    - Library not found → do NOT treat post-ctx pixels as success when
      ``reject_pixel_only`` (ctx paint was used). Prefer DOM gate: fail if
      red/near-pad ``Required`` still visible; else pixels only if allowed.
    """
    try:
        result = await canvas.evaluate(
            """
            (canvas) => {
                function findPad(el) {
                    const direct =
                        el.signaturePad || el._signaturePad || el.__signaturePad;
                    if (direct && typeof direct.isEmpty !== 'undefined') return direct;
                    let node = el;
                    for (let d = 0; d < 8 && node; d++) {
                        try {
                            for (const k of Object.keys(node)) {
                                const v = node[k];
                                if (!v || typeof v !== 'object') continue;
                                if (
                                    typeof v.isEmpty === 'function' ||
                                    typeof v.isEmpty === 'boolean'
                                ) {
                                    if (
                                        v.canvas === el ||
                                        v._canvas === el ||
                                        v.dotSize !== undefined ||
                                        v.toData !== undefined
                                    ) {
                                        return v;
                                    }
                                }
                            }
                        } catch (e) {}
                        node = node.parentElement;
                    }
                    if (
                        window.signaturePad &&
                        window.signaturePad.canvas === el
                    ) {
                        return window.signaturePad;
                    }
                    return null;
                }

                function requiredStillVisible(el) {
                    let node = el.parentElement;
                    for (let d = 0; d < 6 && node; d++) {
                        const walk = node.querySelectorAll
                            ? node.querySelectorAll('span, label, div, p, small, em, strong')
                            : [];
                        for (const t of walk) {
                            const s = ((t.textContent || '') + '').replace(/\\s+/g, ' ').trim();
                            if (!s || s.length > 48) continue;
                            if (!/^required$/i.test(s) && !/\\brequired\\b/i.test(s)) continue;
                            const cls = ((t.className || '') + '').toLowerCase();
                            let color = '';
                            try { color = (window.getComputedStyle(t).color || '').toLowerCase(); } catch (e) {}
                            const redish =
                                color.includes('rgb(255') ||
                                color.includes('rgb(220') ||
                                color.includes('rgb(244') ||
                                color.includes('rgb(239') ||
                                color.includes('#f') ||
                                color.includes('red');
                            const errCls =
                                cls.includes('error') ||
                                cls.includes('invalid') ||
                                cls.includes('required') ||
                                cls.includes('danger') ||
                                cls.includes('warning');
                            if (redish || errCls || /^required$/i.test(s)) return true;
                        }
                        node = node.parentElement;
                    }
                    return false;
                }

                function samplePixels(el) {
                    const ctx = el.getContext('2d');
                    if (!ctx) return { empty: true };
                    const w = el.width || 0;
                    const h = el.height || 0;
                    if (w < 2 || h < 2) return { empty: true };
                    const sample = ctx.getImageData(0, 0, w, h).data;
                    let ink = 0;
                    const step = 16;
                    for (let i = 0; i < sample.length; i += step) {
                        const r = sample[i];
                        const g = sample[i + 1];
                        const b = sample[i + 2];
                        const a = sample[i + 3];
                        if (a > 10 && (r < 250 || g < 250 || b < 250)) {
                            ink++;
                            if (ink > 5) return { empty: false };
                        }
                    }
                    return { empty: ink === 0 };
                }

                const pad = findPad(canvas);
                if (pad && typeof pad.isEmpty === 'function') {
                    const empty = !!pad.isEmpty();
                    // Library present: pixels MUST NOT override
                    return {
                        source: 'signaturepad',
                        empty: empty,
                        has_ink: !empty,
                        library_present: true,
                    };
                }
                if (pad && typeof pad.isEmpty === 'boolean') {
                    const empty = !!pad.isEmpty;
                    return {
                        source: 'signaturepad',
                        empty: empty,
                        has_ink: !empty,
                        library_present: true,
                    };
                }

                const req = requiredStillVisible(canvas);
                if (req) {
                    return {
                        source: 'fail',
                        empty: true,
                        has_ink: false,
                        library_present: false,
                        reason: 'required_still_visible',
                    };
                }

                const pix = samplePixels(canvas);
                if (!pix.empty) {
                    // Required not visible + non-blank pixels → form may accept
                    return {
                        source: 'pixels',
                        empty: false,
                        has_ink: true,
                        library_present: false,
                        required_cleared: true,
                    };
                }
                return {
                    source: 'pixels',
                    empty: true,
                    has_ink: false,
                    library_present: false,
                };
            }
            """
        )
    except Exception as exc:
        logger.warning("[signature_pad] Ink verification evaluate failed: %s", exc)
        return InkVerifyResult(has_ink=False, source="fail")

    if not isinstance(result, dict):
        ok = bool(result)
        source = "unknown" if ok else "fail"
        logger.info(
            "[signature_pad] Ink verify source=%s has_ink=%s (non-dict)",
            source,
            ok,
        )
        return InkVerifyResult(has_ink=ok, source=source)

    library_present = bool(result.get("library_present"))
    empty = result.get("empty", True)
    raw_source = str(result.get("source") or "unknown")
    has_ink = result.get("has_ink")
    if has_ink is None:
        has_ink = empty is False

    # P0: pixels alone must never override SignaturePad empty
    if library_present and empty:
        has_ink = False
        raw_source = "signaturepad"

    # P0: post-ctx cosmetic pixels are not a PASS (fail closed on pixel-only)
    if reject_pixel_only and not library_present and raw_source == "pixels" and has_ink:
        logger.warning(
            "[signature_pad] Rejecting pixel-only ink after ctx paint "
            "(cosmetic ink is not form state)"
        )
        has_ink = False
        raw_source = "fail"

    # Promote clearer source when Required cleared and pixels ok (no library)
    if (
        has_ink
        and not library_present
        and result.get("required_cleared")
        and raw_source == "pixels"
    ):
        raw_source = "required_cleared"
        logger.info(
            "[signature_pad] Ink verify source=required_cleared "
            "(no SignaturePad instance; near-pad Required not visible)"
        )

    if result.get("reason") == "required_still_visible":
        raw_source = "fail"

    logger.info(
        "[signature_pad] Ink verify source=%s empty=%s has_ink=%s "
        "library_present=%s reject_pixel_only=%s",
        raw_source,
        empty,
        has_ink,
        library_present,
        reject_pixel_only,
    )
    return InkVerifyResult(has_ink=bool(has_ink), source=raw_source)


async def sign_canvas(
    page: Any,
    *,
    instruction: Optional[str] = None,
    xpath: Optional[str] = None,
    include_ctx_paint: bool = False,
) -> SignResult:
    """
    Locate canvas, draw multi-strategy stroke, verify ink.

    Returns ``SignResult`` with ``success=False`` and a clear error when no
    canvas is found or ink verification fails (fail closed — never silent PASS).

    ``include_ctx_paint`` defaults to False. If enabled, pixel-only verify after
    ctx paint is rejected (SignaturePad / Required gate still required).
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

    verify = await verify_signature_ink(
        page, canvas, reject_pixel_only=include_ctx_paint
    )
    if not verify.has_ink:
        msg = (
            "Signature pad appears empty after stroke (ink verification failed"
            f"; source={verify.source})"
        )
        logger.warning("[signature_pad] %s", msg)
        return SignResult(
            success=False,
            error=msg,
            ink_verified=False,
            verify_source=verify.source,
        )

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

    logger.info(
        "[signature_pad] Sign succeeded with ink verified source=%s",
        verify.source,
    )
    return SignResult(
        success=True,
        error=None,
        ink_verified=True,
        xpath=resolved_xpath if isinstance(resolved_xpath, str) else xpath,
        verify_source=verify.source,
    )
