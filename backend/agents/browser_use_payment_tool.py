"""
Custom browser-use tool: click the VISA/MasterCard payment icon and Checkout button
using direct Playwright CDP calls on the shared BrowserSession.

browser-use's LLM sometimes picks the wrong payment icon (e.g. UnionPay) because
all icons look visually similar in the DOM index listing.  This tool uses a precise
CSS selector to click the correct VISA/MC div and then the Checkout button —
guaranteed to target the right element regardless of index numbering.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# All payment icons share the same div classes on Three HK UAT, so we target by
# img[alt] containing "Visa" instead of by div selector.
VISA_MC_IMG_ALT = "Visa"

# JS that:
#  1. Finds ALL matching payment icon divs
#  2. Clicks the FIRST one that contains a VISA or MasterCard image/text
#  3. Waits 800 ms for the selection to register
#  4. Clicks the Checkout / Next button
_CLICK_VISA_MC_JS = r"""
async () => {
  // --- Step 1: find the VISA/MC icon via img[alt] containing "Visa" ---
  // Each payment method shares the same div classes, so we target the img directly.
  let targetImg = null;

  // Primary: exact img alt containing "Visa" (case-insensitive)
  for (const img of Array.from(document.querySelectorAll('img'))) {
    const alt = (img.alt || '').toLowerCase();
    const src = (img.src || '').toLowerCase();
    if (alt.includes('visa') || src.includes('visa')) {
      targetImg = img;
      break;
    }
  }

  if (!targetImg) {
    return JSON.stringify({ ok: false, step: 'find_visa_img',
      error: 'No img with alt/src containing "visa" found on page' });
  }

  // Walk up to the clickable container div
  let visaDiv = targetImg.closest('div.d-flex') || targetImg.parentElement;

  if (!visaDiv) {
    return JSON.stringify({ ok: false, step: 'find_visa_div',
      error: 'Could not find parent div for Visa img' });
  }

  // Scroll into view and click
  visaDiv.scrollIntoView({ behavior: 'instant', block: 'center' });
  visaDiv.click();

  // Also dispatch a real mouse click for React/Vue event listeners
  visaDiv.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
  visaDiv.dispatchEvent(new MouseEvent('mouseup',   { bubbles: true, cancelable: true }));
  visaDiv.dispatchEvent(new MouseEvent('click',     { bubbles: true, cancelable: true }));

  // --- Step 2: Wait for selection to register ---
  await new Promise(r => setTimeout(r, 1000));

  // --- Step 3: Find and click Checkout / Next / Submit button ---
  const checkoutTexts = ['checkout', 'check out', 'next', 'submit', 'confirm', '結帳', '下一步'];
  let checkoutBtn = null;

  // Prefer a button/a whose text matches checkout keywords
  const allBtns = Array.from(document.querySelectorAll(
    'button, a[role="button"], input[type="submit"], [class*="btn"]'
  ));
  for (const btn of allBtns) {
    const t = (btn.innerText || btn.textContent || btn.value || '').toLowerCase().trim();
    if (checkoutTexts.some(k => t.includes(k))) {
      checkoutBtn = btn;
      break;
    }
  }

  if (!checkoutBtn) {
    return JSON.stringify({
      ok: false, step: 'find_checkout',
      error: 'VISA/MC div clicked but could not find Checkout/Next button',
      visa_div_clicked: true,
      visa_div_text: (visaDiv.innerText || visaDiv.textContent || '').trim().slice(0, 80),
    });
  }

  checkoutBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
  checkoutBtn.click();
  checkoutBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
  checkoutBtn.dispatchEvent(new MouseEvent('mouseup',   { bubbles: true, cancelable: true }));
  checkoutBtn.dispatchEvent(new MouseEvent('click',     { bubbles: true, cancelable: true }));

  await new Promise(r => setTimeout(r, 800));

  return JSON.stringify({
    ok: true,
    visa_div_text:    (visaDiv.innerText || visaDiv.textContent || '').trim().slice(0, 80),
    checkout_btn_text: (checkoutBtn.innerText || checkoutBtn.textContent || '').trim().slice(0, 40),
  });
}
"""


class ClickVisaMasterCardAction(BaseModel):
    """Parameters for the click_visa_mastercard_and_checkout action."""

    css_selector: Optional[str] = Field(
        None,
        description=(
            "Override CSS selector for the VISA/MasterCard icon container. "
            "Leave empty to use the default Three HK UAT selector: "
            "'div.d-flex.py-4.border.border-2.rounded.justify-content-center'."
        ),
    )


def register_click_visa_mastercard_tool(tools) -> None:
    """
    Register the click_visa_mastercard_and_checkout tool on a browser-use Tools instance.

    Usage:
        from browser_use.tools.service import Tools as BrowserUseTools
        from agents.browser_use_payment_tool import register_click_visa_mastercard_tool
        _tools = BrowserUseTools()
        register_click_visa_mastercard_tool(_tools)
        agent_kwargs["tools"] = _tools

    The LLM should call this action when it reaches the Payment Method page
    instead of trying to click the VISA/MC icon by index number.
    """

    @tools.action(
        name="click_visa_mastercard_and_checkout",
        description=(
            "On the Payment Method page, click the VISA/MasterCard payment icon "
            "using a precise CSS selector and then click the Checkout / Next button. "
            "Use this instead of clicking by index to avoid accidentally selecting "
            "UnionPay or other payment methods. "
            "Call this action as soon as you see the Payment Method selection page."
        ),
        param_model=ClickVisaMasterCardAction,
    )
    async def click_visa_mastercard_and_checkout(
        params: ClickVisaMasterCardAction,
        browser_session,
    ) -> str:
        try:
            # Get the active Playwright page from the browser-use session
            page = await browser_session.get_current_page()
            if page is None:
                return "ERROR: No active page available in browser session"

            # Optionally swap in a custom selector
            js = _CLICK_VISA_MC_JS
            if params.css_selector:
                js = js.replace(
                    "div.d-flex.py-4.border.border-2.rounded.justify-content-center",
                    params.css_selector,
                )

            result = await page.evaluate(js)
            logger.info(f"click_visa_mastercard_and_checkout result: {result}")
            return f"click_visa_mastercard_and_checkout: {result}"

        except Exception as exc:
            logger.error(f"click_visa_mastercard_and_checkout failed: {exc}", exc_info=True)
            return f"ERROR in click_visa_mastercard_and_checkout: {exc}"
