"""
Tier 1: Playwright Direct Execution
Fast, direct Playwright execution with zero LLM costs
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
import logging

logger = logging.getLogger(__name__)


class Tier1PlaywrightExecutor:
    """
    Tier 1: Direct Playwright execution using pre-defined selectors.
    
    This is the fastest and cheapest execution method with zero LLM costs.
    Expected success rate: 85-90%
    """
    
    def __init__(self, timeout_ms: int = 30000):
        """
        Initialize Tier 1 executor.
        
        Args:
            timeout_ms: Timeout in milliseconds for each action (default 30 seconds)
        """
        self.timeout_ms = timeout_ms
    
    async def execute_step(
        self,
        page: Page,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single test step using direct Playwright actions.
        
        Args:
            page: Playwright Page object
            step: Step dictionary containing action, selector, value, etc.
            
        Returns:
            Result dictionary with success status, timing, and error info
        """
        start_time = time.time()
        
        try:
            action = step.get("action", "").lower()
            selector = step.get("selector")
            value = step.get("value", "")
            instruction = step.get("instruction", "")
            
            logger.info(f"[Tier 1] Executing step: {action} - {instruction}")
            
            # Execute action based on type
            if action == "navigate":
                url = value or selector or instruction
                await self._execute_navigate(page, url)
            elif action == "click":
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_click(page, selector)
            elif action in ["fill", "type", "input"]:
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_fill(page, selector, value)
            elif action == "select":
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_select(page, selector, value)
            elif action == "check":
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_check(page, selector)
            elif action == "uncheck":
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_uncheck(page, selector)
            elif action == "hover":
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_hover(page, selector)
            elif action == "assert" or action == "verify":
                if not selector:
                    raise ValueError(f"No selector provided for step: {instruction}")
                await self._execute_assert(page, selector, value)
            elif action == "wait":
                await self._execute_wait(page, selector or value or "1000")
            elif action == "upload_file":
                file_path = step.get("file_path")
                if not file_path:
                    raise ValueError(f"No file_path provided for upload_file action: {instruction}")
                if not selector:
                    raise ValueError(f"No selector provided for upload_file action: {instruction}")
                await self._execute_upload_file(page, selector, file_path)
            else:
                raise ValueError(f"Unsupported action type: {action}")
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[Tier 1] ✅ Step succeeded in {execution_time_ms:.2f}ms")
            
            return {
                "success": True,
                "tier": 1,
                "execution_time_ms": execution_time_ms,
                "error": None
            }
            
        except PlaywrightTimeout as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {self.timeout_ms}ms: {str(e)}"
            logger.warning(f"[Tier 1] ⏰ Timeout: {error_msg}")
            
            return {
                "success": False,
                "tier": 1,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
                "error_type": "timeout"
            }
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.warning(f"[Tier 1] ❌ Failed: {error_msg}")
            
            return {
                "success": False,
                "tier": 1,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
                "error_type": type(e).__name__
            }
    
    async def _execute_navigate(self, page: Page, url: str):
        """Navigate to URL"""
        await page.goto(url, timeout=self.timeout_ms, wait_until="networkidle")
    
    async def _execute_click(self, page: Page, selector: str):
        """Click element and wait for page state to stabilize"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        
        # Check for navigation buttons that might trigger page changes
        element_text = await element.text_content() or ""
        element_text_lower = element_text.lower()
        is_navigation_button = any(
            keyword in element_text_lower 
            for keyword in ["next", "continue", "submit", "proceed", "upload", "confirm"]
        )
        
        await element.click(timeout=self.timeout_ms)
        
        # Wait for any post-click navigation/state changes
        if is_navigation_button:
            logger.info(f"[Tier 1] 🔄 Navigation button detected: '{element_text}' - using extended wait")
        
        try:
            # For navigation buttons, use longer timeout
            wait_timeout = self.timeout_ms if is_navigation_button else 10000
            await page.wait_for_load_state("networkidle", timeout=wait_timeout)
            logger.debug(f"[Tier 1] ✅ Page state stabilized after click")
        except PlaywrightTimeout:
            # If network doesn't idle, wait for DOM ready
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
                logger.debug(f"[Tier 1] ⚠️ DOM loaded after click (network still active)")
            except PlaywrightTimeout:
                # Last resort: small fixed delay
                await asyncio.sleep(1)
                logger.warning(f"[Tier 1] ⚠️ Using fixed delay after click")
        
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
                            logger.info(f"[Tier 1] ⏳ Detected loading indicator: {selector}")
                            await loading_element.wait_for(state="hidden", timeout=10000)
                            logger.info(f"[Tier 1] ✅ Loading indicator disappeared")
                            break
                    except Exception:
                        # This selector doesn't match any element, try next
                        continue
            except Exception as e:
                logger.debug(f"[Tier 1] No loading indicators found or error checking: {str(e)}")
            
            # Additional fixed delay to ensure content is fully rendered
            await asyncio.sleep(2.0)
            logger.debug(f"[Tier 1] ⏱️ Additional 2.0s wait after navigation button")
    
    async def _execute_fill(self, page: Page, selector: str, value: str):
        """Fill input element"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.fill(value, timeout=self.timeout_ms)
        # Small delay to allow input event handlers to complete
        await asyncio.sleep(0.3)
    
    async def _execute_select(self, page: Page, selector: str, value: str):
        """Select dropdown option"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.select_option(value, timeout=self.timeout_ms)
        # Wait for onChange handlers
        await asyncio.sleep(0.3)
    
    async def _execute_check(self, page: Page, selector: str):
        """Check checkbox"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        if not await element.is_checked():
            await element.check(timeout=self.timeout_ms)
            await asyncio.sleep(0.3)
    
    async def _execute_uncheck(self, page: Page, selector: str):
        """Uncheck checkbox"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        if await element.is_checked():
            await element.uncheck(timeout=self.timeout_ms)
            await asyncio.sleep(0.3)
    
    async def _execute_hover(self, page: Page, selector: str):
        """Hover over element"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.hover(timeout=self.timeout_ms)
        await asyncio.sleep(0.2)
    
    async def _execute_assert(self, page: Page, selector: str, expected_value: str):
        """Assert element contains expected value"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        
        # Get text content
        actual_value = await element.text_content()
        
        # Check if expected value is in actual value
        if expected_value not in (actual_value or ""):
            raise AssertionError(
                f"Expected '{expected_value}' in element text, got '{actual_value}'"
            )
    
    async def _execute_wait(self, page: Page, selector_or_time: str):
        """Wait for element or time"""
        try:
            # Try to parse as number (milliseconds)
            wait_ms = int(selector_or_time)
            await asyncio.sleep(wait_ms / 1000)
        except ValueError:
            # Treat as selector
            element = page.locator(selector_or_time).first
            await element.wait_for(state="visible", timeout=self.timeout_ms)
    
    async def _execute_upload_file(self, page: Page, selector: str, file_path: str):
        """
        Upload file to file input element.
        
        Args:
            page: Playwright Page object
            selector: Selector for file input element (e.g., 'input[type="file"]')
            file_path: Absolute path to file to upload
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If element is not a file input
        """
        import os
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Locate file input element
        element = page.locator(selector).first
        await element.wait_for(state="attached", timeout=self.timeout_ms)
        
        # Verify it's a file input
        tag_name = await element.evaluate("el => el.tagName")
        input_type = await element.evaluate("el => el.type")
        
        if tag_name.lower() != "input" or input_type.lower() != "file":
            logger.warning(
                f"[Tier 1] ⚠️ Element {selector} is not a file input "
                f"(tag={tag_name}, type={input_type}). Attempting upload anyway..."
            )
        
        # Upload file using Playwright's set_input_files method
        logger.info(f"[Tier 1] 📤 Uploading file: {file_path}")
        await element.set_input_files(file_path, timeout=self.timeout_ms)
        
        # Small delay to allow file upload event handlers to complete
        await asyncio.sleep(0.5)
        logger.info(f"[Tier 1] ✅ File uploaded successfully")
