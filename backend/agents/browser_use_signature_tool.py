"""
Custom browser-use tool: draw a stroke on signature canvases (same BrowserSession / CDP).

browser-use's default actions are clicks and typing; canvas signature pads need pointer/mouse
drag sequences. The LLM should call `draw_signature_pad` when it sees a contract / subscriber
signature area instead of only single-clicking the canvas.
"""

from __future__ import annotations

import json
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DrawSignaturePadAction(BaseModel):
    """Parameters for the draw_signature_pad action (all optional)."""

    canvas_css_selector: str | None = Field(
        None,
        description=(
            "CSS selector for the signature canvas (e.g. 'canvas#sig', '.signature-pad canvas'). "
            "Leave empty to auto-pick a canvas near 'signature' / 'subscriber' text."
        ),
    )


# JS: dispatch pointer + mouse events on the canvas so typical signature libraries receive a drag.
_SIGNATURE_STROKE_JS = r"""
(selector) => {
  const pick = () => {
    const s = (selector && String(selector).trim()) ? String(selector).trim() : '';
    if (s) {
      try {
        const el = document.querySelector(s);
        if (el) return el;
      } catch (e) {
        return null;
      }
    }
    const canvases = Array.from(document.querySelectorAll('canvas'));
    const byContext = canvases.find((c) => {
      let n = c;
      for (let i = 0; i < 8 && n; i++) {
        const t = (n.innerText || n.textContent || '').toLowerCase();
        if (t.includes('signature') || t.includes('subscriber')) return true;
        n = n.parentElement;
      }
      return false;
    });
    if (byContext) return byContext;
    // Largest visible canvas (often the pad)
    let best = null;
    let bestArea = 0;
    for (const c of canvases) {
      const r = c.getBoundingClientRect();
      const area = r.width * r.height;
      if (r.width >= 80 && r.height >= 40 && area > bestArea) {
        best = c;
        bestArea = area;
      }
    }
    return best;
  };

  const canvas = pick();
  if (!canvas) {
    return JSON.stringify({ ok: false, error: 'no_canvas_found' });
  }
  const r = canvas.getBoundingClientRect();
  if (r.width < 20 || r.height < 20) {
    return JSON.stringify({ ok: false, error: 'canvas_too_small', w: r.width, h: r.height });
  }

  const firePointer = (type, clientX, clientY, buttons) => {
    const opts = {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX,
      clientY,
      pointerId: 1,
      pointerType: 'mouse',
      isPrimary: true,
      pressure: type === 'pointermove' ? 0.45 : 0.5,
    };
    if (type === 'pointerdown') {
      opts.buttons = 1;
      opts.button = 0;
    } else if (type === 'pointermove') {
      opts.buttons = 1;
      opts.button = 0;
    } else {
      opts.buttons = 0;
      opts.button = 0;
    }
    canvas.dispatchEvent(new PointerEvent(type, opts));
  };

  const fireMouse = (type, clientX, clientY, buttons) => {
    const opts = { bubbles: true, cancelable: true, view: window, clientX, clientY, button: 0, buttons };
    canvas.dispatchEvent(new MouseEvent(type, opts));
  };

  const steps = 28;
  const x0 = r.left + r.width * 0.12;
  const y0 = r.top + r.height * 0.52;
  firePointer('pointerdown', x0, y0, 1);
  fireMouse('mousedown', x0, y0, 1);
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const clientX = r.left + r.width * (0.12 + t * 0.72);
    const clientY = r.top + r.height * (0.52 + 0.14 * Math.sin(t * Math.PI));
    firePointer('pointermove', clientX, clientY, 1);
    fireMouse('mousemove', clientX, clientY, 1);
  }
  const xe = r.left + r.width * 0.88;
  const ye = r.top + r.height * 0.48;
  firePointer('pointerup', xe, ye, 0);
  fireMouse('mouseup', xe, ye, 0);

  return JSON.stringify({ ok: true, width: r.width, height: r.height });
}
"""


async def draw_signature_stroke_on_current_page(
    browser_session: BrowserSession,
    canvas_css_selector: str | None = None,
) -> tuple[bool, str]:
    """
    Run signature stroke JS on the focused page. Returns (success, message).
    """
    page = await browser_session.get_current_page()
    if page is None:
        return False, "No current browser page (cannot draw signature)."

    try:
        raw = await page.evaluate(_SIGNATURE_STROKE_JS, canvas_css_selector or "")
        data = json.loads(raw) if raw else {}
    except Exception as e:
        logger.exception("draw_signature_stroke_on_current_page: evaluate failed")
        return False, f"Signature stroke failed: {e}"

    if not isinstance(data, dict):
        return False, f"Unexpected result: {raw!r}"

    if data.get("ok"):
        return True, (
            f"Drew signature stroke on canvas (~{int(data.get('width', 0))}x{int(data.get('height', 0))}px). "
            "Continue with Preview/Next/Submit if shown."
        )
    err = data.get("error", "unknown")
    return False, f"Could not draw signature: {err}"


def register_draw_signature_pad_tool(tools) -> None:
    """
    Register `draw_signature_pad` on a browser-use Tools instance (same registry as built-in actions).
    """
    from browser_use.agent.views import ActionResult

    @tools.registry.action(
        (
            "Draw a handwritten-style stroke on the digital signature canvas (contract / "
            '"Subscriber\'s signature" / sales agreement). Use this when a signature pad is visible '
            "and a single click is not enough. Do not use for normal buttons or checkboxes. "
            "Optional: pass canvas_css_selector if you know the exact canvas selector from find_elements."
        ),
        param_model=DrawSignaturePadAction,
    )
    async def draw_signature_pad(params: DrawSignaturePadAction, browser_session):
        ok, msg = await draw_signature_stroke_on_current_page(
            browser_session,
            canvas_css_selector=params.canvas_css_selector,
        )
        if ok:
            logger.info("draw_signature_pad: %s", msg)
            return ActionResult(extracted_content=msg, long_term_memory=msg)
        logger.warning("draw_signature_pad: %s", msg)
        return ActionResult(error=msg, extracted_content=msg)
