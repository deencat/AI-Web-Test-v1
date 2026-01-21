"""
Tier 2: Hybrid Mode Execution
Stagehand observe() + Playwright execution for self-healing tests
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
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
            action = step.get("action", "").lower()
            instruction = step.get("instruction", "")
            value = step.get("value", "")
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
            
            # Step 1: Try to get XPath from cache
            cached_xpath = self.cache_service.get_cached_xpath(page_url, instruction)
            
            if cached_xpath:
                xpath = cached_xpath["xpath"]
                cache_hit = True
                logger.info(f"[Tier 2] 🎯 Cache hit! Using cached XPath: {xpath}")
            else:
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
            # Perform the click action
            await element.click(timeout=self.timeout_ms)
            
            # Wait for any post-click navigation/state changes
            try:
                # Wait for network to be idle after click (handles AJAX, SPA updates)
                await page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
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
                    
        elif action in ["fill", "type"]:
            await element.fill(value, timeout=self.timeout_ms)
            # Small delay to allow any input event handlers to complete
            await asyncio.sleep(0.3)
            
        elif action == "select":
            await element.select_option(value, timeout=self.timeout_ms)
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
        else:
            raise ValueError(f"Unsupported action type: {action}")
