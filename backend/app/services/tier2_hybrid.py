"""
Tier 2: Hybrid Mode Execution
Stagehand observe() + Playwright execution for self-healing tests
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
import os
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from sqlalchemy.orm import Session
import logging

from app.services.xpath_cache_service import XPathCacheService
from app.services.xpath_extractor import XPathExtractor

logger = logging.getLogger(__name__)


class Tier2HybridExecutor:
    """
    Tier 2: Hybrid execution using Stagehand observe() + Playwright actions.
    
    This method uses cached XPath selectors when available, or extracts them
    using Stagehand observe() and then executes with Playwright.
    
    Expected success rate: 90-95% (when Tier 1 fails)
    Cost: Low-Medium (uses caching to minimize LLM calls)
    """
    
    def __init__(
        self,
        db: Session,
        xpath_extractor: XPathExtractor,
        timeout_ms: int = 30000
    ):
        """
        Initialize Tier 2 executor.
        
        Args:
            db: Database session for cache access
            xpath_extractor: XPath extractor service
            timeout_ms: Timeout in milliseconds for each action
        """
        self.db = db
        self.xpath_extractor = xpath_extractor
        self.timeout_ms = timeout_ms
        self.cache_service = XPathCacheService(db)
        self.payment_direct_enabled = os.getenv("ENABLE_PAYMENT_DIRECT_HANDLING", "false").lower() == "true"
        self.payment_gateway_ready = False
        self.payment_gateway_url = None
    
    async def execute_step(
        self,
        page: Page,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single test step using hybrid mode.
        
        Process:
        1. Try to get XPath from cache
        2. If cache miss, extract XPath using Stagehand observe()
        3. Execute using Playwright with the XPath
        4. Cache the XPath for future use
        
        Args:
            page: Playwright Page object
            step: Step dictionary containing action, instruction, value, etc.
            
        Returns:
            Result dictionary with success status, timing, and error info
        """
        start_time = time.time()
        extraction_time_ms = 0
        xpath = None
        cache_hit = False
        
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
                    raise ValueError(f"No action provided for step: {instruction}")
            
            instruction = step.get("instruction", "")
            value = step.get("value", "")
            file_path = step.get("file_path", "")
            page_url = page.url
            
            logger.info(f"[Tier 2] Executing step: {action} - {instruction}")
            
            # Special handling for navigate action (no XPath needed)
            if action == "navigate":
                await page.goto(value or instruction, timeout=self.timeout_ms, wait_until="networkidle")
                execution_time_ms = (time.time() - start_time) * 1000
                
                logger.info(f"[Tier 2] ✅ Navigate succeeded in {execution_time_ms:.2f}ms")
                
                return {
                    "success": True,
                    "tier": 2,
                    "execution_time_ms": execution_time_ms,
                    "extraction_time_ms": 0,
                    "cache_hit": False,
                    "xpath": None,
                    "error": None
                }
            
            # For upload_file actions, use file_path instead of value
            if action == "upload_file":
                value = file_path or value

            # Payment gateway readiness and direct field handling
            if self._is_payment_instruction(instruction, action):
                await self._maybe_wait_for_payment_gateway(page)
                if self.payment_direct_enabled:
                    direct_result = await self._try_payment_field_action(
                        page,
                        action,
                        instruction,
                        value,
                        start_time
                    )
                    if direct_result:
                        return direct_result
            
            # Step 1: Try to get XPath from cache
            cached_xpath = self.cache_service.get_cached_xpath(page_url, instruction)
            
            if cached_xpath:
                xpath = cached_xpath["xpath"]
                cache_hit = True
                logger.info(f"[Tier 2] 🎯 Cache hit! Validating cached XPath: {xpath}")
                
                # Validate cached xpath - check if element exists on current page
                try:
                    # Quick check with 2 second timeout
                    locator = page.locator(f"xpath={xpath}").first
                    await locator.wait_for(state="attached", timeout=2000)
                    logger.info(f"[Tier 2] ✅ Cached XPath validated successfully")
                except Exception as e:
                    # Element doesn't exist - cache is stale, invalidate and re-extract
                    logger.warning(f"[Tier 2] ⚠️ Cached XPath validation failed: {str(e)}")
                    logger.info(f"[Tier 2] 🔄 Invalidating stale cache and re-extracting...")
                    self.cache_service.invalidate_cache(page_url, instruction, "Element not found on page")
                    cache_hit = False
                    cached_xpath = None
            
            if not cached_xpath:
                # Step 2: Extract XPath using Stagehand observe()
                logger.info(f"[Tier 2] 📡 Cache miss, extracting XPath via observe()...")
                extraction_start = time.time()
                
                extraction_result = await self.xpath_extractor.extract_xpath_with_page(
                    page=page,
                    instruction=instruction
                )
                
                extraction_time_ms = (time.time() - extraction_start) * 1000
                
                if not extraction_result["success"]:
                    raise Exception(f"XPath extraction failed: {extraction_result.get('error')}")
                
                xpath = extraction_result["xpath"]
                logger.info(f"[Tier 2] ✅ Extracted XPath in {extraction_time_ms:.2f}ms: {xpath}")
                
                # Step 4: Cache the XPath for future use
                self.cache_service.cache_xpath(
                    page_url=page_url,
                    instruction=instruction,
                    xpath=xpath,
                    extraction_time_ms=extraction_time_ms,
                    page_title=extraction_result.get("page_title"),
                    element_text=extraction_result.get("element_text")
                )
            
            # Step 3: Execute using Playwright with the XPath
            execution_start = time.time()
            
            await self._execute_action_with_xpath(page, action, xpath, value)
            
            playwright_time_ms = (time.time() - execution_start) * 1000
            total_time_ms = (time.time() - start_time) * 1000
            
            # Validate cache if it was a cache hit
            if cache_hit:
                self.cache_service.validate_and_update(page_url, instruction, is_valid=True)
            
            logger.info(
                f"[Tier 2] ✅ Step succeeded in {total_time_ms:.2f}ms "
                f"(extraction: {extraction_time_ms:.2f}ms, execution: {playwright_time_ms:.2f}ms, "
                f"cache_hit: {cache_hit})"
            )
            
            return {
                "success": True,
                "tier": 2,
                "execution_time_ms": total_time_ms,
                "extraction_time_ms": extraction_time_ms,
                "playwright_time_ms": playwright_time_ms,
                "cache_hit": cache_hit,
                "xpath": xpath,
                "error": None
            }
            
        except PlaywrightTimeout as e:
            total_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {self.timeout_ms}ms: {str(e)}"
            
            # Invalidate cache if it was a cache hit that failed
            if cache_hit and xpath:
                self.cache_service.invalidate_cache(page.url, instruction, error_msg)
            
            logger.warning(f"[Tier 2] ⏰ Timeout: {error_msg}")
            
            return {
                "success": False,
                "tier": 2,
                "execution_time_ms": total_time_ms,
                "extraction_time_ms": extraction_time_ms,
                "cache_hit": cache_hit,
                "xpath": xpath,
                "error": error_msg,
                "error_type": "timeout"
            }
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            # Invalidate cache if it was a cache hit that failed
            if cache_hit and xpath:
                self.cache_service.invalidate_cache(page.url, instruction, error_msg)
            
            logger.warning(f"[Tier 2] ❌ Failed: {error_msg}")
            
            return {
                "success": False,
                "tier": 2,
                "execution_time_ms": total_time_ms,
                "extraction_time_ms": extraction_time_ms,
                "cache_hit": cache_hit,
                "xpath": xpath,
                "error": error_msg,
                "error_type": type(e).__name__
            }
    
    async def _execute_action_with_xpath(
        self,
        page: Page,
        action: str,
        xpath: str,
        value: str = ""
    ):
        """
        Execute action using XPath selector with Playwright.
        
        Args:
            page: Playwright Page object
            action: Action type (click, fill, etc.)
            xpath: XPath selector (may or may not have xpath= prefix)
            value: Value for fill/select actions
        """
        print(f"\n🔥🔥🔥 [TIER2 DEBUG] _execute_action_with_xpath called with action='{action}', xpath='{xpath[:100] if len(xpath) > 100 else xpath}', value='{value}' 🔥🔥🔥\n", flush=True)
        logger.info(f"[Tier 2] 🎬 _execute_action_with_xpath called with action='{action}', xpath='{xpath[:100]}', value='{value}'")
        
        # Ensure xpath doesn't have double prefix
        # XPath should be just the path, e.g., "/html/body/..."
        if xpath.startswith('xpath='):
            xpath = xpath[6:]  # Remove xpath= prefix
        
        # Use XPath locator
        element = page.locator(f"xpath={xpath}").first
        
        # Wait for element to be visible
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        
        # Execute action
        if action == "click":
            # Check for navigation buttons that might trigger page changes
            # Check for navigation buttons that might trigger page changes
            element_text = await element.text_content() or ""
            element_text_lower = element_text.lower()
            is_navigation_button = any(
                keyword in element_text_lower 
                for keyword in ["next", "continue", "submit", "proceed", "upload", "confirm", "checkout", "payment", "pay"]
            )
            
            # Capture current URL before click to detect navigation
            current_url = page.url
            
            # Perform the click action
            await element.click(timeout=self.timeout_ms)
            
            # Wait for any post-click navigation/state changes
            if is_navigation_button:
                logger.info(f"[Tier 2] 🔄 Navigation button detected: '{element_text}' - using extended wait")
            
            try:
                # For navigation buttons, use longer timeout
                wait_timeout = self.timeout_ms if is_navigation_button else 10000
                
                # Wait a bit for any redirect/navigation to start
                await asyncio.sleep(0.5)
                
                # Check if URL changed (indicates navigation/redirect)
                url_changed = page.url != current_url
                if url_changed:
                    logger.info(f"[Tier 2] 🌐 URL changed from {current_url} to {page.url} - waiting for new page to load")
                    # Wait for the new page to fully load
                    try:
                        await page.wait_for_load_state("load", timeout=wait_timeout)
                        logger.debug(f"[Tier 2] ✅ New page loaded")
                    except PlaywrightTimeout:
                        logger.warning(f"[Tier 2] ⚠️ New page load timeout")
                
                # Wait for network to be idle after click (handles AJAX, SPA updates)
                await page.wait_for_load_state("networkidle", timeout=wait_timeout)
                logger.debug(f"[Tier 2] ✅ Page state stabilized after click")
            except PlaywrightTimeout:
                # If network doesn't idle within timeout, wait at least for DOM to be ready
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    logger.debug(f"[Tier 2] ⚠️ DOM loaded after click (network still active)")
                except PlaywrightTimeout:
                    # Last resort: small fixed delay to allow content to update
                    await asyncio.sleep(1)
                    logger.warning(f"[Tier 2] ⚠️ Using fixed delay after click (no stable state detected)")
            
            # Additional wait for navigation buttons to ensure new page content is ready
            if is_navigation_button:
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
                            loading_element = page.locator(selector).first
                            # If loading element exists and is visible, wait for it to be hidden
                            if await loading_element.count() > 0:
                                logger.info(f"[Tier 2] ⏳ Detected loading indicator: {selector}")
                                await loading_element.wait_for(state="hidden", timeout=15000)  # Increased to 15s for payment gateways
                                logger.info(f"[Tier 2] ✅ Loading indicator disappeared")
                                break
                        except Exception:
                            # This selector doesn't match any element, try next
                            continue
                except Exception as e:
                    logger.debug(f"[Tier 2] No loading indicators found or error checking: {str(e)}")
                
                # Additional fixed delay to ensure content is fully rendered (especially for payment gateways)
                await asyncio.sleep(3.0)  # Increased from 2.0s to 3.0s for payment gateway loading
                logger.debug(f"[Tier 2] ⏱️ Additional 3.0s wait after navigation button")
                
                # CRITICAL FIX: For checkout/payment buttons, wait for payment gateway input fields to appear
                if "checkout" in element_text_lower or "payment" in element_text_lower or "pay" in element_text_lower:
                    logger.info(f"[Tier 2] 💳 Checkout/payment button detected - waiting for payment gateway input fields...")
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
                    ]
                    
                    input_found = False
                    for selector in payment_input_selectors:
                        try:
                            payment_input = page.locator(selector).first
                            await payment_input.wait_for(state="visible", timeout=10000)
                            logger.info(f"[Tier 2] ✅ Payment input field found: {selector}")
                            input_found = True
                            break
                        except Exception:
                            continue
                    
                    if input_found:
                        # Additional small delay to ensure field is fully interactive
                        await asyncio.sleep(1.0)
                        logger.info(f"[Tier 2] ✅ Payment gateway ready")
                    else:
                        logger.warning(f"[Tier 2] ⚠️ No payment input fields detected (may be non-standard gateway)")
                    
        elif action in ["fill", "type", "input"]:
            await element.fill(value, timeout=self.timeout_ms)
            # Small delay to allow any input event handlers to complete
            await asyncio.sleep(0.3)
            
        elif action == "select":
            try:
                await element.select_option(value, timeout=self.timeout_ms)
            except Exception:
                await element.select_option(label=value, timeout=self.timeout_ms)
            # Wait for any onChange handlers
            await asyncio.sleep(0.3)
            
        elif action == "check":
            if not await element.is_checked():
                await element.check(timeout=self.timeout_ms)
                await asyncio.sleep(0.3)
                
        elif action == "uncheck":
            if await element.is_checked():
                await element.uncheck(timeout=self.timeout_ms)
                await asyncio.sleep(0.3)
                
        elif action == "hover":
            await element.hover(timeout=self.timeout_ms)
            await asyncio.sleep(0.2)
            
        elif action in ["assert", "verify"]:
            actual_value = await element.text_content()
            if value not in (actual_value or ""):
                raise AssertionError(
                    f"Expected '{value}' in element text, got '{actual_value}'"
                )
        elif action == "wait":
            # Element already waited for above
            pass
        elif action == "upload_file":
            # value contains the file_path for upload_file actions
            file_path = value
            if not file_path:
                raise ValueError("No file_path provided for upload_file action")
            
            import os
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Verify it's a file input element
            tag_name = await element.evaluate("el => el.tagName")
            input_type = await element.evaluate("el => el.type")
            
            if tag_name.lower() != "input" or input_type.lower() != "file":
                logger.warning(
                    f"[Tier 2] ⚠️ Element is not a file input "
                    f"(tag={tag_name}, type={input_type}). Attempting upload anyway..."
                )
            
            # Upload file using Playwright's set_input_files method
            logger.info(f"[Tier 2] 📤 Uploading file via XPath: {file_path}")
            await element.set_input_files(file_path, timeout=self.timeout_ms)

            # Small delay to allow file upload event handlers to complete
            await asyncio.sleep(0.5)
            logger.info(f"[Tier 2] ✅ File uploaded successfully")
        elif action == "draw_signature" or action == "sign":
            # Draw signature on canvas element
            logger.info(f"[Tier 2] 🖊️ Starting signature drawing process for XPath: {xpath}")
            await self._execute_draw_signature(page, xpath, value)
            logger.info(f"[Tier 2] ✅ Signature drawing completed")
        else:
            raise ValueError(f"Unsupported action type: {action}")

    def _is_payment_instruction(self, instruction: str, action: str) -> bool:
        """Check if the instruction relates to payment fields."""
        if not instruction:
            return False

        if action not in ["fill", "type", "input", "select"]:
            return False

        instruction_lower = instruction.lower()
        keywords = [
            "card number",
            "credit card",
            "cardholder",
            "card holder",
            "expiry",
            "expiration",
            "cvv",
            "cvc",
            "security code",
            "payment",
        ]
        return any(keyword in instruction_lower for keyword in keywords)

    async def _maybe_wait_for_payment_gateway(self, page: Page) -> None:
        """Wait once per page for payment gateway fields to appear."""
        if self.payment_gateway_ready and self.payment_gateway_url == page.url:
            return

        payment_input_selectors = [
            "input[name*='card']",
            "input[placeholder*='card']",
            "input[id*='card']",
            "input[autocomplete='cc-number']",
            "input[type='tel'][maxlength='19']",
            "select[name*='month']",
            "select[id*='month']",
            "select[autocomplete='cc-exp-month']",
            "select[name*='year']",
            "select[id*='year']",
            "select[autocomplete='cc-exp-year']",
            "iframe[name*='card']",
            "iframe[title*='payment']",
            "iframe[src*='payment']",
        ]

        for selector in payment_input_selectors:
            try:
                locator = page.locator(selector).first
                await locator.wait_for(state="visible", timeout=8000)
                logger.info(f"[Tier 2] ✅ Payment gateway ready (selector: {selector})")
                self.payment_gateway_ready = True
                self.payment_gateway_url = page.url
                return
            except Exception:
                continue

        logger.warning("[Tier 2] ⚠️ Payment gateway readiness not confirmed")

    async def _try_payment_field_action(
        self,
        page: Page,
        action: str,
        instruction: str,
        value: str,
        start_time: float
    ) -> Optional[Dict[str, Any]]:
        """Try to interact with payment fields directly when possible."""
        instruction_lower = instruction.lower()
        wait_timeout = 3000 if (self.payment_gateway_ready and self.payment_gateway_url == page.url) else 10000

        if action in ["fill", "type", "input"] and not value:
            return None

        input_selectors = []
        select_selectors = []

        if "card number" in instruction_lower or "credit card" in instruction_lower:
            input_selectors = [
                "input[name*='card']",
                "input[id*='card']",
                "input[placeholder*='card']",
                "input[autocomplete='cc-number']",
                "input[type='tel'][maxlength='19']",
            ]
        elif "cvv" in instruction_lower or "cvc" in instruction_lower or "security code" in instruction_lower:
            input_selectors = [
                "input[name*='cvv']",
                "input[name*='cvc']",
                "input[id*='cvv']",
                "input[id*='cvc']",
                "input[autocomplete='cc-csc']",
                "input[type='tel'][maxlength='3']",
            ]
        elif "cardholder" in instruction_lower or "card holder" in instruction_lower:
            input_selectors = [
                "input[name*='name']",
                "input[id*='name']",
                "input[autocomplete='cc-name']",
            ]

        if action == "select" and ("month" in instruction_lower or "year" in instruction_lower or "expiry" in instruction_lower):
            if "month" in instruction_lower:
                select_selectors = [
                    "select[name*='month']",
                    "select[id*='month']",
                    "select[autocomplete='cc-exp-month']",
                ]
            elif "year" in instruction_lower:
                select_selectors = [
                    "select[name*='year']",
                    "select[id*='year']",
                    "select[autocomplete='cc-exp-year']",
                ]

        if not input_selectors and not select_selectors:
            return None

        frame_selectors = [
            "iframe[name*='card']",
            "iframe[title*='payment']",
            "iframe[src*='payment']",
        ]

        async def _try_fill(locator):
            await locator.wait_for(state="visible", timeout=wait_timeout)
            await locator.fill(value, timeout=self.timeout_ms)

        async def _try_select(locator):
            await locator.wait_for(state="visible", timeout=wait_timeout)
            try:
                await locator.select_option(value, timeout=self.timeout_ms)
            except Exception:
                await locator.select_option(label=value, timeout=self.timeout_ms)

        async def _try_label(locator):
            await locator.wait_for(state="visible", timeout=wait_timeout)
            if action == "select":
                try:
                    await locator.select_option(value, timeout=self.timeout_ms)
                except Exception:
                    await locator.select_option(label=value, timeout=self.timeout_ms)
            else:
                await locator.fill(value, timeout=self.timeout_ms)

        try:
            if input_selectors:
                for selector in input_selectors:
                    locator = page.locator(selector).first
                    try:
                        await _try_fill(locator)
                        execution_time_ms = (time.time() - start_time) * 1000
                        logger.info(f"[Tier 2] ✅ Payment input filled using selector: {selector}")
                        self.payment_gateway_ready = True
                        self.payment_gateway_url = page.url
                        return {
                            "success": True,
                            "tier": 2,
                            "execution_time_ms": execution_time_ms,
                            "extraction_time_ms": 0,
                            "cache_hit": False,
                            "xpath": None,
                            "error": None
                        }
                    except Exception:
                        continue

            if select_selectors:
                for selector in select_selectors:
                    locator = page.locator(selector).first
                    try:
                        await _try_select(locator)
                        execution_time_ms = (time.time() - start_time) * 1000
                        logger.info(f"[Tier 2] ✅ Payment select set using selector: {selector}")
                        self.payment_gateway_ready = True
                        self.payment_gateway_url = page.url
                        return {
                            "success": True,
                            "tier": 2,
                            "execution_time_ms": execution_time_ms,
                            "extraction_time_ms": 0,
                            "cache_hit": False,
                            "xpath": None,
                            "error": None
                        }
                    except Exception:
                        continue

            for iframe_selector in frame_selectors:
                frame_locator = page.frame_locator(iframe_selector)
                if input_selectors:
                    for selector in input_selectors:
                        locator = frame_locator.locator(selector).first
                        try:
                            await _try_fill(locator)
                            execution_time_ms = (time.time() - start_time) * 1000
                            logger.info(f"[Tier 2] ✅ Payment input filled in iframe: {iframe_selector} -> {selector}")
                            self.payment_gateway_ready = True
                            self.payment_gateway_url = page.url
                            return {
                                "success": True,
                                "tier": 2,
                                "execution_time_ms": execution_time_ms,
                                "extraction_time_ms": 0,
                                "cache_hit": False,
                                "xpath": None,
                                "error": None
                            }
                        except Exception:
                            continue

                if select_selectors:
                    for selector in select_selectors:
                        locator = frame_locator.locator(selector).first
                        try:
                            await _try_select(locator)
                            execution_time_ms = (time.time() - start_time) * 1000
                            logger.info(f"[Tier 2] ✅ Payment select set in iframe: {iframe_selector} -> {selector}")
                            self.payment_gateway_ready = True
                            self.payment_gateway_url = page.url
                            return {
                                "success": True,
                                "tier": 2,
                                "execution_time_ms": execution_time_ms,
                                "extraction_time_ms": 0,
                                "cache_hit": False,
                                "xpath": None,
                                "error": None
                            }
                        except Exception:
                            continue
            label_candidates = []
            if "card number" in instruction_lower or "credit card" in instruction_lower:
                label_candidates = ["Card number", "Card Number", "Card no", "Card No"]
            elif "cvv" in instruction_lower or "cvc" in instruction_lower or "security code" in instruction_lower:
                label_candidates = ["CVV", "CVC", "Security code", "Security Code"]
            elif "cardholder" in instruction_lower or "card holder" in instruction_lower:
                label_candidates = ["Cardholder name", "Cardholder", "Name on card"]
            elif "month" in instruction_lower:
                label_candidates = ["Expiry month", "Expiration month", "Exp month", "Month"]
            elif "year" in instruction_lower:
                label_candidates = ["Expiry year", "Expiration year", "Exp year", "Year"]

            for label in label_candidates:
                try:
                    locator = page.get_by_label(label, exact=False)
                    await _try_label(locator)
                    execution_time_ms = (time.time() - start_time) * 1000
                    logger.info(f"[Tier 2] ✅ Payment field set using label: {label}")
                    self.payment_gateway_ready = True
                    self.payment_gateway_url = page.url
                    return {
                        "success": True,
                        "tier": 2,
                        "execution_time_ms": execution_time_ms,
                        "extraction_time_ms": 0,
                        "cache_hit": False,
                        "xpath": None,
                        "error": None
                    }
                except Exception:
                    continue

            for iframe_selector in frame_selectors:
                frame_locator = page.frame_locator(iframe_selector)
                for label in label_candidates:
                    try:
                        locator = frame_locator.get_by_label(label, exact=False)
                        await _try_label(locator)
                        execution_time_ms = (time.time() - start_time) * 1000
                        logger.info(f"[Tier 2] ✅ Payment field set in iframe using label: {label}")
                        self.payment_gateway_ready = True
                        self.payment_gateway_url = page.url
                        return {
                            "success": True,
                            "tier": 2,
                            "execution_time_ms": execution_time_ms,
                            "extraction_time_ms": 0,
                            "cache_hit": False,
                            "xpath": None,
                            "error": None
                        }
                    except Exception:
                        continue

        except Exception as e:
            logger.debug(f"[Tier 2] Payment field direct handling failed: {e}")

        return None
    
    async def _execute_draw_signature(self, page: Page, xpath: str, signature_text: str = None):
        """
        Draw a signature on a canvas element using XPath.
        
        Args:
            page: Playwright Page object
            xpath: XPath selector for canvas element
            signature_text: Optional text to include in signature
        """
        # Locate canvas element using XPath
        element = page.locator(f"xpath={xpath}").first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        
        # Verify it's a canvas element
        tag_name = await element.evaluate("el => el.tagName")
        if tag_name.lower() != "canvas":
            logger.warning(
                f"[Tier 2] ⚠️ Element is not a canvas (tag={tag_name}). "
                f"Attempting signature drawing anyway..."
            )
        
        # Get canvas dimensions and position
        bbox = await element.bounding_box()
        if not bbox:
            raise ValueError(f"Cannot get bounding box for canvas with XPath: {xpath}")
        
        # Focus and scroll to canvas to ensure it's ready for interaction
        await element.scroll_into_view_if_needed()
        await element.focus()
        await asyncio.sleep(0.2)  # Allow focus to settle
        
        logger.info(f"[Tier 2] ✍️ Drawing signature on canvas via XPath (bbox: {bbox})")
        
        # Calculate signature path within canvas
        canvas_x = bbox['x']
        canvas_y = bbox['y']
        canvas_width = bbox['width']
        canvas_height = bbox['height']
        
        start_x = canvas_x + canvas_width * 0.2
        start_y = canvas_y + canvas_height * 0.5
        end_x = canvas_x + canvas_width * 0.8
        end_y = canvas_y + canvas_height * 0.5
        
        # First attempt: click + mouse drag to create a stroke
        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await page.mouse.move(end_x, end_y, steps=6)
        await page.mouse.up()
        await asyncio.sleep(0.1)

        # Second attempt: draw directly on the canvas via JS (reliable dot/line)
        await element.evaluate(
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

                ctx.fillStyle = '#000';
                ctx.beginPath();
                ctx.arc(width * 0.2, height * 0.5, 2, 0, Math.PI * 2);
                ctx.fill();

                return true;
            }
            """
        )

        # Third attempt: dispatch pointer/mouse/touch events to satisfy signature pad listeners
        drag_start_x = canvas_x + canvas_width * 0.25
        drag_start_y = canvas_y + canvas_height * 0.5
        drag_end_x = canvas_x + canvas_width * 0.65
        drag_end_y = canvas_y + canvas_height * 0.5

        await element.dispatch_event(
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
        await element.dispatch_event(
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
        await element.dispatch_event(
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

        await element.dispatch_event(
            "mousedown",
            {"clientX": drag_start_x, "clientY": drag_start_y, "buttons": 1, "bubbles": True},
        )
        await element.dispatch_event(
            "mousemove",
            {"clientX": drag_end_x, "clientY": drag_end_y, "buttons": 1, "bubbles": True},
        )
        await element.dispatch_event(
            "mouseup",
            {"clientX": drag_end_x, "clientY": drag_end_y, "buttons": 0, "bubbles": True},
        )

        await element.dispatch_event("click", {"bubbles": True})

        await element.evaluate(
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
                    canvas.dispatchEvent(new TouchEvent('touchstart', { touches: [touch], bubbles: true }));
                    canvas.dispatchEvent(new TouchEvent('touchmove', { touches: [touch], bubbles: true }));
                    canvas.dispatchEvent(new TouchEvent('touchend', { changedTouches: [touch], bubbles: true }));
                } catch (err) {
                    // Ignore if TouchEvent isn't supported
                }
            }
            """
        )

        await element.dispatch_event("input", {"bubbles": True})
        await element.dispatch_event("change", {"bubbles": True})
        
        logger.info(f"[Tier 2] ✅ Signature drawn successfully via XPath")

