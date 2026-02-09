"""
XPath Extractor Service using Stagehand observe()
Extracts XPath selectors for Tier 2 (Hybrid Mode)
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page
from stagehand import Stagehand
import logging

logger = logging.getLogger(__name__)


class XPathExtractor:
    """
    Extracts XPath selectors using Stagehand observe() method.
    
    This is used by Tier 2 to get precise XPath selectors which can then
    be executed quickly with Playwright without repeated LLM calls.
    """
    
    def __init__(self, stagehand: Optional[Stagehand] = None):
        """
        Initialize XPath extractor.
        
        Args:
            stagehand: Optional Stagehand instance (will create if not provided)
        """
        self.stagehand = stagehand
        self._owned_stagehand = stagehand is None
    
    async def initialize(self, user_config: Optional[Dict[str, Any]] = None, cdp_endpoint: Optional[str] = None):
        """
        Initialize Stagehand if not already provided.
        
        Args:
            user_config: Optional user configuration for Stagehand
            cdp_endpoint: Optional CDP endpoint URL to connect to existing browser context
        """
        if not self.stagehand:
            # Import here to avoid circular dependencies
            from app.services.stagehand_service import StagehandExecutionService
            
            if cdp_endpoint:
                # Connect to existing browser via CDP
                logger.info(f"[XPath Extractor] Connecting to existing browser via CDP: {cdp_endpoint}")
                service = StagehandExecutionService(headless=False)
                await service.initialize_with_cdp(cdp_endpoint=cdp_endpoint, user_config=user_config)
            else:
                # Create new browser instance (legacy behavior)
                logger.info("[XPath Extractor] Creating new browser instance")
                service = StagehandExecutionService(headless=True)
                await service.initialize(user_config=user_config)
            
            self.stagehand = service.stagehand
    
    async def extract_xpath(
        self,
        instruction: str,
        page_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract XPath selector for an element using Stagehand observe().
        
        Args:
            instruction: Natural language instruction to find the element
            page_url: Optional URL for context (used for caching)
            
        Returns:
            Dictionary with xpath, extraction_time_ms, element_text, page_title
        """
        if not self.stagehand:
            raise RuntimeError("XPathExtractor not initialized. Call initialize() first.")
        
        start_time = time.time()
        
        try:
            logger.info(f"[XPath Extractor] Extracting XPath for: {instruction}")
            
            # Use Stagehand page.observe() to get element info
            result = await self.stagehand.page.observe(instruction)
            
            if not result or (isinstance(result, list) and len(result) == 0):
                raise ValueError(f"observe() returned no results for: {instruction}")
            
            # observe() returns a list of ObserveResult objects, take first one
            if isinstance(result, list):
                result = result[0]
            
            xpath = result.get('selector') if isinstance(result, dict) else getattr(result, 'selector', None)
            
            if not xpath:
                raise ValueError(f"observe() returned no selector for: {instruction}")
            
            # Strip xpath= prefix if present (observe() returns "xpath=/html/...")
            # We need just "/html/..." because Playwright adds "xpath=" later
            if xpath.startswith('xpath='):
                xpath = xpath[6:]  # Remove "xpath=" prefix
            
            # Get additional info if available
            element_text = getattr(result, 'text', None)
            element_html = getattr(result, 'html', None)
            
            # Get page info if available
            page_title = None
            page_url_from_stagehand = None
            
            if self.stagehand.page:
                try:
                    page_title = await self.stagehand.page.title()
                    page_url_from_stagehand = self.stagehand.page.url
                except:
                    pass
            
            extraction_time_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"[XPath Extractor] ✅ Extracted XPath in {extraction_time_ms:.2f}ms: {xpath}"
            )
            
            return {
                "xpath": xpath,
                "selector_type": "xpath",
                "extraction_time_ms": extraction_time_ms,
                "element_text": element_text,
                "element_html": element_html,
                "page_title": page_title,
                "page_url": page_url_from_stagehand or page_url,
                "success": True
            }
            
        except Exception as e:
            extraction_time_ms = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            logger.error(f"[XPath Extractor] ❌ Failed to extract XPath: {error_msg}")
            
            return {
                "xpath": None,
                "extraction_time_ms": extraction_time_ms,
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }
    
    async def extract_xpath_with_page(
        self,
        page: Page,
        instruction: str
    ) -> Dict[str, Any]:
        """
        Extract XPath selector using an existing Playwright Page.
        
        This method creates a temporary Stagehand instance with the provided page.
        
        Args:
            page: Playwright Page object
            instruction: Natural language instruction to find the element
            
        Returns:
            Dictionary with xpath, extraction_time_ms, element_text, page_title
        """
        start_time = time.time()
        
        try:
            # Get page info
            page_url = page.url
            page_title = await page.title()
            
            logger.info(f"[XPath Extractor] Extracting XPath on {page_url} for: {instruction}")
            
            # Use observe with the page context
            # Note: This requires Stagehand to be initialized with a page
            if not self.stagehand:
                await self.initialize()
            
            # Navigate Stagehand to same URL if needed
            if self.stagehand.page and self.stagehand.page.url != page_url:
                await self.stagehand.page.goto(page_url)
            
            result = await self.stagehand.page.observe(instruction)
            
            if not result or (isinstance(result, list) and len(result) == 0):
                raise ValueError(f"observe() returned no results for: {instruction}")
            
            # observe() returns a list of ObserveResult objects, take first one
            if isinstance(result, list):
                result = result[0]
            
            xpath = result.get('selector') if isinstance(result, dict) else getattr(result, 'selector', None)
            element_text = result.get('description') if isinstance(result, dict) else getattr(result, 'description', None)
            element_html = None  # observe() doesn't return HTML
            
            if not xpath:
                raise ValueError(f"observe() returned no selector for: {instruction}")
            
            # Strip xpath= prefix if present (observe() returns "xpath=/html/...")
            # We need just "/html/..." because Playwright adds "xpath=" later
            if xpath.startswith('xpath='):
                xpath = xpath[6:]  # Remove "xpath=" prefix
            
            extraction_time_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"[XPath Extractor] ✅ Extracted XPath in {extraction_time_ms:.2f}ms: {xpath}"
            )
            
            return {
                "xpath": xpath,
                "selector_type": "xpath",
                "extraction_time_ms": extraction_time_ms,
                "element_text": element_text,
                "element_html": element_html,
                "page_title": page_title,
                "page_url": page_url,
                "success": True
            }
            
        except Exception as e:
            extraction_time_ms = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            logger.error(f"[XPath Extractor] ❌ Failed to extract XPath: {error_msg}")
            
            return {
                "xpath": None,
                "extraction_time_ms": extraction_time_ms,
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__
            }
    
    async def cleanup(self):
        """Clean up resources if we created our own Stagehand instance"""
        if self._owned_stagehand and self.stagehand:
            try:
                await self.stagehand.close()
            except Exception as e:
                logger.warning(f"[XPath Extractor] Error during cleanup: {e}")
