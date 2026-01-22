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
            element_text = await element.text_content() or ""
            element_text_lower = element_text.lower()
            is_navigation_button = any(
                keyword in element_text_lower 
                for keyword in ["next", "continue", "submit", "proceed", "upload", "confirm"]
            )
            
            # Perform the click action
            await element.click(timeout=self.timeout_ms)
            
            # Wait for any post-click navigation/state changes
            if is_navigation_button:
                logger.info(f"[Tier 2] 🔄 Navigation button detected: '{element_text}' - using extended wait")
            
            try:
                # For navigation buttons, use longer timeout
                wait_timeout = self.timeout_ms if is_navigation_button else 10000
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
                        ".overlay"
                    ]
                    
                    for selector in loading_selectors:
                        try:
                            loading_element = page.locator(selector).first
                            # If loading element exists and is visible, wait for it to be hidden
                            if await loading_element.count() > 0:
                                logger.info(f"[Tier 2] ⏳ Detected loading indicator: {selector}")
                                await loading_element.wait_for(state="hidden", timeout=10000)
                                logger.info(f"[Tier 2] ✅ Loading indicator disappeared")
                                break
                        except Exception:
                            # This selector doesn't match any element, try next
                            continue
                except Exception as e:
                    logger.debug(f"[Tier 2] No loading indicators found or error checking: {str(e)}")
                
                # Additional fixed delay to ensure content is fully rendered
                await asyncio.sleep(2.0)
                logger.debug(f"[Tier 2] ⏱️ Additional 2.0s wait after navigation button")
                    
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
        else:
            raise ValueError(f"Unsupported action type: {action}")
