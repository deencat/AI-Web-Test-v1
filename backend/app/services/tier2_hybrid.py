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
# Sprint 10.17: vision screenshot verification
from app.services.screenshot_verification_service import ScreenshotVerificationService
from app.services.universal_llm import VisionNotSupportedError
from app.services.timed_wait import parse_timed_wait_ms, sleep_cancel_aware
from app.services.signature_pad import sign_canvas, infer_signature_step_action

logger = logging.getLogger(__name__)


class Tier2HybridExecutor:
    """
    Tier 2: Hybrid execution using Stagehand observe() + Playwright actions.
    
    This method uses cached XPath selectors when available, or extracts them
    using Stagehand observe() and then executes with Playwright.
    
    Expected success rate: 90-95% (when Tier 1 fails)
    Cost: Low-Medium (uses caching to minimize LLM calls)
    """

    THREE_HK_PLAN_TAB_LABELS = {
        # 5G Monthly SIM Plans category
        "voucher monthly plan": "Voucher Monthly Plan",
        "world plan": "World Plan",
        "5g monthly sim plan": "5G Monthly SIM Plan",
        "diy plan": "DIY Plan",
        "multi-sim plan": "Multi-SIM Plan",
        "roam like home monthly plan": "Roam Like Home Monthly Plan",
        # 4.5G Monthly Plans category
        "4.5g sim monthly plan": "4.5G SIM Monthly Plan",
        "hk-uk pro sharing monthly plan": "HK-UK Pro Sharing Monthly Plan",
        "greater china pro monthly plan": "Greater China Pro Monthly Plan",
        # 5G Broadband category
        "hsbc credit card offer": "HSBC credit card offer",
        "tertiary students and staff offer": "Tertiary students and staff offer",
        "wi-fi 6 monthly plan": "Wi-Fi 6 Monthly Plan",
        "wi-fi 7 monthly plan": "Wi-Fi 7 Monthly Plan",
    }

    THREE_HK_PLAN_TAB_CONTENT_TOKENS = {
        "voucher monthly plan": (
            "5g handset voucher monthly plan",
            "handset voucher",
            "voucher amount",
        ),
        "world plan": (
            "world plan",
            "global data",
        ),
        # 4.5G Monthly Plans
        "hk-uk pro sharing monthly plan": (
            "hk-uk pro sharing",
            "pro sharing",
        ),
        "greater china pro monthly plan": (
            "greater china pro",
            "greater china",
        ),
        "4.5g sim monthly plan": (
            "4.5g sim monthly plan",
            "4.5g",
        ),
        # 5G Broadband
        "hsbc credit card offer": (
            "hsbc credit card",
            "hsbc",
        ),
        "tertiary students and staff offer": (
            "tertiary students",
            "staff offer",
        ),
        "wi-fi 6 monthly plan": (
            "wi-fi 6",
            "wi-fi 6 monthly plan",
        ),
        "wi-fi 7 monthly plan": (
            "wi-fi 7",
            "wi-fi 7 monthly plan",
        ),
    }

    THREE_HK_TAB_ACTIVE_HINTS = ("active", "selected", "current")

    # Mastercard Hosted Checkout gw-proxy iframe selectors by PCI field role (ADR-002-48).
    _GW_PROXY_IFRAME_SELECTORS: Dict[str, list] = {
        "card_number": [
            "iframe.gw-proxy-number",
            "iframe[id*='card-number' i]",
            "iframe[src*='/role/number/' i]",
        ],
        "expiry_month": [
            "iframe.gw-proxy-expiry-month",
            "iframe[src*='/role/expiryMonth/' i]",
            "iframe[src*='/role/expiry-month/' i]",
        ],
        "expiry_year": [
            "iframe.gw-proxy-expiry-year",
            "iframe[src*='/role/expiryYear/' i]",
            "iframe[src*='/role/expiry-year/' i]",
        ],
        "cvv": [
            "iframe.gw-proxy-cvv",
            "iframe.gw-proxy-security-code",
            "iframe[src*='/role/securityCode/' i]",
            "iframe[src*='/role/cvv/' i]",
        ],
        "cardholder": [
            "iframe.gw-proxy-name",
            "iframe[src*='/role/cardholderName/' i]",
            "iframe[src*='/role/name/' i]",
        ],
    }

    _GW_PROXY_INNER_INPUT_SELECTORS = [
        "input:not([type='hidden'])",
        "input[type='text']",
        "input[type='tel']",
        "input[type='password']",
    ]

    _GW_PROXY_INNER_SELECT_SELECTORS = ["select"]

    _LEGACY_PAYMENT_IFRAME_SELECTORS = [
        "iframe[name*='card']",
        "iframe[title*='payment']",
        "iframe[src*='payment']",
    ]

    _GW_PROXY_PAYMENT_IFRAME_SELECTORS = [
        "iframe.gw-proxy-number",
        "iframe.gw-proxy-expiry-month",
        "iframe.gw-proxy-expiry-year",
        "iframe.gw-proxy-cvv",
        "iframe.gw-proxy-name",
        "iframe[class*='gw-proxy']",
        "iframe[src*='gateway.mastercard.com'][src*='/role/']",
        "iframe[src*='/role/number/' i]",
        "iframe[src*='/role/expiryMonth/' i]",
        "iframe[src*='/role/expiryYear/' i]",
        "iframe[src*='/role/securityCode/' i]",
    ]

    # Fast detection for embedded Mastercard Hosted Checkout (ADR-002-49).
    _GW_PROXY_CHECKOUT_DETECT_SELECTORS = [
        "iframe.gw-proxy-number",
        "iframe[class*='gw-proxy']",
        "iframe[src*='gateway.mastercard.com'][src*='/role/']",
    ]
    
    def __init__(
        self,
        db: Session,
        xpath_extractor: XPathExtractor,
        timeout_ms: int = 30000,
        user_ai_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Tier 2 executor.
        
        Args:
            db: Database session for cache access
            xpath_extractor: XPath extractor service
            timeout_ms: Timeout in milliseconds for each action
            user_ai_config: Optional user AI provider config (provider, model, ...).
                            Used by Sprint 10.17 verify_screenshot vision calls.
        """
        self.db = db
        self.xpath_extractor = xpath_extractor
        self.timeout_ms = timeout_ms
        self.user_ai_config: Dict[str, Any] = user_ai_config or {}
        self.cache_service = XPathCacheService(db)
        self.payment_direct_enabled = os.getenv("ENABLE_PAYMENT_DIRECT_HANDLING", "true").lower() != "false"
        self.payment_gateway_ready = False
        self.payment_gateway_url = None
        # RC2 guard: set by _try_three_hk_plan_tab_click on success so the
        # NEXT execute_step re-verifies the tab is still selected after the
        # ADR-002-23 step-boundary spinner-settle (spinner may fire *after*
        # the tab-click step returns and reset the active tab to the default).
        self._pending_three_hk_tab_key: Optional[str] = None
    
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
                inferred = infer_signature_step_action(instruction)
                if inferred == "draw_signature":
                    action = "draw_signature"
                elif inferred == "click":
                    action = "click"
                else:
                    raise ValueError(f"No action provided for step: {instruction}")
            
            instruction = step.get("instruction", "")
            value = step.get("value", "")
            file_path = step.get("file_path", "")
            selector = step.get("selector")
            page_url = page.url
            
            logger.info(f"[Tier 2] Executing step: {action} - {instruction}")

            # RC2: if the previous step was a Three HK plan-tab click, the SPA
            # spinner may have fired *after* that step returned and silently
            # reset the active tab.  ADR-002-23's step-boundary spinner wait
            # (in ThreeTierExecutionService) clears the spinner before we reach
            # here, so this is the correct place to re-verify tab state.
            await self._verify_and_clear_pending_tab_check(page)

            # Special handling for navigate action (no XPath needed)
            if action == "navigate":
                await page.goto(value or instruction, timeout=self.timeout_ms, wait_until="domcontentloaded")
                execution_time_ms = (time.time() - start_time) * 1000
                
                logger.info(f"[Tier 2] âœ… Navigate succeeded in {execution_time_ms:.2f}ms")
                
                return {
                    "success": True,
                    "tier": 2,
                    "execution_time_ms": execution_time_ms,
                    "extraction_time_ms": 0,
                    "cache_hit": False,
                    "xpath": None,
                    "error": None
                }

            # Feature 4: timed wait — sleep without XPath / Stagehand observe
            if action == "wait":
                duration_ms = parse_timed_wait_ms(instruction, step)
                if duration_ms is None:
                    raise ValueError(
                        "Timed wait requires timeout_ms or duration in instruction"
                    )
                cancel_check = step.get("cancel_check")
                cancelled = await sleep_cancel_aware(duration_ms, cancel_check)
                if cancelled:
                    return {
                        "success": False,
                        "cancelled": True,
                        "tier": 2,
                        "execution_time_ms": (time.time() - start_time) * 1000,
                        "error": "Execution cancelled by user",
                    }
                execution_time_ms = (time.time() - start_time) * 1000
                logger.info(f"[Tier 2] Timed wait {duration_ms}ms completed in {execution_time_ms:.2f}ms")
                return {
                    "success": True,
                    "tier": 2,
                    "execution_time_ms": execution_time_ms,
                    "extraction_time_ms": 0,
                    "cache_hit": False,
                    "xpath": None,
                    "error": None,
                    "action": "wait",
                    "duration_ms": duration_ms,
                }

            # Sprint 10.17: vision-based screenshot verification
            if action == "verify_screenshot":
                return await self._execute_verify_screenshot(page, step, start_time)

            # For upload_file actions, use file_path instead of value
            if action == "upload_file":
                value = file_path or value

            instruction_lower = (instruction or "").lower()
            three_hk_guard_relevant = action == "click" and (
                self._extract_hpprm_code(instruction) is not None
                or "moneyback" in instruction_lower
                or "checkout" in instruction_lower
                or "featured monthly plan" in instruction_lower
                or ("plan" in instruction_lower and ("$" in instruction or "month" in instruction_lower))
            )
            looks_like_three_hk_promotion_page = False
            if three_hk_guard_relevant:
                looks_like_three_hk_promotion_page = await self._looks_like_three_hk_promotion_page(
                    page,
                    instruction=instruction,
                )
                logger.info(
                    "[Tier 2] 🔎 Three HK direct-handler guard: host_match=%s page_match=%s hpprm=%s moneyback=%s checkout=%s url=%s",
                    is_three_hk_uat_url(page_url),
                    looks_like_three_hk_promotion_page,
                    self._extract_hpprm_code(instruction) is not None,
                    "moneyback" in instruction_lower,
                    "checkout" in instruction_lower,
                    page_url,
                )

            if self._is_three_hk_plan_tab_click(page_url, instruction, action):
                tab_click_result = await self._try_three_hk_plan_tab_click(
                    page,
                    instruction,
                    extraction_time_ms,
                )
                if tab_click_result:
                    return tab_click_result
                raise ValueError(f"Could not verify Three HK plan tab click for step: {instruction}")

            if self._is_three_hk_promotion_card_click(
                page_url,
                instruction,
                action,
                looks_like_three_hk_promotion_page=looks_like_three_hk_promotion_page,
            ):
                promotion_click_result = await self._try_three_hk_promotion_card_click(
                    page,
                    instruction,
                    extraction_time_ms,
                )
                if promotion_click_result:
                    return promotion_click_result
                raise ValueError(f"Could not click Three HK promotion card for step: {instruction}")

            if self._is_three_hk_moneyback_panel_click(
                page_url,
                instruction,
                action,
                looks_like_three_hk_promotion_page=looks_like_three_hk_promotion_page,
            ):
                moneyback_click_result = await self._try_three_hk_moneyback_panel_click(
                    page,
                    instruction,
                    extraction_time_ms,
                )
                if moneyback_click_result:
                    return moneyback_click_result
                raise ValueError(f"Could not click Three HK Moneyback panel for step: {instruction}")

            if (
                action == "click"
                and looks_like_three_hk_promotion_page
                and "checkout" in instruction_lower
            ):
                footer_text = await self._read_three_hk_footer_cart_text(page)
                if self._three_hk_footer_shows_empty_cart(footer_text):
                    raise ValueError(
                        "Three HK checkout blocked: cart is still $0 — promotion was not selected"
                    )

            # Payment direct handler runs before cache for payment steps (ADR-002-48).
            # Stale cached XPaths to main-page inputs were winning over gw-proxy iframes.
            if self._is_payment_instruction(instruction, action) and self.payment_direct_enabled:
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

                direct_result = await self._try_payment_field_action(
                    page,
                    action,
                    instruction,
                    value,
                    start_time,
                )
                if direct_result:
                    return direct_result

            # Step 1: Try to get XPath from cache
            cached_xpath = self.cache_service.get_cached_xpath(page_url, instruction)
            anchor_retry = False

            if cached_xpath:
                cached_xpath_value = cached_xpath["xpath"]
                if (
                    self._is_payment_instruction(instruction, action)
                    and not self._xpath_targets_iframe(cached_xpath_value)
                    and await self._page_has_gw_proxy_role_iframe(page, instruction, action)
                ):
                    logger.info(
                        "[Tier 2] 🔄 Stale payment cache points to main-page input while gw-proxy iframe exists — invalidating"
                    )
                    self.cache_service.invalidate_cache(
                        page_url,
                        instruction,
                        "Payment field is inside gw-proxy iframe",
                    )
                    cached_xpath = None

            if cached_xpath:
                xpath = cached_xpath["xpath"]
                cache_hit = True
                logger.info(f"[Tier 2] ðŸŽ¯ Cache hit! Validating cached XPath: {xpath}")

                if action in ("fill", "type", "input", "select") and self._xpath_targets_iframe(xpath):
                    logger.info("[Tier 2] ðŸ§­ Cached XPath points to iframe container. Trying in-frame fill/select...")
                    filled_inside_iframe = await self._try_fill_inside_iframe(
                        page=page,
                        action=action,
                        instruction=instruction,
                        value=value,
                        iframe_xpath=xpath,
                    )
                    if filled_inside_iframe:
                        total_time_ms = (time.time() - start_time) * 1000
                        return {
                            "success": True,
                            "tier": 2,
                            "execution_time_ms": total_time_ms,
                            "extraction_time_ms": 0,
                            "playwright_time_ms": 0,
                            "cache_hit": True,
                            "xpath": None,
                            "error": None
                        }

                    logger.warning("[Tier 2] âš ï¸ Cached iframe XPath fill/select failed — invalidating")
                    self.cache_service.invalidate_cache(
                        page_url,
                        instruction,
                        "Cached iframe XPath is not fillable",
                    )
                    cache_hit = False
                    cached_xpath = None
                    xpath = None
                else:
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

                        logger.info(f"[Tier 2] âœ… Cached XPath validated successfully")
                    except Exception as e:
                        # Element doesn't exist - cache is stale, invalidate and re-extract
                        logger.warning(f"[Tier 2] âš ï¸ Cached XPath validation failed: {str(e)}")
                        logger.info(f"[Tier 2] ðŸ”„ Invalidating stale cache and re-extracting...")
                        self.cache_service.invalidate_cache(page_url, instruction, "Element not found on page")
                        cache_hit = False
                        cached_xpath = None
                        if action == "click" and self._extract_click_anchor_phrases(instruction):
                            anchor_retry = True

            if not cached_xpath:
                # Step 2: Extract XPath using Stagehand observe()
                logger.info(f"[Tier 2] ðŸ“¡ Cache miss, extracting XPath via observe()...")
                extraction_start = time.time()

                observe_instruction = instruction
                if anchor_retry:
                    observe_instruction = self._augment_observe_instruction_with_anchors(instruction)
                    logger.info(
                        "[Tier 2] Using anchor-augmented observe instruction after cache rejection"
                    )

                if self._should_wait_for_three_hk_observe_readiness(
                    page_url,
                    instruction,
                    action,
                    looks_like_three_hk_promotion_page=looks_like_three_hk_promotion_page,
                ):
                    logger.info(
                        "[Tier 2] ⏳ Three HK promotion catalog step — waiting for catalog readiness before observe()..."
                    )
                    await self._wait_for_page_interactable_for_observe(page, instruction=instruction)

                extraction_result = await self.xpath_extractor.extract_xpath_with_page(
                    page=page,
                    instruction=observe_instruction
                )

                if self._should_retry_observe_extraction(
                    extraction_result=extraction_result,
                    action=action,
                    selector=selector,
                    instruction=instruction,
                ):
                    logger.info("[Tier 2] ðŸ”„ observe() returned no results. Waiting for page to become interactable, then retrying once...")
                    await self._wait_for_page_interactable_for_observe(page, instruction=instruction)
                    extraction_result = await self.xpath_extractor.extract_xpath_with_page(
                        page=page,
                        instruction=observe_instruction
                    )
                
                extraction_time_ms = (time.time() - extraction_start) * 1000
                
                if not extraction_result["success"]:
                    # Feature 5 / Sprint 12: canvas often absent from a11y tree.
                    # Try DOM heuristics before escalating to Tier 3.
                    if action in ("draw_signature", "sign"):
                        logger.info(
                            "[Tier 2] observe() empty for signature — trying canvas heuristics"
                        )
                        sign_result = await sign_canvas(
                            page, instruction=instruction
                        )
                        if sign_result.success and sign_result.ink_verified:
                            total_time_ms = (time.time() - start_time) * 1000
                            if sign_result.xpath:
                                try:
                                    self.cache_service.cache_xpath(
                                        page_url=page_url,
                                        instruction=instruction,
                                        xpath=sign_result.xpath,
                                        extraction_time_ms=extraction_time_ms,
                                        page_title=None,
                                        element_text="signature-canvas",
                                    )
                                except Exception:
                                    pass
                            logger.info(
                                "[Tier 2] ✅ Signature via canvas heuristics "
                                "(ink verified) in %.2fms",
                                total_time_ms,
                            )
                            return {
                                "success": True,
                                "tier": 2,
                                "execution_time_ms": total_time_ms,
                                "extraction_time_ms": extraction_time_ms,
                                "playwright_time_ms": 0,
                                "cache_hit": False,
                                "xpath": sign_result.xpath,
                                "error": None,
                            }
                        logger.warning(
                            "[Tier 2] Canvas heuristics failed for signature: %s",
                            sign_result.error,
                        )
                    raise Exception(
                        f"XPath extraction failed: {extraction_result.get('error')}"
                    )
                
                xpath = extraction_result["xpath"]

                if action == "click" and self._xpath_targets_iframe(xpath):
                    logger.info("[Tier 2] ðŸ§­ XPath points to iframe container. Trying in-frame click fallback...")
                    clicked_inside_iframe = await self._try_click_inside_iframe(page, instruction, xpath)
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

                    raise ValueError(f"Could not verify iframe click fallback for step: {instruction}")

                if action in ("fill", "type", "input", "select") and self._xpath_targets_iframe(xpath):
                    logger.info("[Tier 2] ðŸ§­ XPath points to iframe container. Trying in-frame fill/select fallback...")
                    filled_inside_iframe = await self._try_fill_inside_iframe(
                        page=page,
                        action=action,
                        instruction=instruction,
                        value=value,
                        iframe_xpath=xpath,
                    )
                    if filled_inside_iframe:
                        playwright_time_ms = 0
                        total_time_ms = (time.time() - start_time) * 1000
                        return {
                            "success": True,
                            "tier": 2,
                            "execution_time_ms": total_time_ms,
                            "extraction_time_ms": extraction_time_ms,
                            "playwright_time_ms": playwright_time_ms,
                            "cache_hit": cache_hit,
                            "xpath": None,
                            "error": None
                        }

                    raise ValueError(f"Could not fill/select inside iframe for step: {instruction}")

                logger.info(f"[Tier 2] âœ… Extracted XPath in {extraction_time_ms:.2f}ms: {xpath}")
                
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
                f"[Tier 2] âœ… Step succeeded in {total_time_ms:.2f}ms "
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
            
            logger.warning(f"[Tier 2] â° Timeout: {error_msg}")
            
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
            
            # Sprint 10.17: let VisionNotSupportedError propagate so that
            # ThreeTierExecutionService can escalate verify_screenshot to Tier 3.
            if isinstance(e, VisionNotSupportedError):
                raise

            # Invalidate cache if it was a cache hit that failed
            if cache_hit and xpath:
                self.cache_service.invalidate_cache(page.url, instruction, error_msg)
            
            logger.warning(f"[Tier 2] âŒ Failed: {error_msg}")
            
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

        if action in ("click", "check"):
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

    def _payment_iframe_frame_selectors(self) -> list[str]:
        """Combined legacy and gw-proxy iframe selectors for readiness and fan-out."""
        return self._LEGACY_PAYMENT_IFRAME_SELECTORS + self._GW_PROXY_PAYMENT_IFRAME_SELECTORS

    def _infer_payment_field_role(self, instruction_lower: str, action: str) -> Optional[str]:
        """Map a payment step instruction to a gw-proxy PCI field role."""
        if "month" in instruction_lower and (
            action == "select" or "expiry" in instruction_lower or "expiration" in instruction_lower
        ):
            return "expiry_month"
        if "year" in instruction_lower and (
            action == "select" or "expiry" in instruction_lower or "expiration" in instruction_lower
        ):
            return "expiry_year"

        if "card number" in instruction_lower or "credit card" in instruction_lower:
            return "card_number"
        if "cvv" in instruction_lower or "cvc" in instruction_lower or "security code" in instruction_lower:
            return "cvv"
        if "cardholder" in instruction_lower or "card holder" in instruction_lower:
            return "cardholder"

        return None

    def _payment_field_success_result(
        self,
        start_time: float,
        page: Page,
        log_message: str,
    ) -> Dict[str, Any]:
        """Build a standard success payload for payment direct-handler actions."""
        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(log_message)
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

    def _normalize_payment_value(self, value: str, role: Optional[str]) -> str:
        """Normalize values for post-fill verification."""
        if role == "card_number":
            return re.sub(r"\D", "", value or "")
        return (value or "").strip()

    def _parse_date_value(self, value: str) -> Optional[tuple[int, int, int]]:
        """Parse yyyy/mm/dd or yyyy-mm-dd date strings."""
        if not value:
            return None
        match = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", value.strip())
        if not match:
            return None
        return int(match.group(1)), int(match.group(2)), int(match.group(3))

    def _normalize_date_for_compare(self, value: str) -> Optional[str]:
        """Normalize date strings to yyyy-mm-dd for comparison."""
        parsed = self._parse_date_value(value)
        if not parsed:
            return None
        year, month, day = parsed
        return f"{year:04d}-{month:02d}-{day:02d}"

    def _is_date_instruction(self, instruction: str, value: str) -> bool:
        """Return True when instruction/value refer to a date picker field."""
        instruction_lower = (instruction or "").lower()
        if any(
            token in instruction_lower
            for token in ("birth", "date of birth", "date picker", "date field", "dob")
        ):
            return True
        return self._parse_date_value(value or "") is not None

    def _extract_click_anchor_phrases(self, instruction: str) -> list[str]:
        """Extract anchor phrases like next to 'Collect Personal Info:' from instructions."""
        if not instruction:
            return []

        anchors: list[str] = []
        patterns = [
            r"next to\s+['\"]([^'\"]+)['\"]",
            r"near\s+['\"]([^'\"]+)['\"]",
            r"under\s+['\"]([^'\"]+)['\"]",
            r"next to\s+([^,\.;]+?)(?:\s+in\s+|\s+on\s+|\s*$)",
            r"near\s+([^,\.;]+?)(?:\s+in\s+|\s+on\s+|\s*$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                anchor = match.group(1).strip().strip("'\"")
                if anchor and anchor not in anchors:
                    anchors.append(anchor)
        return anchors

    def _augment_observe_instruction_with_anchors(self, instruction: str) -> str:
        """Add anchor hints for observe() when click-target validation failed."""
        anchors = self._extract_click_anchor_phrases(instruction)
        if not anchors:
            return instruction
        anchor_hint = "; ".join(f"adjacent to '{anchor}'" for anchor in anchors)
        return (
            f"{instruction} (IMPORTANT: click target must be {anchor_hint}, "
            "NOT header/nav/top-controls)"
        )

    async def _verify_filled_value(self, locator, value: str, role: Optional[str]) -> bool:
        """Verify a fill/select action populated the target field."""
        try:
            if role == "cvv":
                return bool((await locator.input_value() or "").strip())
            filled_raw = await locator.input_value() or ""
            if not filled_raw.strip():
                try:
                    filled_raw = (await locator.inner_text() or "").strip()
                except Exception:
                    filled_raw = filled_raw or ""

            filled_value = self._normalize_payment_value(filled_raw, role)
            expected_value = self._normalize_payment_value(value, role)
            if role == "card_number":
                return filled_value == expected_value and bool(expected_value)

            filled_date = self._normalize_date_for_compare(filled_value)
            expected_date = self._normalize_date_for_compare(expected_value)
            if filled_date and expected_date:
                return filled_date == expected_date

            return filled_value == expected_value
        except Exception:
            return False

    async def _page_has_gw_proxy_role_iframe(
        self,
        page: Page,
        instruction: str,
        action: str,
    ) -> bool:
        """Return True when a gw-proxy iframe exists for this payment step role."""
        role = self._infer_payment_field_role((instruction or "").lower(), action)
        if not role:
            return False

        for iframe_selector in self._GW_PROXY_IFRAME_SELECTORS.get(role, []):
            try:
                if await page.locator(iframe_selector).count() > 0:
                    return True
            except Exception:
                continue
        return False

    async def _gw_proxy_checkout_active(self, page: Page) -> bool:
        """Return True when Mastercard gw-proxy checkout iframes are in the DOM."""
        for iframe_selector in self._GW_PROXY_CHECKOUT_DETECT_SELECTORS:
            try:
                if await page.locator(iframe_selector).count() > 0:
                    return True
            except Exception:
                continue
        return False

    async def _fill_payment_locator(self, locator, value: str, role: Optional[str]) -> bool:
        """Fill a payment input, falling back to sequential keypress for stubborn gateways."""
        await locator.click(timeout=self.timeout_ms)
        await locator.fill(value, timeout=self.timeout_ms)
        if await self._verify_filled_value(locator, value, role):
            return True

        await locator.fill("", timeout=self.timeout_ms)
        await locator.press_sequentially(value, delay=30, timeout=self.timeout_ms)
        return await self._verify_filled_value(locator, value, role)

    async def _try_gw_proxy_payment_field(
        self,
        page: Page,
        action: str,
        instruction_lower: str,
        value: str,
        start_time: float,
        wait_timeout: int,
    ) -> Optional[Dict[str, Any]]:
        """Fill or select inside a role-specific Mastercard gw-proxy iframe."""
        role = self._infer_payment_field_role(instruction_lower, action)
        if not role:
            return None

        iframe_selectors = self._GW_PROXY_IFRAME_SELECTORS.get(role, [])
        for iframe_selector in iframe_selectors:
            try:
                iframe_locator = page.locator(iframe_selector)
                if await iframe_locator.count() == 0:
                    continue

                frame_locator = page.frame_locator(iframe_selector)
                if action == "select":
                    for inner_selector in self._GW_PROXY_INNER_SELECT_SELECTORS:
                        locator = frame_locator.locator(inner_selector).first
                        try:
                            await locator.wait_for(state="visible", timeout=wait_timeout)
                            try:
                                await locator.select_option(value, timeout=self.timeout_ms)
                            except Exception:
                                await locator.select_option(label=value, timeout=self.timeout_ms)
                            return self._payment_field_success_result(
                                start_time,
                                page,
                                f"[Tier 2] ✅ Payment select set in gw-proxy iframe: {iframe_selector} -> {inner_selector}",
                            )
                        except Exception:
                            continue
                elif action in ("fill", "type", "input"):
                    for inner_selector in self._GW_PROXY_INNER_INPUT_SELECTORS:
                        locator = frame_locator.locator(inner_selector).first
                        try:
                            await locator.wait_for(state="visible", timeout=wait_timeout)
                            if await self._fill_payment_locator(locator, value, role):
                                return self._payment_field_success_result(
                                    start_time,
                                    page,
                                    f"[Tier 2] ✅ Payment input filled in gw-proxy iframe: {iframe_selector} -> {inner_selector}",
                                )
                        except Exception:
                            continue
            except Exception:
                continue

        return None

    async def _try_fill_inside_iframe(
        self,
        page: Page,
        action: str,
        instruction: str,
        value: str,
        iframe_xpath: Optional[str] = None,
    ) -> bool:
        """Fill or select inside the iframe identified by observe() or cache."""
        target_frame = await self._resolve_iframe_target_frame(page, iframe_xpath)
        if not target_frame:
            return False

        instruction_lower = (instruction or "").lower()
        role = self._infer_payment_field_role(instruction_lower, action)
        inner_selectors = (
            self._GW_PROXY_INNER_SELECT_SELECTORS
            if action == "select"
            else self._GW_PROXY_INNER_INPUT_SELECTORS
        )

        for inner_selector in inner_selectors:
            locator = target_frame.locator(inner_selector).first
            try:
                await locator.wait_for(state="visible", timeout=2000)
                if action == "select":
                    try:
                        await locator.select_option(value, timeout=self.timeout_ms)
                    except Exception:
                        await locator.select_option(label=value, timeout=self.timeout_ms)
                    return True

                if await self._fill_payment_locator(locator, value, role):
                    return True
            except Exception:
                continue

        return False

    def _select_xpath_from_option_xpath(self, xpath: str) -> str:
        """Convert option XPath to parent select XPath for Playwright select_option()."""
        if not xpath:
            return xpath

        if "/option[" in xpath:
            return xpath.split("/option[", 1)[0]
        if xpath.endswith("/option"):
            return xpath[: -len("/option")]
        return xpath

    def _iframe_button_keywords(self, instruction: str) -> list[str]:
        """Infer likely button labels for iframe fallback clicks from the step text."""
        instruction_lower = (instruction or "").lower()
        keywords = []

        if "submit" in instruction_lower:
            keywords.append("submit")

        if any(keyword in instruction_lower for keyword in ["pay", "payment", "checkout"]):
            keywords.append("pay")

        if any(keyword in instruction_lower for keyword in ["continue", "next"]):
            keywords.append("continue")

        if any(keyword in instruction_lower for keyword in ["confirm", "proceed"]):
            keywords.append("confirm")

        if any(keyword in instruction_lower for keyword in ["login", "log in", "log-in", "sign in", "sign-in", "signin"]):
            keywords.append("login")

        if not keywords:
            keywords.extend(["submit", "pay"])

        return list(dict.fromkeys(keywords))

    def _normalize_iframe_label_text(self, raw_value: Any) -> str:
        """Normalize locator text/attribute values for iframe button matching."""
        if not isinstance(raw_value, str):
            return ""
        return raw_value.strip().lower()

    async def _iframe_locator_matches_instruction(self, locator, instruction: str) -> bool:
        """Return True when a visible iframe candidate's label matches the click instruction."""
        target_keywords = self._iframe_button_keywords(instruction)
        if not target_keywords:
            return True

        metadata_parts = []

        try:
            text_content = self._normalize_iframe_label_text(await locator.text_content())
            if text_content:
                metadata_parts.append(text_content)
        except Exception:
            pass

        for attr_name in ["value", "aria-label", "title", "name", "id"]:
            try:
                attr_value = self._normalize_iframe_label_text(await locator.get_attribute(attr_name))
                if attr_value:
                    metadata_parts.append(attr_value)
            except Exception:
                continue

        if not metadata_parts:
            logger.info("[Tier 2] Skipping iframe candidate with no readable label for instruction: %s", instruction)
            return False

        candidate_text = " ".join(dict.fromkeys(metadata_parts))
        return any(keyword in candidate_text for keyword in target_keywords)

    def _iframe_click_selector_candidates(self, instruction: str) -> list[str]:
        """Build resilient selector candidates for generic in-frame button clicks."""
        selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "input[type='image']",
        ]

        for keyword in self._iframe_button_keywords(instruction):
            selectors.extend([
                f"button[name*='{keyword}' i]",
                f"button[id*='{keyword}' i]",
                f"input[value*='{keyword}' i]",
                f"input[type='button'][value*='{keyword}' i]",
                f"[aria-label*='{keyword}' i]",
                f"[title*='{keyword}' i]",
                f"[role='button'][name*='{keyword}' i]",
            ])

        return selectors

    async def _resolve_iframe_target_frame(self, page: Page, iframe_xpath: Optional[str]):
        """Resolve the concrete Frame for an iframe XPath returned by observe()."""
        if not iframe_xpath:
            return None

        try:
            iframe_locator = page.locator(f"xpath={iframe_xpath}").first
            iframe_handle = await iframe_locator.element_handle()
            if not iframe_handle:
                logger.warning("[Tier 2] âš ï¸ Could not resolve iframe element handle for XPath: %s", iframe_xpath)
                return None

            target_frame = await iframe_handle.content_frame()
            if not target_frame:
                logger.warning("[Tier 2] âš ï¸ Could not resolve content frame for XPath: %s", iframe_xpath)
                return None

            return target_frame
        except Exception as exc:
            logger.warning("[Tier 2] âš ï¸ Failed to resolve iframe frame for XPath %s: %s", iframe_xpath, exc)
            return None

    async def _click_iframe_locator_and_verify(
        self,
        page: Page,
        locator,
        instruction: str,
        log_label: str,
    ) -> Optional[bool]:
        """Click a locator inside an iframe and verify the click progressed the page."""
        try:
            await locator.wait_for(state="visible", timeout=1200)
        except Exception:
            return None

        if not await self._iframe_locator_matches_instruction(locator, instruction):
            logger.info("[Tier 2] Skipping iframe candidate via %s because its label does not match '%s'", log_label, instruction)
            return None

        try:
            await self._wait_for_element_enabled_before_click(locator, instruction)
            element_text = await locator.text_content() or ""
            current_url = page.url
            await locator.click(timeout=self.timeout_ms)
            click_state = await wait_for_post_click_readiness(
                page=page,
                clicked_element=locator,
                instruction=instruction,
                element_text=element_text,
                current_url=current_url,
                timeout_ms=self.timeout_ms,
                logger=logger,
            )

            if click_state.get("is_navigation_click") and page.url == current_url:
                try:
                    if await locator.is_visible():
                        logger.warning(
                            "[Tier 2] âš ï¸ In-frame click left navigation control visible with no URL change: %s",
                            instruction,
                        )
                        return False
                except Exception:
                    logger.warning(
                        "[Tier 2] âš ï¸ In-frame click produced no URL change for navigation instruction: %s",
                        instruction,
                    )
                    return False

            logger.info("[Tier 2] âœ… Clicked iframe element using %s", log_label)
            return True
        except Exception as exc:
            logger.warning("[Tier 2] âš ï¸ In-frame click attempt failed via %s: %s", log_label, exc)
            return False

    THREE_HK_PROMOTION_LOADING_TEXT = "Loading promotions"

    def _extract_hpprm_code(self, instruction: str) -> Optional[str]:
        """Extract a Three HK promotion id such as HPPRM0000002896 from the step text."""
        match = re.search(r"(HPPRM\d+)", instruction or "", re.IGNORECASE)
        return match.group(1).upper() if match else None

    def _extract_three_hk_wifi_family(self, instruction: str) -> Optional[str]:
        """Return '6' or '7' when the instruction targets a Wi-Fi generation plan."""
        instruction_lower = (instruction or "").lower()
        if re.search(r"\b(?:wifi|wi\s*-?\s*fi)\s*-?\s*6\b", instruction_lower):
            return "6"
        if re.search(r"\b(?:wifi|wi\s*-?\s*fi)\s*-?\s*7\b", instruction_lower):
            return "7"
        return None

    def _contradictory_wifi_family_tokens(self, wifi_family: str) -> tuple[str, ...]:
        """Tokens that indicate the opposite Wi-Fi generation from the requested family."""
        if wifi_family == "6":
            return ("wifi7", "wifi 7", "wi-fi 7", "wi fi 7")
        if wifi_family == "7":
            return ("wifi6", "wifi 6", "wi-fi 6", "wi fi 6")
        return ()

    def _snippet_has_contradictory_wifi_family(
        self,
        instruction: str,
        snippet: Optional[str],
    ) -> bool:
        """Return True when snippet text names the opposite Wi-Fi generation."""
        wifi_family = self._extract_three_hk_wifi_family(instruction)
        if not wifi_family or not snippet:
            return False
        snippet_lower = snippet.lower()
        return any(
            token in snippet_lower
            for token in self._contradictory_wifi_family_tokens(wifi_family)
        )

    def _extract_three_hk_promotion_text_variants(self, instruction: str) -> tuple[str, ...]:
        """Extract narrow text variants for plan-name promotion steps like 'wifi7 plan'."""
        instruction_lower = (instruction or "").lower()
        variants = []

        if re.search(r"\b(?:wifi|wi\s*-?\s*fi)\s*-?\s*6\b", instruction_lower):
            variants.extend(["wifi6", "wifi 6", "wi-fi 6"])

        if re.search(r"\b(?:wifi|wi\s*-?\s*fi)\s*-?\s*7\b", instruction_lower):
            variants.extend(["wifi7", "wifi 7", "wi-fi 7"])

        return tuple(dict.fromkeys(variants))

    def _three_hk_wifi_family_xpath_exclusion(
        self,
        instruction: str,
        normalized_text_expr: str,
    ) -> str:
        """Build XPath AND-clauses that exclude the opposite Wi-Fi generation."""
        wifi_family = self._extract_three_hk_wifi_family(instruction)
        if not wifi_family:
            return ""
        exclusions = [
            f"not(contains({normalized_text_expr}, '{token}'))"
            for token in self._contradictory_wifi_family_tokens(wifi_family)
        ]
        return " and " + " and ".join(exclusions)

    def _instruction_matches_three_hk_promotion_snippet(
        self,
        instruction: str,
        snippet: Optional[str],
    ) -> bool:
        """Return True when a local card snippet still matches the requested promotion."""
        if not snippet:
            return False
        if self._snippet_has_contradictory_wifi_family(instruction, snippet):
            return False

        snippet_lower = snippet.lower()
        hpprm_code = self._extract_hpprm_code(instruction)
        if hpprm_code:
            return hpprm_code.lower() in snippet_lower

        text_variants = self._extract_three_hk_promotion_text_variants(instruction)
        if not text_variants:
            return False

        if not any(variant in snippet_lower for variant in text_variants):
            return False

        price = self._extract_plan_price(instruction)
        if price and f"${price}" not in snippet_lower and price not in snippet_lower:
            return False

        return True

    async def _read_three_hk_promotion_card_snippet(self, locator) -> Optional[str]:
        """Read a compact text snippet from a promotion card locator."""
        try:
            snippet = await locator.evaluate(
                """(el) => {
                    const container =
                      el.closest('[role="button"], button, label, div, section, article, li') || el;
                    return String(container.innerText || el.innerText || '')
                      .replace(/\\s+/g, ' ')
                      .trim()
                      .slice(0, 240);
                }"""
            )
            return snippet if snippet else None
        except Exception:
            return None

    async def _is_valid_three_hk_promotion_card_candidate(
        self,
        locator,
        instruction: str,
    ) -> bool:
        """Return True when a locator points at the requested promotion card."""
        snippet = await self._read_three_hk_promotion_card_snippet(locator)
        return self._instruction_matches_three_hk_promotion_snippet(instruction, snippet)

    async def _pick_smallest_valid_promotion_card_locator(
        self,
        page: Page,
        xpath_candidate: str,
        instruction: str,
    ):
        """Pick the smallest visible card whose snippet matches the instruction."""
        try:
            matches = page.locator(f"xpath={xpath_candidate}")
            count = await matches.count()
            if count == 0:
                return None

            best_locator = None
            best_len = None
            for index in range(min(count, 12)):
                candidate = matches.nth(index)
                try:
                    await candidate.wait_for(
                        state="visible",
                        timeout=min(self.timeout_ms, 2000),
                    )
                except Exception:
                    continue
                if not await self._is_valid_three_hk_promotion_card_candidate(
                    candidate,
                    instruction,
                ):
                    continue
                snippet = await self._read_three_hk_promotion_card_snippet(candidate)
                snippet_len = len(snippet or "")
                if best_len is None or snippet_len < best_len:
                    best_locator = candidate
                    best_len = snippet_len
            return best_locator
        except Exception:
            return None

    async def _prefer_actionable_promotion_click_target(self, card_locator):
        """Prefer a button/role=button inside the scoped promotion card."""
        try:
            button = card_locator.locator("button, [role='button']").first
            if await button.count() > 0:
                await button.wait_for(
                    state="visible",
                    timeout=min(self.timeout_ms, 3000),
                )
                return button
        except Exception:
            pass
        return card_locator

    async def _looks_like_three_hk_promotion_page(
        self,
        page: Page,
        instruction: str = "",
    ) -> bool:
        """Detect the Three HK promotion-selection SPA from stable DOM markers, not host alone."""
        page_url = getattr(page, "url", "") or ""
        if is_three_hk_uat_url(page_url):
            return True

        try:
            if await page.locator("app-new-card-footer").count() > 0:
                return True
        except Exception:
            pass

        marker_locators = [
            page.get_by_text("Featured Monthly Plans", exact=False),
            page.locator("text=/HPPRM\\d+/i"),
            page.get_by_text("Moneyback", exact=False),
        ]
        for marker in marker_locators:
            try:
                if await marker.count() > 0:
                    return True
            except Exception:
                continue

        instruction_lower = (instruction or "").lower()
        if (
            self._extract_hpprm_code(instruction) is not None
            or "moneyback" in instruction_lower
            or "checkout" in instruction_lower
            or "featured monthly plan" in instruction_lower
        ):
            try:
                title = await page.title()
                if "sales portal" in (title or "").lower():
                    return True
            except Exception:
                pass

        return False

    def _should_wait_for_three_hk_observe_readiness(
        self,
        page_url: str,
        instruction: str,
        action: str,
        looks_like_three_hk_promotion_page: bool = False,
    ) -> bool:
        """True when observe() should wait for the Three HK promotion catalog to hydrate."""
        if (
            action != "click"
            or not (looks_like_three_hk_promotion_page or is_three_hk_uat_url(page_url))
        ):
            return False

        instruction_lower = (instruction or "").lower()
        if self._extract_hpprm_code(instruction):
            return True
        if "moneyback" in instruction_lower:
            return True
        if "featured monthly plan" in instruction_lower:
            return True
        if "plan" in instruction_lower and ("$" in instruction or "month" in instruction_lower):
            return True
        return self._is_three_hk_plan_selection_click(page_url, instruction, action)

    async def _wait_for_three_hk_promotion_catalog_ready(
        self,
        page: Page,
        instruction: str = "",
    ) -> None:
        """Wait for Three HK plan cards to finish loading before observe() reads the a11y tree."""
        if not await self._looks_like_three_hk_promotion_page(page, instruction):
            return

        timeout_ms = min(self.timeout_ms, 15000)
        hpprm_code = self._extract_hpprm_code(instruction)

        loading_locator = page.get_by_text(self.THREE_HK_PROMOTION_LOADING_TEXT, exact=False)
        try:
            if await loading_locator.count() > 0 and await loading_locator.first.is_visible():
                logger.info(
                    "[Tier 2] ⏳ Waiting for Three HK promotion catalog loader to hide..."
                )
                await loading_locator.first.wait_for(state="hidden", timeout=timeout_ms)
        except Exception:
            logger.debug("[Tier 2] Promotion loading indicator wait timed out or was not present")

        if hpprm_code:
            try:
                await page.get_by_text(hpprm_code, exact=False).first.wait_for(
                    state="visible",
                    timeout=timeout_ms,
                )
                logger.info("[Tier 2] ✅ Three HK promotion catalog ready: found %s", hpprm_code)
                await asyncio.sleep(0.3)
                return
            except Exception:
                logger.warning(
                    "[Tier 2] ⚠️ Timed out waiting for promotion %s to appear in DOM before observe()",
                    hpprm_code,
                )

        catalog_markers = [
            page.get_by_text("Featured Monthly Plans", exact=False).first,
            page.locator("text=/HPPRM\\d+/i").first,
        ]
        for marker in catalog_markers:
            try:
                await marker.wait_for(state="visible", timeout=min(timeout_ms, 8000))
                logger.info("[Tier 2] ✅ Three HK promotion catalog marker visible before observe()")
                await asyncio.sleep(0.3)
                return
            except Exception:
                continue

        logger.warning(
            "[Tier 2] ⚠️ Three HK promotion catalog readiness markers not found; proceeding to observe() anyway"
        )

    async def _wait_for_page_interactable_for_observe(
        self,
        page: Page,
        instruction: str = "",
    ) -> None:
        """Wait for common loading/skeleton blockers to clear before running observe()."""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            logger.debug("[Tier 2] DOMContentLoaded wait timed out before observe retry")

        try:
            await page.wait_for_load_state("load", timeout=5000)
        except Exception:
            logger.debug("[Tier 2] Load-state wait timed out before observe retry")

        looks_like_three_hk_promotion_page = await self._looks_like_three_hk_promotion_page(
            page,
            instruction,
        )
        if self._should_wait_for_three_hk_observe_readiness(
            page.url,
            instruction,
            "click",
            looks_like_three_hk_promotion_page=looks_like_three_hk_promotion_page,
        ):
            await self._wait_for_three_hk_promotion_catalog_ready(page, instruction)

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
                    logger.info(f"[Tier 2] â³ Waiting for loading blocker to hide: {loading_selector}")
                    await loading_element.wait_for(state="hidden", timeout=5000)
            except Exception:
                continue

        await asyncio.sleep(0.4)

    def _is_three_hk_promotion_card_click(
        self,
        page_url: str,
        instruction: str,
        action: str,
        looks_like_three_hk_promotion_page: bool = False,
    ) -> bool:
        """True for Three HK UAT promotion-card clicks identified by HPPRM code in the step."""
        if (
            action != "click"
            or not (looks_like_three_hk_promotion_page or is_three_hk_uat_url(page_url))
        ):
            return False
        if self._extract_hpprm_code(instruction) is not None:
            return True

        instruction_lower = (instruction or "").lower()
        return (
            "plan" in instruction_lower
            and self._extract_plan_price(instruction) is not None
            and bool(self._extract_three_hk_promotion_text_variants(instruction))
        )

    def _is_three_hk_moneyback_panel_click(
        self,
        page_url: str,
        instruction: str,
        action: str,
        looks_like_three_hk_promotion_page: bool = False,
    ) -> bool:
        """True for Three HK UAT Moneyback reward panel clicks after a promotion card is chosen."""
        if (
            action != "click"
            or not (looks_like_three_hk_promotion_page or is_three_hk_uat_url(page_url))
        ):
            return False
        return "moneyback" in (instruction or "").lower()

    def _extract_three_hk_section_qualifier(self, instruction: str) -> Optional[str]:
        """Extract a quoted parent section label from instructions like under "Exclusion Promotion"."""
        match = re.search(
            r"\bunder\s+[\"']([^\"']+)[\"']",
            instruction or "",
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        section_label = re.sub(r"\s+", " ", match.group(1)).strip()
        return section_label or None

    def _xpath_literal(self, value: str) -> str:
        """Escape a Python string for safe embedding in an XPath literal."""
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'

        parts = value.split("'")
        return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"

    async def _read_three_hk_footer_cart_text(self, page: Page) -> str:
        """Read footer cart summary text from the Three HK plan-selection SPA."""
        try:
            footer = page.locator("app-new-card-footer").first
            if await footer.count() == 0:
                return (await page.locator("body").inner_text())[:500]
            return (await footer.inner_text()) or ""
        except Exception:
            return ""

    def _three_hk_footer_shows_empty_cart(self, footer_text: str) -> bool:
        """Return True when the sticky footer still shows an empty cart ($0)."""
        normalized = re.sub(r"\s+", "", footer_text or "").lower()
        return normalized == "$0" or normalized.endswith("$0")

    async def _find_three_hk_promotion_card_locator(self, page: Page, instruction: str):
        """Locate a visible Three HK promotion card using HPPRM id and optional price."""
        hpprm_code = self._extract_hpprm_code(instruction)
        text_variants = self._extract_three_hk_promotion_text_variants(instruction)
        if not hpprm_code and not text_variants:
            return None, None

        await self._wait_for_three_hk_promotion_catalog_ready(page, instruction)
        await self._wait_for_spa_spinner_settle(page)

        price = self._extract_plan_price(instruction)
        normalized_text = (
            "translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
        )
        wifi_exclusion = self._three_hk_wifi_family_xpath_exclusion(
            instruction,
            normalized_text,
        )
        xpath_candidates = []
        if hpprm_code:
            if price:
                xpath_candidates.append(
                    "(//*[contains(normalize-space(.), '{hpprm}')]"
                    "/ancestor::*[self::div or self::section or self::article]"
                    "[contains(., '${price}') or contains(., '{price}')][1])[1]".format(
                        hpprm=hpprm_code,
                        price=price,
                    )
                )
            xpath_candidates.extend([
                f"(//*[contains(normalize-space(.), '{hpprm_code}')])[1]",
                (
                    f"(//*[contains(., '{hpprm_code}')]"
                    f"/ancestor-or-self::*[self::div or self::section or self::article][1])[1]"
                ),
            ])

        if text_variants:
            text_predicate = " or ".join(
                f"contains({normalized_text}, '{variant}')"
                for variant in text_variants
            )
            if price:
                xpath_candidates.append(
                    "(//*[self::div or self::section or self::article or self::li]"
                    f"[({text_predicate}){wifi_exclusion}"
                    f" and (contains(., '${price}') or contains(., '{price}'))])[1]"
                )
            xpath_candidates.append(
                "(//*[self::div or self::section or self::article or self::li]"
                f"[({text_predicate}){wifi_exclusion}])[1]"
            )

        for xpath_candidate in xpath_candidates:
            locator = await self._pick_smallest_valid_promotion_card_locator(
                page,
                xpath_candidate,
                instruction,
            )
            if locator is not None:
                click_target = await self._prefer_actionable_promotion_click_target(locator)
                return click_target, xpath_candidate

        text_fallbacks = [hpprm_code] if hpprm_code else []
        text_fallbacks.extend(text_variants)
        for text_value in text_fallbacks:
            try:
                locator = page.get_by_text(text_value, exact=False).first
                await locator.wait_for(state="visible", timeout=min(self.timeout_ms, 5000))
                if await self._is_valid_three_hk_promotion_card_candidate(
                    locator,
                    instruction,
                ):
                    click_target = await self._prefer_actionable_promotion_click_target(locator)
                    return click_target, f"text={text_value}"
            except Exception:
                continue

        return None, None

    async def _verify_three_hk_promotion_card_selected(
        self,
        page: Page,
        instruction: str,
        card_locator=None,
        before_footer_text: str = "",
    ) -> bool:
        """Verify the requested promotion card became active, not just that *some* plan is selected."""
        hpprm_code = self._extract_hpprm_code(instruction)
        text_variants = self._extract_three_hk_promotion_text_variants(instruction)
        if not hpprm_code and not text_variants:
            return False

        local_selected = False
        local_snippet = None
        if card_locator is not None:
            try:
                local_state = await card_locator.evaluate(
                    """(el) => {
                        const container =
                          el.closest('[role="button"], button, label, div, section, article, li') || el;
                        const nodes = [
                          container,
                          ...container.querySelectorAll('*'),
                        ].slice(0, 80);
                        const selected = nodes.some((node) => {
                          const className = String(node.className || '').toLowerCase();
                          return node.getAttribute('aria-selected') === 'true'
                            || node.getAttribute('aria-checked') === 'true'
                            || node.getAttribute('aria-pressed') === 'true'
                            || node.getAttribute('data-selected') === 'true'
                            || /(active|selected|checked|current)/.test(className);
                        });
                        const snippet = String(container.innerText || el.innerText || '')
                          .replace(/\\s+/g, ' ')
                          .trim()
                          .slice(0, 160);
                        return { selected, snippet };
                    }"""
                )
                if isinstance(local_state, dict):
                    local_selected = bool(local_state.get("selected"))
                    local_snippet = local_state.get("snippet") or None
            except Exception:
                local_selected = False
                local_snippet = None

        target_matches_local_snippet = self._instruction_matches_three_hk_promotion_snippet(
            instruction,
            local_snippet,
        )

        logger.info(
            "[Tier 2] 🔎 Promotion verification hpprm=%s text_variants=%s local_selected=%s target_matches=%s snippet=%r",
            hpprm_code,
            text_variants,
            local_selected,
            target_matches_local_snippet,
            local_snippet,
        )
        if local_selected and (local_snippet is None or target_matches_local_snippet):
            return True

        moneyback = page.get_by_text("Moneyback", exact=False)
        reward_options_visible = False
        try:
            if await moneyback.count() > 0 and await moneyback.first.is_visible():
                reward_options_visible = True
        except Exception:
            pass

        footer_text = await self._read_three_hk_footer_cart_text(page)
        footer_non_empty = not self._three_hk_footer_shows_empty_cart(footer_text)
        footer_changed = re.sub(r"\s+", "", footer_text or "") != re.sub(
            r"\s+", "", before_footer_text or ""
        )

        promotion_error = page.get_by_text("Please select a promotion", exact=False)
        promotion_error_visible = False
        try:
            if await promotion_error.count() > 0:
                promotion_error_visible = await promotion_error.first.is_visible()
        except Exception:
            promotion_error_visible = False

        logger.info(
            "[Tier 2] 🔎 Promotion verification hpprm=%s before_footer=%r after_footer=%r changed=%s rewards_visible=%s promotion_error_visible=%s",
            hpprm_code,
            before_footer_text,
            footer_text,
            footer_changed,
            reward_options_visible,
            promotion_error_visible,
        )

        # First plan selection can legitimately prove progress by opening rewards or
        # changing the cart away from $0. When a plan is already selected, those
        # broader page signals are stale; require a target-card state change instead.
        if self._three_hk_footer_shows_empty_cart(before_footer_text):
            progress = reward_options_visible or (
                footer_non_empty and not promotion_error_visible
            )
            if not progress:
                return False
            if target_matches_local_snippet:
                return True
            footer_matches = self._instruction_matches_three_hk_promotion_snippet(
                instruction,
                footer_text,
            )
            return footer_matches

        return local_selected and target_matches_local_snippet

    async def _try_three_hk_promotion_card_click(
        self,
        page: Page,
        instruction: str,
        extraction_time_ms: float = 0,
    ) -> Optional[Dict[str, Any]]:
        """Click Three HK promotion cards via Playwright locators instead of observe()."""
        direct_click_start = time.time()
        hpprm_code = self._extract_hpprm_code(instruction)
        text_variants = self._extract_three_hk_promotion_text_variants(instruction)
        if not hpprm_code and not text_variants:
            return None
        target_label = hpprm_code or text_variants[0]

        locator, strategy = await self._find_three_hk_promotion_card_locator(page, instruction)
        if locator is None:
            logger.warning(
                "[Tier 2] ⚠️ Could not find a direct Three HK promotion card for step: %s",
                instruction,
            )
            return None

        before_footer_text = await self._read_three_hk_footer_cart_text(page)
        current_url = page.url
        await locator.click(timeout=self.timeout_ms)
        logger.info(
            "[Tier 2] 🎯 Clicked Three HK promotion card %s using %s",
            target_label,
            strategy,
        )

        await wait_for_post_click_readiness(
            page=page,
            clicked_element=locator,
            instruction=instruction,
            element_text=target_label,
            current_url=current_url,
            timeout_ms=self.timeout_ms,
            logger=logger,
        )
        await self._wait_for_spa_spinner_settle(page)

        verified = await self._verify_three_hk_promotion_card_selected(
            page,
            instruction,
            card_locator=locator,
            before_footer_text=before_footer_text,
        )
        selected_locator = locator
        if not verified:
            logger.warning(
                "[Tier 2] ⚠️ Three HK promotion card click did not expose reward options. "
                "Dismissing modal and retrying once..."
            )
            await auto_dismiss_blocking_modals(page, logger)
            retry_locator, retry_strategy = await self._find_three_hk_promotion_card_locator(
                page,
                instruction,
            )
            if retry_locator is not None:
                await retry_locator.click(timeout=self.timeout_ms)
                logger.info(
                    "[Tier 2] 🔁 Retried Three HK promotion card %s using %s",
                    target_label,
                    retry_strategy,
                )
                await self._wait_for_spa_spinner_settle(page)
                selected_locator = retry_locator

            verified = await self._verify_three_hk_promotion_card_selected(
                page,
                instruction,
                card_locator=selected_locator,
                before_footer_text=before_footer_text,
            )

        if not verified:
            raise ValueError(
                f"Three HK promotion card '{target_label}' did not appear selected after click"
            )

        execution_time_ms = (time.time() - direct_click_start) * 1000
        return {
            "success": True,
            "tier": 2,
            "execution_time_ms": execution_time_ms,
            "extraction_time_ms": extraction_time_ms,
            "playwright_time_ms": execution_time_ms,
            "cache_hit": False,
            "xpath": None,
            "error": None,
        }

    async def _find_three_hk_moneyback_panel_locator(self, page: Page, instruction: str):
        """Locate the Moneyback reward panel/card on the Three HK plan page."""
        await self._wait_for_spa_spinner_settle(page)

        label_candidates = ["Moneyback point", "Moneyback"]
        instruction_lower = (instruction or "").lower()
        section_label = self._extract_three_hk_section_qualifier(instruction)
        if "moneyback point" in instruction_lower:
            label_candidates = ["Moneyback point", "Moneyback"]
        else:
            label_candidates = ["Moneyback", "Moneyback point"]

        if section_label:
            logger.info(
                "[Tier 2] 🔎 Moneyback direct lookup extracted section qualifier=%r",
                section_label,
            )
            section_literal = self._xpath_literal(section_label)
            section_xpath_candidates = [
                (
                    "(//*[self::section or self::article or self::div or self::li]"
                    f"[contains(normalize-space(.), {section_literal})"
                    f" and .//*[contains(normalize-space(.), {self._xpath_literal(label)})]][1])"
                )
                for label in label_candidates
            ]
            section_xpath_candidates.append(
                "(//*[self::section or self::article or self::div or self::li]"
                f"[contains(normalize-space(.), {section_literal})][1])"
            )

            section_container = None
            for xpath_candidate in section_xpath_candidates:
                try:
                    section_container = page.locator(f"xpath={xpath_candidate}").first
                    await section_container.wait_for(
                        state="visible",
                        timeout=min(self.timeout_ms, 5000),
                    )
                    break
                except Exception:
                    section_container = None

            if section_container is None:
                logger.warning(
                    "[Tier 2] ⚠️ Moneyback section qualifier=%r not found; refusing global fallback",
                    section_label,
                )
                return None, None, "section-scoped", section_label, None

            container_snippet = None
            try:
                container_snippet = re.sub(
                    r"\s+",
                    " ",
                    (await section_container.inner_text()) or "",
                ).strip()[:160]
            except Exception:
                container_snippet = None

            for label in label_candidates:
                locator = section_container.get_by_text(label, exact=False).first
                try:
                    await locator.wait_for(state="visible", timeout=min(self.timeout_ms, 5000))
                    return locator, label, "section-scoped", section_label, container_snippet
                except Exception:
                    continue

            logger.warning(
                "[Tier 2] ⚠️ Moneyback section qualifier=%r found but no scoped label matched; refusing global fallback",
                section_label,
            )
            return None, None, "section-scoped", section_label, container_snippet

        for label in label_candidates:
            locator = page.get_by_text(label, exact=False).first
            try:
                await locator.wait_for(state="visible", timeout=min(self.timeout_ms, 8000))
                return locator, label, "global", None, None
            except Exception:
                continue

        return None, None, "global", section_label, None

    async def _verify_three_hk_moneyback_panel_selected(
        self,
        page: Page,
        panel_locator=None,
        section_label: Optional[str] = None,
    ) -> bool:
        """Verify Moneyback selection with local-state checks before broader page signals."""
        local_selected = False
        local_snippet = None
        if panel_locator is not None:
            try:
                local_state = await panel_locator.evaluate(
                    """(el) => {
                        const container =
                          el.closest('[role="button"], button, label, div, section, article, li') || el;
                        const nodes = [el, container].filter(Boolean);
                        const selected = nodes.some((node) => {
                          const className = String(node.className || '').toLowerCase();
                          return node.getAttribute('aria-selected') === 'true'
                            || node.getAttribute('aria-checked') === 'true'
                            || node.getAttribute('aria-pressed') === 'true'
                            || node.getAttribute('data-selected') === 'true'
                            || /(active|selected|checked|current)/.test(className);
                        });
                        const snippet = String(container.innerText || el.innerText || '')
                          .replace(/\\s+/g, ' ')
                          .trim()
                          .slice(0, 160);
                        return { selected, snippet };
                    }"""
                )
                if isinstance(local_state, dict):
                    local_selected = bool(local_state.get("selected"))
                    local_snippet = local_state.get("snippet") or None
            except Exception:
                local_selected = False
                local_snippet = None

        logger.info(
            "[Tier 2] 🔎 Moneyback verification section=%r local_selected=%s snippet=%r",
            section_label,
            local_selected,
            local_snippet,
        )
        if local_selected:
            return True
        if section_label:
            return False

        footer_text = await self._read_three_hk_footer_cart_text(page)
        footer_non_empty = not self._three_hk_footer_shows_empty_cart(footer_text)

        promotion_error = page.get_by_text("Please select a promotion", exact=False)
        try:
            if await promotion_error.count() == 0:
                return footer_non_empty
            return footer_non_empty and not await promotion_error.first.is_visible()
        except Exception:
            return False

    async def _try_three_hk_moneyback_panel_click(
        self,
        page: Page,
        instruction: str,
        extraction_time_ms: float = 0,
    ) -> Optional[Dict[str, Any]]:
        """Click the Three HK Moneyback reward panel via Playwright locators."""
        direct_click_start = time.time()
        locator, label, strategy, section_label, container_snippet = (
            await self._find_three_hk_moneyback_panel_locator(page, instruction)
        )
        if locator is None:
            logger.warning(
                "[Tier 2] ⚠️ Could not find a direct Three HK Moneyback panel for step: %s "
                "(section=%r strategy=%s snippet=%r)",
                instruction,
                section_label,
                strategy,
                container_snippet,
            )
            return None

        current_url = page.url
        await locator.click(timeout=self.timeout_ms)
        logger.info(
            "[Tier 2] 🎯 Clicked Three HK Moneyback panel strategy=%s section=%r label=%r snippet=%r",
            strategy,
            section_label,
            label,
            container_snippet,
        )

        await wait_for_post_click_readiness(
            page=page,
            clicked_element=locator,
            instruction=instruction,
            element_text=label,
            current_url=current_url,
            timeout_ms=self.timeout_ms,
            logger=logger,
        )
        await self._wait_for_spa_spinner_settle(page)

        verification_locator = locator
        if not await self._verify_three_hk_moneyback_panel_selected(
            page,
            panel_locator=verification_locator,
            section_label=section_label,
        ):
            await auto_dismiss_blocking_modals(page, logger)
            retry_locator, retry_label, retry_strategy, retry_section_label, retry_snippet = (
                await self._find_three_hk_moneyback_panel_locator(
                    page,
                    instruction,
                )
            )
            if retry_locator is not None:
                await retry_locator.click(timeout=self.timeout_ms)
                logger.info(
                    "[Tier 2] 🔁 Retried Three HK Moneyback panel strategy=%s section=%r label=%r snippet=%r",
                    retry_strategy,
                    retry_section_label,
                    retry_label,
                    retry_snippet,
                )
                verification_locator = retry_locator
                await self._wait_for_spa_spinner_settle(page)

        if not await self._verify_three_hk_moneyback_panel_selected(
            page,
            panel_locator=verification_locator,
            section_label=section_label,
        ):
            raise ValueError("Three HK Moneyback panel click did not update the cart")

        execution_time_ms = (time.time() - direct_click_start) * 1000
        return {
            "success": True,
            "tier": 2,
            "execution_time_ms": execution_time_ms,
            "extraction_time_ms": extraction_time_ms,
            "playwright_time_ms": execution_time_ms,
            "cache_hit": False,
            "xpath": None,
            "error": None,
        }

    async def _try_click_inside_iframe(
        self,
        page: Page,
        instruction: str,
        iframe_xpath: Optional[str] = None,
    ) -> bool:
        """Try clicking actionable controls inside the specific iframe identified by observe()."""
        target_frame = await self._resolve_iframe_target_frame(page, iframe_xpath)
        if target_frame:
            frames_to_try = [target_frame]
        else:
            frames_to_try = [frame for frame in page.frames if frame != page.main_frame]
            if len(frames_to_try) > 1:
                logger.warning(
                    "[Tier 2] âš ï¸ Refusing generic iframe fallback across %s frames without a resolved target iframe",
                    len(frames_to_try),
                )
                return False

        if not frames_to_try:
            logger.warning("[Tier 2] âš ï¸ Could not find any candidate iframe to inspect for step: %s", instruction)
            return False

        selector_candidates = self._iframe_click_selector_candidates(instruction)
        role_candidates = self._iframe_button_keywords(instruction)

        for frame in frames_to_try:
            for role_name in role_candidates:
                button = frame.get_by_role("button", name=role_name, exact=False).first
                click_result = await self._click_iframe_locator_and_verify(
                    page,
                    button,
                    instruction,
                    f"role button '{role_name}'",
                )
                if click_result is True:
                    return True
                if click_result is False:
                    return False

            for selector in selector_candidates:
                locator = frame.locator(selector).first
                click_result = await self._click_iframe_locator_and_verify(
                    page,
                    locator,
                    instruction,
                    f"selector {selector}",
                )
                if click_result is True:
                    return True
                if click_result is False:
                    return False

        logger.warning("[Tier 2] âš ï¸ Could not find a verified clickable control inside iframe for step: %s", instruction)
        return False

    def _extract_three_hk_plan_tab_key(self, instruction: str) -> Optional[str]:
        """Return the canonical Three HK plan-tab key referenced by the instruction."""
        instruction_lower = (instruction or "").lower()
        for tab_key in sorted(self.THREE_HK_PLAN_TAB_LABELS, key=len, reverse=True):
            if tab_key in instruction_lower:
                return tab_key
        return None

    def _is_three_hk_plan_tab_click(self, page_url: str, instruction: str, action: str) -> bool:
        """True for same-page Three HK plan-tab clicks that need explicit tab-state validation."""
        if action != "click" or not is_three_hk_uat_url(page_url):
            return False

        instruction_lower = (instruction or "").lower()
        if "tab" not in instruction_lower:
            return False

        return self._extract_three_hk_plan_tab_key(instruction) is not None

    def _expected_three_hk_plan_tab_tokens(self, tab_key: str) -> tuple[str, ...]:
        return self.THREE_HK_PLAN_TAB_CONTENT_TOKENS.get(tab_key, (tab_key,))

    async def _find_three_hk_plan_tab_locator(self, page: Page, instruction: str):
        """Find the target Three HK plan-tab control using role/text locators instead of cached XPath.

        After a cross-category navigation the SPA may not have hydrated the new tab
        row yet when this is called from _try_three_hk_plan_tab_click.  If every
        candidate reports count()==0 we do one bounded wait_for(state='visible') on
        the role='tab' candidate before giving up, so the tab row has time to render
        (ADR-002-37 Root Cause 1).
        """
        tab_key = self._extract_three_hk_plan_tab_key(instruction)
        if not tab_key:
            return None, None, None

        label = self.THREE_HK_PLAN_TAB_LABELS[tab_key]
        locator_candidates = [
            ("role 'tab'", page.get_by_role("tab", name=label, exact=False).first),
            ("role 'button'", page.get_by_role("button", name=label, exact=False).first),
            ("text", page.get_by_text(label, exact=False).first),
        ]

        # First pass: instant check for already-rendered tab row
        first_candidate_locator = None
        for strategy, locator in locator_candidates:
            try:
                if await locator.count() == 0:
                    if first_candidate_locator is None:
                        first_candidate_locator = locator
                    continue
                if not await locator.is_visible():
                    continue
                return locator, label, strategy
            except Exception:
                continue

        # Second pass: tab row not yet rendered â€” wait for the first candidate to appear
        if first_candidate_locator is not None:
            _TAB_ROW_APPEAR_TIMEOUT_MS = min(self.timeout_ms, 5000)
            try:
                await first_candidate_locator.wait_for(
                    state="visible", timeout=_TAB_ROW_APPEAR_TIMEOUT_MS
                )
                logger.info(
                    "[Tier 2] âŒ› Tab row appeared after bounded wait (%dms) for '%s'",
                    _TAB_ROW_APPEAR_TIMEOUT_MS, label,
                )
                return first_candidate_locator, label, "role 'tab' (waited)"
            except Exception:
                pass

        return None, label, None

    async def _is_three_hk_plan_tab_selected(self, page: Page, tab_key: str) -> bool:
        """Heuristic selected-state check for the visible plan tab matching the target label."""
        label = self.THREE_HK_PLAN_TAB_LABELS.get(tab_key)
        if not label:
            return False

        locator_candidates = [
            page.get_by_role("tab", name=label, exact=False).first,
            page.get_by_role("button", name=label, exact=False).first,
            page.get_by_text(label, exact=False).first,
        ]

        for locator in locator_candidates:
            try:
                if await locator.count() == 0 or not await locator.is_visible():
                    continue

                aria_selected = (await locator.get_attribute("aria-selected") or "").lower()
                aria_current = (await locator.get_attribute("aria-current") or "").lower()
                data_state = (await locator.get_attribute("data-state") or "").lower()
                class_name = (await locator.get_attribute("class") or "").lower()

                if aria_selected == "true":
                    return True
                if aria_current in {"true", "page", "step", "location"}:
                    return True
                if data_state in self.THREE_HK_TAB_ACTIVE_HINTS:
                    return True
                if any(token in class_name for token in self.THREE_HK_TAB_ACTIVE_HINTS):
                    return True
            except Exception:
                continue

        return False

    async def _capture_three_hk_plan_tab_snapshot(self, page: Page, instruction: str) -> Optional[Dict[str, Any]]:
        """Capture a compact target-tab snapshot so same-url tab clicks can prove visible progress."""
        tab_key = self._extract_three_hk_plan_tab_key(instruction)
        if not tab_key:
            return None

        body_text = ""
        try:
            body_text = ((await page.locator("body").first.text_content()) or "").lower()
        except Exception:
            body_text = ""

        matching_tokens = tuple(
            token for token in self._expected_three_hk_plan_tab_tokens(tab_key)
            if token in body_text
        )
        target_selected = await self._is_three_hk_plan_tab_selected(page, tab_key)

        return {
            "tab_key": tab_key,
            "target_selected": target_selected,
            "matching_tokens": matching_tokens,
            "signature": (page.url, target_selected, matching_tokens),
        }

    def _has_three_hk_plan_tab_progress(
        self,
        before_snapshot: Optional[Dict[str, Any]],
        after_snapshot: Optional[Dict[str, Any]],
    ) -> bool:
        """Return True only when the target tab is now visibly active and the snapshot changed."""
        if not after_snapshot:
            return False

        if not after_snapshot["target_selected"] and not after_snapshot["matching_tokens"]:
            return False

        if before_snapshot is None:
            return True

        return after_snapshot["signature"] != before_snapshot["signature"]

    async def _wait_for_three_hk_plan_tab_transition(
        self,
        page: Page,
        current_url: str,
        instruction: str,
        before_snapshot: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Wait briefly for a same-url Three HK tab click to surface the requested tab content."""
        deadline = time.time() + (min(self.timeout_ms, 5000) / 1000.0)

        while time.time() < deadline:
            if page.url != current_url:
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=1000)
                except Exception:
                    pass

            after_snapshot = await self._capture_three_hk_plan_tab_snapshot(page, instruction)
            if self._has_three_hk_plan_tab_progress(before_snapshot, after_snapshot):
                return True

            await asyncio.sleep(0.25)

        return False

    async def _retry_three_hk_plan_tab_click(self, page: Page, instruction: str) -> bool:
        """Retry a Three HK tab click using the tab label instead of a generic cached container."""
        locator, label, strategy = await self._find_three_hk_plan_tab_locator(page, instruction)
        if locator is None:
            return False

        try:
            await locator.wait_for(state="visible", timeout=2000)
            await locator.click(timeout=self.timeout_ms)
            logger.info("[Tier 2] ðŸŽ¯ Clicked Three HK tab using %s '%s'", strategy, label)
            return True
        except Exception:
            return False

    async def _ensure_three_hk_plan_tab_click_progressed(
        self,
        page: Page,
        instruction: str,
        current_url: str,
        before_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Ensure a Three HK tab click actually leaves the page on the requested tab."""
        if not self._is_three_hk_plan_tab_click(current_url, instruction, "click"):
            return

        if await self._wait_for_three_hk_plan_tab_transition(page, current_url, instruction, before_snapshot):
            return

        logger.warning(
            "[Tier 2] âš ï¸ Three HK plan tab click was not verified. Dismissing modal and retrying once..."
        )

        await auto_dismiss_blocking_modals(page, logger)
        # Settle any spinner triggered by the modal dismiss before re-checking tab state
        await self._wait_for_spa_spinner_settle(page)

        if await self._wait_for_three_hk_plan_tab_transition(page, current_url, instruction, before_snapshot):
            return

        retried = await self._retry_three_hk_plan_tab_click(page, instruction)
        if retried:
            await self._wait_for_spa_spinner_settle(page)
        if retried and await self._wait_for_three_hk_plan_tab_transition(page, current_url, instruction, before_snapshot):
            return

        raise ValueError("Three HK plan tab did not stay on the requested tab")

    async def _wait_for_spa_spinner_settle(self, page: Page) -> None:
        """Wait for the Three HK SPA spinner-border lifecycle to complete after a tab click.

        The SPA mounts a Bootstrap spinner when it fetches plan data after a tab switch.
        The spinner may appear up to ~500 ms after the click and takes ~3 s to clear.
        Verifying tab state before this cycle completes gives a false positive because
        React overwrites the active-tab class when the data fetch resolves (RC1 / RC2).
        """
        _SPINNER_CSS = "div[role='status'].spinner-border, [role='status'].spinner-border"
        _APPEAR_TIMEOUT_MS = 1500  # how long to wait for spinner to mount (SPA mounts ~1170ms after click)
        _SETTLE_TIMEOUT_MS = min(self.timeout_ms, 8000)  # how long to wait for it to clear

        try:
            spinner = page.locator(_SPINNER_CSS)
            # Probe whether the spinner appears within the appear window
            try:
                await spinner.first.wait_for(state="visible", timeout=_APPEAR_TIMEOUT_MS)
            except Exception:
                # Spinner never mounted â€” tab click had no fetch cycle; nothing to wait for
                return

            # Spinner is visible â€” wait for it to clear before checking tab state
            count = await spinner.count()
            if count > 0:
                await spinner.wait_for(state="hidden", timeout=_SETTLE_TIMEOUT_MS)
                logger.info("[Tier 2] âŒ› Three HK SPA spinner cleared after tab click")
        except Exception as exc:
            logger.debug("[Tier 2] _wait_for_spa_spinner_settle: %s", exc)

    async def _recovery_click_three_hk_tab(self, page: Page, tab_key: str) -> bool:
        """One-shot recovery: re-click the tab by tab_key and wait for spinner settle.

        Called by _verify_and_clear_pending_tab_check when the tab has already
        reverted.  Returns True if the tab is selected after the recovery click,
        False otherwise (including locator-not-found and click exceptions).
        """
        recovery_instruction = f"click {tab_key} tab"
        locator, label, strategy = await self._find_three_hk_plan_tab_locator(page, recovery_instruction)
        if locator is None:
            logger.warning(
                "[Tier 2] âŒ Recovery re-click: locator not found for tab key '%s'", tab_key
            )
            return False
        try:
            await locator.click(timeout=min(self.timeout_ms, 5000))
            logger.info("[Tier 2] ðŸ”„ Recovery re-click: clicked '%s' tab via %s", tab_key, strategy)
            await self._wait_for_spa_spinner_settle(page)
            recovered = await self._is_three_hk_plan_tab_selected(page, tab_key)
            if recovered:
                logger.info("[Tier 2] âœ… Recovery re-click: '%s' tab is now selected", tab_key)
            else:
                logger.warning("[Tier 2] âŒ Recovery re-click: '%s' tab still not selected", tab_key)
            return recovered
        except Exception as exc:
            logger.warning("[Tier 2] âŒ Recovery re-click raised: %s", exc)
            return False

    async def _verify_and_clear_pending_tab_check(self, page: Page) -> None:
        """RC2 guard + RC3 recovery: re-verify the previously-clicked Three HK plan tab.

        Called at the start of execute_step *after* the ADR-002-23 step-boundary
        spinner-settle has already cleared.  If the spinner fired after the
        tab-click step returned and the SPA silently reset the active tab to its
        default (World Plan), a single recovery re-click is attempted before
        raising ValueError so executions are not unnecessarily failed.
        """
        if self._pending_three_hk_tab_key is None:
            return

        tab_key = self._pending_three_hk_tab_key
        self._pending_three_hk_tab_key = None  # clear regardless of outcome

        still_selected = await self._is_three_hk_plan_tab_selected(page, tab_key)
        if still_selected:
            logger.info(
                "[Tier 2] \u2705 Post-settle tab re-check: '%s' tab is still selected", tab_key
            )
            return

        logger.warning(
            "[Tier 2] \u26a0\ufe0f Post-settle tab re-check: '%s' tab reverted after SPA spinner. "
            "Attempting recovery re-click.",
            tab_key,
        )
        recovered = await self._recovery_click_three_hk_tab(page, tab_key)
        if recovered:
            return

        logger.warning(
            "[Tier 2] \u274c Post-settle tab re-check: '%s' tab reverted and recovery failed. "
            "Raising ValueError so the plan-tab step is retried.",
            tab_key,
        )
        raise ValueError(
            f"Three HK plan tab '{tab_key}' reverted to default after SPA spinner-settle. "
            "The tab-click step must be retried."
        )

    async def _try_three_hk_plan_tab_click(
        self,
        page: Page,
        instruction: str,
        extraction_time_ms: float = 0,
    ) -> Optional[Dict[str, Any]]:
        """Execute Three HK plan-tab clicks via label-first locators and require visible tab-state progress."""
        direct_click_start = time.time()
        before_snapshot = await self._capture_three_hk_plan_tab_snapshot(page, instruction)
        locator, label, strategy = await self._find_three_hk_plan_tab_locator(page, instruction)
        if locator is None:
            logger.warning("[Tier 2] âš ï¸ Could not find a direct Three HK tab locator for step: %s", instruction)
            return None

        current_url = page.url

        await locator.wait_for(state="visible", timeout=self.timeout_ms)
        await locator.click(timeout=self.timeout_ms)
        logger.info("[Tier 2] ðŸŽ¯ Clicked Three HK tab using %s '%s'", strategy, label)

        await wait_for_post_click_readiness(
            page=page,
            clicked_element=locator,
            instruction=instruction,
            element_text=label,
            current_url=current_url,
            timeout_ms=self.timeout_ms,
            logger=logger,
        )

        # RC1/RC2: wait_for_post_click_readiness exits early for same-URL tab clicks
        # (non-navigation). Explicitly settle the SPA data-fetch spinner so the
        # progress check runs against the final DOM state, not the immediate DOM event.
        await self._wait_for_spa_spinner_settle(page)

        await self._ensure_three_hk_plan_tab_click_progressed(
            page,
            instruction,
            current_url,
            before_snapshot,
        )

        # RC2: store the tab key so the NEXT execute_step can re-verify
        # after the ADR-002-23 step-boundary spinner clears (the spinner
        # may mount *after* this step returns, resetting the active tab).
        tab_key = self._extract_three_hk_plan_tab_key(instruction)
        if tab_key:
            self._pending_three_hk_tab_key = tab_key
            logger.info("[Tier 2] ðŸ“Œ Registered pending tab re-check for key: %s", tab_key)

        execution_time_ms = (time.time() - direct_click_start) * 1000
        return {
            "success": True,
            "tier": 2,
            "execution_time_ms": execution_time_ms,
            "extraction_time_ms": extraction_time_ms,
            "playwright_time_ms": execution_time_ms,
            "cache_hit": False,
            "xpath": None,
            "error": None,
        }

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
        text_variants = self._extract_three_hk_promotion_text_variants(instruction)
        wifi_family = self._extract_three_hk_wifi_family(instruction)
        xpath_candidates = []

        normalized_text = (
            "translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
        )
        wifi_exclusion = self._three_hk_wifi_family_xpath_exclusion(
            instruction,
            normalized_text,
        )

        if text_variants:
            text_predicate = " or ".join(
                f"contains({normalized_text}, '{variant}')"
                for variant in text_variants
            )
            card_scope = (
                f"//*[self::div or self::section or self::article or self::li]"
                f"[({text_predicate}){wifi_exclusion}"
            )
            if price:
                price_text = f"${price}"
                xpath_candidates.extend([
                    (
                        f"({card_scope} and (contains(., '{price_text}') "
                        f"or contains(., '{price}'))]"
                        f"//button[normalize-space()='Select'])[1]"
                    ),
                    (
                        f"({card_scope} and (contains(., '{price_text}') "
                        f"or contains(., '{price}'))]"
                        f"/following::button[normalize-space()='Select'][1])[1]"
                    ),
                ])
            else:
                xpath_candidates.append(
                    f"({card_scope}]//button[normalize-space()='Select'])[1]"
                )

        if price:
            price_text = f"${price}"
            xpath_candidates.extend([
                (
                    f"(//*[self::div or self::section or self::article or self::li]"
                    f"[(contains(., '{price_text}') or contains(., '{price}'))"
                    f"{wifi_exclusion}]//button[normalize-space()='Select'])[1]"
                ),
                (
                    f"(//*[contains(., '{price_text}') or contains(., '{price}')]"
                    f"/following::button[normalize-space()='Select'][1])[1]"
                ),
            ])

        if not wifi_family:
            xpath_candidates.append("(//button[normalize-space()='Select'])[1]")

        for xpath_candidate in xpath_candidates:
            try:
                button = page.locator(f"xpath={xpath_candidate}").first
                await button.wait_for(state="visible", timeout=2000)
                await button.click(timeout=self.timeout_ms)
                logger.info("[Tier 2] ðŸ” Retried Three HK plan click using XPath: %s", xpath_candidate)
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
            "[Tier 2] âš ï¸ Three HK plan click stayed on the selection page. Dismissing modal and retrying once..."
        )

        await auto_dismiss_blocking_modals(page, logger)

        if await self._wait_for_three_hk_plan_transition(page, current_url):
            return

        retried = await self._retry_three_hk_plan_click(page, instruction)
        if retried and await self._wait_for_three_hk_plan_transition(page, current_url):
            return

        raise ValueError("Three HK plan selection did not advance from the plan selection page")

    async def _element_in_header_or_nav(self, locator) -> bool:
        """Return True when the locator resolves inside header/nav/top-controls."""
        try:
            return await locator.evaluate(
                """el => {
                    let node = el;
                    while (node) {
                        const tag = (node.tagName || '').toLowerCase();
                        const role = node.getAttribute && node.getAttribute('role');
                        const cls = (node.className || '').toString().toLowerCase();
                        if (
                            tag === 'header' || tag === 'nav' ||
                            role === 'navigation' || role === 'banner' ||
                            cls.includes('header') || cls.includes('navbar') ||
                            cls.includes('top-controls') || cls.includes('topbar')
                        ) {
                            return true;
                        }
                        node = node.parentElement;
                    }
                    return false;
                }"""
            )
        except Exception:
            return False

    async def _anchor_text_in_main_content(self, page: Page, anchor: str) -> bool:
        """Return True when anchor text appears in main content (not header-only)."""
        try:
            return await page.evaluate(
                """(anchor) => {
                    const main = document.querySelector('main')
                        || document.querySelector('[role="main"]')
                        || document.body;
                    return (main.innerText || '').includes(anchor);
                }""",
                anchor,
            )
        except Exception:
            return True

    async def _elements_are_proximate(self, page: Page, locator, anchor: str) -> bool:
        """Heuristic: click target should be near the anchor text on the page."""
        try:
            box = await locator.bounding_box()
            if not box:
                return True

            anchor_locator = page.get_by_text(anchor, exact=False).first
            if await anchor_locator.count() == 0:
                return True

            anchor_box = await anchor_locator.bounding_box()
            if not anchor_box:
                return True

            click_cx = box["x"] + box["width"] / 2
            click_cy = box["y"] + box["height"] / 2
            anchor_cx = anchor_box["x"] + anchor_box["width"] / 2
            anchor_cy = anchor_box["y"] + anchor_box["height"] / 2
            distance = ((click_cx - anchor_cx) ** 2 + (click_cy - anchor_cy) ** 2) ** 0.5
            return distance <= 600
        except Exception:
            return True

    async def _validate_click_target_for_instruction(
        self,
        page: Page,
        locator,
        instruction: str,
    ) -> bool:
        """Validate click target against anchor phrases in the instruction."""
        anchors = self._extract_click_anchor_phrases(instruction)
        if not anchors:
            return True

        for anchor in anchors:
            try:
                anchor_locator = page.get_by_text(anchor, exact=False).first
                if await anchor_locator.count() == 0 or not await anchor_locator.is_visible():
                    logger.info(
                        "[Tier 2] Click anchor '%s' not visible on page",
                        anchor,
                    )
                    return False
            except Exception:
                return False

            click_in_header = await self._element_in_header_or_nav(locator)
            anchor_in_main = await self._anchor_text_in_main_content(page, anchor)
            if click_in_header and anchor_in_main:
                logger.info(
                    "[Tier 2] Click target in header/nav but anchor '%s' is in main content",
                    anchor,
                )
                return False

            if not await self._elements_are_proximate(page, locator, anchor):
                logger.info(
                    "[Tier 2] Click target too far from anchor '%s'",
                    anchor,
                )
                return False

        return True

    async def _read_date_picker_header_month_year(self, page: Page) -> Optional[tuple[int, int]]:
        """Read visible month/year from an open date picker header."""
        header_selectors = [
            "[class*='picker'] [class*='header']",
            "[class*='calendar'] [class*='header']",
            ".datepicker-header",
            "[role='heading']",
        ]
        month_names = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        for selector in header_selectors:
            try:
                header = page.locator(selector).first
                if await header.count() == 0:
                    continue
                header_text = (await header.inner_text() or "").lower()
                year_match = re.search(r"(20\d{2})", header_text)
                if not year_match:
                    continue
                year = int(year_match.group(1))
                month = None
                for name, number in month_names.items():
                    if name in header_text:
                        month = number
                        break
                if month:
                    return year, month
            except Exception:
                continue
        return None

    async def _navigate_date_picker_to(self, page: Page, target_year: int, target_month: int) -> None:
        """Navigate an open date picker calendar to the target month/year."""
        prev_selectors = [
            "[aria-label*='Previous']",
            "[aria-label*='prev']",
            "button[class*='prev']",
            ".datepicker-prev",
        ]
        next_selectors = [
            "[aria-label*='Next']",
            "[aria-label*='next']",
            "button[class*='next']",
            ".datepicker-next",
        ]

        for _ in range(24):
            current = await self._read_date_picker_header_month_year(page)
            if current == (target_year, target_month):
                return

            if not current:
                return

            current_year, current_month = current
            go_forward = (current_year, current_month) < (target_year, target_month)
            selectors = next_selectors if go_forward else prev_selectors
            clicked = False
            for selector in selectors:
                try:
                    button = page.locator(selector).first
                    if await button.count() > 0 and await button.is_visible():
                        await button.click(timeout=self.timeout_ms)
                        clicked = True
                        await asyncio.sleep(0.2)
                        break
                except Exception:
                    continue
            if not clicked:
                return

    async def _fill_date_picker_field(self, locator, value: str, page: Page) -> bool:
        """Fill a custom date picker and verify the value persists."""
        parsed = self._parse_date_value(value)
        if not parsed:
            return False

        target_year, target_month, target_day = parsed
        normalized_value = f"{target_year}/{target_month:02d}/{target_day:02d}"

        await locator.wait_for(state="visible", timeout=self.timeout_ms)
        await locator.click(timeout=self.timeout_ms)
        await asyncio.sleep(0.2)

        await self._navigate_date_picker_to(page, target_year, target_month)

        day_str = str(target_day)
        day_clicked = False
        day_locator_groups = [
            page.get_by_role("gridcell", name=day_str),
            page.locator(f"[role='gridcell']:has-text('{day_str}')"),
            page.locator(f"td:has-text('{day_str}')"),
            page.locator(f"button:has-text('{day_str}')"),
        ]
        for group in day_locator_groups:
            try:
                count = await group.count()
                for index in range(count):
                    cell = group.nth(index)
                    cell_text = (await cell.inner_text() or "").strip()
                    if cell_text != day_str:
                        continue
                    await cell.click(timeout=self.timeout_ms)
                    day_clicked = True
                    break
                if day_clicked:
                    break
            except Exception:
                continue

        if not day_clicked:
            await locator.fill(normalized_value, timeout=self.timeout_ms)
            await locator.press("Enter")

        await asyncio.sleep(0.3)
        try:
            await locator.evaluate("el => el.blur()")
        except Exception:
            pass

        calendar = await self._read_date_picker_header_month_year(page)
        if calendar and calendar != (target_year, target_month):
            logger.warning(
                "[Tier 2] Date picker calendar month mismatch after fill: expected %s-%02d, got %s",
                target_year,
                target_month,
                calendar,
            )
            return False

        for candidate in (value, normalized_value, f"{target_year}-{target_month:02d}-{target_day:02d}"):
            if await self._verify_filled_value(locator, candidate, role=None):
                return True
        return False

    async def _try_custom_dropdown_select(
        self,
        page: Page,
        instruction: str,
        value: str,
        xpath: str,
    ) -> bool:
        """Two-phase custom dropdown: open trigger, pick option, verify selection."""
        if not value:
            return False

        xpath_clean = xpath[6:] if xpath.startswith("xpath=") else xpath
        trigger_xpath = xpath_clean
        if self._looks_like_option_xpath(xpath_clean):
            trigger_xpath = self._select_xpath_from_option_xpath(xpath_clean)

        trigger = page.locator(f"xpath={trigger_xpath}").first
        await trigger.wait_for(state="visible", timeout=self.timeout_ms)

        try:
            tag_name = (await trigger.evaluate("el => el.tagName") or "").lower()
        except Exception:
            tag_name = ""

        if tag_name == "select":
            return False

        await trigger.click(timeout=self.timeout_ms)

        listbox_selectors = [
            "[role='listbox']",
            "[role='menu']",
            ".dropdown-menu",
            "[class*='dropdown-menu']",
        ]
        for selector in listbox_selectors:
            try:
                listbox = page.locator(selector).first
                await listbox.wait_for(state="visible", timeout=2000)
                break
            except Exception:
                continue

        option_clicked = False
        option_locators = [
            page.get_by_role("option", name=value),
            page.get_by_role("menuitem", name=value),
            page.locator(f"[role='option']:has-text('{value}')"),
            page.locator(f"li:has-text('{value}')"),
            page.get_by_text(value, exact=True),
        ]
        for option_locator in option_locators:
            try:
                if await option_locator.count() == 0:
                    continue
                await option_locator.first.click(timeout=self.timeout_ms)
                option_clicked = True
                break
            except Exception:
                continue

        if not option_clicked:
            raise ValueError(f"Could not find dropdown option '{value}' for step: {instruction}")

        await asyncio.sleep(0.3)

        display_text = ""
        try:
            display_text = (await trigger.inner_text() or "").strip()
        except Exception:
            display_text = ""

        if value.lower() not in display_text.lower():
            try:
                parent = trigger.locator("xpath=..")
                display_text = (await parent.inner_text() or "").strip()
            except Exception:
                display_text = display_text or ""

        if value.lower() not in display_text.lower():
            raise ValueError(
                f"Custom dropdown verification failed: expected '{value}', got '{display_text}'"
            )

        return True
    
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
        print(f"\nðŸ”¥ðŸ”¥ðŸ”¥ [TIER2 DEBUG] _execute_action_with_xpath called with action='{action}', xpath='{xpath[:100] if len(xpath) > 100 else xpath}', value='{value}' ðŸ”¥ðŸ”¥ðŸ”¥\n", flush=True)
        logger.info(f"[Tier 2] ðŸŽ¬ _execute_action_with_xpath called with action='{action}', xpath='{xpath[:100]}', value='{value}'")
        
        # Ensure xpath doesn't have double prefix
        # XPath should be just the path, e.g., "/html/body/..."
        if xpath.startswith('xpath='):
            xpath = xpath[6:]  # Remove xpath= prefix
        
        # Use XPath locator
        element = page.locator(f"xpath={xpath}").first
        
        # Execute action
        if action == "click":
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            if not await self._validate_click_target_for_instruction(page, element, instruction):
                raise ValueError(
                    f"Click target failed anchor validation for step: {instruction}"
                )
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
                logger.info(f"[Tier 2] ðŸ’³ Checkout/payment button detected - waiting for payment gateway input fields...")
                input_found = False
                gateway_timeout = 12000 if self._is_external_payment_gateway_url(page.url) else 2500
                try:
                    await page.wait_for_selector(
                        self._payment_input_css_selector(),
                        state="visible",
                        timeout=gateway_timeout,
                    )
                    logger.info("[Tier 2] âœ… Payment input field detected")
                    input_found = True
                except Exception:
                    input_found = False
                
                if input_found:
                    await asyncio.sleep(0.3)
                    logger.info(f"[Tier 2] âœ… Payment gateway ready")
                else:
                    logger.warning(f"[Tier 2] âš ï¸ No payment input fields detected (may be non-standard gateway)")

            await self._ensure_three_hk_plan_click_progressed(page, instruction, current_url)
                    
        elif action in ["fill", "type", "input"]:
            await element.wait_for(state="visible", timeout=self.timeout_ms)
            instruction_lower = (instruction or "").lower()
            role = self._infer_payment_field_role(instruction_lower, action)
            if self._is_payment_instruction(instruction, action) and role:
                filled = await self._fill_payment_locator(element, value, role)
                if not filled:
                    raise ValueError(
                        f"Payment field fill did not stick for step: {instruction}"
                    )
            elif self._is_date_instruction(instruction, value):
                filled = await self._fill_date_picker_field(element, value, page)
                if not filled:
                    raise ValueError(
                        f"Date picker fill did not persist for step: {instruction}"
                    )
            else:
                await element.fill(value, timeout=self.timeout_ms)
                await asyncio.sleep(0.3)
                if value and not await self._verify_filled_value(element, value, role=None):
                    logger.warning(
                        "[Tier 2] Generic fill verification failed for step: %s",
                        instruction,
                    )
            
        elif action == "select":
            custom_selected = await self._try_custom_dropdown_select(
                page,
                instruction,
                value,
                xpath,
            )
            if custom_selected:
                await asyncio.sleep(0.3)
                return

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
                if not await element.is_checked():
                    raise ValueError(
                        "Checkbox is still unchecked after check() â€” "
                        "element may not be a native checkbox or the click did not register"
                    )
                
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
            # Backstop if wait somehow reached xpath path — never silent pass
            duration_ms = parse_timed_wait_ms(
                instruction,
                {"action": "wait", "value": value},
            )
            if duration_ms is None:
                raise ValueError(
                    "Timed wait requires timeout_ms or duration in instruction"
                )
            cancelled = await sleep_cancel_aware(duration_ms)
            if cancelled:
                raise InterruptedError("Timed wait cancelled by user")
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
                    f"[Tier 2] âš ï¸ Element is not a file input "
                    f"(tag={tag_name}, type={input_type}). Attempting upload anyway..."
                )
            
            # Upload file using Playwright's set_input_files method
            logger.info(f"[Tier 2] ðŸ“¤ Uploading file via XPath: {file_path}")
            await element.set_input_files(file_path, timeout=self.timeout_ms)

            # Small delay to allow file upload event handlers to complete
            await asyncio.sleep(0.5)
            logger.info(f"[Tier 2] âœ… File uploaded successfully")
        elif action == "draw_signature" or action == "sign":
            # Draw signature on canvas element
            logger.info(f"[Tier 2] ðŸ–Šï¸ Starting signature drawing process for XPath: {xpath}")
            await self._execute_draw_signature(page, xpath, value)
            logger.info(f"[Tier 2] âœ… Signature drawing completed")
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
                "[Tier 2] âš ï¸ Click target still disabled after wait (instruction=%s)",
                instruction,
            )
            instruction_lower = (instruction or "").lower()
            if "subscribe now" in instruction_lower:
                raise ValueError(
                    "Subscribe Now button is still disabled after wait â€” "
                    "prerequisite (e.g., T&C checkbox) may not have been completed"
                )
        except ValueError:
            raise
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

        if action == "click" and self._is_three_hk_promotion_card_click(
            page.url,
            instruction,
            action,
        ):
            try:
                element_text = (await locator.inner_text()) or ""
            except Exception:
                element_text = ""
            if not self._instruction_matches_three_hk_promotion_snippet(
                instruction,
                element_text,
            ):
                logger.info(
                    "[Tier 2] Cached promotion card semantic mismatch for instruction"
                )
                return False
            if self._snippet_has_contradictory_wifi_family(instruction, element_text):
                logger.info(
                    "[Tier 2] Cached promotion card contradicts requested Wi-Fi family"
                )
                return False

        if action == "click":
            if not await self._validate_click_target_for_instruction(page, locator, instruction):
                logger.info("[Tier 2] Cached click target failed anchor validation")
                return False

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
            logger.info("[Tier 2] ðŸ” Cached field semantic mismatch: expected password field")
            return False

        if expected_email and looks_like_password:
            logger.info("[Tier 2] ðŸ” Cached field semantic mismatch: expected email/non-password field")
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
        ]
        selectors.extend(self._payment_iframe_frame_selectors())
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
        """Wait once per checkout session for payment gateway fields to appear."""
        if self.payment_gateway_ready:
            return

        if await self._gw_proxy_checkout_active(page):
            logger.info("[Tier 2] Payment gateway ready (gw-proxy iframes visible)")
            self.payment_gateway_ready = True
            self.payment_gateway_url = page.url
            return

        timeout_ms = 8000 if self._is_external_payment_gateway_url(page.url) else 1500
        try:
            await page.wait_for_selector(
                self._payment_input_css_selector(),
                state="visible",
                timeout=timeout_ms,
            )
            logger.info(f"[Tier 2] âœ… Payment gateway ready (timeout={timeout_ms}ms)")
            self.payment_gateway_ready = True
            self.payment_gateway_url = page.url
            return
        except Exception:
            logger.warning("[Tier 2] âš ï¸ Payment gateway readiness not confirmed")

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
        gw_proxy_active = await self._gw_proxy_checkout_active(page)

        if self.payment_gateway_ready:
            wait_timeout = 300 if gw_proxy_active else 3000
        elif gw_proxy_active:
            wait_timeout = 1500
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

        frame_selectors = self._payment_iframe_frame_selectors()

        label_candidates = []
        if "card number" in instruction_lower or "credit card" in instruction_lower:
            label_candidates = ["Card number", "Card Number", "Card no", "Card No", "Credit Card No.", "Credit Card Number"]
        elif "cvv" in instruction_lower or "cvc" in instruction_lower or "security code" in instruction_lower:
            label_candidates = ["CVV", "CVC", "Security code", "Security Code"]
        elif "cardholder" in instruction_lower or "card holder" in instruction_lower:
            label_candidates = ["Cardholder name", "Card Holder Name", "Cardholder", "Name on card"]
        elif action in ["fill", "type", "input"] and (
            "exp. date" in instruction_lower or "exp date" in instruction_lower or "expiry" in instruction_lower or "expiration" in instruction_lower
        ):
            label_candidates = [
                "Exp. Date (MM/YY)",
                "Exp. Date (MM/YYYY)",
                "Exp. Date",
                "Expiry date",
                "Expiration date",
                "Exp date",
            ]
        elif "month" in instruction_lower:
            label_candidates = ["Expiry month", "Expiration month", "Exp month", "Month"]
        elif "year" in instruction_lower:
            label_candidates = ["Expiry year", "Expiration year", "Exp year", "Year"]

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

        async def _existing_payment_frames(selectors_to_scan):
            existing_frames = []
            for iframe_selector in selectors_to_scan:
                try:
                    iframe_locator = page.locator(iframe_selector)
                    if await iframe_locator.count() > 0:
                        existing_frames.append((iframe_selector, page.frame_locator(iframe_selector)))
                except Exception:
                    continue
            return existing_frames

        def _payment_success(execution_time_ms: float, log_message: str) -> Dict[str, Any]:
            logger.info(log_message)
            self.payment_gateway_ready = True
            self.payment_gateway_url = page.url
            return {
                "success": True,
                "tier": 2,
                "execution_time_ms": execution_time_ms,
                "extraction_time_ms": 0,
                "cache_hit": False,
                "xpath": None,
                "error": None,
            }

        try:
            if gw_proxy_active:
                gw_proxy_result = await self._try_gw_proxy_payment_field(
                    page=page,
                    action=action,
                    instruction_lower=instruction_lower,
                    value=value,
                    start_time=start_time,
                    wait_timeout=wait_timeout,
                )
                if gw_proxy_result:
                    return gw_proxy_result
            else:
                if input_selectors:
                    for selector in input_selectors:
                        locator = page.locator(selector).first
                        try:
                            await _try_fill(locator)
                            execution_time_ms = (time.time() - start_time) * 1000
                            return _payment_success(
                                execution_time_ms,
                                f"[Tier 2] Payment input filled using selector: {selector}",
                            )
                        except Exception:
                            continue

                if select_selectors:
                    for selector in select_selectors:
                        locator = page.locator(selector).first
                        try:
                            await _try_select(locator)
                            execution_time_ms = (time.time() - start_time) * 1000
                            return _payment_success(
                                execution_time_ms,
                                f"[Tier 2] Payment select set using selector: {selector}",
                            )
                        except Exception:
                            continue

                for label in label_candidates:
                    try:
                        locator = page.get_by_label(label, exact=False)
                        await _try_label(locator)
                        execution_time_ms = (time.time() - start_time) * 1000
                        return _payment_success(
                            execution_time_ms,
                            f"[Tier 2] Payment field set using label: {label}",
                        )
                    except Exception:
                        continue

                if self._is_cross_origin_payment_host(page.url):
                    gw_proxy_result = await self._try_gw_proxy_payment_field(
                        page=page,
                        action=action,
                        instruction_lower=instruction_lower,
                        value=value,
                        start_time=start_time,
                        wait_timeout=wait_timeout,
                    )
                    if gw_proxy_result:
                        return gw_proxy_result

            role = self._infer_payment_field_role(instruction_lower, action)
            if gw_proxy_active and role:
                iframe_scan_selectors = self._GW_PROXY_IFRAME_SELECTORS.get(role, [])
            else:
                iframe_scan_selectors = frame_selectors

            existing_frames = await _existing_payment_frames(iframe_scan_selectors)

            for iframe_selector, frame_locator in existing_frames:
                if input_selectors:
                    for selector in input_selectors:
                        locator = frame_locator.locator(selector).first
                        try:
                            await _try_fill(locator)
                            execution_time_ms = (time.time() - start_time) * 1000
                            logger.info(f"[Tier 2] âœ… Payment input filled in iframe: {iframe_selector} -> {selector}")
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
                            logger.info(f"[Tier 2] âœ… Payment select set in iframe: {iframe_selector} -> {selector}")
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

            for iframe_selector, frame_locator in existing_frames:
                for label in label_candidates:
                    try:
                        locator = frame_locator.get_by_label(label, exact=False)
                        await _try_label(locator)
                        execution_time_ms = (time.time() - start_time) * 1000
                        logger.info(f"[Tier 2] âœ… Payment field set in iframe using label: {label}")
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
        Draw a signature on a canvas element using the shared signature_pad helper.

        Prefer pointer/mouse/touch events; ink verification is required before success.
        """
        logger.info(f"[Tier 2] ✍️ Drawing signature via shared helper (xpath={xpath})")
        result = await sign_canvas(page, xpath=xpath, instruction=signature_text)
        if not result.success or not result.ink_verified:
            raise ValueError(
                result.error
                or "Signature pad appears empty after stroke (ink verification failed)"
            )
        logger.info("[Tier 2] ✅ Signature drawn and ink verified via shared helper")



    # ------------------------------------------------------------------
    # Sprint 10.17: AI Screenshot Verification
    # ------------------------------------------------------------------

    async def _execute_verify_screenshot(
        self,
        page: Page,
        step: Dict[str, Any],
        start_time: float,
    ) -> Dict[str, Any]:
        """Handle a verify_screenshot step using vision AI.

        Calls ScreenshotVerificationService.  When VisionNotSupportedError is
        raised (provider is cerebras / local_vllm) the exception is propagated
        so ThreeTierExecutionService can escalate to Tier 3.
        """
        import json as _json

        instruction = step.get("instruction", "")
        expected_items = step.get("expected_items") or []
        screenshot_region = step.get("screenshot_region", "viewport")
        provider = self.user_ai_config.get("execution_provider") or self.user_ai_config.get("provider", "openrouter")
        model = self.user_ai_config.get("execution_model") or self.user_ai_config.get("model")

        logger.info(
            "[Tier 2] 📸 verify_screenshot — provider=%s model=%s instruction=%s",
            provider,
            model,
            instruction,
        )

        # VisionNotSupportedError is intentionally NOT caught here.
        # ThreeTierExecutionService catches it and escalates to Tier 3.
        svc = ScreenshotVerificationService()
        verdict = await svc.verify(
            page=page,
            instruction=instruction,
            expected_items=expected_items,
            screenshot_region=screenshot_region,
            provider=provider,
            model=model,
        )

        execution_time_ms = (time.time() - start_time) * 1000
        passed = verdict.get("verdict", "FAIL").upper() == "PASS"
        verdict_json = _json.dumps(verdict)

        if passed:
            logger.info("[Tier 2] ✅ verify_screenshot PASS in %.0fms", execution_time_ms)
        else:
            logger.warning("[Tier 2] ❌ verify_screenshot FAIL: %s", verdict.get("reason"))

        return {
            "success": passed,
            "tier": 2,
            "execution_time_ms": execution_time_ms,
            "extraction_time_ms": 0,
            "playwright_time_ms": 0,
            "cache_hit": False,
            "xpath": None,
            "error": None if passed else verdict.get("reason"),
            "error_type": None if passed else "verification_failed",
            "ai_verification_result": verdict_json,
        }
