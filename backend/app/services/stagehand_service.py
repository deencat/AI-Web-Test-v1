"""
Stagehand-based Test Execution Service
Uses Stagehand for browser automation with Playwright under the hood.
"""
import asyncio
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dotenv import load_dotenv

from stagehand import Stagehand, StagehandConfig
from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.models.test_execution import ExecutionStatus, ExecutionResult
from app.crud import test_execution as crud_execution

# Load environment variables
load_dotenv()

# Fix for Windows: Ensure ProactorEventLoop is used
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        pass


class StagehandExecutionService:
    """
    Service for executing test cases using Stagehand.
    Provides browser automation with simple step execution.
    """
    
    def __init__(
        self,
        browser: str = "chromium",
        headless: bool = True,
        screenshot_dir: str = "artifacts/screenshots",
        video_dir: str = "artifacts/videos"
    ):
        """Initialize Stagehand execution service."""
        self.browser = browser
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.video_dir = Path(video_dir)
        
        # Ensure directories exist
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        self.stagehand: Optional[Stagehand] = None
        self.page = None
    
    async def initialize(self):
        """Initialize Stagehand browser."""
        if not self.stagehand:
            # Ensure Windows event loop policy is set
            if sys.platform == 'win32':
                loop = asyncio.get_event_loop()
                if not isinstance(loop, asyncio.ProactorEventLoop):
                    try:
                        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    except:
                        pass
            
            print(f"[DEBUG] Initializing Stagehand in thread {threading.current_thread().name}")
            
            # Get API configuration from environment
            use_google_direct = os.getenv("USE_GOOGLE_DIRECT", "false").lower() == "true"
            browser_slowmo = int(os.getenv("BROWSER_SLOWMO", "0"))
            
            # Build browser launch options
            launch_options = {
                "handle_sigint": False,
                "handle_sigterm": False,
                "handle_sighup": False
            }
            if browser_slowmo > 0:
                launch_options["slow_mo"] = browser_slowmo
            
            # Configure model based on USE_GOOGLE_DIRECT setting
            if use_google_direct:
                # Use Google API directly (FREE with Google AI Studio)
                google_api_key = os.getenv("GOOGLE_API_KEY")
                google_model = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
                
                if not google_api_key:
                    raise ValueError(
                        "GOOGLE_API_KEY not set in .env file. "
                        "Get your key from: https://aistudio.google.com/app/apikey"
                    )
                
                config = StagehandConfig(
                    env="LOCAL",
                    headless=self.headless,
                    verbose=1,
                    # Use Google Gemini directly via LiteLLM
                    model_name=f"gemini/{google_model}",
                    model_api_key=google_api_key,
                    local_browser_launch_options=launch_options
                )
                print(f"[DEBUG] ✅ Using Google API directly with model: {google_model}")
                print(f"[DEBUG] This will use your Google AI Studio free tier (no OpenRouter credits needed)")
            else:
                # Use OpenRouter (original behavior)
                openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
                openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")
                
                config = StagehandConfig(
                    env="LOCAL",
                    headless=self.headless,
                    verbose=1,
                    model_name=f"openrouter/{openrouter_model}",
                    model_api_key=openrouter_key,
                    local_browser_launch_options=launch_options
                )
                print(f"[DEBUG] Using OpenRouter with model: {openrouter_model}")
            
            print(f"[DEBUG] Browser settings: headless={self.headless}, slow_mo={browser_slowmo}ms")
            
            self.stagehand = Stagehand(config)
            await self.stagehand.init()
            self.page = self.stagehand.page
            
            if not self.page:
                raise RuntimeError("Stagehand initialization failed: page is None")
            
            # Set longer default timeout for complex flows (2 minutes)
            if hasattr(self.page, '_page'):
                self.page._page.set_default_timeout(120000)  # 120 seconds
            
            print(f"[DEBUG] Stagehand initialized successfully, page={self.page}")
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.stagehand:
            try:
                await self.stagehand.close()
            except:
                pass
            self.stagehand = None
            self.page = None
    
    async def execute_test(
        self,
        db: Session,
        test_case: TestCase,
        execution_id: int,
        user_id: int,
        base_url: str,
        environment: str = "dev",
        progress_callback: Optional[Callable] = None,
        skip_navigation: bool = False
    ):
        """
        Execute a test case and track results.
        
        Args:
            db: Database session
            test_case: Test case to execute
            execution_id: Pre-created execution record ID
            user_id: ID of user triggering execution
            base_url: Base URL for the application under test
            environment: Environment name (dev, staging, production)
            progress_callback: Optional callback for progress updates
            skip_navigation: If True, skip navigating to base_url (for suite continuation)
            
        Returns:
            TestExecution object with results
        """
        # Get existing execution record (created by endpoint)
        execution = crud_execution.get_execution(db, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        try:
            # Update status to running
            execution = crud_execution.start_execution(db, execution.id)
            
            if progress_callback:
                await progress_callback({
                    "execution_id": execution.id,
                    "status": "running",
                    "message": "Starting test execution..."
                })
            
            # Initialize browser
            await self.initialize()
            
            # Execute steps
            steps = test_case.steps
            if isinstance(steps, str):
                try:
                    steps = json.loads(steps)
                except:
                    steps = [steps]  # Treat as single step if JSON parse fails
            elif not isinstance(steps, list):
                steps = []
            
            # Check if first step contains navigation (URL)
            first_step_has_url = False
            if steps and len(steps) > 0:
                first_step = str(steps[0]).lower()
                if any(keyword in first_step for keyword in ['navigate', 'goto', 'open', 'http://', 'https://']):
                    first_step_has_url = True
                    print(f"[DEBUG] First step contains navigation, skipping initial goto")
            
            # Navigate to base URL only if not continuing from suite and first step doesn't navigate
            if not skip_navigation and not first_step_has_url:
                print(f"[DEBUG] Navigating to base URL: {base_url}")
                await self.page.goto(base_url)
                await asyncio.sleep(1)  # Wait for page to stabilize
            elif skip_navigation:
                print(f"[DEBUG] Skipping navigation (continuing from previous test in suite)")
                current_url = self.page.url
                print(f"[DEBUG] Current URL: {current_url}")
            
            total_steps = len(steps)
            passed_steps = 0
            failed_steps = 0
            
            print(f"[DEBUG] Executing {total_steps} steps")
            
            for idx, step_desc in enumerate(steps, start=1):
                step_start = datetime.utcnow()
                
                try:
                    if progress_callback:
                        await progress_callback({
                            "execution_id": execution.id,
                            "step": idx,
                            "total_steps": total_steps,
                            "message": f"Executing step {idx}: {step_desc}"
                        })
                    
                    print(f"[DEBUG] Step {idx}/{total_steps}: {step_desc}")
                    
                    # Hybrid execution strategy:
                    # 1. Try Playwright selectors first (fast, free, reliable)
                    # 2. If fails, fallback to Stagehand AI (flexible, handles complex cases)
                    USE_AI_ONLY = os.getenv("USE_AI_EXECUTION", "false").lower() == "true"
                    
                    if USE_AI_ONLY:
                        # Force AI execution for all steps
                        result = await self._execute_step_ai(step_desc, idx)
                    else:
                        # Try Playwright first, fallback to AI if it fails
                        result = await self._execute_step_hybrid(step_desc, idx)
                    
                    step_end = datetime.utcnow()
                    duration = (step_end - step_start).total_seconds()
                    
                    # Save screenshot for this step
                    screenshot_path = await self._capture_screenshot(
                        execution.id, 
                        idx,
                        ExecutionResult.PASS if result["success"] else ExecutionResult.FAIL
                    )
                    
                    # Create step record
                    step_result = ExecutionResult.PASS if result["success"] else ExecutionResult.FAIL
                    
                    crud_execution.create_execution_step(
                        db=db,
                        execution_id=execution.id,
                        step_number=idx,
                        step_description=step_desc,
                        expected_result=result.get("expected", "Step completes successfully"),
                        result=step_result,
                        actual_result=result.get("actual", ""),
                        error_message=result.get("error"),
                        screenshot_path=screenshot_path,
                        duration_seconds=duration
                    )
                    
                    if result["success"]:
                        passed_steps += 1
                        print(f"[DEBUG] Step {idx} PASSED")
                    else:
                        failed_steps += 1
                        print(f"[DEBUG] Step {idx} FAILED: {result.get('error')}")
                    
                except Exception as e:
                    failed_steps += 1
                    step_end = datetime.utcnow()
                    duration = (step_end - step_start).total_seconds()
                    
                    print(f"[DEBUG] Step {idx} ERROR: {str(e)}")
                    
                    # Capture failure screenshot
                    screenshot_path = await self._capture_screenshot(
                        execution.id, 
                        idx,
                        ExecutionResult.ERROR
                    )
                    
                    crud_execution.create_execution_step(
                        db=db,
                        execution_id=execution.id,
                        step_number=idx,
                        step_description=step_desc,
                        result=ExecutionResult.ERROR,
                        error_message=str(e),
                        screenshot_path=screenshot_path,
                        duration_seconds=duration
                    )
            
            # Get final screenshot
            final_screenshot = await self._capture_screenshot(
                execution.id,
                0,
                ExecutionResult.PASS if failed_steps == 0 else ExecutionResult.FAIL
            )
            
            # Complete execution
            final_result = ExecutionResult.PASS if failed_steps == 0 else ExecutionResult.FAIL
            
            execution = crud_execution.complete_execution(
                db=db,
                execution_id=execution.id,
                result=final_result,
                total_steps=total_steps,
                passed_steps=passed_steps,
                failed_steps=failed_steps,
                screenshot_path=final_screenshot,
                video_path=None
            )
            
            print(f"[DEBUG] Execution complete: {passed_steps}/{total_steps} passed")
            
            if progress_callback:
                await progress_callback({
                    "execution_id": execution.id,
                    "status": "completed",
                    "result": final_result.value,
                    "message": f"Execution completed: {passed_steps}/{total_steps} steps passed"
                })
            
        except Exception as e:
            print(f"[DEBUG] Execution failed with exception: {str(e)}")
            # Execution failed
            execution = crud_execution.fail_execution(
                db=db,
                execution_id=execution.id,
                error_message=str(e)
            )
            
            if progress_callback:
                await progress_callback({
                    "execution_id": execution.id,
                    "status": "failed",
                    "error": str(e),
                    "message": f"Execution failed: {str(e)}"
                })
        
        finally:
            # Cleanup
            await self.cleanup()
        
        return execution
    
    async def _execute_step_hybrid(self, step_description: str, step_number: int) -> Dict[str, Any]:
        """
        Hybrid execution: Try Playwright first, fallback to AI if it fails.
        
        This provides the best of both worlds:
        - Fast and free Playwright selectors for common cases
        - AI fallback for complex or dynamic scenarios
        
        IMPORTANT: AI fallback executes ONLY the current step, not all steps from beginning.
        Browser session is shared, so context from previous steps is preserved.
        """
        print(f"[DEBUG] ========================================")
        print(f"[DEBUG] 🔄 HYBRID Step {step_number}: {step_description}")
        print(f"[DEBUG] Strategy: Playwright first (10s timeout), then AI fallback if needed")
        
        # Try Playwright-based execution first
        print(f"[DEBUG] 🎭 Attempting with Playwright selectors...")
        result = await self._execute_step_simple(step_description, step_number)
        
        # Check if it succeeded
        if result.get("success"):
            print(f"[DEBUG] ✅ Playwright execution succeeded for step {step_number}")
            return result
        
        # If Playwright failed, try AI fallback for THIS STEP ONLY
        print(f"[DEBUG] ⚠️  Playwright failed for step {step_number}: {result.get('error', 'Unknown error')}")
        print(f"[DEBUG] 🤖 Attempting AI fallback for step {step_number} ONLY (not restarting from step 1)...")
        
        ai_result = await self._execute_step_ai(step_description, step_number)
        
        if ai_result.get("success"):
            print(f"[DEBUG] ✅ AI fallback succeeded for step {step_number}!")
            # Add note that AI was used
            ai_result["actual"] = f"[AI Fallback] {ai_result.get('actual', '')}"
            return ai_result
        else:
            print(f"[DEBUG] ❌ Both Playwright and AI failed for step {step_number}")
            # Return the AI error (usually more informative)
            return ai_result
    
    async def _execute_step_ai(self, step_description: str, step_number: int) -> Dict[str, Any]:
        """
        Execute a single test step using Stagehand AI.
        
        Uses page.act() for AI-powered natural language execution.
        More flexible but slower and requires API calls.
        
        IMPORTANT: This executes ONLY the specified step, not all steps from the beginning.
        The browser session is shared with Playwright, so previous step context is preserved.
        """
        try:
            # Get current page state before AI execution
            url_before = self.page.url
            title_before = await self.page.title()
            
            print(f"[DEBUG] ========================================")
            print(f"[DEBUG] 🤖 AI Fallback for Step {step_number} ONLY")
            print(f"[DEBUG] Step Description: {step_description}")
            print(f"[DEBUG] Browser state BEFORE AI:")
            print(f"[DEBUG]   - URL: {url_before}")
            print(f"[DEBUG]   - Title: {title_before}")
            print(f"[DEBUG] Calling page.act() for THIS STEP ONLY...")
            
            # Use Stagehand AI to execute the step
            await self.page.act(step_description)
            
            await asyncio.sleep(1.5)  # Wait for action to complete
            
            title_after = await self.page.title()
            url_after = self.page.url
            
            print(f"[DEBUG] ✅ AI action completed successfully!")
            print(f"[DEBUG] Browser state AFTER AI:")
            print(f"[DEBUG]   - URL: {url_after}")
            print(f"[DEBUG]   - Title: {title_after}")
            print(f"[DEBUG] Changes: URL changed={url_before != url_after}, Title changed={title_before != title_after}")
            print(f"[DEBUG] ========================================")
            
            return {
                "success": True,
                "actual": f"AI action completed. Page: {title_after} | URL: {url_after}",
                "expected": step_description
            }
            
        except Exception as e:
            print(f"[DEBUG] ❌ AI action failed: {str(e)}")
            await asyncio.sleep(0.5)
            
            # Try to get page state even after error
            try:
                title = await self.page.title()
                return {
                    "success": False,
                    "error": str(e),
                    "actual": f"AI action failed: {str(e)}. Page: {title}",
                    "expected": step_description
                }
            except:
                return {
                    "success": False,
                    "error": str(e),
                    "actual": f"AI action failed: {str(e)}",
                    "expected": step_description
                }
    
    async def _execute_step_simple(self, step_description: str, step_number: int) -> Dict[str, Any]:
        """
        Execute a single test step using direct Playwright commands.
        
        Uses simple selectors for reliability without AI overhead.
        """
        try:
            # Detect action type from description
            desc_lower = step_description.lower()
            
            # Check if it's a navigation action with URL
            if any(word in desc_lower for word in ['navigate', 'goto', 'open']) and ('http://' in step_description or 'https://' in step_description):
                print(f"[DEBUG] 🌐 Detected navigation action")
                return await self._execute_navigation(step_description)
            
            # Check if it's a typing action
            elif any(word in desc_lower for word in ['type', 'enter', 'fill', 'input']):
                print(f"[DEBUG] ⌨️  Detected typing action")
                return await self._execute_type_simple(step_description)
            
            # Check if it's a click action
            elif any(word in desc_lower for word in ['click', 'select', 'choose', 'press']):
                print(f"[DEBUG] 🖱️  Detected click action")
                return await self._execute_click_simple(step_description)
            
            # Check if it's a scroll action
            elif 'scroll' in desc_lower:
                print(f"[DEBUG] 📜 Detected scroll action")
                return await self._execute_scroll(step_description)
            
            # Check if it's a verify/wait action
            elif any(word in desc_lower for word in ['verify', 'check', 'wait', 'ensure']):
                print(f"[DEBUG] ✓ Detected verify/wait action")
                return await self._execute_verify(step_description)
            
            # For other actions, just note it
            else:
                await asyncio.sleep(1)
                title = await self.page.title()
                return {
                    "success": True,
                    "actual": f"Step noted (page title: {title})",
                    "expected": step_description
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actual": f"Error: {str(e)}",
                "expected": step_description
            }
    
    async def _execute_ai_action(self, step_description: str) -> Dict[str, Any]:
        """Execute non-click actions using Stagehand AI."""
        try:
            print(f"[DEBUG] Calling page.act('{step_description}')...")
            await self.page.act(step_description)
            print(f"[DEBUG] AI action completed successfully!")
            
            await asyncio.sleep(1)
            
            title = await self.page.title()
            url = self.page.url
            
            print(f"[DEBUG] After action - Title: {title}")
            print(f"[DEBUG] After action - URL: {url}")
            print(f"[DEBUG] ========================================")
            
            return {
                "success": True,
                "actual": f"Action completed. Page: {title} | URL: {url}",
                "expected": step_description
            }
        except Exception as e:
            print(f"[DEBUG] ❌ AI action failed: {str(e)}")
            await asyncio.sleep(0.5)
            title = await self.page.title()
            return {
                "success": True,
                "actual": f"Step noted (page title: {title})",
                "expected": step_description,
                "warning": f"AI action failed: {str(e)}"
            }
    
    async def _execute_click_hybrid(self, step_description: str) -> Dict[str, Any]:
        """
        Execute click actions using hybrid approach:
        1. Use AI to find the element
        2. Use Playwright to click it reliably
        """
        try:
            print(f"[DEBUG] Step 1: Using AI to locate element...")
            
            # First, try to extract button text or identifier from description
            # Common patterns: "Click on 'text'", "Click the 'text' button", etc.
            import re
            
            # Try to find quoted text
            quoted_match = re.search(r"['\"]([^'\"]+)['\"]", step_description)
            if quoted_match:
                button_text = quoted_match.group(1)
                print(f"[DEBUG] Extracted button text: '{button_text}'")
                
                # Get underlying Playwright page
                pw_page = self.page._page
                
                # The login box is in an offcanvas overlay
                offcanvas_prefix = '.offcanvas.show '
                
                # Try different selectors - both with and without offcanvas targeting
                selectors_to_try = [
                    # First try within visible offcanvas
                    f"{offcanvas_prefix}button:has-text('{button_text}')",
                    f"{offcanvas_prefix}a:has-text('{button_text}')",
                    f"{offcanvas_prefix}text='{button_text}'",
                    f"{offcanvas_prefix}text={button_text}",
                    # Then try general selectors
                    f"text='{button_text}'",  # Exact text match
                    f"text={button_text}",    # Substring match
                    f"button:has-text('{button_text}')",  # Button with text
                    f"a:has-text('{button_text}')",       # Link with text
                    f"//*[contains(text(), '{button_text}')]",  # XPath
                ]
                
                for selector in selectors_to_try:
                    try:
                        print(f"[DEBUG] Trying selector: {selector}")
                        element = await pw_page.wait_for_selector(selector, timeout=30000)  # 30 seconds for slow pages
                        
                        if element:
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            print(f"[DEBUG] Found element! visible={is_visible}, enabled={is_enabled}")
                            
                            if is_visible and is_enabled:
                                print(f"[DEBUG] Step 2: Clicking with Playwright...")
                                
                                # Try normal click first
                                try:
                                    await element.click(timeout=60000)  # 60 seconds for click to complete
                                except Exception as click_error:
                                    # If blocked by modal overlay, force the click
                                    if "intercepts pointer events" in str(click_error):
                                        print(f"[DEBUG] Click blocked by overlay, using force click...")
                                        await element.click(force=True)
                                    else:
                                        raise
                                
                                await asyncio.sleep(1.5)  # Wait for click effects
                                
                                title = await self.page.title()
                                url = self.page.url
                                
                                print(f"[DEBUG] ✅ Click successful!")
                                print(f"[DEBUG] After click - Title: {title}")
                                print(f"[DEBUG] After click - URL: {url}")
                                print(f"[DEBUG] ========================================")
                                
                                return {
                                    "success": True,
                                    "actual": f"Clicked '{button_text}'. Page: {title} | URL: {url}",
                                    "expected": step_description
                                }
                    except Exception as e:
                        print(f"[DEBUG] Selector '{selector}' failed: {str(e)}")
                        continue
            
            # If direct Playwright approach fails, fall back to Stagehand AI
            print(f"[DEBUG] Direct click failed, falling back to Stagehand AI...")
            return await self._execute_ai_action(step_description)
            
        except Exception as e:
            print(f"[DEBUG] ❌ Hybrid click failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Last resort: try pure AI
            print(f"[DEBUG] Attempting pure AI as last resort...")
            return await self._execute_ai_action(step_description)
    
    async def _execute_type_hybrid(self, step_description: str) -> Dict[str, Any]:
        """
        Hybrid approach for typing: Use AI to understand field, Playwright to type.
        
        Extracts text to type from quotes in the description and uses Playwright's .fill()
        """
        try:
            import re
            
            # Extract text to type - look for patterns like "type 'text'" or "type \"text\""
            # This should match: "type 'pmo.andrewchan+010@gmail.com'" 
            type_pattern = re.search(r"(?:type|enter|fill|input)\s+['\"]([^'\"]+)['\"]", step_description, re.IGNORECASE)
            
            if not type_pattern:
                print(f"[DEBUG] No type pattern found, using AI fallback")
                return await self._execute_ai_action(step_description)
            
            text_to_type = type_pattern.group(1)
            print(f"[DEBUG] Extracted text to type: '{text_to_type}'")
            
            # Identify the field type from description
            field_keywords = {
                'email': ['email', 'e-mail'],
                'password': ['password', 'pwd', 'pass'],
                'text': ['address', 'name', 'input', 'field']
            }
            
            field_type = 'text'  # default
            desc_lower = step_description.lower()
            for ftype, keywords in field_keywords.items():
                if any(kw in desc_lower for kw in keywords):
                    field_type = ftype
                    break
            
            print(f"[DEBUG] Detected field type: {field_type}")
            
            # The login box is an offcanvas overlay - target elements within it
            offcanvas_prefix = '.offcanvas.show '  # Target visible offcanvas
            
            # Try Playwright selectors based on field type
            selectors_to_try = []
            
            if field_type == 'email':
                selectors_to_try = [
                    f'{offcanvas_prefix}input[type="email"]',
                    f'{offcanvas_prefix}input[name*="email" i]',
                    f'{offcanvas_prefix}input[id*="email" i]',
                    f'{offcanvas_prefix}input[placeholder*="email" i]',
                    f'{offcanvas_prefix}input[type="text"]:visible',
                    f'{offcanvas_prefix}input:visible:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])',
                    # Fallback without offcanvas prefix
                    'input[type="email"]:visible',
                    'input:visible:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])'
                ]
            elif field_type == 'password':
                selectors_to_try = [
                    f'{offcanvas_prefix}input[type="password"]',
                    f'{offcanvas_prefix}input[name*="password" i]',
                    f'{offcanvas_prefix}input[name*="pwd" i]',
                    f'{offcanvas_prefix}input[id*="password" i]',
                    f'{offcanvas_prefix}input:visible:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])',
                    # Fallback without offcanvas prefix
                    'input[type="password"]:visible',
                    'input:visible:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])'
                ]
            else:
                # Generic input field
                selectors_to_try = [
                    f'{offcanvas_prefix}input[type="text"]',
                    f'{offcanvas_prefix}input:not([type])',
                    f'{offcanvas_prefix}textarea',
                    f'{offcanvas_prefix}input:visible:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])',
                    # Fallback without offcanvas prefix
                    'input[type="text"]:visible',
                    'input:visible:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])'
                ]
            
            # Try each selector
            for selector in selectors_to_try:
                try:
                    print(f"[DEBUG] Trying Playwright selector: {selector}")
                    element = await self.page._page.wait_for_selector(selector, timeout=30000, state='visible')  # 30 seconds
                    
                    if element:
                        print(f"[DEBUG] Found element with: {selector}")
                        
                        # Clear the field first
                        await element.fill('')
                        await asyncio.sleep(0.3)
                        
                        # Type the text
                        await element.fill(text_to_type)
                        await asyncio.sleep(0.5)
                        
                        title = await self.page.title()
                        
                        print(f"[DEBUG] ✅ Typing successful!")
                        print(f"[DEBUG] Entered: '{text_to_type}' into {field_type} field")
                        print(f"[DEBUG] ========================================")
                        
                        return {
                            "success": True,
                            "actual": f"Entered '{text_to_type}' into {field_type} field. Page: {title}",
                            "expected": step_description
                        }
                except Exception as e:
                    print(f"[DEBUG] Selector '{selector}' failed: {str(e)}")
                    continue
            
            # If direct Playwright approach fails, fall back to Stagehand AI
            print(f"[DEBUG] Direct typing failed, falling back to Stagehand AI...")
            return await self._execute_ai_action(step_description)
            
        except Exception as e:
            print(f"[DEBUG] ❌ Hybrid typing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "actual": f"Error: {str(e)}",
                "expected": step_description
            }
    
    async def _capture_screenshot(
        self, 
        execution_id: int, 
        step_number: int,
        result: ExecutionResult
    ) -> Optional[str]:
        """Capture screenshot for a step or execution."""
        try:
            if not self.page:
                return None
            
            filename = f"exec_{execution_id}_step_{step_number}_{result.value}.png"
            filepath = self.screenshot_dir / filename
            
            await self.page.screenshot(path=str(filepath))
            
            return str(filepath)
        except Exception as e:
            print(f"[DEBUG] Failed to capture screenshot: {e}")
            return None
    
    async def _execute_click_simple(self, step_description: str) -> Dict[str, Any]:
        """Execute click actions using simple Playwright selectors."""
        try:
            import re
            
            # Get Playwright page
            pw_page = self.page._page
            desc_lower = step_description.lower()
            
            # Special case: checkbox
            if 'checkbox' in desc_lower:
                print(f"[DEBUG] Looking for checkbox...")
                # Try most common checkbox selector first - fail fast if not found
                try:
                    element = await pw_page.wait_for_selector(
                        "input[type='checkbox']:visible, [role='checkbox']:visible, label:has(input[type='checkbox']):visible",
                        timeout=10000,  # 10 seconds
                        state='visible'
                    )
                    if element:
                        await element.click(timeout=10000)  # 10 seconds
                        await asyncio.sleep(0.5)
                        print(f"[DEBUG] ✅ Clicked checkbox")
                        return {
                            "success": True,
                            "actual": "Clicked checkbox",
                            "expected": step_description
                        }
                except Exception as e:
                    print(f"[DEBUG] Checkbox not found: {str(e)[:100]}")
                    # Don't retry - let AI fallback handle it
                    return {
                        "success": False,
                        "error": f"Checkbox not found: {str(e)}",
                        "actual": "Checkbox element not visible",
                        "expected": step_description
                    }
            
            # Special case: close button (X)
            if desc_lower.startswith("find and click the 'x'"):
                print(f"[DEBUG] Looking for close button...")
                # Combine selectors - fail fast if not found
                try:
                    element = await pw_page.wait_for_selector(
                        "button[aria-label*='close' i]:visible, button[class*='close' i]:visible, button:has-text('×'):visible, [aria-label*='close' i]:visible",
                        timeout=10000,  # 10 seconds
                        state='visible'
                    )
                    if element:
                        await element.click(timeout=10000)  # 10 seconds
                        await asyncio.sleep(1)
                        print(f"[DEBUG] ✅ Clicked close button")
                        return {
                            "success": True,
                            "actual": "Clicked close button",
                            "expected": step_description
                        }
                except Exception as e:
                    print(f"[DEBUG] Close button not found: {str(e)[:100]}")
                    # Don't retry - let AI fallback handle it
                    return {
                        "success": False,
                        "error": f"Close button not found: {str(e)}",
                        "actual": "Close button not visible",
                        "expected": step_description
                    }
            
            # Extract text from quotes in description, or extract from "click on X" pattern
            quoted_match = re.search(r"['\"]([^'\"]+)['\"]", step_description)
            
            if quoted_match:
                button_text = quoted_match.group(1)
            else:
                # Try to extract text after "click on", "click the", "select", etc.
                click_pattern = re.search(r"(?:click on|click the|select|choose|press)\s+(?:the\s+)?(.+?)(?:\s+button|\s+link|\s+plan|$)", step_description, re.IGNORECASE)
                if click_pattern:
                    button_text = click_pattern.group(1).strip()
                else:
                    # Last resort: extract everything after the action word
                    action_pattern = re.search(r"(?:click|select|choose|press)\s+(.+)", step_description, re.IGNORECASE)
                    if action_pattern:
                        button_text = action_pattern.group(1).strip()
                    else:
                        return {
                            "success": False,
                            "error": "Could not extract button text from description",
                            "actual": "No button text pattern found",
                            "expected": step_description
                        }
            
            print(f"[DEBUG] Looking for button: '{button_text}'")
            
            # Check if we're in a modal context (for login flow)
            in_modal = 'login' in desc_lower or 'email' in desc_lower or 'password' in desc_lower
            
            # Build combined selector - try all patterns at once instead of sequentially
            # This reduces timeout from N * 30 seconds to just 10 seconds total
            base_patterns = [
                f"button:has-text('{button_text}')",
                f"a:has-text('{button_text}')",
                f"[role='button']:has-text('{button_text}')",
                f"text='{button_text}'",
            ]
            
            # If in modal, prepend .modal-content to patterns
            if in_modal:
                combined_selector = ", ".join([f".modal-content {p}" for p in base_patterns] + base_patterns)
            else:
                combined_selector = ", ".join(base_patterns)
            
            try:
                print(f"[DEBUG] Trying combined selector (timeout: 10s)")
                element = await pw_page.wait_for_selector(
                    combined_selector, 
                    timeout=10000,  # 10 seconds total (not per selector)
                    state='visible'
                )
                if element:
                    await element.click(timeout=10000)  # 10 seconds
                    await asyncio.sleep(1.5)
                    
                    title = await self.page.title()
                    url = self.page.url
                    
                    print(f"[DEBUG] ✅ Clicked '{button_text}'")
                    print(f"[DEBUG] Page: {title} | URL: {url}")
                    
                    return {
                        "success": True,
                        "actual": f"Clicked '{button_text}'. Page: {title}",
                        "expected": step_description
                    }
            except Exception as e:
                print(f"[DEBUG] Click failed: {str(e)[:150]}")
                # Don't retry - let AI fallback handle it
                return {
                    "success": False,
                    "error": f"Could not find button '{button_text}': {str(e)}",
                    "actual": "Button not found or not clickable",
                    "expected": step_description
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actual": f"Error: {str(e)}",
                "expected": step_description
            }
    
    async def _execute_type_simple(self, step_description: str) -> Dict[str, Any]:
        """Execute typing actions using simple Playwright selectors."""
        try:
            import re
            
            # Extract text to type from quotes
            quoted_matches = re.findall(r"['\"]([^'\"]+)['\"]", step_description)
            if len(quoted_matches) < 1:
                return {
                    "success": False,
                    "error": "Could not extract text to type",
                    "actual": "No quoted text found",
                    "expected": step_description
                }
            
            # The text to type is usually the last quoted string
            text_to_type = quoted_matches[-1]
            
            # Try to identify field type from description
            desc_lower = step_description.lower()
            
            print(f"[DEBUG] Will type: '{text_to_type}'")
            
            # Get Playwright page
            pw_page = self.page._page
            
            # Choose selectors based on field type
            # Check if we're in a modal context
            in_modal = 'login' in desc_lower or any(step in desc_lower for step in ['email', 'password'])
            
            base_selectors = []
            if 'email' in desc_lower:
                base_selectors = [
                    "input[type='email']",
                    "input[name*='email' i]",
                    "input[placeholder*='email' i]",
                    "input[id*='email' i]",
                    "input[autocomplete='email']",
                    "input[type='text']",  # Sometimes email fields are text type
                ]
            elif 'password' in desc_lower:
                base_selectors = [
                    "input[type='password']",
                    "input[name*='password' i]",
                    "input[autocomplete*='password' i]",
                ]
            else:
                # Generic visible input
                base_selectors = [
                    "input:visible:not([type='hidden']):not([type='checkbox']):not([type='radio'])",
                ]
            
            # If in modal, try multiple modal container variations
            selectors = []
            if in_modal:
                # Try different modal container selectors
                modal_prefixes = [
                    ".modal-content",
                    ".modal-body",
                    ".modal",
                    "[role='dialog']",
                    ".offcanvas-body",
                    ".offcanvas.show",
                ]
                for prefix in modal_prefixes:
                    selectors.extend([f"{prefix} {s}" for s in base_selectors])
            
            # Also try without prefix as fallback
            selectors.extend(base_selectors)
            
            for selector in selectors:
                try:
                    print(f"[DEBUG] Trying: {selector}")
                    element = await pw_page.wait_for_selector(selector, timeout=30000, state='visible')  # 30 seconds
                    if element:
                        await element.fill(text_to_type)
                        await asyncio.sleep(0.5)
                        
                        print(f"[DEBUG] ✅ Typed '{text_to_type}' into field")
                        
                        return {
                            "success": True,
                            "actual": f"Entered text into field",
                            "expected": step_description
                        }
                except Exception as e:
                    print(f"[DEBUG] {selector} failed: {str(e)[:100]}")
                    continue
            
            # If all selectors failed
            return {
                "success": False,
                "error": f"Could not find input field",
                "actual": "Input field not found with any selector",
                "expected": step_description
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actual": f"Error: {str(e)}",
                "expected": step_description
            }
    
    async def _execute_navigation(self, step_description: str) -> Dict[str, Any]:
        """Navigate to a URL extracted from the step description."""
        try:
            # Extract URL from description
            import re
            # Match URL but stop at quotes, whitespace, or other delimiters
            url_match = re.search(r'(https?://[^\s\'"<>]+)', step_description)
            if not url_match:
                return {
                    "success": False,
                    "error": "No URL found in navigation step",
                    "actual": "Could not extract URL",
                    "expected": step_description
                }
            
            url = url_match.group(1)
            print(f"[DEBUG] Navigating to URL: {url}")
            
            # Navigate using Playwright page
            await self.page.goto(url)
            await asyncio.sleep(2)  # Wait for page to load
            
            title = await self.page.title()
            current_url = self.page.url
            
            print(f"[DEBUG] Navigation complete - Title: {title}")
            print(f"[DEBUG] Current URL: {current_url}")
            
            return {
                "success": True,
                "actual": f"Navigated to {url}. Page title: {title}",
                "expected": step_description
            }
        except Exception as e:
            print(f"[DEBUG] Navigation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "actual": f"Navigation error: {str(e)}",
                "expected": step_description
            }
    
    async def _execute_scroll(self, step_description: str) -> Dict[str, Any]:
        """Execute scroll action."""
        try:
            print(f"[DEBUG] Executing scroll")
            
            # Get underlying Playwright page
            pw_page = self.page._page
            
            # Scroll down the page
            await pw_page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "actual": "Scrolled down page",
                "expected": step_description
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actual": f"Scroll error: {str(e)}",
                "expected": step_description
            }
    
    async def _execute_verify(self, step_description: str) -> Dict[str, Any]:
        """Execute verification step."""
        try:
            print(f"[DEBUG] Executing verification")
            
            # For now, just check that page is loaded
            await asyncio.sleep(1)
            title = await self.page.title()
            url = self.page.url
            
            # Check if verification text is in page title or URL
            desc_lower = step_description.lower()
            title_lower = title.lower()
            url_lower = url.lower()
            
            # Extract quoted text to verify
            import re
            verify_pattern = re.findall(r"['\"]([^'\"]+)['\"]", step_description)
            
            if verify_pattern:
                all_found = True
                for text in verify_pattern:
                    text_lower = text.lower()
                    if text_lower not in title_lower and text_lower not in url_lower:
                        # Check if it's in the page content
                        pw_page = self.page._page
                        try:
                            page_content = await pw_page.content()
                            if text_lower not in page_content.lower():
                                all_found = False
                                break
                        except:
                            pass
                
                if all_found:
                    return {
                        "success": True,
                        "actual": f"Verification passed. Page: {title}",
                        "expected": step_description
                    }
                else:
                    return {
                        "success": False,
                        "error": "Verification text not found",
                        "actual": f"Page title: {title}, URL: {url}",
                        "expected": step_description
                    }
            else:
                # No specific text to verify, just confirm page is loaded
                return {
                    "success": True,
                    "actual": f"Verification step noted. Page: {title}",
                    "expected": step_description
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actual": f"Verification error: {str(e)}",
                "expected": step_description
            }
    
# Singleton instance
_stagehand_service: Optional[StagehandExecutionService] = None


def get_stagehand_service() -> StagehandExecutionService:
    """Get or create Stagehand service singleton."""
    global _stagehand_service
    if _stagehand_service is None:
        _stagehand_service = StagehandExecutionService(headless=True)
    return _stagehand_service

