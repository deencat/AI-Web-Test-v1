"""
Tier 3: Stagehand Only Execution
Full AI reasoning with Stagehand act() for complex interactions
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from stagehand import Stagehand
import logging

from app.services.signature_pad import sign_canvas

logger = logging.getLogger(__name__)

_GW_PROXY_IFRAME_SELECTORS = {
    "card_number": [
        "iframe.gw-proxy-number",
        "iframe[id*='card-number' i]",
        "iframe[src*='/role/number/' i]",
    ],
    "expiry_month": [
        "iframe.gw-proxy-expiry-month",
        "iframe[src*='/role/expiryMonth/' i]",
    ],
    "expiry_year": [
        "iframe.gw-proxy-expiry-year",
        "iframe[src*='/role/expiryYear/' i]",
    ],
    "cvv": [
        "iframe.gw-proxy-cvv",
        "iframe[src*='/role/securityCode/' i]",
    ],
    "cardholder": [
        "iframe.gw-proxy-name",
        "iframe[src*='/role/cardholderName/' i]",
    ],
}


class Tier3StagehandExecutor:
    """
    Tier 3: Full Stagehand act() execution with AI reasoning.
    
    This is the last resort fallback when Tier 1 and Tier 2 fail.
    Uses full LLM reasoning to understand and interact with the page.
    
    Expected success rate: 60-70% (when Tier 1 and Tier 2 fail)
    Cost: High (full LLM reasoning for each action)
    Speed: Slowest (full AI processing)
    """
    
    def __init__(
        self,
        stagehand: Stagehand,
        timeout_ms: int = 30000
    ):
        """
        Initialize Tier 3 executor.
        
        Args:
            stagehand: Stagehand instance for execution
            timeout_ms: Timeout in milliseconds for each action
        """
        self.stagehand = stagehand
        self.timeout_ms = timeout_ms

    def _stagehand_act_returned_no_elements(self, result) -> bool:
        """True when Stagehand act()/observe-style responses contain no actionable elements."""
        if result is None:
            return True
        if isinstance(result, list):
            return len(result) == 0
        if isinstance(result, dict):
            elements = result.get("elements")
            if elements is not None:
                return len(elements) == 0
        return False

    def _is_payment_field_instruction(self, instruction: str, action: str) -> bool:
        if not instruction or action not in ("fill", "type", "input", "select"):
            return False
        instruction_lower = instruction.lower()
        keywords = [
            "card number", "credit card", "cardholder", "card holder",
            "expiry", "expiration", "exp. date", "exp date", "cvv", "cvc",
            "security code",
        ]
        return any(keyword in instruction_lower for keyword in keywords)

    def _is_cross_origin_payment_host(self, url: str) -> bool:
        hostname = (urlparse(url or "").hostname or "").lower()
        return any(
            kw in hostname
            for kw in ("gateway", "mastercard", "checkout", "pay", "payment", "adyen", "stripe")
        )

    def _infer_payment_field_role(self, instruction_lower: str, action: str) -> Optional[str]:
        if action == "select":
            if "month" in instruction_lower:
                return "expiry_month"
            if "year" in instruction_lower:
                return "expiry_year"
        if "card number" in instruction_lower or "credit card" in instruction_lower:
            return "card_number"
        if "cvv" in instruction_lower or "cvc" in instruction_lower or "security code" in instruction_lower:
            return "cvv"
        if "cardholder" in instruction_lower or "card holder" in instruction_lower:
            return "cardholder"
        return None

    async def _verify_payment_field_populated(
        self,
        instruction: str,
        value: str,
        action: str,
    ) -> bool:
        """Verify gw-proxy payment fields were populated after Stagehand act()."""
        page = self.stagehand.page
        if not self._is_cross_origin_payment_host(page.url):
            return True

        instruction_lower = (instruction or "").lower()
        role = self._infer_payment_field_role(instruction_lower, action)
        if not role:
            return True

        iframe_selectors = _GW_PROXY_IFRAME_SELECTORS.get(role, [])
        for iframe_selector in iframe_selectors:
            try:
                if await page.locator(iframe_selector).count() == 0:
                    continue
                frame = page.frame_locator(iframe_selector)
                if action == "select":
                    locator = frame.locator("select").first
                    await locator.wait_for(state="visible", timeout=2000)
                    selected = await locator.input_value()
                    return selected == value or bool(selected)
                locator = frame.locator("input:not([type='hidden'])").first
                await locator.wait_for(state="visible", timeout=2000)
                filled = (await locator.input_value() or "").strip()
                if role == "cvv":
                    return bool(filled)
                return filled == value
            except Exception:
                continue

        return False
    
    async def execute_step(
        self,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single test step using full Stagehand act().
        
        Args:
            step: Step dictionary containing action, instruction, value, etc.
            
        Returns:
            Result dictionary with success status, timing, and error info
        """
        start_time = time.time()
        
        try:
            action = step.get("action")
            if action:
                action = action.lower()
            else:
                # If no action provided, try to infer from instruction
                instruction = step.get("instruction", "")
                if any(word in instruction.lower() for word in ["sign", "signature", "draw"]):
                    action = "draw_signature"
                else:
                    # Let Stagehand handle it with act()
                    action = "act"
            
            instruction = step.get("instruction", "")
            value = step.get("value", "")
            file_path = step.get("file_path", "")
            
            logger.info(f"[Tier 3] Executing step with full AI reasoning: {instruction}")
            
            # Check if this is a navigation action (button text contains navigation keywords)
            instruction_lower = instruction.lower()
            is_navigation_action = any(
                keyword in instruction_lower 
                for keyword in ["next", "continue", "submit", "proceed", "upload", "confirm", "click", "checkout", "payment", "pay"]
            )
            
            # Capture current URL before action to detect navigation
            current_url = self.stagehand.page.url
            
            # Build action instruction for Stagehand
            if action == "navigate":
                # Use goto instead of act for navigation
                url = value or instruction
                await self.stagehand.page.goto(url, timeout=self.timeout_ms, wait_until="networkidle")

            elif action == "verify_screenshot":
                # Sprint 10.17: vision not available → semantic text fallback via extract()
                return await self._execute_verify_screenshot_fallback(step, start_time)

            elif action in ["fill", "type"] and value:
                # Combine action with value for better instruction
                full_instruction = f"{instruction} with value '{value}'"
                result = await self.stagehand.page.act(full_instruction)
                if self._is_payment_field_instruction(instruction, action):
                    verified = await self._verify_payment_field_populated(instruction, value, action)
                    if not verified:
                        raise ValueError(
                            f"Tier 3 act() did not populate payment field: {instruction}"
                        )
                
            elif action == "select" and value:
                # Handle dropdown/select actions with explicit value
                full_instruction = f"{instruction}. Select option with value or text '{value}'"
                logger.info(f"[Tier 3] 🎯 Dropdown select: {full_instruction}")
                result = await self.stagehand.page.act(full_instruction)
                
                # Small delay for onChange handlers
                await asyncio.sleep(0.3)
                if self._is_payment_field_instruction(instruction, action):
                    verified = await self._verify_payment_field_populated(instruction, value, action)
                    if not verified:
                        raise ValueError(
                            f"Tier 3 act() did not populate payment field: {instruction}"
                        )
                
            elif action in ["assert", "verify"]:
                # Use extract to verify content
                extract_instruction = f"Get the text that should contain: {value}"
                result = await self.stagehand.page.extract(extract_instruction)
                
                if value not in str(result):
                    raise AssertionError(
                        f"Expected '{value}' in extracted text, got '{result}'"
                    )
            
            elif action == "upload_file":
                # Handle file upload action
                upload_file_path = file_path or value
                if not upload_file_path:
                    raise ValueError("No file_path provided for upload_file action")
                
                import os
                if not os.path.exists(upload_file_path):
                    raise FileNotFoundError(f"File not found: {upload_file_path}")
                
                logger.info(f"[Tier 3] 📤 Uploading file: {upload_file_path}")
                
                # Try AI act() first with file upload instruction
                try:
                    # Attempt to use Stagehand's AI to find and interact with file input
                    upload_instruction = f"{instruction}. File path: {upload_file_path}"
                    result = await self.stagehand.page.act(upload_instruction)
                    logger.info(f"[Tier 3] ✅ File upload via AI act() succeeded")
                except Exception as act_error:
                    # Fallback: Use programmatic file input
                    logger.warning(f"[Tier 3] ⚠️ AI act() failed for upload, using fallback: {str(act_error)}")
                    
                    # Find file input element programmatically
                    file_input = self.stagehand.page.locator("input[type='file']").first
                    await file_input.wait_for(state="attached", timeout=self.timeout_ms)
                    await file_input.set_input_files(upload_file_path, timeout=self.timeout_ms)
                    logger.info(f"[Tier 3] ✅ File uploaded via fallback method")
                
                # Small delay to allow file upload handlers to complete
                await asyncio.sleep(0.5)
            
            elif action == "draw_signature" or action == "sign":
                # Feature 5: programmatic stroke + ink verify is source of truth.
                # act() may scroll/locate only — NEVER treat soft act success as signed.
                logger.info(
                    "[Tier 3] ✍️ Signature step — act() locator aid optional; "
                    "programmatic stroke + ink verify required"
                )

                try:
                    signature_instruction = (
                        f"{instruction}. Draw a signature on the signature pad or canvas."
                    )
                    await self.stagehand.page.act(signature_instruction)
                    logger.info(
                        "[Tier 3] act() finished (locator/scroll aid only — not a PASS signal)"
                    )
                except Exception as act_error:
                    logger.warning(
                        "[Tier 3] ⚠️ AI act() failed for signature "
                        "(continuing with programmatic stroke): %s",
                        act_error,
                    )

                # Always stroke + verify — reachable on soft act() success (#1120/#1122)
                await self._execute_draw_signature_fallback(instruction=instruction)

            else:
                # Use act() for all other actions
                result = await self.stagehand.page.act(instruction)

                if action == "click" and self._stagehand_act_returned_no_elements(result):
                    raise ValueError(
                        f"Stagehand act() returned no elements for: {instruction}"
                    )
                
                # Wait for page to stabilize after navigation actions
                if is_navigation_action:
                    logger.info(f"[Tier 3] 🔄 Navigation action detected - waiting for page to stabilize")
                    
                    # Wait a bit for any redirect/navigation to start
                    await asyncio.sleep(0.5)
                    
                    # Check if URL changed (indicates navigation/redirect)
                    url_changed = self.stagehand.page.url != current_url
                    if url_changed:
                        logger.info(f"[Tier 3] 🌐 URL changed from {current_url} to {self.stagehand.page.url} - waiting for new page to load")
                        # Wait for the new page to fully load
                        try:
                            await self.stagehand.page.wait_for_load_state("load", timeout=self.timeout_ms)
                            logger.debug(f"[Tier 3] ✅ New page loaded")
                        except Exception:
                            logger.warning(f"[Tier 3] ⚠️ New page load timeout")
                    
                    try:
                        await self.stagehand.page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
                        logger.debug(f"[Tier 3] ✅ Page state stabilized after action")
                    except Exception as e:
                        # If network doesn't idle, wait for DOM ready
                        try:
                            await self.stagehand.page.wait_for_load_state("domcontentloaded", timeout=5000)
                            logger.debug(f"[Tier 3] ⚠️ DOM loaded after action (network still active)")
                        except Exception:
                            # Last resort: fixed delay
                            await asyncio.sleep(1.5)
                            logger.warning(f"[Tier 3] ⚠️ Using fixed delay after action")
                    
                    # Wait for common loading indicators to disappear
                    try:
                        # Check for loading overlays, spinners, or "loading" text
                        loading_selectors = [
                            "[class*='loading']",
                            "[class*='spinner']",
                            "[class*='overlay']",
                            "[aria-busy='true']",
                            ".loading",
                            ".spinner",
                            ".overlay",
                            # Payment gateway specific loaders
                            "iframe[class*='load']",
                            "[id*='loading']",
                            "[id*='spinner']"
                        ]
                        
                        for selector in loading_selectors:
                            try:
                                loading_element = self.stagehand.page.locator(selector).first
                                # If loading element exists and is visible, wait for it to be hidden
                                if await loading_element.count() > 0:
                                    logger.info(f"[Tier 3] ⏳ Detected loading indicator: {selector}")
                                    await loading_element.wait_for(state="hidden", timeout=15000)  # Increased to 15s for payment gateways
                                    logger.info(f"[Tier 3] ✅ Loading indicator disappeared")
                                    break
                            except Exception:
                                # This selector doesn't match any element, try next
                                continue
                    except Exception as e:
                        logger.debug(f"[Tier 3] No loading indicators found or error checking: {str(e)}")
                    
                    # Additional fixed delay to ensure content is fully rendered (especially for payment gateways)
                    await asyncio.sleep(3.0)  # Increased from 2.0s to 3.0s for payment gateway loading
                    logger.debug(f"[Tier 3] ⏱️ Additional 3.0s wait after navigation action")
                    
                    # CRITICAL FIX: For checkout/payment buttons, wait for payment gateway input fields to appear
                    if "checkout" in instruction_lower or "payment" in instruction_lower or "pay" in instruction_lower:
                        logger.info(f"[Tier 3] 💳 Checkout/payment button detected - waiting for payment gateway input fields...")
                        # Wait for common payment gateway input fields to appear
                        payment_input_selectors = [
                            "input[name*='card']",  # Card number input
                            "input[placeholder*='card']",
                            "input[id*='card']",
                            "input[type='tel'][maxlength='19']",  # Common for card number fields
                            "input[autocomplete='cc-number']",
                            "input[name*='cardnumber']",
                            "iframe[name*='card']",  # Payment gateway iframes
                            "iframe[src*='payment']",
                            "iframe[class*='gw-proxy']",
                            "iframe.gw-proxy-number",
                            "iframe[src*='gateway.mastercard.com']",
                        ]
                        
                        input_found = False
                        for selector in payment_input_selectors:
                            try:
                                payment_input = self.stagehand.page.locator(selector).first
                                await payment_input.wait_for(state="visible", timeout=10000)
                                logger.info(f"[Tier 3] ✅ Payment input field found: {selector}")
                                input_found = True
                                break
                            except Exception:
                                continue
                        
                        if input_found:
                            # Additional small delay to ensure field is fully interactive
                            await asyncio.sleep(1.0)
                            logger.info(f"[Tier 3] ✅ Payment gateway ready")
                        else:
                            logger.warning(f"[Tier 3] ⚠️ No payment input fields detected (may be non-standard gateway)")
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[Tier 3] ✅ Step succeeded in {execution_time_ms:.2f}ms")
            
            return {
                "success": True,
                "tier": 3,
                "execution_time_ms": execution_time_ms,
                "error": None
            }
            
        except asyncio.TimeoutError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {self.timeout_ms}ms: {str(e)}"
            logger.warning(f"[Tier 3] ⏰ Timeout: {error_msg}")
            
            return {
                "success": False,
                "tier": 3,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
                "error_type": "timeout"
            }
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.warning(f"[Tier 3] ❌ Failed: {error_msg}")
            
            return {
                "success": False,
                "tier": 3,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
                "error_type": type(e).__name__
            }
    
    async def _execute_draw_signature_fallback(
        self, instruction: Optional[str] = None
    ):
        """
        Programmatic signature stroke + ink verification (Feature 5).

        Always invoked for draw_signature/sign — not only when act() throws.
        Soft act() success (scrollIntoView / locator) must not skip this path.
        """
        logger.info("[Tier 3] ✍️ Programmatic signature stroke + ink verify")
        result = await sign_canvas(
            self.stagehand.page,
            instruction=instruction,
        )
        if not result.success or not result.ink_verified:
            raise ValueError(
                result.error
                or (
                    "Signature pad appears empty after stroke "
                    f"(ink verification failed; source={result.verify_source})"
                )
            )
        logger.info(
            "[Tier 3] ✅ Signature ink verified via shared signature_pad helper "
            "(verify_source=%s)",
            result.verify_source,
        )

    # ------------------------------------------------------------------
    # Sprint 10.17: verify_screenshot semantic fallback
    # ------------------------------------------------------------------

    async def _execute_verify_screenshot_fallback(
        self,
        step: Dict[str, Any],
        start_time: float,
    ) -> Dict[str, Any]:
        """Fallback for verify_screenshot when vision AI is unavailable.

        DOM text search CANNOT reliably verify that content is visually shown
        on screen — navigation tabs, hidden sections, or off-screen elements
        all contain text that would produce false PASSes.

        Therefore this fallback always returns FAIL with an explicit message
        telling the user they need a vision-capable provider (OpenRouter with
        a vision model, Azure OpenAI, or Google Gemini).
        """
        import json as _json

        instruction = step.get("instruction", "")
        expected_items: list = step.get("expected_items") or []

        logger.warning(
            "[Tier 3] ⚠️  verify_screenshot requires vision AI — "
            "current provider does not support vision.  Returning FAIL.  "
            "Configure a vision-capable provider (OpenRouter/Azure/Google). "
            "Instruction: %s",
            instruction,
        )

        reason = (
            "Vision AI unavailable: verify_screenshot requires a vision-capable provider "
            "(OpenRouter with a vision model, Azure OpenAI, or Google Gemini). "
            "DOM text search cannot distinguish whether content is actually visible on screen."
        )
        verdict_dict = {
            "verdict": "FAIL",
            "reason": reason,
            "provider": "none (vision_required)",
            "model": None,
        }
        execution_time_ms = (time.time() - start_time) * 1000

        return {
            "success": False,
            "tier": 3,
            "execution_time_ms": execution_time_ms,
            "error": reason,
            "error_type": "vision_ai_unavailable",
            "ai_verification_result": _json.dumps(verdict_dict),
        }


# Import asyncio for timeout handling
import asyncio

