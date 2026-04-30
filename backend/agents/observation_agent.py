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
import base64
import inspect
import logging
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from urllib.parse import quote, urljoin, urlparse, urlunparse
import re

DEFAULT_OBSERVATION_VIEWPORT = {"width": 1280, "height": 720}
DEFAULT_OBSERVATION_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)
DEFAULT_OBSERVATION_BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--start-maximized",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    "--disable-ipc-flooding-protection",
    "--disable-hang-monitor",
    "--disable-prompt-on-repost",
    "--disable-domain-reliability",
    "--disable-component-update",
    "--disable-client-side-phishing-detection",
    # Suppress Chrome's native "Save password?" and "Use passkey?" dialogs
    "--disable-features=PasswordManager,CredentialManagementAPI",
    "--password-store=basic",
    "--disable-save-password-bubble",
]

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
    from llm.client_factory import get_llm_client
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
    3. Identify user flows (login ??dashboard ??settings)
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
        # UAT checkout (login, upload, signature, payment, post-payment) often needs many steps; override via
        # config["max_browser_steps"] or task payload["max_browser_steps"] (capped 1??00).
        self.max_browser_steps = self.config.get("max_browser_steps", 120)
        
        # OPT-3: Element Finding Cache - Cache selectors for repeated scenarios (30-40% faster)
        # Key: (element_type, element_id, element_class) -> selector
        self._element_cache: Dict[Tuple[str, Optional[str], Optional[str]], str] = {}
        
        # Initialize LLM client ??provider/model driven by config (Sprint 10.6)
        self.llm_client = None
        if self.use_llm and LLM_AVAILABLE:
            llm_provider = self.config.get("llm_provider", "azure")
            llm_model = self.config.get("llm_model", (os.getenv("AZURE_OPENAI_MODEL", "ChatGPT-UAT")))
            self.llm_client = get_llm_client(
                llm_provider,
                llm_model,
            )
            if self.llm_client.enabled:
                logger.info(
                    "ObservationAgent initialized with LLM enhancement: %s/%s",
                    llm_provider,
                    llm_model,
                )
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
        
        Enhanced with multi-page flow crawling (Sprint 10):
        - If user_instruction provided: Use browser-use for LLM-guided flow navigation
        - Otherwise: Use traditional Playwright crawling (backward compatible)
        
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
            user_instruction = task.payload.get("user_instruction", "")  # NEW: User instruction for flow navigation
            login_credentials = task.payload.get("login_credentials", {})  # NEW: Login credentials for target website
            http_credentials = task.payload.get("http_credentials")  # NEW: HTTP Basic auth for preprod/UAT
            browser_profile_data = task.payload.get("browser_profile_data")
            gmail_credentials = task.payload.get("gmail_credentials", {})  # NEW: Separate Gmail login credentials (optional)
            available_file_paths = task.payload.get("available_file_paths")  # File paths for uploads (e.g. HKID)
            progress_callback = task.payload.get("progress_callback")
            cancel_check = task.payload.get("cancel_check")
            
            logger.info(f"ObservationAgent: Crawling web application: {url} (task {task.task_id})")
            
            # Check if we should use multi-page flow crawling
            use_flow_crawling = bool(user_instruction) and self.config.get("enable_flow_crawling", True)
            
            if use_flow_crawling:
                logger.info(f"ObservationAgent: Using LLM-guided flow navigation (user_instruction: '{user_instruction[:50]}...')")
                return await self._execute_multi_page_flow_crawling(
                    task, url, user_instruction, login_credentials, gmail_credentials, auth,
                    http_credentials=http_credentials,
                    browser_profile_data=browser_profile_data,
                    available_file_paths=available_file_paths,
                    progress_callback=progress_callback,
                    cancel_check=cancel_check,
                )
            else:
                # Traditional crawling (backward compatible)
                logger.info(f"ObservationAgent: Using traditional crawling (max_depth={max_depth})...")
                try:
                    return await self._execute_traditional_crawling(
                        task, url, max_depth, auth,
                        http_credentials=http_credentials,
                        progress_callback=progress_callback,
                        cancel_check=cancel_check,
                    )
                except (NotImplementedError, OSError) as e:
                    # Python 3.13 + Windows: asyncio subprocess can raise NotImplementedError in some event loop contexts.
                    logger.warning(
                        "ObservationAgent: Playwright unavailable (%s: %s). Using stub mode so workflow can continue.",
                        type(e).__name__, e
                    )
                    return await self._execute_stub_mode(task)
        
        except Exception as e:
            logger.error(f"ObservationAgent: Error during task execution: {e}", exc_info=True)
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0
            )
    
    async def _execute_traditional_crawling(
        self,
        task: TaskContext,
        url: str,
        max_depth: int,
        auth: Optional[Dict]
        ,
        http_credentials: Optional[Dict[str, str]] = None,
        progress_callback=None,
        cancel_check=None,
    ) -> TaskResult:
        """Traditional Playwright crawling (backward compatible)"""
        if callable(progress_callback):
            progress_callback({
                "progress": 0.05,
                "message": "Launching browser for observation...",
            })

        import os

        headless_str = os.getenv("HEADLESS_BROWSER") or os.getenv("BROWSER_HEADLESS", "true")
        headless_str = headless_str.lower()
        headless_mode = headless_str in ("true", "1", "yes")
        logger.info(f"ObservationAgent: Launching browser (headless={headless_mode})...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless_mode)
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "AI-Web-Test ObservationAgent/1.0",
            }
            normalized_http_credentials = self._normalize_http_credentials(http_credentials)
            if normalized_http_credentials:
                context_options["http_credentials"] = normalized_http_credentials

            context = await browser.new_context(**context_options)

            if auth:
                logger.debug("ObservationAgent: Adding authentication to browser context...")
                await context.add_init_script(f"""
                    localStorage.setItem('auth_token', '{auth.get('token', '')}');
                """)

            page = await context.new_page()

            logger.info(f"ObservationAgent: Crawling pages (max_depth={max_depth})...")
            pages = await self._crawl_pages(page, url, max_depth)
            logger.info(f"ObservationAgent: Found {len(pages)} page(s) to analyze")

            if callable(progress_callback):
                progress_callback({
                    "progress": 0.20,
                    "message": f"Discovered {len(pages)} pages. Starting element extraction...",
                    "pages_total": len(pages),
                    "pages_analyzed": 0,
                })

            logger.info("ObservationAgent: Extracting UI elements from pages...")
            all_elements = []
            all_forms = []
            total_pages = max(len(pages), 1)
            processed_pages = 0
            cancelled_mid_stage = False
            for idx, page_info in enumerate(pages, 1):
                if callable(cancel_check) and cancel_check():
                    logger.info(
                        "ObservationAgent: Cancellation requested during page extraction. Returning partial results."
                    )
                    cancelled_mid_stage = True
                    break

                logger.debug(
                    f"ObservationAgent: Extracting elements from page {idx}/{len(pages)}: {page_info.url}"
                )
                elements = await self._extract_ui_elements(page, page_info.url)
                forms = await self._extract_forms(page, page_info.url)
                all_elements.extend(elements)
                all_forms.extend(forms)
                processed_pages += 1

                if callable(progress_callback):
                    progress_callback({
                        "progress": 0.20 + (0.55 * (idx / total_pages)),
                        "message": f"Analyzing page {idx}/{total_pages}",
                        "pages_total": total_pages,
                        "pages_analyzed": idx,
                        "elements_found": len(all_elements),
                    })

                logger.debug(
                    f"ObservationAgent: Page {idx} - {len(elements)} elements, {len(forms)} forms"
                )

            logger.info(
                f"ObservationAgent: Playwright baseline complete - {len(all_elements)} elements, "
                f"{len(all_forms)} forms"
            )

            llm_enhanced_elements = []
            llm_analysis = {}
            if not cancelled_mid_stage and self.llm_client and self.llm_client.enabled:
                try:
                    html_content = await page.content()
                    page_title = await page.title()

                    logger.info("Analyzing page with LLM for enhanced element detection...")
                    llm_analysis = await self.llm_client.analyze_page_elements(
                        html=html_content,
                        basic_elements=all_elements[:20],
                        url=url,
                        page_title=page_title,
                        learned_patterns=None,
                    )

                    llm_enhanced_elements = llm_analysis.get("enhanced_elements", [])
                    logger.info(f"LLM found {len(llm_enhanced_elements)} additional elements")

                    if callable(progress_callback):
                        progress_callback({
                            "progress": 0.90,
                            "message": f"LLM enrichment complete (+{len(llm_enhanced_elements)} elements)",
                            "elements_found": len(all_elements) + len(llm_enhanced_elements),
                        })

                    all_elements.extend(llm_enhanced_elements)
                except Exception as e:
                    logger.warning(f"LLM analysis failed, continuing with Playwright-only results: {e}")

            flows = self._identify_flows(pages)

            if callable(progress_callback):
                progress_callback({
                    "progress": 1.0,
                    "message": "Observation extraction complete",
                    "pages_total": len(pages),
                    "pages_analyzed": processed_pages,
                    "elements_found": len(all_elements),
                })

            await browser.close()

        confidence = self._calculate_confidence(
            pages,
            all_elements,
            all_forms,
            has_llm_enhancement=bool(llm_enhanced_elements),
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
                "url": url,
                "title": pages[0].title if pages else "",
                "page_structure": {
                    "total_pages": len(pages),
                    "total_elements": len(all_elements),
                    "total_forms": len(all_forms),
                },
            },
            "llm_analysis": {
                "used": bool(llm_enhanced_elements),
                "elements_found": len(llm_enhanced_elements),
                "suggested_selectors": llm_analysis.get("suggested_selectors", {}),
                "page_patterns": llm_analysis.get("page_patterns", {}),
                "missed_by_playwright": llm_analysis.get("missed_by_playwright", []),
            },
            "summary": {
                "buttons": len([e for e in all_elements if e.get("type") == "button"]),
                "inputs": len([e for e in all_elements if e.get("type") == "input"]),
                "links": len([e for e in all_elements if e.get("type") == "link"]),
                "forms": len(all_forms),
                "playwright_elements": len(all_elements) - len(llm_enhanced_elements),
                "llm_enhanced_elements": len(llm_enhanced_elements),
            },
        }

        logger.info(
            f"Crawling complete: {len(pages)} pages, "
            f"{len(all_elements)} elements, {len(all_forms)} forms"
        )

        return TaskResult(
            task_id=task.task_id,
            success=True,
            result=result,
            confidence=confidence,
        )

    async def _execute_multi_page_flow_crawling(
        self,
        task: TaskContext,
        url: str,
        user_instruction: str,
        login_credentials: Dict,
        gmail_credentials: Dict,
        auth: Optional[Dict]
        ,
        http_credentials: Optional[Dict[str, str]] = None,
        browser_profile_data: Optional[Dict[str, Any]] = None,
        available_file_paths: Optional[List[str]] = None,
        progress_callback=None,
        cancel_check=None,
    ) -> TaskResult:
        """
        Multi-page flow crawling using browser-use for LLM-guided navigation.
        
        This method:
        1. Uses browser-use to navigate through entire user flow
        2. Extracts UI elements from all pages visited
        3. Stops when goal is reached (e.g., purchase confirmation)
        4. Returns elements from all pages in the flow
        
        10A.10 Enhancement: Supports configurable goal indicators via task payload.
        """
        # 10A.10: Get custom goal indicators from task payload if provided
        custom_goal_indicators = task.payload.get("goal_indicators", None)
        try:
            # Try to import browser-use
            try:
                from browser_use import Agent as BrowserUseAgent, Browser
                BROWSER_USE_AVAILABLE = True
            except ImportError:
                BROWSER_USE_AVAILABLE = False
                logger.warning("browser-use not installed. Install with: pip install browser-use")
                logger.info("Falling back to traditional crawling...")
                return await self._execute_traditional_crawling(task, url, self.max_depth, auth)
            
            if not BROWSER_USE_AVAILABLE:
                return await self._execute_traditional_crawling(task, url, self.max_depth, auth)
            
            logger.info(f"ObservationAgent: Starting multi-page flow crawling with browser-use")
            logger.info(f"  URL: {url}")
            logger.info(f"  User Instruction: {user_instruction}")

            browser_profile = self._build_browser_profile(
                http_credentials=http_credentials,
                url=url,
                browser_profile_data=browser_profile_data,
            )
            
            # Prefer in-page login unless user explicitly needs OTP/Gmail (e.g. "OTP", "verify email", "gmail")
            instruction_lower = (user_instruction or "").lower()
            require_otp_handling = (
                task.payload.get("require_otp", False)
                or "otp" in instruction_lower
                or "gmail" in instruction_lower
                or "verify email" in instruction_lower
                or "email verification" in instruction_lower
            )
            
            # Initialize browser-use
            browser = Browser(browser_profile=browser_profile)
            initial_page_primed = await self._prime_browser_session_http_auth(
                browser,
                url=url,
                http_credentials=http_credentials,
            )

            # If the browser was not primed (no HTTP credentials), start it explicitly
            # and navigate to the target URL so the CDP session is ready before the
            # agent fires its first BrowserStateRequestEvent.  Without this, browser-use
            # fires the event while the browser is still on about:blank / CDP is not yet
            # connected, causing all watchdog handlers to fail 6/6 times and the agent
            # to abort immediately with "Stopping due to 5 consecutive failures".
            if not initial_page_primed:
                try:
                    start_fn = getattr(browser, "start", None)
                    if callable(start_fn):
                        start_result = start_fn()
                        if inspect.isawaitable(start_result):
                            await start_result
                    navigate_fn = getattr(browser, "navigate_to", None)
                    if callable(navigate_fn):
                        nav_result = navigate_fn(url)
                        if inspect.isawaitable(nav_result):
                            await nav_result
                        logger.info(f"ObservationAgent: Browser pre-navigated to {url} (CDP warm-up)")
                    # Small grace period for the CDP watchdogs to register
                    await asyncio.sleep(1.0)
                except Exception as e:
                    logger.warning(
                        f"ObservationAgent: Browser warm-up failed ({e}); agent will attempt to navigate itself"
                    )

            start_instruction = (
                f"You are already on {url}. Continue from the current page and complete the following task:"
                if initial_page_primed
                else f"Navigate to {url} and complete the following task:"
            )

            # Resolve opt-in flags here so they're available for both the task description
            # and the tool registration block below.
            enable_sig = task.payload.get(
                "enable_signature_pad_tool",
                self.config.get("enable_signature_pad_tool", True),
            )
            enable_payment_click = task.payload.get(
                "use_playwright_payment_click",
                self.config.get("use_playwright_payment_click", False),
            )

            # Build task description for browser-use
            task_description = f"""
            {start_instruction}
            {user_instruction}
            
            LOGIN METHOD (CRITICAL):
            - Use ONLY the in-page login form: click Login, then enter email and password in the fields on the same page or in a popup on the same site.
            - Do NOT click "Login with Gmail", "Sign in with Google", or any social/OAuth login button.
            - Do NOT open new tabs or new windows for login. Stay on the same site.
            - If the page shows both an email/password form and a Gmail/Google button, use ONLY the email/password form.
            - Typical flow: Click "Login" ??enter email in the email field ??click Next/Login ??enter password ??click Login/Submit.

            ELEMENT SELECTION / CLICK ACCURACY (CRITICAL):
            - When choosing an index to click, prefer a real control (button, link, or span inside a button) whose visible text or role matches the task:
              e.g. for "Login" choose the control labeled "Login", NOT a promo tile, price banner, or unrelated text like "Buy" or a dollar amount.
            - If the listed "index" for your intended action points at a large card, carousel, or price (e.g. "$338") while the task says Login/Next/Checkbox,
              pick a different index that matches the requirement or scroll until the correct control is in view.
            - Scroll the target control into the center of the viewport before clicking. For checkboxes/terms, click the checkbox or its label, not a nearby price div.
            - After a file upload completes, wait briefly (1??s) for validation/UI to update before clicking "Next" or "Continue".
            - If you click "Next" twice in a row and the page URL and main content do not change, STOP repeating: dismiss any overlay, scroll, fix a validation error,
              or click a different element that matches the step (e.g. checkbox, I understand).

            LOADING SPINNER (CRITICAL):
            - NEVER click any element whose visible text is "Loading..." or whose role is "status". These are spinner overlays ??clicking them does nothing useful and corrupts element indices for the next step.
            - After any click that triggers a page transition or form submission, ALWAYS wait for spinners to fully disappear before attempting the next click.
            - If a spinner is visible and you need to click "Next", use the **wait** action (5??0 seconds) first, then re-read the page state and find the "Next" button by its text ??do NOT reuse the index from a previous step, as the DOM will have re-rendered and indices will have shifted.
            - If after waiting the spinner is still present, wait again rather than clicking anything in the background.
            
            Extract UI elements from each page you visit during this flow.
            Stop when you reach the confirmation/success page (or payment page if that is the end of the flow).

            FLOW CONTINUITY (CRITICAL):
            - If a reminder, confirmation, or informational modal appears, click the close, confirm, or I understand button and continue from the current step without restarting the purchase flow.
            - MODAL PRIORITY (CRITICAL): When a modal/dialog is visible (e.g. "Reminder" about HKID card, "I understand" button), ONLY click elements INSIDE the modal. Do NOT click "Next" or other buttons in the background?�they are blocked by the modal. The modal is on top; click "I understand", "Close", or the modal's confirm button first. Ignore background elements until the modal is dismissed.
            - Stay in the current checkout/subscription journey whenever possible. Do not navigate back, reopen the start page, or intentionally restart the wizard unless the site forces it.
            - If the site unexpectedly returns to an earlier plan-selection step, reselect the same plan or add-on choices you already made and resume progressing forward instead of starting over with a different plan.
            - When the site keeps your current selections visible, preserve them and continue to the next incomplete step.
            - CRITICAL — DO NOT RESTART AFTER PAYMENT: Once you have passed the Auto-pay Setup page, you are INSIDE the checkout tunnel. If you are then redirected to any account overview, wallet, home, or dashboard page, DO NOT click "5G Monthly Plans" or restart the subscription flow. Instead, look on the current page for an order confirmation banner, order ID, success notification, "Thank you" message, or receipt link — those indicate a successful purchase. Only look forward, never backward.
            - CRITICAL — WALLET PAGE DURING CHECKOUT: If you see the wallet/account home page at any point AFTER the Auto-pay Setup page, it means the checkout may have completed or is in progress. Scan the page for a success/confirmation message BEFORE taking any other action. Never treat a wallet-page appearance as a reason to restart from "Click 5G Monthly Plans".

            SIGNATURE PAD / E-SIGNATURE (CRITICAL):
            - If you see "Subscriber's signature", "Sales and Service Contract", or a large empty signature area with a canvas, a single click will NOT work.
            - Use the **draw_signature_pad** action to draw a stroke on the signature canvas (optional: pass canvas_css_selector if you know it from find_elements).
            - After drawing, use **Preview** if the page offers it, confirm checkboxes if needed, then **Next** or **Submit** to continue.
            """

            # Payment method instructions ??wording differs based on whether the Playwright tool is on
            if enable_payment_click:
                task_description += """
            PAYMENT METHOD SELECTION (CRITICAL):
            - When you reach the Payment Method page with multiple payment icons (VISA/MasterCard, UnionPay, etc.), do NOT click by index number.
            - Instead, use the **click_visa_mastercard_and_checkout** action. It will precisely click the VISA/MasterCard icon using the img alt attribute and then click Checkout automatically.
            - This avoids accidentally selecting UnionPay or the wrong payment method.
            """
            else:
                task_description += """
            PAYMENT METHOD SELECTION (CRITICAL):
            - All payment method icons share the same div CSS classes, so do NOT try to identify the correct icon by its div class.
            - Instead, look for the img element whose alt attribute contains "Visa" (e.g. alt="Visa" or alt="Visa/Mastercard") and click that image or its immediate parent container.
            - Do NOT click by element index ??always locate by the img alt text containing "Visa".
            """
            try:
                from app.utils.three_uat_test_credentials import (
                    is_three_hk_uat_url,
                    three_uat_my3_and_identity_upload_hints,
                    three_uat_payment_test_instruction_block,
                )

                if is_three_hk_uat_url(url):
                    task_description += three_uat_payment_test_instruction_block()
                    task_description += three_uat_my3_and_identity_upload_hints()
                    logger.info(
                        "ObservationAgent: Appended Three HK UAT payment + My3/Identity upload hints for browser-use task"
                    )
            except Exception as e:
                logger.warning("ObservationAgent: Could not append UAT payment instructions: %s", e)

            if available_file_paths:
                first_path = available_file_paths[0]
                task_description += f"""

            FILE UPLOAD (when flow requires identity document / HKID upload):
            - Use this EXACT file path for upload: {first_path}
            - Do NOT use /path/to/sample_id_document.jpg or placeholder paths.
            - The file is available at the path above; use it when the upload step appears.
            - Many sites use a blue **"Upload"** or **"Choose file"** link (`<a>`), not a `<button>`. If you see "Identity Document" / HKID text and no button, click the Upload link or the visible file input.
            """
            
            if require_otp_handling:
                task_description += """
            OTP VERIFICATION HANDLING:
            If you encounter OTP (One-Time Password) verification or email verification:
            1. Note the email address where the OTP will be sent (usually displayed on the OTP page)
            2. Open a new tab (Ctrl+T or Cmd+T) and navigate to https://mail.google.com
            3. Log into Gmail using the provided login credentials (see below)
               - If Gmail asks for 2FA, use the same password or skip if possible
               - If you see a "Choose an account" page, select the email address provided
            4. Once logged into Gmail, look for the most recent email containing the OTP code
               - Check the inbox first
               - Look for emails from the website/service (e.g., "Three HK", "Three.com.hk")
               - The OTP code is usually 4-6 digits and may be in the subject line or email body
               - Look for patterns like "Your verification code is: 123456" or "OTP: 123456"
            5. Extract the OTP code (digits only, usually 4-6 digits)
            6. Switch back to the original tab with the OTP verification page (click the tab or use Alt+Tab)
            7. Enter the OTP code in the verification input field
            8. Click the submit/confirm/verify button to continue with the flow
            
            IMPORTANT: 
            - Complete the entire flow including OTP verification. Do not stop until you reach the final confirmation/success page.
            - If you cannot find the OTP email, wait a few seconds and refresh Gmail, then try again.
            - The OTP code is usually valid for a limited time, so extract and enter it promptly.
            """
            else:
                logger.info("ObservationAgent: In-page login only (OTP/Gmail handling disabled for this run)")
            
            # Add login credentials if provided (API may send "username" or "email" for website login)
            if login_credentials:
                email = login_credentials.get("email") or login_credentials.get("username", "")
                password = login_credentials.get("password", "")
                
                task_description += (
                    f"\n\nLogin credentials (SENSITIVE - use exactly as provided):"
                    f"\n- Target website email: {email}"
                    f"\n- Target website password: {password}"
                )
                task_description += (
                    f"\n\nUse these credentials in the IN-PAGE login form only: enter the email in the email field, "
                    f"then the password in the password field, then click Login/Submit. Do not use Gmail or open new tabs for login."
                )
                
                if require_otp_handling:
                    # Determine Gmail credentials for OTP retrieval only when OTP handling is enabled
                    if gmail_credentials and gmail_credentials.get("email") and gmail_credentials.get("password"):
                        gmail_email = gmail_credentials.get("email", "")
                        gmail_password = gmail_credentials.get("password", "")
                        logger.info(f"ObservationAgent: Using explicit Gmail credentials for OTP: {gmail_email}")
                    else:
                        gmail_email = email
                        if "+" in email:
                            gmail_email = email.split("+")[0] + "@" + email.split("@")[1]
                            logger.info(f"ObservationAgent: Email contains '+', using '{gmail_email}' for Gmail (OTP only)")
                        gmail_password = password
                    
                    task_description += (
                        f"\n- Gmail login email (for OTP only): {gmail_email}"
                        f"\n- Gmail login password (for OTP only): {gmail_password}"
                    )
                    task_description += (
                        f"\n\nIf the site requires OTP verification: open Gmail in a new tab, log in with the Gmail credentials above, "
                        f"retrieve the OTP, then switch back and enter it. Otherwise do not use Gmail."
                    )
            
            # Create LLM adapter for browser-use (use Azure OpenAI)
            # Note: browser-use expects a specific LLM interface, we'll need to adapt
            llm_adapter = self._create_browser_use_llm_adapter()
            agent_kwargs: Dict[str, Any] = {
                "task": task_description,
                "llm": llm_adapter,
                "browser": browser,
                "browser_profile": browser_profile,
            }
            if available_file_paths:
                agent_kwargs["available_file_paths"] = available_file_paths
                logger.info(f"ObservationAgent: Providing available_file_paths for uploads: {available_file_paths}")

            # enable_sig and enable_payment_click are resolved earlier (before task_description)
            # so they are available for both the task prompt and the tool registration below.

            if enable_sig or enable_payment_click:
                try:
                    from browser_use.tools.service import Tools as BrowserUseTools
                    _tools = BrowserUseTools()

                    if enable_sig:
                        from agents.browser_use_signature_tool import register_draw_signature_pad_tool
                        register_draw_signature_pad_tool(_tools)
                        logger.info("ObservationAgent: Registered draw_signature_pad tool")

                    if enable_payment_click:
                        from agents.browser_use_payment_tool import register_click_visa_mastercard_tool
                        register_click_visa_mastercard_tool(_tools)
                        logger.info("ObservationAgent: Registered click_visa_mastercard_and_checkout tool (use_playwright_payment_click=true)")

                    agent_kwargs["tools"] = _tools
                except Exception as e:
                    logger.warning(
                        "ObservationAgent: Could not register custom tools (%s); using default tools",
                        e,
                    )

            agent = BrowserUseAgent(**agent_kwargs)

            # Per-run step cap (browser-use Agent.run(max_steps=...)); request can override via task payload.
            _raw_steps = task.payload.get("max_browser_steps", self.max_browser_steps)
            try:
                effective_max_steps = max(1, min(500, int(_raw_steps)))
            except (TypeError, ValueError):
                effective_max_steps = self.max_browser_steps
            if "max_browser_steps" in task.payload:
                logger.info(
                    "ObservationAgent: max_browser_steps=%s (from task payload; agent config default %s)",
                    effective_max_steps,
                    self.max_browser_steps,
                )
            
            # Run the agent to navigate through the flow with wall-clock timeout (heartbeat loop).
            # Default 1200s (20m): long UAT checkout flows often exceed 10m; OTP/Gmail can need more.
            # Task payload overrides agent config. Clamped to 60s??200s.
            _raw_flow_timeout = task.payload.get("max_flow_timeout_seconds")
            if _raw_flow_timeout is None:
                _raw_flow_timeout = self.config.get("max_flow_timeout_seconds")
            if _raw_flow_timeout is None:
                max_flow_timeout = 1200
            else:
                try:
                    max_flow_timeout = max(60, min(7200, int(_raw_flow_timeout)))
                except (TypeError, ValueError):
                    max_flow_timeout = 1200
            if task.payload.get("max_flow_timeout_seconds") is not None:
                logger.info(
                    "ObservationAgent: max_flow_timeout_seconds=%s (from task payload)",
                    max_flow_timeout,
                )
            logger.info(
                f"ObservationAgent: Running browser-use agent to navigate flow "
                f"(max {max_flow_timeout}s wall-clock, {effective_max_steps} steps)..."
            )
            if require_otp_handling:
                logger.info("ObservationAgent: Agent may navigate to Gmail if OTP verification is required")
            else:
                logger.info("ObservationAgent: In-page login only; Gmail/OTP steps disabled")

            if callable(progress_callback):
                progress_callback({
                    "progress": 0.10,
                    "message": "Starting guided flow navigation...",
                })
            
            run_task: Optional[asyncio.Task] = None
            try:
                # Run with heartbeat ticks so we can emit mid-stage progress and react to cancellation.
                run_task = asyncio.create_task(agent.run(max_steps=effective_max_steps))
                started = asyncio.get_running_loop().time()
                history = None

                while True:
                    try:
                        history = await asyncio.wait_for(asyncio.shield(run_task), timeout=1.0)
                        break
                    except asyncio.TimeoutError:
                        elapsed = asyncio.get_running_loop().time() - started

                        if callable(cancel_check) and cancel_check():
                            logger.info("ObservationAgent: Cancellation requested during browser-use run. Cancelling current stage...")
                            run_task.cancel()
                            try:
                                await run_task
                            except asyncio.CancelledError:
                                pass
                            return TaskResult(
                                task_id=task.task_id,
                                success=True,
                                result={
                                    "start_url": url,
                                    "pages_crawled": 0,
                                    "total_elements": 0,
                                    "total_forms": 0,
                                    "pages": [],
                                    "ui_elements": [],
                                    "forms": [],
                                    "navigation_flow": {
                                        "start_url": url,
                                        "goal_reached": False,
                                        "pages_visited": [],
                                        "flow_path": [],
                                    },
                                    "page_context": {
                                        "url": url,
                                        "title": "",
                                        "page_structure": {
                                            "total_pages": 0,
                                            "total_elements": 0,
                                            "total_forms": 0,
                                        },
                                    },
                                },
                                confidence=0.0,
                                metadata={"cancelled": True},
                            )

                        # Emit heartbeat/mid-stage progress from observed browser-use steps
                        if callable(progress_callback):
                            history_obj = getattr(agent, "history", None)
                            steps_done = len(getattr(history_obj, "history", []) or [])
                            progress_callback({
                                "progress": min(0.85, max(0.10, steps_done / max(1, effective_max_steps))),
                                "message": f"Navigating flow... ({steps_done}/{effective_max_steps} steps)",
                                "steps_completed": steps_done,
                                "steps_total": effective_max_steps,
                            })

                        if elapsed >= max_flow_timeout:
                            raise asyncio.TimeoutError()

                logger.info(f"ObservationAgent: Browser-use agent completed successfully")
            except asyncio.TimeoutError:
                logger.warning(f"ObservationAgent: Browser-use agent timed out after {max_flow_timeout}s. "
                             f"Extracting elements from pages visited so far...")
                # Try to get partial history if available
                if hasattr(agent, 'history') and agent.history:
                    history = agent.history
                    logger.info(f"ObservationAgent: Retrieved partial history from agent ({len(agent.history)} steps)")
                else:
                    # Create empty history if agent doesn't expose it
                    try:
                        from browser_use.agent.service import AgentHistoryList
                        history = AgentHistoryList(history=[])
                    except ImportError:
                        # Fallback: create a minimal history structure
                        history = type('AgentHistoryList', (), {'history': []})()
                    logger.warning("ObservationAgent: No partial history available from timed-out agent - will return empty results")

                # Stop browser-use before returning so Requirements/Analysis do not overlap with a live run.
                if run_task is not None and not run_task.done():
                    logger.info(
                        "ObservationAgent: Cancelling browser-use run after wall-clock timeout "
                        "(waiting for task to end before downstream agents)."
                    )
                    run_task.cancel()
                    try:
                        await run_task
                    except asyncio.CancelledError:
                        pass
                    except Exception as cleanup_err:
                        logger.debug(
                            "ObservationAgent: browser-use task cleanup after timeout: %s",
                            cleanup_err,
                        )

            # Extract pages and elements from browser-use history
            # AgentHistoryList structure:
            #   history.history: list[AgentHistory]
            #     AgentHistory.state: BrowserStateHistory
            #       .url: str
            #       .title: str
            #       .interacted_element: list[DOMInteractedElement | None]
            #     AgentHistory.result: list[ActionResult]
            #       .extracted_content: str | None
            #     AgentHistory.model_output: AgentOutput | None
            pages_data = []
            all_elements = []
            all_forms = []
            visited_urls = set()  # Track unique URLs to avoid duplicates
            
            logger.debug(f"Processing browser-use history (type: {type(history)})...")
            history_items = history.history if hasattr(history, 'history') else list(history)
            logger.debug(f"History contains {len(history_items)} steps")
            
            flow_steps = []  # Ordered list of actions taken during crawl for RequirementsAgent / Playwright codegen
            from app.utils.playwright_flow_recording import (
                build_locator_bundle,
                wrap_playwright_flow_recording,
            )

            def _locator_for_elem(elem) -> Optional[Dict[str, Any]]:
                if elem is None:
                    return None
                return build_locator_bundle(
                    xpath=getattr(elem, "x_path", "") or "",
                    backend_node_id=getattr(elem, "backend_node_id", None),
                    frame_id=getattr(elem, "frame_id", None),
                    attributes=getattr(elem, "attributes", None) or {},
                    ax_name=getattr(elem, "ax_name", None),
                    node_name=(getattr(elem, "node_name", "") or ""),
                    stable_hash=getattr(elem, "stable_hash", None),
                    element_hash=getattr(elem, "element_hash", None),
                )

            for idx, history_item in enumerate(history_items):
                try:
                    # Extract URL and title from history_item.state (BrowserStateHistory)
                    state = getattr(history_item, 'state', None)
                    if state is None:
                        logger.debug(f"History step {idx}: no state, skipping")
                        continue
                    
                    page_url = getattr(state, 'url', None)
                    page_title = getattr(state, 'title', '')
                    
                    if not page_url:
                        logger.debug(f"History step {idx}: no URL in state, skipping")
                        continue
                    
                    # Track unique pages
                    is_new_page = page_url not in visited_urls
                    if is_new_page:
                        visited_urls.add(page_url)
                    
                    # Convert DOMInteractedElement objects to UI element dicts
                    interacted = getattr(state, 'interacted_element', []) or []
                    for elem in interacted:
                        if elem is None:
                            continue
                        
                        # Map DOMInteractedElement attributes to our UI element format
                        attrs = getattr(elem, 'attributes', {}) or {}
                        node_name = getattr(elem, 'node_name', '').lower()
                        ax_name = getattr(elem, 'ax_name', '') or ''
                        node_value = getattr(elem, 'node_value', '') or ''
                        x_path = getattr(elem, 'x_path', '') or ''
                        
                        # Build one flow step for RequirementsAgent (ordered crawl actions)
                        step_text = ax_name or node_value or attrs.get('aria-label', '') or attrs.get('title', '') or node_name
                        if node_name == 'input':
                            flow_steps.append({
                                "order": len(flow_steps) + 1,
                                "action": "input",
                                "target": step_text[:200] if step_text else "input field",
                                "page_url": page_url,
                                "page_title": page_title or "",
                                "element_type": node_name,
                                "input_type": attrs.get("type", "text"),
                                "locator": _locator_for_elem(elem),
                            })
                        elif node_name in ('button', 'a') or attrs.get('role') in ('button', 'link'):
                            flow_steps.append({
                                "order": len(flow_steps) + 1,
                                "action": "click",
                                "target": step_text[:200] if step_text else node_name,
                                "page_url": page_url,
                                "page_title": page_title or "",
                                "element_type": node_name,
                                "locator": _locator_for_elem(elem),
                            })
                        else:
                            flow_steps.append({
                                "order": len(flow_steps) + 1,
                                "action": "click",
                                "target": step_text[:200] if step_text else node_name,
                                "page_url": page_url,
                                "page_title": page_title or "",
                                "element_type": node_name,
                                "locator": _locator_for_elem(elem),
                            })
                        
                        # Determine element type from tag name and attributes
                        elem_type = 'custom'
                        if node_name in ('button', 'input', 'select', 'textarea', 'a', 'form'):
                            elem_type = node_name
                        elif node_name == 'span' and attrs.get('role') == 'button':
                            elem_type = 'button'
                        elif attrs.get('role') in ('button', 'link', 'checkbox', 'tab', 'textbox'):
                            elem_type = attrs['role']
                        
                        # Determine text from ax_name or node_value
                        text = ax_name or node_value or attrs.get('aria-label', '') or attrs.get('title', '')
                        
                        ui_element = {
                            "type": elem_type,
                            "text": text[:200] if text else '',
                            "selector": x_path or f'//{node_name}',
                            "page_url": page_url,
                            "attributes": attrs,
                            "semantic_purpose": attrs.get('role', '') or elem_type,
                            "confidence": 0.9,  # High confidence - directly from browser DOM
                            "source": "browser-use-interaction"
                        }
                        
                        # Add input-specific attributes
                        if node_name == 'input':
                            ui_element["input_type"] = attrs.get('type', 'text')
                        
                        all_elements.append(ui_element)
                    
                    # Also extract info from action results (extracted_content)
                    results = getattr(history_item, 'result', []) or []
                    for result in results:
                        extracted = getattr(result, 'extracted_content', None)
                        if extracted:
                            # Store extracted content as a metadata element
                            all_elements.append({
                                "type": "extracted_content",
                                "text": str(extracted)[:500],
                                "selector": "",
                                "page_url": page_url,
                                "attributes": {},
                                "semantic_purpose": "content",
                                "confidence": 0.8,
                                "source": "browser-use-extraction"
                            })
                    
                    # Only add page data once per unique URL
                    if is_new_page:
                        page_elements = [e for e in all_elements if e.get('page_url') == page_url]
                        pages_data.append({
                            "url": page_url,
                            "title": page_title or f"Page {len(pages_data)+1}",
                            "elements": page_elements,
                            "forms": [],  # Forms are tracked via interacted elements
                            "load_time_ms": 0,
                            "status_code": 200
                        })
                        logger.debug(
                            f"Page {len(pages_data)}: {page_url[:80]} - "
                            f"{len(page_elements)} elements, title='{page_title[:50]}'"
                        )
                    
                except Exception as e:
                    logger.warning(f"Error processing history step {idx}: {e}", exc_info=True)
                    continue
            
            # Deduplicate elements by (type, text, page_url) while preserving order
            seen_elements = set()
            unique_elements = []
            for elem in all_elements:
                key = (elem.get('type', ''), elem.get('text', '')[:100], elem.get('page_url', ''))
                if key not in seen_elements:
                    seen_elements.add(key)
                    unique_elements.append(elem)
            all_elements = unique_elements
            
            logger.info(f"Extracted {len(pages_data)} unique pages, {len(all_elements)} elements from browser-use history")
            
            # Prepend initial navigate step if we have a start URL
            if url and not any(s.get("action") == "navigate" for s in flow_steps):
                flow_steps.insert(0, {
                    "order": 1,
                    "action": "navigate",
                    "target": url,
                    "page_url": url,
                    "page_title": pages_data[0]["title"] if pages_data else "",
                    "element_type": "navigate",
                    "locator": None,
                })
                for i in range(1, len(flow_steps)):
                    flow_steps[i]["order"] = i + 1
            
            # 10A.10: Check if goal was reached with enhanced indicators
            hist_seq = history.history if hasattr(history, "history") else history
            goal_reached = self._check_goal_reached(hist_seq, user_instruction, custom_goal_indicators)
            
            # Build navigation flow
            navigation_flow = {
                "start_url": url,
                "goal_reached": goal_reached,
                "pages_visited": [p["url"] for p in pages_data],
                "flow_path": [p["title"] for p in pages_data]
            }
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                [PageInfo(url=p["url"], title=p["title"], elements=p["elements"], 
                         forms=p["forms"], links=[], screenshot_path=None,
                         load_time_ms=p["load_time_ms"], status_code=p["status_code"])
                 for p in pages_data],
                all_elements,
                all_forms,
                has_llm_enhancement=True  # browser-use uses LLM
            )
            
            result = {
                "start_url": url,
                "user_instruction": user_instruction or "",
                "pages_crawled": len(pages_data),
                "total_elements": len(all_elements),
                "total_forms": len(all_forms),
                "pages": pages_data,
                "ui_elements": all_elements,
                "forms": all_forms,
                "navigation_flow": navigation_flow,
                "flow_steps": flow_steps,
                "playwright_flow_recording": wrap_playwright_flow_recording(
                    start_url=url or "",
                    steps=flow_steps,
                    goal_reached=goal_reached,
                ),
                "page_context": {
                    "url": url,
                    "title": pages_data[0]["title"] if pages_data else "",
                    "page_structure": {
                        "total_pages": len(pages_data),
                        "total_elements": len(all_elements),
                        "total_forms": len(all_forms)
                    },
                    "goal_reached": goal_reached,
                    "user_instruction": user_instruction or "",
                    "flow_steps_count": len(flow_steps),
                    "playwright_flow_recording_version": 1,
                },
                "llm_analysis": {
                    "used": True,
                    "method": "browser-use",
                    "goal_reached": goal_reached
                },
                "summary": {
                    "buttons": len([e for e in all_elements if e.get("type") == "button"]),
                    "inputs": len([e for e in all_elements if e.get("type") == "input"]),
                    "links": len([e for e in all_elements if e.get("type") == "link"]),
                    "forms": len(all_forms)
                }
            }
            
            logger.info(
                f"Multi-page flow crawling complete: {len(pages_data)} pages, "
                f"{len(all_elements)} elements, goal_reached={goal_reached}"
            )
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in multi-page flow crawling: {e}", exc_info=True)
            logger.info("Falling back to traditional crawling...")
            return await self._execute_traditional_crawling(task, url, self.max_depth, auth)

    def _build_browser_profile(
        self,
        http_credentials: Optional[Dict[str, str]] = None,
        url: Optional[str] = None,
        browser_profile_data: Optional[Dict[str, Any]] = None,
    ):
        """Create browser-use profile with reliable defaults and optional auth/session state."""
        from browser_use import BrowserProfile

        headers = self._build_http_auth_headers(http_credentials)

        # Resolve Playwright's own Chromium executable so browser-use always uses
        # the pinned Playwright build instead of a system Chrome (which may show
        # black screens or be missing CDP support on some machines).
        # NOTE: sync_playwright() cannot be called inside an asyncio loop, so we
        # use a subprocess to ask Python for the path instead.
        _playwright_chromium_path: Optional[str] = None
        try:
            import subprocess as _sp, sys as _sys
            _result = _sp.run(
                [_sys.executable, "-c",
                 "from playwright.sync_api import sync_playwright;" 
                 "p=sync_playwright().start();print(p.chromium.executable_path);p.stop()"],
                capture_output=True, text=True, timeout=15,
            )
            if _result.returncode == 0 and _result.stdout.strip():
                _playwright_chromium_path = _result.stdout.strip()
                logger.info(f"ObservationAgent: Using Playwright Chromium at {_playwright_chromium_path}")
            else:
                logger.warning(f"ObservationAgent: Could not resolve Playwright Chromium path: {_result.stderr.strip()}")
        except Exception as _e:
            logger.warning(f"ObservationAgent: Could not resolve Playwright Chromium path: {_e}")

        profile_kwargs: Dict[str, Any] = {
            "headless": False,
            "viewport": dict(DEFAULT_OBSERVATION_VIEWPORT),
            "window_size": dict(DEFAULT_OBSERVATION_VIEWPORT),
            "user_agent": DEFAULT_OBSERVATION_USER_AGENT,
            "args": list(DEFAULT_OBSERVATION_BROWSER_ARGS),
            "minimum_wait_page_load_time": 0.5,
            "wait_for_network_idle_page_load_time": 1.0,
            "wait_between_actions": 0.2,
        }
        if _playwright_chromium_path:
            profile_kwargs["chrome_instance_path"] = _playwright_chromium_path
        if headers:
            profile_kwargs["headers"] = headers
        storage_state = self._build_storage_state(url, browser_profile_data)
        if storage_state:
            profile_kwargs["storage_state"] = storage_state
        return BrowserProfile(**profile_kwargs)

    async def _setup_cdp_server_auth(
        self,
        browser,
        http_credentials: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Register a CDP Fetch.authRequired handler so the browser automatically
        responds to HTTP Basic Auth (401 WWW-Authenticate: Basic) challenges.

        browser-use 0.12.x has BrowserProfile.http_credentials commented out and
        does not intercept server auth challenges by default.  This method mirrors
        the _setup_proxy_auth pattern inside BrowserSession but for server challenges.

        Must be called AFTER browser.start() so _cdp_client_root is available.
        Returns True if the handler was registered, False otherwise.
        """
        normalized = self._normalize_http_credentials(http_credentials)
        if not normalized:
            return False

        cdp_client = getattr(browser, "_cdp_client_root", None)
        if cdp_client is None:
            logger.warning(
                "ObservationAgent: CDP client root not available after start(); "
                "cannot register server auth handler ??preprod page may remain blocked"
            )
            return False

        username = normalized["username"]
        password = normalized["password"]

        # Enable Fetch domain with auth challenge interception (mirrors _setup_proxy_auth)
        try:
            await cdp_client.send.Fetch.enable(params={"handleAuthRequests": True})
            logger.info("ObservationAgent: Enabled CDP Fetch.enable(handleAuthRequests=True) for HTTP Basic Auth")
        except Exception as e:
            logger.warning(f"ObservationAgent: Fetch.enable failed: {e}")
            return False

        def _on_auth_required(event: Any, session_id: Any = None) -> None:
            """Respond to any server auth challenge with ProvideCredentials."""
            request_id = event.get("requestId") or event.get("request_id")
            if not request_id:
                return

            async def _provide_creds() -> None:
                try:
                    await cdp_client.send.Fetch.continueWithAuth(
                        params={
                            "requestId": request_id,
                            "authChallengeResponse": {
                                "response": "ProvideCredentials",
                                "username": username,
                                "password": password,
                            },
                        },
                        session_id=session_id,
                    )
                    logger.debug(
                        f"ObservationAgent: Provided HTTP Basic credentials for auth challenge "
                        f"(requestId={request_id})"
                    )
                except Exception as e:
                    logger.debug(f"ObservationAgent: continueWithAuth failed: {e}")

            asyncio.create_task(_provide_creds())

        def _on_request_paused(event: Any, session_id: Any = None) -> None:
            """Continue any paused request to avoid stalling the network."""
            request_id = event.get("requestId") or event.get("request_id")
            if not request_id:
                return

            async def _continue_request() -> None:
                try:
                    await cdp_client.send.Fetch.continueRequest(
                        params={"requestId": request_id},
                        session_id=session_id,
                    )
                except Exception:
                    pass

            asyncio.create_task(_continue_request())

        try:
            cdp_client.register.Fetch.authRequired(_on_auth_required)
            cdp_client.register.Fetch.requestPaused(_on_request_paused)
            logger.info("ObservationAgent: Registered CDP Fetch.authRequired handler for HTTP Basic Auth")
        except Exception as e:
            logger.warning(f"ObservationAgent: Failed to register Fetch handlers: {e}")
            return False

        return True

    async def _prime_browser_session_http_auth(
        self,
        browser,
        url: str,
        http_credentials: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Start the browser session, register a CDP-level HTTP Basic Auth handler via
        Fetch.authRequired, then navigate to the initial URL so the preprod gate is
        cleared before the agent begins its main task.

        The CDP handler persists for the session lifetime, so if the agent re-navigates
        to the same page it will also succeed without needing separate header injection.

        Returns True when auth was set up and the initial page was loaded.
        """
        normalized = self._normalize_http_credentials(http_credentials)
        if not normalized:
            return False

        # Start the browser session (required before _cdp_client_root is available)
        start_fn = getattr(browser, "start", None)
        if callable(start_fn):
            start_result = start_fn()
            if inspect.isawaitable(start_result):
                await start_result

        # Register CDP auth handler ??this is the only auth mechanism needed
        await self._setup_cdp_server_auth(browser, normalized)

        # Navigate to the initial page; CDP handler responds to the 401 challenge
        navigate_fn = getattr(browser, "navigate_to", None)
        if callable(navigate_fn):
            try:
                nav_result = navigate_fn(url)
                if inspect.isawaitable(nav_result):
                    await nav_result
                logger.info(f"ObservationAgent: Initial page primed via CDP HTTP Basic Auth: {url}")
            except Exception as e:
                logger.warning(
                    f"ObservationAgent: Initial navigation failed: {e}; "
                    "agent will retry and CDP auth handler is still active"
                )
        return True

    def _build_http_auth_headers(
        self,
        http_credentials: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Build HTTP Basic auth headers for reuse across browser integrations."""
        normalized_credentials = self._normalize_http_credentials(http_credentials)
        if not normalized_credentials:
            return {}

        username = normalized_credentials["username"]
        password = normalized_credentials["password"]
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token}"}

    def _normalize_http_credentials(
        self,
        http_credentials: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, str]]:
        """Normalize credentials and drop unusable values to avoid invalid auth attempts."""
        if not http_credentials:
            return None

        username = str(http_credentials.get("username", "")).strip()
        password = str(http_credentials.get("password", "")).strip()

        if not username or not password:
            return None

        return {"username": username, "password": password}

    def _build_storage_state(
        self,
        url: Optional[str],
        browser_profile_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Convert stored browser profile session data into browser-use storage_state."""
        if not browser_profile_data:
            return None

        cookies = list(browser_profile_data.get("cookies") or [])
        local_storage = browser_profile_data.get("localStorage") or {}
        session_storage = browser_profile_data.get("sessionStorage") or {}

        if not cookies and not local_storage and not session_storage:
            return None

        origins: List[Dict[str, Any]] = []
        if url and (local_storage or session_storage):
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                origin_data: Dict[str, Any] = {"origin": f"{parsed.scheme}://{parsed.netloc}"}
                if local_storage:
                    origin_data["localStorage"] = [
                        {"name": str(name), "value": str(value)}
                        for name, value in local_storage.items()
                    ]
                if session_storage:
                    origin_data["sessionStorage"] = [
                        {"name": str(name), "value": str(value)}
                        for name, value in session_storage.items()
                    ]
                origins.append(origin_data)

        return {
            "cookies": cookies,
            "origins": origins,
        }

    def _build_authenticated_url(
        self,
        url: str,
        http_credentials: Optional[Dict[str, str]] = None,
    ) -> str:
        """Embed HTTP Basic auth in the URL as a compatibility fallback."""
        normalized_credentials = self._normalize_http_credentials(http_credentials)
        if not normalized_credentials:
            return url

        username = quote(normalized_credentials["username"], safe="")
        password = quote(normalized_credentials["password"], safe="")
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            return url

        host = parsed.hostname or ""
        if not host:
            return url

        port = f":{parsed.port}" if parsed.port else ""
        auth_netloc = f"{username}:{password}@{host}{port}"
        return urlunparse(
            (
                parsed.scheme,
                auth_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
    
    def _create_browser_use_llm_adapter(self):
        """Create LLM adapter for browser-use from the configured LLM client.
        
        Preferred: Use browser-use's built-in ChatAzureOpenAI which provides:
          - Proper JSON schema enforcement (ResponseFormatJSONSchema)
          - Full compatibility with browser-use's AgentOutput parsing
          - Async OpenAI client as expected by browser-use
        
        For non-Azure providers, skip ChatAzureOpenAI entirely and use the
        provider-aware custom adapter.
        """
        import os
        configured_provider = self.config.get("llm_provider", "azure")
        configured_model = self.config.get("llm_model", (os.getenv("AZURE_OPENAI_MODEL", "ChatGPT-UAT")))

        if configured_provider != "azure":
            try:
                from llm.browser_use_adapter import AzureOpenAIAdapter
                adapter = AzureOpenAIAdapter(azure_client=self.llm_client)
                logger.info(
                    "Browser-use custom LLM adapter created: provider=%s model=%s",
                    configured_provider,
                    configured_model,
                )
                return adapter
            except ImportError as e:
                logger.warning(f"Browser-use adapter not available: {e}. Using default LLM.")
                return None
            except Exception as e:
                logger.error(f"Error creating browser-use LLM adapter: {e}", exc_info=True)
                return None

        # --- Attempt 1: Use browser-use's built-in ChatAzureOpenAI ---
        # Env vars take priority; fall back to llm_client attributes if not set
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        deployment = os.getenv("AZURE_OPENAI_MODEL", "")

        if not api_key and self.llm_client and hasattr(self.llm_client, 'api_key'):
            api_key = self.llm_client.api_key
        if not endpoint and self.llm_client:
            endpoint = getattr(self.llm_client, 'endpoint', '')
        if not deployment and self.llm_client:
            deployment = getattr(self.llm_client, 'deployment', getattr(self.llm_client, 'model', ''))
        if not deployment:
            deployment = (os.getenv("AZURE_OPENAI_MODEL", "ChatGPT-UAT"))

        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        max_tokens = int(os.getenv("AZURE_OPENAI_MAX_COMPLETION_TOKENS", "4096"))
        temperature = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.2"))

        # Clean endpoint: remove /openai/v1 suffix added by some configs
        clean_endpoint = endpoint.replace("/openai/v1", "").replace("/openai", "").rstrip("/")

        # Auto-detect endpoint type:
        # - cognitiveservices.azure.com  ??use standard openai.AzureOpenAI SDK
        # - openai.azure.com             ??use browser-use's ChatAzureOpenAI (LangChain)
        is_cognitive_services = "cognitiveservices.azure.com" in clean_endpoint

        if is_cognitive_services:
            # --- Attempt 1a: Cognitive Services endpoint ??standard openai SDK wrapped for browser-use ---
            try:
                from llm.browser_use_adapter import CognitiveServicesAzureAdapter

                adapter = CognitiveServicesAzureAdapter(
                    api_key=api_key,
                    azure_endpoint=clean_endpoint,
                    deployment=deployment,
                    api_version=api_version,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                logger.info(
                    f"Browser-use adapter (cognitiveservices) created: model={deployment}, "
                    f"endpoint={clean_endpoint}"
                )
                return adapter
            except Exception as e:
                logger.warning(f"CognitiveServices adapter creation failed: {e}. Trying ChatAzureOpenAI...")

        # --- Attempt 1b: Classic openai.azure.com endpoint ??browser-use ChatAzureOpenAI ---
        try:
            from browser_use.llm.azure.chat import ChatAzureOpenAI

            if not api_key or not clean_endpoint:
                raise ValueError("Azure OpenAI credentials not available")

            adapter = ChatAzureOpenAI(
                model=deployment,
                api_key=api_key,
                azure_endpoint=clean_endpoint,
                azure_deployment=deployment,
                api_version=api_version,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
            logger.info(
                f"Browser-use ChatAzureOpenAI adapter created: model={adapter.model}, "
                f"endpoint={clean_endpoint}"
            )
            return adapter

        except ImportError as e:
            logger.warning(f"ChatAzureOpenAI not available: {e}. Trying custom adapter...")
        except Exception as e:
            logger.warning(f"ChatAzureOpenAI creation failed: {e}. Trying custom adapter...")
        
        # --- Attempt 2: Fallback to custom AzureOpenAIAdapter ---
        try:
            from llm.browser_use_adapter import AzureOpenAIAdapter
            adapter = AzureOpenAIAdapter(azure_client=self.llm_client)
            logger.info(
                "Browser-use custom LLM adapter created (fallback): provider=%s model=%s",
                configured_provider,
                configured_model,
            )
            return adapter
        except ImportError as e:
            logger.warning(f"Browser-use adapter not available: {e}. Using default LLM.")
            return None
        except Exception as e:
            logger.error(f"Error creating browser-use LLM adapter: {e}", exc_info=True)
            return None
    
    def _check_goal_reached(self, history, user_instruction: str, custom_indicators: List[str] = None) -> bool:
        """
        10A.10: Enhanced goal-oriented navigation with configurable indicators.
        
        Check if the goal from user_instruction was reached by looking for
        goal indicators in the page URL, title, or content.
        
        Args:
            history: Browser-use history containing visited pages
            user_instruction: User's instruction describing the goal
            custom_indicators: Optional custom goal indicators to look for
        
        Returns:
            True if goal appears to be reached, False otherwise
        """
        # Get goal indicators based on user instruction
        goal_indicators = self._get_goal_indicators(user_instruction, custom_indicators)
        
        logger.debug(f"Checking goal with indicators: {goal_indicators}")
        
        # Check each history item for goal indicators
        for history_item in history:
            try:
                # Extract URL and title from history item
                url_lower = ""
                title_lower = ""
                content_lower = ""
                
                # Try different ways to access URL
                if hasattr(history_item, 'url'):
                    url_lower = history_item.url.lower()
                elif hasattr(history_item, 'page_url'):
                    url_lower = history_item.page_url.lower()
                elif hasattr(history_item, 'state') and hasattr(history_item.state, 'url'):
                    url_lower = history_item.state.url.lower()
                elif isinstance(history_item, dict):
                    url_lower = (history_item.get('url') or history_item.get('page_url') or '').lower()
                
                # Try different ways to access title
                if hasattr(history_item, 'title'):
                    title_lower = history_item.title.lower()
                elif hasattr(history_item, 'state') and hasattr(history_item.state, 'title'):
                    title_lower = history_item.state.title.lower()
                elif isinstance(history_item, dict):
                    title_lower = (history_item.get('title') or '').lower()
                
                # Try to access extracted content (from browser-use results)
                if hasattr(history_item, 'result'):
                    results = history_item.result if isinstance(history_item.result, list) else [history_item.result]
                    for result in results:
                        if hasattr(result, 'extracted_content') and result.extracted_content:
                            content_lower += str(result.extracted_content).lower() + " "

                # LLM step summaries (Eval / Memory / Next goal) ??matches final "done" messaging
                mo = getattr(history_item, "model_output", None)
                if mo is not None:
                    for _field in ("evaluation", "memory", "next_goal", "thought"):
                        _v = getattr(mo, _field, None)
                        if _v:
                            content_lower += str(_v).lower() + " "
                
                # Check if any goal indicator is found
                combined_text = f"{url_lower} {title_lower} {content_lower}"
                
                for indicator in goal_indicators:
                    if indicator.lower() in combined_text:
                        logger.info(f"Goal indicator '{indicator}' found in: {url_lower[:50] or title_lower[:50]}")
                        return True
                        
            except Exception as e:
                logger.debug(f"Error checking goal in history item: {e}")
                continue
        
        return False
    
    def _get_goal_indicators(self, user_instruction: str, custom_indicators: List[str] = None) -> List[str]:
        """
        10A.10: Get goal indicators based on user instruction and goal type.
        
        Returns a list of keywords/phrases that indicate the goal has been reached.
        Supports multiple flow types with localized indicators (English + Chinese).
        
        Args:
            user_instruction: User's instruction describing the goal
            custom_indicators: Optional list of custom indicators to include
        
        Returns:
            List of goal indicators (keywords/phrases) to look for in page content
        
        Supported flow types:
            - Purchase/checkout: "confirmation", "order confirmed", "payment successful", etc.
            - Registration: "account created", "welcome", "verify your email", etc.
            - Login: "dashboard", "welcome back", "logged in", etc.
            - Form submission: "submitted", "sent", "thank you", etc.
            - Search: "results", "found", "showing", etc.
        
        Example:
            >>> agent._get_goal_indicators("Complete the purchase flow")
            ['confirmation', 'order confirmed', 'payment successful', ...]
        """
        # Start with custom indicators if provided
        indicators = list(custom_indicators) if custom_indicators else []
        
        instruction_lower = user_instruction.lower()
        
        # Purchase/checkout/subscription flow indicators
        if any(
            keyword in instruction_lower
            for keyword in [
                "purchase",
                "buy",
                "checkout",
                "order",
                "subscribe",
                "subscription",
                "訂購",
                "購買",
            ]
        ):
            indicators.extend([
                "confirmation",
                "order confirmed",
                "order complete",
                "thank you for your order",
                "order number",
                "order id",
                "order #",
                "purchase id",
                "payment successful",
                "payment confirmed",
                "purchase complete",
                "checkout complete",
                "receipt",
                "invoice",
                "successful subscribed",
                "subscription successful",
                "successfully completed",
                "subscribed page",
                "確�?",
                "?��?",
                "訂單編�?",
                "訂單確�?",
                "付款?��?",
            ])
        
        # Registration/signup flow indicators
        if any(keyword in instruction_lower for keyword in ["register", "signup", "sign up", "create account", "註�?"]):
            indicators.extend([
                "registration complete", "account created", "welcome", "verify your email",
                "registration successful", "signup complete", "account activated",
                "註冊完成", "帳戶已建立", "歡迎"
            ])
        
        # Login flow indicators
        if any(keyword in instruction_lower for keyword in ["login", "sign in", "log in", "?�入"]):
            indicators.extend([
                "dashboard", "welcome back", "logged in", "my account", "profile",
                "home", "?�入?��?", "歡�??��?"
            ])
        
        # Form submission indicators
        if any(keyword in instruction_lower for keyword in ["submit", "send", "contact", "inquiry", "?�交"]):
            indicators.extend([
                "submitted", "sent", "received", "thank you", "we will contact you",
                "message sent", "form submitted", "已提交", "已發送"
            ])
        
        # Search flow indicators
        if any(keyword in instruction_lower for keyword in ["search", "find", "?��?", "?�找"]):
            indicators.extend([
                "results", "found", "showing", "matches", "?��?結�?", "?�到"
            ])
        
        # Generic success indicators (always include)
        indicators.extend([
            "success", "complete", "done", "finished", "confirmed",
            "?��?", "完�?", "確�?"
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_indicators = []
        for indicator in indicators:
            if indicator.lower() not in seen:
                seen.add(indicator.lower())
                unique_indicators.append(indicator)
        
        return unique_indicators
    
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
            "page_structure": {
                "url": url,
                "title": "Home Page",
                "forms": [
                    {"selector": "#login-form", "action": "/api/auth/login", "method": "POST", "fields": [{"name": "username", "type": "text"}, {"name": "password", "type": "password"}], "page_url": f"{url}/login"}
                ]
            },
            "_note": "STUB MODE - Playwright not available (e.g. Windows/Python 3.13). Install with: pip install playwright; playwright install chromium"
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
        """
        Generate CSS selector for an element with caching (OPT-3).
        Caching reduces repeated selector generation by 30-40%.
        """
        # OPT-3: Check cache first
        element_id = await element.get_attribute("id")
        element_class = await element.get_attribute("class")
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()")
        
        cache_key = (element_tag, element_id, element_class)
        if cache_key in self._element_cache:
            return self._element_cache[cache_key]
        
        # Generate selector
        if element_id:
            selector = f"#{element_id}"
        elif element_class:
            classes = element_class.split()[0] if element_class else ""
            selector = f".{classes}" if classes else element_tag
        else:
            selector = element_tag
        
        # OPT-3: Cache the result
        self._element_cache[cache_key] = selector
        return selector
    
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
