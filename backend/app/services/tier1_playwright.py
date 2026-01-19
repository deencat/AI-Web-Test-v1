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
            elif action == "fill" or action == "type":
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
        """Click element"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.click(timeout=self.timeout_ms)
    
    async def _execute_fill(self, page: Page, selector: str, value: str):
        """Fill input element"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.fill(value, timeout=self.timeout_ms)
    
    async def _execute_select(self, page: Page, selector: str, value: str):
        """Select dropdown option"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.select_option(value, timeout=self.timeout_ms)
    
    async def _execute_check(self, page: Page, selector: str):
        """Check checkbox"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        if not await element.is_checked():
            await element.check(timeout=self.timeout_ms)
    
    async def _execute_uncheck(self, page: Page, selector: str):
        """Uncheck checkbox"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        if await element.is_checked():
            await element.uncheck(timeout=self.timeout_ms)
    
    async def _execute_hover(self, page: Page, selector: str):
        """Hover over element"""
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=self.timeout_ms)
        await element.hover(timeout=self.timeout_ms)
    
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
