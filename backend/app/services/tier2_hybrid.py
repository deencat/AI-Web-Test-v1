"""
Tier 2: Hybrid Mode Execution
Stagehand observe() + Playwright execution for self-healing tests
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
import os
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import re
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from sqlalchemy.orm import Session
import logging

from app.services.post_click_readiness import auto_dismiss_blocking_modals, wait_for_post_click_readiness
from app.services.xpath_cache_service import XPathCacheService
from app.services.xpath_extractor import XPathExtractor
from app.utils.three_uat_test_credentials import is_three_hk_uat_url

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
        self.payment_direct_enabled = os.getenv("ENABLE_PAYMENT_DIRECT_HANDLING", "true").lower() != "false"
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
            selector = step.get("selector")
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
                selector = step.get("selector")
                if selector:
                    try:
                        await page.locator(selector).first.wait_for(state="visible", timeout=1500)
                        self.payment_gateway_ready = True
                        self.payment_gateway_url = page.url
                    except Exception:
                        await self._maybe_wait_for_payment_gateway(page)
                else:
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
                
                # Validate cached xpath - ensure element exists and matches step intent
                try:
                    is_valid_cache = await self._validate_cached_xpath_for_step(
                        page=page,
                        xpath=xpath,
                        action=action,
                        instruction=instruction,
                        value=value,
                    )
                    if not is_valid_cache:
                        raise ValueError("Cached XPath does not match current step intent")

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

                if self._should_retry_observe_extraction(
                    extraction_result=extraction_result,
                    action=action,
                    selector=selector,
                    instruction=instruction,
                ):
                    logger.info("[Tier 2] 🔄 observe() returned no results. Waiting for page to become interactable, then retrying once...")
                    await self._wait_for_page_interactable_for_observe(page)
                    extraction_result = await self.xpath_extractor.extract_xpath_with_page(
                        page=page,
                        instruction=instruction
                    )
                
                extraction_time_ms = (time.time() - extraction_start) * 1000
                
                if not extraction_result["success"]:
                    raise Exception(f"XPath extraction failed: {extraction_result.get('error')}")
                
                xpath = extraction_result["xpath"]

                if action == "click" and self._xpath_targets_iframe(xpath):
                    logger.info("[Tier 2] 🧭 XPath points to iframe container. Trying in-frame click fallback...")
                    clicked_inside_iframe = await self._try_click_inside_iframe(page, instruction)
                    if clicked_inside_iframe:
                        playwright_time_ms = 0
                        total_time_ms = (time.time() - start_time) * 1000
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
            
            await self._execute_action_with_xpath(page, action, xpath, value, instruction)
            
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

    def _should_retry_observe_extraction(
        self,
        extraction_result: Dict[str, Any],
        action: str,
        selector: Optional[str],
        instruction: str = "",
    ) -> bool:
        """Retry observe() once when click step has no selector and page may still be loading."""
        if selector:
            return False

        if extraction_result.get("success") is True:
            return False

        error_text = (extraction_result.get("error") or "").lower()

        if "execution context was destroyed" in error_text or "because of a navigation" in error_text:
            return True

        if "observe() returned no results" not in error_text:
            return False

        if action == "click":
            return True

        return self._is_payment_instruction(instruction, action)

    def _looks_like_option_xpath(self, xpath: str) -> bool:
        """Return True when XPath points to an <option> instead of a <select>."""
        normalized_xpath = (xpath or "").lower()
        return "/option[" in normalized_xpath or normalized_xpath.endswith("/option")

    def _xpath_targets_iframe(self, xpath: str) -> bool:
        """Return True when XPath points to an iframe container element."""
        normalized_xpath = (xpath or "").lower()
        return "/iframe[" in normalized_xpath or normalized_xpath.endswith("/iframe")

    def _select_xpath_from_option_xpath(self, xpath: str) -> str:
        """Convert option XPath to parent select XPath for Playwright select_option()."""
        if not xpath:
            return xpath

        if "/option[" in xpath:
            return xpath.split("/option[", 1)[0]
        if xpath.endswith("/option"):
            return xpath[: -len("/option")]
        return xpath

    async def _wait_for_page_interactable_for_observe(self, page: Page) -> None:
        """Wait for common loading/skeleton blockers to clear before running observe()."""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            logger.debug("[Tier 2] DOMContentLoaded wait timed out before observe retry")

        try:
            await page.wait_for_load_state("load", timeout=5000)
        except Exception:
            logger.debug("[Tier 2] Load-state wait timed out before observe retry")

        loading_selectors = [
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
            "[id*='loading']",
            "[id*='spinner']",
            "[id*='skeleton']",
        ]

        for loading_selector in loading_selectors:
            try:
                loading_element = page.locator(loading_selector).first
                if await loading_element.count() > 0:
                    logger.info(f"[Tier 2] ⏳ Waiting for loading blocker to hide: {loading_selector}")
                    await loading_element.wait_for(state="hidden", timeout=5000)
            except Exception:
                continue

        await asyncio.sleep(0.4)

    async def _try_click_inside_iframe(self, page: Page, instruction: str) -> bool:
        """Try clicking actionable controls inside page iframes for generic click instructions."""
        instruction_lower = (instruction or "").lower()

        selector_candidates = [
            "button[type='submit']",
            "input[type='submit']",
            "button[name*='submit' i]",
            "button[id*='submit' i]",
            "[role='button'][name*='submit' i]",
        ]

        if any(keyword in instruction_lower for keyword in ["pay", "payment"]):
            selector_candidates = selector_candidates + [
                "button[id*='pay' i]",
                "button[name*='pay' i]",
                "input[type='button'][value*='pay' i]",
            ]

        for frame in page.frames:
            if frame == page.main_frame:
                continue

            for selector in selector_candidates:
                try:
                    locator = frame.locator(selector).first
                    await locator.wait_for(state="visible", timeout=1200)
                    await locator.click(timeout=self.timeout_ms)
                    logger.info(f"[Tier 2] ✅ Clicked iframe element using selector: {selector}")
                    return True
                except Exception:
                    continue

            try:
                button = frame.get_by_role("button", name="submit", exact=False).first
                await button.wait_for(state="visible", timeout=1200)
                await button.click(timeout=self.timeout_ms)
                logger.info("[Tier 2] ✅ Clicked iframe button by role name 'submit'")
                return True
            except Exception:
                pass

        logger.warning("[Tier 2] ⚠️ Could not find clickable submit/pay control inside iframe")
        return False

    def _is_three_hk_plan_selection_click(self, page_url: str, instruction: str, action: str) -> bool:
        """True for Three HK UAT plan-selection clicks that can bounce back on preprod."""
        if action != "click" or not is_three_hk_uat_url(page_url):
            return False

        instruction_lower = (instruction or "").lower()
        return "plan" in instruction_lower and "select" in instruction_lower

    def _extract_plan_price(self, instruction: str) -> Optional[str]:
        """Extract the numeric plan price from instructions like 'Select a $338 plan'."""
        match = re.search(r"\$\s*(\d{2,4})", instruction or "")
        if not match:
            return None
        return match.group(1)

    async def _looks_like_three_hk_plan_selection_page(self, page: Page) -> bool:
        """Heuristic: the plan-selection page shows multiple visible 'Select' buttons."""
        try:
            select_buttons = page.locator("button:has-text('Select')")
            return await select_buttons.count() >= 2
        except Exception:
            return False

    async def _wait_for_three_hk_plan_transition(self, page: Page, current_url: str) -> bool:
        """Wait briefly for the plan click to leave the selection page or complete the bounce."""
        deadline = time.time() + (min(self.timeout_ms, 5000) / 1000.0)

        while time.time() < deadline:
            if page.url != current_url:
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=1000)
                except Exception:
                    pass

            if not await self._looks_like_three_hk_plan_selection_page(page):
                return True

            await asyncio.sleep(0.25)

        return False

    async def _retry_three_hk_plan_click(self, page: Page, instruction: str) -> bool:
        """Retry the plan click using a price-aware locator instead of the generic cached XPath."""
        price = self._extract_plan_price(instruction)
        xpath_candidates = []

        if price:
            price_text = f"${price}"
            xpath_candidates.extend([
                f"(//*[self::div or self::section or self::article or self::li][contains(., '{price_text}') or contains(., '{price}')]//button[normalize-space()='Select'])[1]",
                f"(//*[contains(., '{price_text}') or contains(., '{price}')]/following::button[normalize-space()='Select'][1])[1]",
            ])

        xpath_candidates.append("(//button[normalize-space()='Select'])[1]")

        for xpath_candidate in xpath_candidates:
            try:
                button = page.locator(f"xpath={xpath_candidate}").first
                await button.wait_for(state="visible", timeout=2000)
                await button.click(timeout=self.timeout_ms)
                logger.info("[Tier 2] 🔁 Retried Three HK plan click using XPath: %s", xpath_candidate)
                return True
            except Exception:
                continue

        return False

    async def _ensure_three_hk_plan_click_progressed(
        self,
        page: Page,
        instruction: str,
        current_url: str,
    ) -> None:
        """Ensure Three HK preprod plan clicks actually advance instead of silently bouncing back."""
        if not self._is_three_hk_plan_selection_click(current_url, instruction, "click"):
            return

        if await self._wait_for_three_hk_plan_transition(page, current_url):
            return

        logger.warning(
            "[Tier 2] ⚠️ Three HK plan click stayed on the selection page. Dismissing modal and retrying once..."
        )

        await auto_dismiss_blocking_modals(page, logger)

        if await self._wait_for_three_hk_plan_transition(page, current_url):
            return

        retried = await self._retry_three_hk_plan_click(page, instruction)
        if retried and await self._wait_for_three_hk_plan_transition(page, current_url):
            return

        raise ValueError("Three HK plan selection did not advance from the plan selection page")
    
    async def _execute_action_with_xpath(
        self,
        page: Page,
        action: str,
        xpath: str,
        value: str = "",
        instruction: str = ""
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
        
        # Execute action
        if action == "click":
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            await self._wait_for_element_enabled_before_click(element, instruction)
            element_text = await element.text_content() or ""
            
            # Capture current URL before click to detect navigation
            current_url = page.url
            
            # Perform the click action
            await element.click(timeout=self.timeout_ms)
            
            click_state = await wait_for_post_click_readiness(
                page=page,
                clicked_element=element,
                instruction=instruction,
                element_text=element_text,
                current_url=current_url,
                timeout_ms=self.timeout_ms,
                logger=logger,
            )
            
            if click_state["is_payment_click"]:
                logger.info(f"[Tier 2] 💳 Checkout/payment button detected - waiting for payment gateway input fields...")
                input_found = False
                gateway_timeout = 12000 if self._is_external_payment_gateway_url(page.url) else 2500
                try:
                    await page.wait_for_selector(
                        self._payment_input_css_selector(),
                        state="visible",
                        timeout=gateway_timeout,
                    )
                    logger.info("[Tier 2] ✅ Payment input field detected")
                    input_found = True
                except Exception:
                    input_found = False
                
                if input_found:
                    await asyncio.sleep(0.3)
                    logger.info(f"[Tier 2] ✅ Payment gateway ready")
                else:
                    logger.warning(f"[Tier 2] ⚠️ No payment input fields detected (may be non-standard gateway)")

            await self._ensure_three_hk_plan_click_progressed(page, instruction, current_url)
                    
        elif action in ["fill", "type", "input"]:
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            await element.fill(value, timeout=self.timeout_ms)
            # Small delay to allow any input event handlers to complete
            await asyncio.sleep(0.3)
            
        elif action == "select":
            select_xpath = xpath
            if self._looks_like_option_xpath(xpath):
                select_xpath = self._select_xpath_from_option_xpath(xpath)

            select_element = page.locator(f"xpath={select_xpath}").first
            await select_element.wait_for(state="attached", timeout=self.timeout_ms)
            try:
                await select_element.select_option(value, timeout=self.timeout_ms)
            except Exception:
                await select_element.select_option(label=value, timeout=self.timeout_ms)
            # Wait for any onChange handlers
            await asyncio.sleep(0.3)
            
        elif action == "check":
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            if not await element.is_checked():
                await element.check(timeout=self.timeout_ms)
                await asyncio.sleep(0.3)
                
        elif action == "uncheck":
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            if await element.is_checked():
                await element.uncheck(timeout=self.timeout_ms)
                await asyncio.sleep(0.3)
                
        elif action == "hover":
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            await element.hover(timeout=self.timeout_ms)
            await asyncio.sleep(0.2)
            
        elif action in ["assert", "verify"]:
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            actual_value = await element.text_content()
            if value not in (actual_value or ""):
                raise AssertionError(
                    f"Expected '{value}' in element text, got '{actual_value}'"
                )
        elif action == "wait":
            # Element already waited for above
            pass
        elif action == "upload_file":
            await element.wait_for(state="visible", timeout=self.timeout_ms)
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

    async def _wait_for_element_enabled_before_click(self, element, instruction: str) -> None:
        """Wait briefly for element to become enabled before clicking."""
        try:
            if await element.is_enabled():
                return

            wait_deadline = time.time() + (min(self.timeout_ms, 8000) / 1000.0)
            while time.time() < wait_deadline:
                await asyncio.sleep(0.2)
                if await element.is_enabled():
                    return

            logger.warning(
                "[Tier 2] ⚠️ Click target still disabled after wait (instruction=%s)",
                instruction,
            )
        except Exception:
            # Ignore pre-check issues and let Playwright click handling raise if needed.
            return

    async def _validate_cached_xpath_for_step(
        self,
        page: Page,
        xpath: str,
        action: str,
        instruction: str,
        value: Optional[str],
    ) -> bool:
        """Validate cache entry against both DOM presence and step semantics."""
        locator = page.locator(f"xpath={xpath}").first
        await locator.wait_for(state="attached", timeout=2000)

        if action not in ["fill", "type", "input"]:
            return True

        instruction_lower = (instruction or "").lower()
        value_text = (value or "").strip().lower()

        expected_password = "password" in instruction_lower
        expected_email = ("email" in instruction_lower) or ("@" in value_text)

        if not expected_password and not expected_email:
            return True

        field_type = (await locator.get_attribute("type") or "").lower()
        field_name = (await locator.get_attribute("name") or "").lower()
        field_id = (await locator.get_attribute("id") or "").lower()
        field_placeholder = (await locator.get_attribute("placeholder") or "").lower()
        field_label = (await locator.get_attribute("aria-label") or "").lower()
        field_autocomplete = (await locator.get_attribute("autocomplete") or "").lower()

        field_hints = " ".join([
            field_type,
            field_name,
            field_id,
            field_placeholder,
            field_label,
            field_autocomplete,
        ])

        looks_like_password = (
            field_type == "password"
            or "password" in field_hints
            or "pwd" in field_hints
        )
        looks_like_email = (
            field_type == "email"
            or "email" in field_hints
            or "e-mail" in field_hints
        )

        if expected_password and not looks_like_password:
            logger.info("[Tier 2] 🔍 Cached field semantic mismatch: expected password field")
            return False

        if expected_email and looks_like_password:
            logger.info("[Tier 2] 🔍 Cached field semantic mismatch: expected email/non-password field")
            return False

        return True

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
            "exp. date",
            "exp date",
            "cvv",
            "cvc",
            "security code",
            "payment",
        ]
        return any(keyword in instruction_lower for keyword in keywords)

    def _payment_input_css_selector(self) -> str:
        """Combined CSS selector used to detect payment inputs quickly."""
        selectors = [
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
        return ", ".join(selectors)

    # Gateway hostnames shared by both detection methods below.
    _GATEWAY_HOST_KEYWORDS = [
        "gateway", "mastercard", "checkout", "pay", "payment",
        "3dsecure", "adyen", "stripe", "paypal", "cybersource",
    ]

    def _is_cross_origin_payment_host(self, url: str) -> bool:
        """Return True only when the URL hostname belongs to a known external
        payment gateway (mastercard, stripe, adyen, etc.).

        Unlike _is_external_payment_gateway_url(), this method does NOT match
        same-origin autopay pages (e.g. three.com.hk/...?step=autopay).
        Used in _try_payment_field_action to select the per-selector probe
        timeout: cross-origin iframes load slowly, same-origin forms do not.
        """
        if not url:
            return False
        hostname = (urlparse(url).hostname or "").lower()
        return any(kw in hostname for kw in self._GATEWAY_HOST_KEYWORDS)

    def _is_external_payment_gateway_url(self, url: str) -> bool:
        """Detect payment pages requiring longer readiness waits (8s).

        Returns True for:
        - External payment gateway hostnames (mastercard, stripe, adyen, etc.)
        - Same-origin autopay/checkout pages identified by URL path or query
          (e.g. ?step=autopay on wwwuat.three.com.hk).
        """
        if not url:
            return False

        if self._is_cross_origin_payment_host(url):
            return True

        # Also treat same-origin autopay pages as needing the extended wait.
        # The Three HK autopay form is SPA-rendered and takes >1500ms to mount.
        parsed = urlparse(url)
        path_and_query = (parsed.path + "?" + (parsed.query or "")).lower()
        autopay_keywords = ["autopay", "auto-pay", "step=autopay", "step=auto-pay"]
        return any(keyword in path_and_query for keyword in autopay_keywords)

    async def _maybe_wait_for_payment_gateway(self, page: Page) -> None:
        """Wait once per page for payment gateway fields to appear."""
        if self.payment_gateway_ready and self.payment_gateway_url == page.url:
            return

        timeout_ms = 8000 if self._is_external_payment_gateway_url(page.url) else 1500
        try:
            await page.wait_for_selector(
                self._payment_input_css_selector(),
                state="visible",
                timeout=timeout_ms,
            )
            logger.info(f"[Tier 2] ✅ Payment gateway ready (timeout={timeout_ms}ms)")
            self.payment_gateway_ready = True
            self.payment_gateway_url = page.url
            return
        except Exception:
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
        if self.payment_gateway_ready and self.payment_gateway_url == page.url:
            wait_timeout = 3000
        elif self._is_cross_origin_payment_host(page.url):
            # Cross-origin gateway iframe content can be slow to load
            wait_timeout = 5000
        else:
            # Same-origin page (e.g. autopay setup form): probe quickly.
            # A 10000ms fallback here causes a ~50s stall when CSS selectors
            # don't match the page's actual field attributes (ADR-002-16 gap).
            wait_timeout = 1500

        if action in ["fill", "type", "input"] and not value:
            return None

        if action == "select" and not value:
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
        elif "exp. date" in instruction_lower or "exp date" in instruction_lower or "expiry" in instruction_lower or "expiration" in instruction_lower:
            if action in ["fill", "type", "input"]:
                # Combined MM/YY or MM/YYYY expiry input (single text field)
                input_selectors = [
                    "input[name*='expiry']",
                    "input[id*='expiry']",
                    "input[name*='expiration']",
                    "input[id*='expiration']",
                    "input[name*='exp']",
                    "input[id*='exp']",
                    "input[autocomplete='cc-exp']",
                    "input[placeholder*='MM']",
                    "input[placeholder*='mm']",
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
                label_candidates = ["Card number", "Card Number", "Card no", "Card No", "Credit Card No.", "Credit Card Number"]
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

