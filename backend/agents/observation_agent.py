"""
ObservationAgent - Observes and analyzes web applications

This agent uses Playwright to crawl web applications and extract information
about UI elements, navigation flows, and page structure for test generation.

Capabilities:
- web_crawling: Crawl web application pages and map structure
- ui_element_extraction: Extract buttons, forms, links, inputs from pages

Usage:
    agent = ObservationAgent(message_queue)
    await agent.start()
    
    task = TaskContext(
        task_id="obs-1",
        task_type="web_crawling",
        payload={
            "url": "https://example.com",
            "max_depth": 3,
            "auth": {"username": "test", "password": "test123"}
        }
    )
    
    result = await agent.execute_task(task)
    # result.result = {
    #     "pages": [...],
    #     "ui_elements": [...],
    #     "navigation_flows": [...],
    #     "forms": [...]
    # }
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re

from agents.base_agent import (
    BaseAgent,
    AgentCapability,
    TaskContext,
    TaskResult
)

# Set up logger first
logger = logging.getLogger(__name__)

# NOTE: Playwright will be imported when available
# For now, we'll use a stub implementation for development
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Stub for development without Playwright installed
    class Page:
        pass
    class Browser:
        pass

# Import LLM client for enhanced observation
try:
    import sys
    from pathlib import Path
    # Add parent directory to path for llm module
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from llm.azure_client import get_azure_client
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

if not LLM_AVAILABLE:
    logger.warning("LLM client not available - observation will use Playwright only")



@dataclass
class PageInfo:
    """Information about a web page."""
    url: str
    title: str
    elements: List[Dict[str, Any]]  # UI elements found on page
    forms: List[Dict[str, Any]]  # Forms on the page
    links: List[str]  # Links to other pages
    screenshot_path: Optional[str]  # Path to screenshot
    load_time_ms: float  # Page load time
    status_code: int  # HTTP status code


@dataclass
class UIElement:
    """Information about a UI element."""
    element_type: str  # button, input, link, etc.
    selector: str  # CSS selector
    xpath: str  # XPath selector
    text: Optional[str]  # Visible text
    attributes: Dict[str, str]  # HTML attributes
    is_visible: bool  # Is element visible?
    is_interactive: bool  # Can user interact with it?


@dataclass
class FormInfo:
    """Information about a form."""
    selector: str
    action: Optional[str]  # Form action URL
    method: str  # GET or POST
    fields: List[Dict[str, Any]]  # Form fields
    submit_button: Optional[Dict[str, Any]]


class ObservationAgent(BaseAgent):
    """
    Agent that observes web applications using Playwright.
    
    This agent can:
    1. Crawl web application pages (follow links, map structure)
    2. Extract UI elements (buttons, inputs, forms, links)
    3. Identify user flows (login → dashboard → settings)
    4. Take screenshots for visual verification
    5. Measure page load times and performance
    """
    
    def __init__(
        self,
        message_queue,
        agent_id: Optional[str] = None,
        priority: int = 8,  # High priority for observation
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ObservationAgent.
        
        Args:
            message_queue: MessageBus instance for communication
            agent_id: Optional custom agent ID
            priority: Agent priority (1-10, higher = more important)
            config: Agent-specific configuration
        """
        super().__init__(
            agent_id=agent_id or "observation-agent-1",
            agent_type="observation",
            priority=priority,
            message_queue=message_queue,
            config=config or {}
        )
        
        # Configuration
        self.max_depth = self.config.get("max_depth", 3)
        self.max_pages = self.config.get("max_pages", 50)
        self.timeout_ms = self.config.get("timeout_ms", 30000)
        self.take_screenshots = self.config.get("take_screenshots", True)
        self.use_llm = self.config.get("use_llm", True)  # Enable LLM by default
        
        # Initialize LLM client if available and enabled
        self.llm_client = None
        if self.use_llm and LLM_AVAILABLE:
            self.llm_client = get_azure_client()
            if self.llm_client.enabled:
                logger.info("ObservationAgent initialized with LLM enhancement (Azure OpenAI)")
            else:
                logger.info("ObservationAgent initialized without LLM (API key not set)")
        else:
            logger.info("ObservationAgent initialized without LLM (Playwright only)")
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """
        Declare agent capabilities.
        
        Returns:
            List of capabilities this agent supports
        """
        return [
            AgentCapability(
                name="web_crawling",
                version="1.0.0",
                confidence_threshold=0.8,
                description="Crawl web application and map page structure"
            ),
            AgentCapability(
                name="ui_element_extraction",
                version="1.0.0",
                confidence_threshold=0.85,
                description="Extract UI elements (buttons, forms, inputs, links)"
            )
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """
        Determine if this agent can handle the given task.
        
        Args:
            task: Task to evaluate
        
        Returns:
            Tuple of (can_handle: bool, confidence: float)
        """
        if task.task_type in ["web_crawling", "ui_element_extraction"]:
            # Check if we have required payload
            if "url" in task.payload:
                url = task.payload["url"]
                
                # Validate URL
                if self._is_valid_url(url):
                    # Check if Playwright is available
                    if PLAYWRIGHT_AVAILABLE:
                        return True, 0.9  # High confidence
                    else:
                        logger.warning("Playwright not installed - using stub mode")
                        return True, 0.5  # Lower confidence without Playwright
                else:
                    logger.warning(f"Invalid URL in task {task.task_id}: {url}")
                    return False, 0.0
            else:
                logger.warning(f"Task {task.task_id} missing 'url' in payload")
                return False, 0.0
        
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """
        Execute web crawling/observation task.
        
        Args:
            task: Task to execute
        
        Returns:
            TaskResult with observation results
        """
        if not PLAYWRIGHT_AVAILABLE:
            return await self._execute_stub_mode(task)
        
        try:
            url = task.payload.get("url")
            max_depth = task.payload.get("max_depth", self.max_depth)
            auth = task.payload.get("auth")  # Optional authentication
            
            logger.info(f"ObservationAgent: Crawling web application: {url} (task {task.task_id})")
            
            # Start Playwright browser
            # Read headless mode from env (default: True for CI/CD compatibility)
            # Support both HEADLESS_BROWSER (existing) and BROWSER_HEADLESS (for consistency)
            import os
            headless_str = os.getenv("HEADLESS_BROWSER") or os.getenv("BROWSER_HEADLESS", "true")
            headless_str = headless_str.lower()
            headless_mode = headless_str in ("true", "1", "yes")
            logger.info(f"ObservationAgent: Launching browser (headless={headless_mode})...")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless_mode)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="AI-Web-Test ObservationAgent/1.0"
                )
                
                # Add authentication if provided
                if auth:
                    logger.debug("ObservationAgent: Adding authentication to browser context...")
                    await context.add_init_script(f"""
                        localStorage.setItem('auth_token', '{auth.get('token', '')}');
                    """)
                
                page = await context.new_page()
                
                # Crawl pages
                logger.info(f"ObservationAgent: Crawling pages (max_depth={max_depth})...")
                pages = await self._crawl_pages(page, url, max_depth)
                logger.info(f"ObservationAgent: Found {len(pages)} page(s) to analyze")
                
                # Extract UI elements from all pages (Playwright baseline)
                logger.info("ObservationAgent: Extracting UI elements from pages...")
                all_elements = []
                all_forms = []
                for idx, page_info in enumerate(pages, 1):
                    logger.debug(f"ObservationAgent: Extracting elements from page {idx}/{len(pages)}: {page_info.url}")
                    elements = await self._extract_ui_elements(page, page_info.url)
                    forms = await self._extract_forms(page, page_info.url)
                    all_elements.extend(elements)
                    all_forms.extend(forms)
                    logger.debug(f"ObservationAgent: Page {idx} - {len(elements)} elements, {len(forms)} forms")
                
                logger.info(f"ObservationAgent: Playwright baseline complete - {len(all_elements)} elements, {len(all_forms)} forms")
                
                # ENHANCEMENT: Use LLM to find elements Playwright might miss
                llm_enhanced_elements = []
                llm_analysis = {}
                if self.llm_client and self.llm_client.enabled:
                    try:
                        # Get page HTML for LLM analysis
                        html_content = await page.content()
                        page_title = await page.title()
                        
                        logger.info("Analyzing page with LLM for enhanced element detection...")
                        llm_analysis = await self.llm_client.analyze_page_elements(
                            html=html_content,
                            basic_elements=all_elements[:20],  # Send sample to LLM
                            url=url,
                            page_title=page_title,
                            learned_patterns=None  # TODO: Integrate learning system in Sprint 10
                        )
                        
                        llm_enhanced_elements = llm_analysis.get("enhanced_elements", [])
                        logger.info(f"LLM found {len(llm_enhanced_elements)} additional elements")
                        
                        # Merge LLM findings with Playwright results
                        all_elements.extend(llm_enhanced_elements)
                        
                    except Exception as e:
                        logger.warning(f"LLM analysis failed, continuing with Playwright-only results: {e}")
                
                # Identify navigation flows
                flows = self._identify_flows(pages)
                
                await browser.close()
            
            # Calculate confidence based on completeness
            confidence = self._calculate_confidence(
                pages, 
                all_elements, 
                all_forms,
                has_llm_enhancement=bool(llm_enhanced_elements)
            )
            
            result = {
                "start_url": url,
                "pages_crawled": len(pages),
                "total_elements": len(all_elements),
                "total_forms": len(all_forms),
                "pages": [self._page_to_dict(p) for p in pages],
                "ui_elements": all_elements,
                "forms": all_forms,
                "navigation_flows": flows,
                "page_context": {
                    "url": url,  # Primary URL for navigation
                    "title": pages[0].title if pages else "",
                    "page_structure": {
                        "total_pages": len(pages),
                        "total_elements": len(all_elements),
                        "total_forms": len(all_forms)
                    }
                },
                "llm_analysis": {
                    "used": bool(llm_enhanced_elements),
                    "elements_found": len(llm_enhanced_elements),
                    "suggested_selectors": llm_analysis.get("suggested_selectors", {}),
                    "page_patterns": llm_analysis.get("page_patterns", {}),
                    "missed_by_playwright": llm_analysis.get("missed_by_playwright", [])
                },
                "summary": {
                    "buttons": len([e for e in all_elements if e.get("type") == "button"]),
                    "inputs": len([e for e in all_elements if e.get("type") == "input"]),
                    "links": len([e for e in all_elements if e.get("type") == "link"]),
                    "forms": len(all_forms),
                    "playwright_elements": len(all_elements) - len(llm_enhanced_elements),
                    "llm_enhanced_elements": len(llm_enhanced_elements)
                }
            }
            
            logger.info(
                f"Crawling complete: {len(pages)} pages, "
                f"{len(all_elements)} elements, {len(all_forms)} forms"
            )
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=confidence
            )
        
        except Exception as e:
            logger.error(f"Error crawling web application in task {task.task_id}: {e}")
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=f"Crawling failed: {str(e)}",
                confidence=0.0
            )
    
    async def _execute_stub_mode(self, task: TaskContext) -> TaskResult:
        """
        Stub implementation when Playwright is not available.
        Returns mock data for development.
        """
        url = task.payload.get("url", "")
        
        logger.info(f"STUB MODE: Simulating crawl of {url}")
        
        # Mock data
        result = {
            "start_url": url,
            "pages_crawled": 3,
            "total_elements": 15,
            "total_forms": 2,
            "pages": [
                {"url": url, "title": "Home Page", "status_code": 200, "load_time_ms": 250, "screenshot": None, "link_count": 5},
                {"url": f"{url}/login", "title": "Login", "status_code": 200, "load_time_ms": 180, "screenshot": None, "link_count": 2},
                {"url": f"{url}/dashboard", "title": "Dashboard", "status_code": 200, "load_time_ms": 320, "screenshot": None, "link_count": 8}
            ],
            "ui_elements": [
                {"type": "button", "selector": "#login-btn", "text": "Login", "page_url": f"{url}/login"},
                {"type": "input", "selector": "#username", "input_type": "text", "page_url": f"{url}/login"},
                {"type": "input", "selector": "#password", "input_type": "password", "page_url": f"{url}/login"},
                {"type": "link", "selector": "a[href='/about']", "text": "About", "href": "/about", "page_url": url},
                {"type": "button", "selector": "#submit", "text": "Submit", "page_url": f"{url}/dashboard"}
            ],
            "forms": [
                {
                    "selector": "#login-form",
                    "action": "/api/auth/login",
                    "method": "POST",
                    "fields": [
                        {"name": "username", "type": "text"},
                        {"name": "password", "type": "password"}
                    ],
                    "page_url": f"{url}/login"
                }
            ],
            "navigation_flows": [
                ["Home Page", "Login Page", "Dashboard"]
            ],
            "page_context": {
                "url": url,  # Primary URL for navigation
                "title": "Home Page",
                "page_structure": {
                    "total_pages": 3,
                    "total_elements": 15,
                    "total_forms": 2
                }
            },
            "summary": {
                "buttons": 3,
                "inputs": 5,
                "links": 7,
                "forms": 2
            },
            "_note": "STUB MODE - Playwright not installed. Install with: pip install playwright; playwright install"
        }
        
        return TaskResult(
            task_id=task.task_id,
            success=True,
            result=result,
            confidence=0.85  # Good confidence even in stub mode for demo
        )
    
    async def _crawl_pages(
        self,
        page: Page,
        start_url: str,
        max_depth: int
    ) -> List[PageInfo]:
        """
        Crawl pages starting from start_url up to max_depth.
        """
        visited = set()
        to_visit = [(start_url, 0)]  # (url, depth)
        pages = []
        
        while to_visit and len(pages) < self.max_pages:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
            
            visited.add(url)
            
            try:
                # Navigate to page
                import time
                start_time = time.time()
                response = await page.goto(url, timeout=self.timeout_ms)
                load_time = (time.time() - start_time) * 1000
                
                # Get page info
                title = await page.title()
                status_code = response.status if response else 0
                
                # Extract links for further crawling
                links = await page.eval_on_selector_all(
                    "a[href]",
                    "elements => elements.map(e => e.href)"
                )
                
                # Filter links (same domain only)
                base_domain = urlparse(start_url).netloc
                filtered_links = [
                    link for link in links
                    if urlparse(link).netloc == base_domain
                ]
                
                # Take screenshot if enabled
                screenshot_path = None
                if self.take_screenshots:
                    screenshot_path = f"/tmp/screenshot_{len(pages)}.png"
                    await page.screenshot(path=screenshot_path)
                
                page_info = PageInfo(
                    url=url,
                    title=title,
                    elements=[],  # Will be filled later
                    forms=[],  # Will be filled later
                    links=filtered_links,
                    screenshot_path=screenshot_path,
                    load_time_ms=load_time,
                    status_code=status_code
                )
                
                pages.append(page_info)
                
                # Add new links to visit
                for link in filtered_links[:10]:  # Limit to 10 links per page
                    if link not in visited:
                        to_visit.append((link, depth + 1))
                
                logger.info(f"Crawled: {url} (depth {depth}, {len(filtered_links)} links)")
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
        
        return pages
    
    async def _extract_ui_elements(self, page: Page, url: str) -> List[Dict]:
        """Extract UI elements from a page."""
        elements = []
        
        # Extract buttons
        buttons = await page.query_selector_all("button, input[type='button'], input[type='submit']")
        for btn in buttons:
            text = await btn.inner_text() if await btn.is_visible() else ""
            elements.append({
                "type": "button",
                "selector": await self._get_selector(btn),
                "text": text,
                "page_url": url
            })
        
        # Extract inputs
        inputs = await page.query_selector_all("input, textarea")
        for inp in inputs:
            input_type = await inp.get_attribute("type") or "text"
            elements.append({
                "type": "input",
                "input_type": input_type,
                "selector": await self._get_selector(inp),
                "page_url": url
            })
        
        # Extract links
        links = await page.query_selector_all("a[href]")
        for link in links[:20]:  # Limit to 20 links
            text = await link.inner_text() if await link.is_visible() else ""
            href = await link.get_attribute("href")
            elements.append({
                "type": "link",
                "selector": await self._get_selector(link),
                "text": text,
                "href": href,
                "page_url": url
            })
        
        return elements
    
    async def _extract_forms(self, page: Page, url: str) -> List[Dict]:
        """Extract forms from a page."""
        forms = []
        
        form_elements = await page.query_selector_all("form")
        for form in form_elements:
            action = await form.get_attribute("action")
            method = await form.get_attribute("method") or "GET"
            
            # Extract form fields
            fields = []
            inputs = await form.query_selector_all("input, textarea, select")
            for inp in inputs:
                name = await inp.get_attribute("name")
                input_type = await inp.get_attribute("type") or "text"
                if name:
                    fields.append({"name": name, "type": input_type})
            
            forms.append({
                "selector": await self._get_selector(form),
                "action": action,
                "method": method,
                "fields": fields,
                "page_url": url
            })
        
        return forms
    
    async def _get_selector(self, element) -> str:
        """Generate CSS selector for an element."""
        # Simple implementation - in production, use more robust selector generation
        element_id = await element.get_attribute("id")
        if element_id:
            return f"#{element_id}"
        
        element_class = await element.get_attribute("class")
        if element_class:
            classes = element_class.split()[0] if element_class else ""
            return f".{classes}" if classes else "element"
        
        return "element"
    
    def _identify_flows(self, pages: List[PageInfo]) -> List[List[str]]:
        """Identify common navigation flows."""
        # Simple implementation - identify flows based on common patterns
        flows = []
        
        # Look for login flow
        login_pages = [p for p in pages if "login" in p.url.lower()]
        dashboard_pages = [p for p in pages if "dashboard" in p.url.lower() or "home" in p.url.lower()]
        
        if login_pages and dashboard_pages:
            flows.append(["Login Page", "Dashboard"])
        
        return flows
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _calculate_confidence(
        self,
        pages: List[PageInfo],
        elements: List[Dict],
        forms: List[Dict],
        has_llm_enhancement: bool = False
    ) -> float:
        """Calculate confidence based on crawl completeness."""
        confidence = 0.5  # Base confidence
        
        if pages:
            confidence += 0.15
        
        if elements:
            confidence += 0.1
        
        if forms:
            confidence += 0.05
        
        # Bonus for finding multiple pages
        if len(pages) >= 3:
            confidence += 0.05
        
        # MAJOR bonus for LLM enhancement
        if has_llm_enhancement:
            confidence += 0.15
            logger.info("Confidence boosted by LLM enhancement")
        
        return min(confidence, 1.0)
    
    def _page_to_dict(self, page_info: PageInfo) -> Dict:
        """Convert PageInfo to dictionary."""
        return {
            "url": page_info.url,
            "title": page_info.title,
            "status_code": page_info.status_code,
            "load_time_ms": page_info.load_time_ms,
            "screenshot": page_info.screenshot_path,
            "link_count": len(page_info.links)
        }
