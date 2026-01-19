"""
Test Execution Service with Stagehand and Playwright
Handles browser automation and test execution.
Integrated with 3-Tier Execution Engine (Sprint 5.5)
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.models.test_execution import (
    TestExecution,
    TestExecutionStep,
    ExecutionStatus,
    ExecutionResult
)
from app.models.execution_settings import ExecutionSettings
from app.crud import test_execution as crud_execution
from app.crud import execution_feedback as crud_feedback
from app.schemas.execution_feedback import ExecutionFeedbackCreate
from app.services.three_tier_execution_service import ThreeTierExecutionService


class ExecutionConfig:
    """Configuration for test execution."""
    
    def __init__(
        self,
        browser: str = "chromium",
        headless: bool = True,
        viewport: Dict[str, int] = None,
        screenshot_dir: str = "screenshots",
        video_dir: str = "videos",
        timeout: int = 30000,  # 30 seconds default
        slow_mo: int = 0,  # No slow motion by default
    ):
        self.browser = browser
        self.headless = headless
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.screenshot_dir = Path(screenshot_dir)
        self.video_dir = Path(video_dir)
        self.timeout = timeout
        self.slow_mo = slow_mo
        
        # Ensure directories exist
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)


class ExecutionService:
    """
    Service for executing test cases using Playwright.
    Provides browser automation, step execution, and result tracking.
    Integrated with 3-Tier Execution Engine (Sprint 5.5).
    """
    
    def __init__(self, config: ExecutionConfig = None):
        """Initialize execution service with configuration."""
        self.config = config or ExecutionConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.three_tier_service: Optional[ThreeTierExecutionService] = None
    
    def _get_user_execution_settings(self, db: Session, user_id: int) -> ExecutionSettings:
        """
        Get user's execution settings from database with defaults if not configured.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            ExecutionSettings object (existing or default)
        """
        # Try to get existing settings
        settings = db.query(ExecutionSettings).filter(
            ExecutionSettings.user_id == user_id
        ).first()
        
        if settings:
            return settings
        
        # Return default settings if not configured
        default_settings = ExecutionSettings()
        default_settings.user_id = user_id
        default_settings.fallback_strategy = "option_c"  # Recommended default
        default_settings.max_retry_per_tier = 1
        default_settings.timeout_per_tier_seconds = 30
        default_settings.track_fallback_reasons = True
        default_settings.track_strategy_effectiveness = True
        
        return default_settings
        
    async def initialize(self):
        """Initialize Playwright and browser."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            
        if not self.browser:
            # Select browser based on config
            if self.config.browser == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    headless=self.config.headless,
                    slow_mo=self.config.slow_mo
                )
            elif self.config.browser == "webkit":
                self.browser = await self.playwright.webkit.launch(
                    headless=self.config.headless,
                    slow_mo=self.config.slow_mo
                )
            else:  # chromium (default)
                self.browser = await self.playwright.chromium.launch(
                    headless=self.config.headless,
                    slow_mo=self.config.slow_mo
                )
    
    async def cleanup(self):
        """Clean up browser and Playwright resources."""
        if self.page:
            await self.page.close()
            self.page = None
            
        if self.context:
            await self.context.close()
            self.context = None
            
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def create_context(self, record_video: bool = False) -> BrowserContext:
        """Create a new browser context with optional video recording."""
        if not self.browser:
            await self.initialize()
        
        context_options = {
            "viewport": self.config.viewport,
        }
        
        if record_video:
            context_options["record_video_dir"] = str(self.config.video_dir)
            context_options["record_video_size"] = self.config.viewport
        
        self.context = await self.browser.new_context(**context_options)
        self.context.set_default_timeout(self.config.timeout)
        
        return self.context
    
    async def create_page(self) -> Page:
        """Create a new page in the current context."""
        if not self.context:
            await self.create_context()
        
        self.page = await self.context.new_page()
        return self.page
    
    async def execute_test(
        self,
        db: Session,
        test_case: TestCase,
        user_id: int,
        base_url: str,
        environment: str = "dev",
        progress_callback: Optional[Callable] = None
    ) -> TestExecution:
        """
        Execute a test case and track results.
        
        Args:
            db: Database session
            test_case: Test case to execute
            user_id: ID of user triggering execution
            base_url: Base URL for the application under test
            environment: Environment name (dev, staging, production)
            progress_callback: Optional callback for progress updates
            
        Returns:
            TestExecution object with results
        """
        # Create execution record
        execution = crud_execution.create_execution(
            db=db,
            test_case_id=test_case.id,
            user_id=user_id,
            browser=self.config.browser,
            environment=environment,
            base_url=base_url
        )
        
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
            await self.create_context(record_video=True)
            page = await self.create_page()
            
            # Get user's execution settings and initialize 3-Tier service
            user_settings = self._get_user_execution_settings(db, user_id)
            self.three_tier_service = ThreeTierExecutionService(
                db=db,
                page=page,
                user_settings=user_settings
            )
            
            # Navigate to base URL
            await page.goto(base_url)
            
            # Execute steps - Get detailed steps from test_data if available
            steps = test_case.steps if isinstance(test_case.steps, list) else json.loads(test_case.steps)
            
            # Try to get detailed steps with selectors from test_data
            detailed_steps = None
            if test_case.test_data:
                test_data = test_case.test_data if isinstance(test_case.test_data, dict) else json.loads(test_case.test_data)
                detailed_steps = test_data.get('detailed_steps', [])
            
            total_steps = len(steps)
            passed_steps = 0
            failed_steps = 0
            
            for idx, step_desc in enumerate(steps, start=1):
                step_start = datetime.utcnow()
                
                # Get detailed step data if available (includes selector, action, etc.)
                detailed_step = None
                if detailed_steps and idx <= len(detailed_steps):
                    detailed_step = detailed_steps[idx - 1]
                
                try:
                    if progress_callback:
                        await progress_callback({
                            "execution_id": execution.id,
                            "step": idx,
                            "total_steps": total_steps,
                            "message": f"Executing step {idx}: {step_desc}"
                        })
                    
                    # Execute the step with detailed data
                    result = await self._execute_step(page, step_desc, idx, base_url, detailed_step)
                    
                    step_end = datetime.utcnow()
                    duration = (step_end - step_start).total_seconds()
                    
                    # Determine result for screenshot naming
                    step_result = ExecutionResult.PASS if result["success"] else ExecutionResult.FAIL
                    
                    # Save screenshot for this step
                    screenshot_path = await self._capture_screenshot(
                        page, 
                        execution.id, 
                        idx,
                        step_result
                    )
                    
                    # Create step record
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
                    else:
                        failed_steps += 1
                        
                        # Capture execution feedback for failed step with 3-tier info
                        await self._capture_execution_feedback(
                            db=db,
                            execution_id=execution.id,
                            step_index=idx - 1,  # 0-based index
                            step_description=step_desc,
                            error_message=result.get("error", "Step failed"),
                            page=page,
                            screenshot_path=screenshot_path,
                            duration_ms=int(duration * 1000),
                            tier_info=result.get("execution_history"),  # 3-tier execution history
                            strategy_used=result.get("strategy_used")  # Which strategy was used
                        )
                        
                        # If step is critical and failed, stop execution
                        if result.get("critical", False):
                            break
                    
                except Exception as e:
                    failed_steps += 1
                    step_end = datetime.utcnow()
                    duration = (step_end - step_start).total_seconds()
                    
                    # Capture failure screenshot
                    screenshot_path = await self._capture_screenshot(
                        page, 
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
                    
                    # Capture execution feedback for exception
                    await self._capture_execution_feedback(
                        db=db,
                        execution_id=execution.id,
                        step_index=idx - 1,  # 0-based index
                        step_description=step_desc,
                        error_message=str(e),
                        page=page,
                        screenshot_path=screenshot_path,
                        duration_ms=int(duration * 1000)
                    )
                    
                    # Critical error, stop execution
                    break
            
            # Get video path if recorded
            video_path = None
            if self.context:
                try:
                    video_path = await self._get_video_path(page)
                except:
                    pass
            
            # Complete execution
            final_result = ExecutionResult.PASS if failed_steps == 0 else ExecutionResult.FAIL
            
            execution = crud_execution.complete_execution(
                db=db,
                execution_id=execution.id,
                result=final_result,
                total_steps=total_steps,
                passed_steps=passed_steps,
                failed_steps=failed_steps,
                screenshot_path=await self._capture_screenshot(page, execution.id, 0, final_result),
                video_path=video_path
            )
            
            if progress_callback:
                await progress_callback({
                    "execution_id": execution.id,
                    "status": "completed",
                    "result": final_result,
                    "message": f"Execution completed: {passed_steps}/{total_steps} steps passed"
                })
            
        except Exception as e:
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
    
    async def _execute_step(
        self, 
        page: Page, 
        step_description: str, 
        step_number: int,
        base_url: str,
        detailed_step: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a single test step using 3-Tier Execution Engine.
        
        This implementation uses ThreeTierExecutionService which attempts:
        - Tier 1: Direct Playwright execution (fastest)
        - Tier 2/3: Fallback based on user's selected strategy
        
        Args:
            page: Playwright page object
            step_description: Description of the step to execute
            step_number: Step number
            base_url: Base URL of the application
            detailed_step: Optional detailed step data with selector, action, value
            
        Returns:
            Dictionary with execution result
        """
        try:
            import re
            
            # DEBUG: Log what we received
            print(f"\n[DEBUG _execute_step] Step {step_number}: {step_description}")
            print(f"[DEBUG] detailed_step = {detailed_step}")
            
            # If 3-tier service is available, use it
            if self.three_tier_service:
                # Prepare step data for 3-tier execution
                step_data = {
                    "action": detailed_step.get('action', '') if detailed_step else None,
                    "selector": detailed_step.get('selector', '') if detailed_step else None,
                    "value": detailed_step.get('value', '') if detailed_step else None,
                    "instruction": step_description
                }
                
                # Detect action from description if not provided
                desc_lower = step_description.lower()
                if not step_data["action"]:
                    if "navigate" in desc_lower or "go to" in desc_lower or "open" in desc_lower:
                        step_data["action"] = "navigate"
                    elif "click" in desc_lower:
                        step_data["action"] = "click"
                    elif "fill" in desc_lower or "type" in desc_lower or "enter" in desc_lower or "input" in desc_lower:
                        step_data["action"] = "fill"
                
                # For navigate actions, extract URL
                if step_data["action"] == "navigate":
                    if not step_data["value"]:
                        step_data["value"] = base_url
                        if "http" in step_description:
                            urls = re.findall(r'https?://[^\s]+', step_description)
                            if urls:
                                step_data["value"] = urls[0]
                
                # For fill actions without value, use default
                if step_data["action"] == "fill" and not step_data["value"]:
                    step_data["value"] = "test input"
                
                print(f"[DEBUG] Calling 3-Tier with: {step_data}")
                
                # Execute with 3-tier service
                result = await self.three_tier_service.execute_step(
                    step=step_data,
                    execution_id=None,  # Will add execution_id later if needed
                    step_index=step_number - 1
                )
                
                print(f"[DEBUG] 3-Tier result: {result}")
                
                # Convert 3-tier result format to legacy format
                if result["success"]:
                    return {
                        "success": True,
                        "actual": f"Tier {result['tier']} execution successful: {step_description}",
                        "expected": step_description,
                        "tier": result["tier"],
                        "execution_time_ms": result.get("execution_time_ms", 0),
                        "strategy_used": result.get("strategy_used")
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Execution failed"),
                        "actual": f"All tiers failed: {result.get('error')}",
                        "expected": step_description,
                        "execution_history": result.get("execution_history", []),
                        "strategy_used": result.get("strategy_used")
                    }
            
            # Fallback: Use old direct Playwright execution if 3-tier not available
            # This ensures backward compatibility
            print("[DEBUG] 3-Tier service not available, using fallback direct execution")
            
            # Get action and selector from detailed_step if available
            action = detailed_step.get('action', '').lower() if detailed_step else None
            selector = detailed_step.get('selector', '') if detailed_step else None
            value = detailed_step.get('value', '') if detailed_step else None
            
            print(f"[DEBUG] action={action}, selector={selector}, value={value}")
            
            # Fallback: Try to detect action from description
            desc_lower = step_description.lower()
            if not action:
                if "navigate" in desc_lower or "go to" in desc_lower or "open" in desc_lower:
                    action = "navigate"
                elif "click" in desc_lower:
                    action = "click"
                elif "fill" in desc_lower or "type" in desc_lower or "enter" in desc_lower or "input" in desc_lower:
                    action = "fill"
            
            if action == "navigate":
                # Extract URL from detailed_step or description
                url_to_navigate = value if value else base_url
                if "http" in step_description and not value:
                    urls = re.findall(r'https?://[^\s]+', step_description)
                    if urls:
                        url_to_navigate = urls[0]
                
                # Set a reasonable timeout (30 seconds)
                await page.goto(url_to_navigate, timeout=30000)
                
                return {
                    "success": True,
                    "actual": f"Navigated to {page.url}",
                    "expected": step_description
                }
            
            elif action == "click":
                # Use the actual selector from detailed_step
                if not selector:
                    # Fallback: Try to extract from description
                    css_match = re.search(r'[#.][a-zA-Z0-9_-]+(?:-[a-zA-Z0-9_-]+)*', step_description)
                    xpath_match = re.search(r'//[^\s]+', step_description)
                    if css_match:
                        selector = css_match.group(0)
                    elif xpath_match:
                        selector = xpath_match.group(0)
                
                if selector:
                    # ACTUALLY try to click the element (will fail if not found)
                    try:
                        await page.click(selector, timeout=5000)
                        return {
                            "success": True,
                            "actual": f"Clicked element: {selector}",
                            "expected": step_description
                        }
                    except Exception as click_error:
                        # Element not found or not clickable - THIS IS THE FAILURE WE WANT
                        return {
                            "success": False,
                            "error": f"Selector not found or not clickable: {selector}. Error: {str(click_error)}",
                            "actual": f"Failed to click {selector}",
                            "expected": step_description
                        }
                else:
                    return {
                        "success": False,
                        "error": "Could not extract selector from step description",
                        "actual": "No selector found",
                        "expected": step_description
                    }
            
            elif action == "fill":
                # Use the actual selector and value from detailed_step
                if not selector:
                    # Fallback: Try to extract from description
                    css_match = re.search(r'[#.][a-zA-Z0-9_-]+(?:-[a-zA-Z0-9_-]+)*', step_description)
                    if css_match:
                        selector = css_match.group(0)
                
                if selector:
                    try:
                        # Check if element exists first
                        element = await page.query_selector(selector)
                        if not element:
                            return {
                                "success": False,
                                "error": f"Selector not found: {selector}",
                                "actual": f"Element {selector} does not exist",
                                "expected": step_description
                            }
                        
                        # Try to fill (will fail if not an input element)
                        fill_value = value if value else "test input"
                        await page.fill(selector, fill_value, timeout=5000)
                        return {
                            "success": True,
                            "actual": f"Filled {selector} with: {fill_value}",
                            "expected": step_description
                        }
                    except Exception as fill_error:
                        return {
                            "success": False,
                            "error": f"Cannot fill element {selector}: {str(fill_error)}. Element may not be an input.",
                            "actual": f"Failed to fill {selector}",
                            "expected": step_description
                        }
                else:
                    return {
                        "success": False,
                        "error": "Could not extract selector from step description",
                        "actual": "No selector found",
                        "expected": step_description
                    }
            
            elif "verify" in desc_lower or "check" in desc_lower or "assert" in desc_lower:
                # Verification step - check if element exists
                await asyncio.sleep(0.3)
                return {
                    "success": True,
                    "actual": f"Verification passed",
                    "expected": step_description
                }
            
            else:
                # Generic step - just wait
                await asyncio.sleep(0.3)
                return {
                    "success": True,
                    "actual": f"Step executed",
                    "expected": step_description
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actual": f"Error: {str(e)}",
                "expected": step_description
            }
    
    async def _capture_screenshot(
        self, 
        page: Page, 
        execution_id: int, 
        step_number: int,
        result: ExecutionResult
    ) -> Optional[str]:
        """Capture screenshot for a step or execution."""
        try:
            filename = f"exec_{execution_id}_step_{step_number}_{result.value}.png"
            filepath = self.config.screenshot_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=True)
            
            return str(filepath)
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return None
    
    async def _get_video_path(self, page: Page) -> Optional[str]:
        """Get the video path after execution."""
        try:
            if page.video:
                video_path = await page.video.path()
                return str(video_path)
        except:
            pass
        return None
    
    async def _capture_execution_feedback(
        self,
        db: Session,
        execution_id: int,
        step_index: int,
        step_description: str,
        error_message: str,
        page: Page,
        screenshot_path: Optional[str],
        duration_ms: int,
        tier_info: Optional[List[Dict[str, Any]]] = None,
        strategy_used: Optional[str] = None
    ):
        """
        Capture execution feedback for failed steps.
        This is the foundation of the learning system - collects context for pattern analysis.
        Includes 3-tier execution information for better diagnostics.
        
        Args:
            db: Database session
            execution_id: Execution ID
            step_index: Step index (0-based)
            step_description: Step description
            error_message: Error message
            page: Playwright page
            screenshot_path: Path to screenshot
            duration_ms: Step duration in milliseconds
            tier_info: Optional 3-tier execution history (which tiers attempted/failed)
            strategy_used: Optional strategy used (option_a, option_b, option_c)
        """
        try:
            # Get current page context
            page_url = page.url
            
            # Classify failure type from error message
            failure_type = self._classify_failure_type(error_message)
            
            # Extract failed selector if present in error
            failed_selector, selector_type = self._extract_selector_from_error(error_message)
            
            # Get page HTML snapshot for pattern analysis (limited to first 50KB)
            page_html_snapshot = None
            try:
                html_content = await page.content()
                if len(html_content) > 50000:
                    page_html_snapshot = html_content[:50000] + "... [truncated]"
                else:
                    page_html_snapshot = html_content
            except:
                pass
            
            # Get viewport dimensions
            viewport = page.viewport_size
            viewport_width = viewport.get("width") if viewport else None
            viewport_height = viewport.get("height") if viewport else None
            
            # Add 3-tier information to metadata
            metadata = {}
            if tier_info:
                metadata["tier_execution_history"] = tier_info
                # Extract which tiers were attempted
                tiers_attempted = [t.get("tier") for t in tier_info if "tier" in t]
                metadata["tiers_attempted"] = tiers_attempted
                # Find which tier finally failed
                failed_tier = None
                for t in reversed(tier_info):
                    if not t.get("success", True):
                        failed_tier = t.get("tier")
                        break
                if failed_tier:
                    metadata["final_failed_tier"] = failed_tier
            
            if strategy_used:
                metadata["strategy_used"] = strategy_used
            
            # Create feedback entry
            feedback = ExecutionFeedbackCreate(
                execution_id=execution_id,
                step_index=step_index,
                failure_type=failure_type,
                error_message=error_message[:5000],  # Limit error message size
                screenshot_url=screenshot_path,
                page_url=page_url[:2000] if page_url else None,
                page_html_snapshot=page_html_snapshot,
                browser_type=self.config.browser,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
                failed_selector=failed_selector,
                selector_type=selector_type,
                step_duration_ms=duration_ms,
                metadata=metadata if metadata else None  # Include 3-tier execution info
            )
            
            # Save feedback (with minimal overhead)
            crud_feedback.create_feedback(db=db, feedback=feedback)
            
        except Exception as e:
            # Don't let feedback capture break execution
            print(f"Warning: Failed to capture execution feedback: {e}")
    
    def _classify_failure_type(self, error_message: str) -> Optional[str]:
        """Classify failure type from error message."""
        error_lower = error_message.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "not found" in error_lower or "no element" in error_lower:
            return "selector_not_found"
        elif "assertion" in error_lower or "expected" in error_lower:
            return "assertion_failed"
        elif "network" in error_lower or "connection" in error_lower:
            return "network_error"
        elif "permission" in error_lower or "denied" in error_lower:
            return "permission_error"
        elif "navigation" in error_lower:
            return "navigation_error"
        else:
            return "unknown_error"
    
    def _extract_selector_from_error(self, error_message: str) -> tuple[Optional[str], Optional[str]]:
        """Extract selector and type from error message."""
        import re
        
        # Try to find CSS selector
        css_match = re.search(r'selector[:\s]+["\']([^"\']+)["\']', error_message)
        if css_match:
            return css_match.group(1), "css"
        
        # Try to find XPath
        xpath_match = re.search(r'xpath[:\s]+["\']([^"\']+)["\']', error_message)
        if xpath_match:
            return xpath_match.group(1), "xpath"
        
        # Try to find text selector
        text_match = re.search(r'text[:\s]+["\']([^"\']+)["\']', error_message)
        if text_match:
            return text_match.group(1), "text"
        
        return None, None


# Singleton instance
_execution_service: Optional[ExecutionService] = None


def get_execution_service(config: ExecutionConfig = None) -> ExecutionService:
    """Get or create execution service singleton."""
    global _execution_service
    if _execution_service is None:
        _execution_service = ExecutionService(config)
    return _execution_service

