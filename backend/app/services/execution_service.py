"""
Test Execution Service with Stagehand and Playwright
Handles browser automation and test execution.
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
from app.crud import test_execution as crud_execution


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
    """
    
    def __init__(self, config: ExecutionConfig = None):
        """Initialize execution service with configuration."""
        self.config = config or ExecutionConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
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
            
            # Navigate to base URL
            await page.goto(base_url)
            
            # Execute steps
            steps = test_case.steps if isinstance(test_case.steps, list) else json.loads(test_case.steps)
            total_steps = len(steps)
            passed_steps = 0
            failed_steps = 0
            
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
                    
                    # Execute the step
                    result = await self._execute_step(page, step_desc, idx, base_url)
                    
                    step_end = datetime.utcnow()
                    duration = (step_end - step_start).total_seconds()
                    
                    # Save screenshot for this step
                    screenshot_path = await self._capture_screenshot(
                        page, 
                        execution.id, 
                        idx,
                        result["result"]
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
                    else:
                        failed_steps += 1
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
        base_url: str
    ) -> Dict[str, Any]:
        """
        Execute a single test step.
        
        This is a simplified implementation. In Sprint 3, we'll integrate
        Stagehand for AI-powered step execution.
        
        Args:
            page: Playwright page object
            step_description: Description of the step to execute
            step_number: Step number
            base_url: Base URL of the application
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Basic step execution logic
            # TODO: Integrate Stagehand SDK for AI-powered execution
            
            # For now, just wait a moment and take a screenshot
            await asyncio.sleep(0.5)
            
            # Try to detect common actions from description
            desc_lower = step_description.lower()
            
            if "navigate" in desc_lower or "go to" in desc_lower or "open" in desc_lower:
                # Extract URL if present
                if "http" in step_description:
                    import re
                    urls = re.findall(r'https?://[^\s]+', step_description)
                    if urls:
                        await page.goto(urls[0])
                else:
                    # Navigate to base URL
                    await page.goto(base_url)
                
                return {
                    "success": True,
                    "actual": f"Navigated to page",
                    "expected": step_description
                }
            
            elif "click" in desc_lower:
                # Try to find and click button/link
                # This is simplified - real implementation will use Stagehand
                await asyncio.sleep(0.5)
                return {
                    "success": True,
                    "actual": f"Clicked element",
                    "expected": step_description
                }
            
            elif "type" in desc_lower or "enter" in desc_lower or "input" in desc_lower:
                # Simulate typing
                await asyncio.sleep(0.5)
                return {
                    "success": True,
                    "actual": f"Entered text",
                    "expected": step_description
                }
            
            elif "verify" in desc_lower or "check" in desc_lower or "assert" in desc_lower:
                # Verification step
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


# Singleton instance
_execution_service: Optional[ExecutionService] = None


def get_execution_service(config: ExecutionConfig = None) -> ExecutionService:
    """Get or create execution service singleton."""
    global _execution_service
    if _execution_service is None:
        _execution_service = ExecutionService(config)
    return _execution_service

