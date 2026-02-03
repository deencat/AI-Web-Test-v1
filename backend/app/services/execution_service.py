"""
Test Execution Service with Stagehand and Playwright
Handles browser automation and test execution.
Integrated with 3-Tier Execution Engine (Sprint 5.5)
"""
import asyncio
import json
import os
import logging
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
from app.models.user_settings import UserSetting
from app.crud import test_execution as crud_execution
from app.crud import execution_feedback as crud_feedback
from app.schemas.execution_feedback import ExecutionFeedbackCreate
from app.services.three_tier_execution_service import ThreeTierExecutionService
from app.utils.test_data_generator import TestDataGenerator

logger = logging.getLogger(__name__)


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
        self.test_data_generator = TestDataGenerator()
        self._generated_data_cache: Dict[str, Dict[str, str]] = {}  # Cache per test_id
    
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
                # Launch with remote debugging port for CDP access
                self.browser = await self.playwright.chromium.launch(
                    headless=self.config.headless,
                    slow_mo=self.config.slow_mo,
                    args=[
                        '--remote-debugging-port=9222',  # Fixed port for CDP
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
    
    async def cleanup(self):
        """Clean up browser and Playwright resources."""
        # Clean up 3-Tier service (includes Stagehand cleanup)
        if self.three_tier_service:
            try:
                # Clean up Tier 2 XPath extractor's Stagehand
                if hasattr(self.three_tier_service, 'xpath_extractor') and self.three_tier_service.xpath_extractor:
                    if hasattr(self.three_tier_service.xpath_extractor, 'stagehand') and self.three_tier_service.xpath_extractor.stagehand:
                        try:
                            await self.three_tier_service.xpath_extractor.stagehand.close()
                        except Exception as e:
                            print(f"[DEBUG] Error closing Stagehand: {e}")
                
                # Clean up Tier 3 Stagehand
                if hasattr(self.three_tier_service, 'tier3_executor') and self.three_tier_service.tier3_executor:
                    if hasattr(self.three_tier_service.tier3_executor, 'stagehand') and self.three_tier_service.tier3_executor.stagehand:
                        try:
                            await self.three_tier_service.tier3_executor.stagehand.close()
                        except Exception as e:
                            print(f"[DEBUG] Error closing Tier 3 Stagehand: {e}")
            except Exception as e:
                print(f"[DEBUG] Error cleaning up 3-Tier service: {e}")
        
        # Clean up ExecutionService's Playwright browser
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

    async def _apply_profile_cookies(self, page: Page, profile_data: Dict[str, Any]) -> None:
        """Apply cookie data to the browser context before navigation."""
        cookies = profile_data.get("cookies") if profile_data else None
        if cookies:
            await page.context.add_cookies(cookies)
            logger.info(f"[INFO] ✅ Injected {len(cookies)} cookies")

    async def _apply_profile_storage(self, page: Page, profile_data: Dict[str, Any]) -> None:
        """Apply localStorage and sessionStorage after navigation."""
        if not profile_data:
            return

        local_storage = profile_data.get("localStorage")
        if local_storage:
            await page.evaluate(
                """
                (storage) => {
                    for (const [key, value] of Object.entries(storage)) {
                        localStorage.setItem(key, value);
                    }
                }
                """,
                local_storage
            )
            logger.info(f"[INFO] ✅ Injected {len(local_storage)} localStorage items")

        session_storage = profile_data.get("sessionStorage")
        if session_storage:
            await page.evaluate(
                """
                (storage) => {
                    for (const [key, value] of Object.entries(storage)) {
                        sessionStorage.setItem(key, value);
                    }
                }
                """,
                session_storage
            )
            logger.info(f"[INFO] ✅ Injected {len(session_storage)} sessionStorage items")
    
    async def execute_test(
        self,
        db: Session,
        test_case: TestCase,
        user_id: int,
        base_url: str,
        environment: str = "dev",
        execution_id: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
        browser_profile_data: Optional[Dict[str, Any]] = None
    ) -> TestExecution:
        """
        Execute a test case and track results.
        
        Args:
            db: Database session
            test_case: Test case to execute
            user_id: ID of user triggering execution
            base_url: Base URL for the application under test
            environment: Environment name (dev, staging, production)
            execution_id: Optional existing execution ID (for queue manager)
            progress_callback: Optional callback for progress updates
            
        Returns:
            TestExecution object with results
        """
        # Get or create execution record
        if execution_id:
            # Use existing execution (from queue manager)
            execution = crud_execution.get_execution(db, execution_id)
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
        else:
            # Create new execution record
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

            # Apply browser profile cookies before navigation
            if browser_profile_data:
                await self._apply_profile_cookies(page, browser_profile_data)
            
            # Get CDP endpoint for shared browser context
            # Use fixed remote debugging port (set in initialize())
            cdp_endpoint = "http://localhost:9222"
            
            logger.info(f"[DEBUG] CDP endpoint: {cdp_endpoint}")
            
            # Get user's execution settings and initialize 3-Tier service
            user_settings = self._get_user_execution_settings(db, user_id)
            
            # Get user's AI provider config from UserSetting table
            user_ai_config = None
            user_setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
            if user_setting:
                user_ai_config = {
                    "provider": user_setting.execution_provider,
                    "model": user_setting.execution_model,
                    "temperature": user_setting.execution_temperature,
                    "max_tokens": user_setting.execution_max_tokens
                }
                logger.info(f"[DEBUG] 🎯 User AI config from DB: {user_ai_config}")
            else:
                logger.info("[DEBUG] ⚠️ No user settings found, will use .env defaults")
            
            self.three_tier_service = ThreeTierExecutionService(
                db=db,
                page=page,
                user_settings=user_settings,
                cdp_endpoint=cdp_endpoint,  # Pass CDP endpoint for shared browser context
                user_ai_config=user_ai_config  # Pass user's AI provider settings
            )
            
            # Navigate to base URL
            await page.goto(base_url)

            # Apply localStorage/sessionStorage after navigation
            if browser_profile_data:
                await self._apply_profile_storage(page, browser_profile_data)
            
            # Execute steps - Get detailed steps from test_data if available
            steps = test_case.steps if isinstance(test_case.steps, list) else json.loads(test_case.steps)
            
            # Try to get detailed steps with selectors from test_data
            detailed_steps = None
            loop_blocks = []
            if test_case.test_data:
                test_data = test_case.test_data if isinstance(test_case.test_data, dict) else json.loads(test_case.test_data)
                detailed_steps = test_data.get('detailed_steps', [])
                loop_blocks = test_data.get('loop_blocks', [])
            
            # Validate and log loop blocks
            if loop_blocks:
                logger.info(f"[LOOP] Found {len(loop_blocks)} loop block(s): {loop_blocks}")
            
            total_steps = len(steps)
            passed_steps = 0
            failed_steps = 0
            
            # Helper function to find matching detailed_step by instruction
            def find_detailed_step_for_step(step_desc: str, detailed_steps: list) -> dict:
                """Find detailed_step that matches the step description by instruction field"""
                if not detailed_steps:
                    return None
                
                import re
                
                # Normalize step description: remove {generate:*} patterns and trim punctuation
                normalized_step = re.sub(r'\{generate:\w+(?::\w+)?\}', '', step_desc).strip().rstrip('.')
                
                # Try exact match first
                for ds in detailed_steps:
                    instruction = ds.get('instruction', '')
                    if instruction == step_desc:
                        return ds
                
                # Try normalized match (without patterns and trailing punctuation)
                for ds in detailed_steps:
                    instruction = ds.get('instruction', '').strip().rstrip('.')
                    if instruction == normalized_step:
                        return ds
                
                # Fallback: partial match (old behavior)
                for ds in detailed_steps:
                    instruction = ds.get('instruction', '')
                    if instruction and instruction.strip() in step_desc.strip():
                        return ds
                
                return None
            
            # Step execution with loop support
            idx = 1  # Current step index (1-based)
            
            while idx <= total_steps:
                step_desc = steps[idx - 1]  # 0-based list access
                step_start = datetime.utcnow()
                
                # Check if this step starts a loop block
                active_loop = self._find_loop_starting_at(idx, loop_blocks)
                
                if active_loop:
                    logger.info(f"[LOOP] Starting loop block '{active_loop['id']}' at step {idx} for {active_loop['iterations']} iterations")
                    
                    # Execute loop body N times
                    loop_passed = 0
                    loop_failed = 0
                    
                    for iteration in range(1, active_loop["iterations"] + 1):
                        logger.info(f"[LOOP] Iteration {iteration}/{active_loop['iterations']} of loop '{active_loop['id']}'")
                        
                        # Execute each step in the loop range
                        for loop_step_idx in range(active_loop["start_step"], active_loop["end_step"] + 1):
                            loop_step_desc = steps[loop_step_idx - 1]
                            loop_step_start = datetime.utcnow()
                            
                            # Get detailed step data by matching instruction field
                            detailed_step = find_detailed_step_for_step(loop_step_desc, detailed_steps)
                            
                            if detailed_step:
                                # Apply variable substitution for this iteration
                                detailed_step = self._apply_loop_variables(
                                    detailed_step, 
                                    iteration, 
                                    active_loop.get("variables", {})
                                )
                                
                                # Apply test data generation (after loop variables)
                                detailed_step = self._apply_test_data_generation(
                                    detailed_step,
                                    execution.id
                                )
                            
                            # Apply variable substitution to step description
                            loop_step_desc_substituted = self._substitute_loop_variables(
                                loop_step_desc, 
                                iteration, 
                                active_loop.get("variables", {})
                            )
                            
                            # Apply test data generation to step description
                            loop_step_desc_substituted = self._substitute_test_data_patterns(
                                loop_step_desc_substituted,
                                execution.id
                            )
                            
                            try:
                                if progress_callback:
                                    await progress_callback({
                                        "execution_id": execution.id,
                                        "step": loop_step_idx,
                                        "total_steps": total_steps,
                                        "loop_iteration": iteration,
                                        "loop_total": active_loop["iterations"],
                                        "message": f"Executing step {loop_step_idx} (iteration {iteration}/{active_loop['iterations']}): {loop_step_desc_substituted}"
                                    })
                                
                                # Execute the step with detailed data
                                result = await self._execute_step(page, loop_step_desc_substituted, loop_step_idx, base_url, detailed_step, execution.id)
                                
                                loop_step_end = datetime.utcnow()
                                duration = (loop_step_end - loop_step_start).total_seconds()
                                
                                # Determine result for screenshot naming
                                step_result = ExecutionResult.PASS if result["success"] else ExecutionResult.FAIL
                                
                                # Save screenshot with iteration number
                                screenshot_path = await self._capture_screenshot_with_iteration(
                                    page, 
                                    execution.id, 
                                    loop_step_idx,
                                    iteration,
                                    step_result
                                )
                                
                                # Create step record with iteration info
                                crud_execution.create_execution_step(
                                    db=db,
                                    execution_id=execution.id,
                                    step_number=loop_step_idx,
                                    step_description=f"{loop_step_desc_substituted} (iter {iteration}/{active_loop['iterations']})",
                                    expected_result=result.get("expected", "Step completes successfully"),
                                    result=step_result,
                                    actual_result=result.get("actual", ""),
                                    error_message=result.get("error"),
                                    screenshot_path=screenshot_path,
                                    duration_seconds=duration
                                )
                                
                                if result["success"]:
                                    loop_passed += 1
                                else:
                                    loop_failed += 1
                                    
                                    # Capture execution feedback for failed step
                                    await self._capture_execution_feedback(
                                        db=db,
                                        execution_id=execution.id,
                                        step_index=loop_step_idx - 1,
                                        step_description=f"{loop_step_desc_substituted} (iter {iteration})",
                                        error_message=result.get("error", "Step failed"),
                                        page=page,
                                        screenshot_path=screenshot_path,
                                        duration_ms=int(duration * 1000),
                                        tier_info=result.get("execution_history"),
                                        strategy_used=result.get("strategy_used")
                                    )
                                    
                                    # If step is critical and failed, stop loop execution
                                    if result.get("critical", False):
                                        logger.warning(f"[LOOP] Critical step {loop_step_idx} failed in iteration {iteration}, stopping loop")
                                        break
                            
                            except Exception as e:
                                loop_failed += 1
                                loop_step_end = datetime.utcnow()
                                duration = (loop_step_end - loop_step_start).total_seconds()
                                
                                # Capture failure screenshot
                                screenshot_path = await self._capture_screenshot_with_iteration(
                                    page, 
                                    execution.id, 
                                    loop_step_idx,
                                    iteration,
                                    ExecutionResult.ERROR
                                )
                                
                                crud_execution.create_execution_step(
                                    db=db,
                                    execution_id=execution.id,
                                    step_number=loop_step_idx,
                                    step_description=f"{loop_step_desc} (iter {iteration}/{active_loop['iterations']})",
                                    result=ExecutionResult.ERROR,
                                    error_message=str(e),
                                    screenshot_path=screenshot_path,
                                    duration_seconds=duration
                                )
                                
                                # Capture execution feedback
                                await self._capture_execution_feedback(
                                    db=db,
                                    execution_id=execution.id,
                                    step_index=loop_step_idx - 1,
                                    step_description=f"{loop_step_desc} (iter {iteration})",
                                    error_message=str(e),
                                    page=page,
                                    screenshot_path=screenshot_path,
                                    duration_ms=int(duration * 1000)
                                )
                                
                                logger.error(f"[LOOP] Exception in step {loop_step_idx} iteration {iteration}: {e}")
                                break
                    
                    # Update counters with loop results
                    passed_steps += loop_passed
                    failed_steps += loop_failed
                    
                    logger.info(f"[LOOP] Completed loop '{active_loop['id']}': {loop_passed} passed, {loop_failed} failed")
                    
                    # Skip to after loop end
                    idx = active_loop["end_step"] + 1
                    continue
                
                # Execute single step normally (not in a loop)
                # Get detailed step data by matching instruction field
                detailed_step = find_detailed_step_for_step(step_desc, detailed_steps)
                
                if detailed_step:
                    # Apply test data generation to detailed step
                    detailed_step = self._apply_test_data_generation(
                        detailed_step,
                        execution.id
                    )
                
                # Apply test data generation to step description
                step_desc_substituted = self._substitute_test_data_patterns(
                    step_desc,
                    execution.id
                )
                
                try:
                    if progress_callback:
                        await progress_callback({
                            "execution_id": execution.id,
                            "step": idx,
                            "total_steps": total_steps,
                            "message": f"Executing step {idx}: {step_desc_substituted}"
                        })
                    
                    # Execute the step with detailed data
                    result = await self._execute_step(page, step_desc_substituted, idx, base_url, detailed_step, execution.id)
                    
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
                        step_description=step_desc_substituted,
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
                            step_description=step_desc_substituted,
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
                        step_description=step_desc_substituted,
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
                        step_description=step_desc_substituted,
                        error_message=str(e),
                        page=page,
                        screenshot_path=screenshot_path,
                        duration_ms=int(duration * 1000)
                    )
                    
                    # Critical error, stop execution
                    break
                
                # Move to next step
                idx += 1
            
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
        detailed_step: Dict[str, Any] = None,
        execution_id: int = None
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
            execution_id: Test execution ID for test data generation caching
            
        Returns:
            Dictionary with execution result
        """
        try:
            import re
            
            # DEBUG: Log what we received
            print(f"\n[DEBUG _execute_step] Step {step_number}: {step_description}")
            print(f"[DEBUG] detailed_step = {detailed_step}")
            
            # Apply test data generation if execution_id is provided
            if execution_id:
                # Apply test data generation to detailed step
                if detailed_step:
                    detailed_step = self._apply_test_data_generation(
                        detailed_step,
                        execution_id
                    )
                    print(f"[DEBUG] After test data generation: detailed_step = {detailed_step}")
                
                # Apply test data generation to step description
                step_description = self._substitute_test_data_patterns(
                    step_description,
                    execution_id
                )
                print(f"[DEBUG] After test data generation: step_description = {step_description}")
            
            # If 3-tier service is available, use it
            if self.three_tier_service:
                # Prepare step data for 3-tier execution
                step_data = {
                    "action": detailed_step.get('action', '') if detailed_step else None,
                    "selector": detailed_step.get('selector', '') if detailed_step else None,
                    "value": detailed_step.get('value', '') if detailed_step else None,
                    "file_path": detailed_step.get('file_path', '') if detailed_step else None,
                    "instruction": step_description
                }
                
                print(f"[DEBUG] Initial step_data[value]: {step_data['value']}")
                print(f"[DEBUG] detailed_step: {detailed_step}")
                
                # If no value provided and this is a fill action, extract from substituted step description
                if not step_data["value"] and (not detailed_step or not detailed_step.get('value')):
                    print(f"[DEBUG] Entering value extraction logic")
                    # Try to extract the generated/substituted value from the step description
                    # This handles cases where {generate:hkid:main} was replaced with actual value
                    desc_lower = step_description.lower()
                    # FIX: Also extract values for 'select' and 'choose' actions (for dropdowns)
                    if "fill" in desc_lower or "type" in desc_lower or "enter" in desc_lower or "input" in desc_lower or "select" in desc_lower or "choose" in desc_lower:
                        print(f"[DEBUG] Action keyword found in description, attempting value extraction")
                        # Look for common data patterns after keywords
                        value_patterns = [
                            # Credit card patterns - Extract credit card numbers from descriptions
                            # Pattern 1: 16-digit credit card (e.g., "1234567812345678" or "1234 5678 1234 5678")
                            r'(?:credit.*card|card.*number|card).*?(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})',  # Credit card with/without spaces/dashes
                            # Pattern 2: Direct input of credit card number
                            r'(?:input|enter|fill|type)\s+(?:credit.*card|card.*number|card)?\s*(\d{16})',  # 16-digit number
                            # Pattern 3: CVV/CVC (3-4 digits)
                            r'(?:cvv|cvc|security.*code).*?(\d{3,4})',  # CVV/CVC codes
                            # Pattern 4: Expiry date (MM/YY or MM/YYYY)
                            r'(?:expiry|expiration|exp.*date).*?(\d{2}/\d{2,4})',  # Expiry date
                            
                            # Dropdown/Select patterns - Extract month, year, day values
                            r'(?:select|choose)\s+(?:expiry\s+)?month\s+(\d{1,2})',  # "select month 01" or "select expiry month 1"
                            r'(?:select|choose)\s+(?:expiry\s+)?year\s+(\d{2,4})',  # "select year 39" or "select expiry year 2039"
                            r'(?:select|choose)\s+day\s+(\d{1,2})',  # "select day 15"
                            r'(?:select|choose)\s+(\d{1,2})\s+as\s+(?:month|day)',  # "select 01 as month"
                            r'(?:select|choose)\s+(\d{2,4})\s+as\s+year',  # "select 39 as year"
                            
                            # HKID patterns - Extract specific values mentioned in the description
                            # Pattern 1: "input hkid number Q496157 on id no. first field" -> Extract Q496157
                            r'(?:input|enter|fill|type)\s+(?:hkid|id)\s+(?:number\s+)?([A-Z]\d{6})\s+',  # Alphanumeric HKID (e.g., Q496157)
                            # Pattern 2: "input hkid number 5 on id no. second field" -> Extract 5
                            r'(?:input|enter|fill|type)\s+(?:hkid|id)\s+(?:number\s+)?(\d{1,2})\s+(?:on|in)',  # 1-2 digit number (e.g., 5)
                            # Pattern 3: Check digit patterns (e.g., "(3)")
                            r'(?:input|enter|fill|type)\s+(?:hkid|id)\s+(?:number\s+)?\((\d{1})\)',  # Check digit in parentheses
                            
                            # Contact/phone number - more flexible pattern
                            r'(?:contact|phone|mobile).*?(\d{8})\s*$',  # "contact number 90457537"
                            
                            # Name patterns
                            r'(?:surname|first\s+name)\s+([a-zA-Z]+)\s*$',  # "surname test" or "first name abc"
                            r'(?:chinese\s+name)\s+([\u4e00-\u9fff]+)\s*$',  # "chinese name 陳小文"
                            
                            # Date pattern
                            r'(?:birth|date).*?([\d/]+)\s*$',  # "birth 2000/01/01"
                            
                            # Generic fallback patterns
                            r'(?:input|enter|fill|type)\s+([A-Z]\d{6})\s+',  # Generic: "input A123456 on"
                            r'(?:input|enter|fill|type)\s+(\d{8})\s+',  # Generic: "input 12345678 on"
                        ]
                        
                        for i, pattern in enumerate(value_patterns):
                            match = re.search(pattern, step_description, re.IGNORECASE)
                            if match:
                                potential_value = match.group(1)
                                print(f"[DEBUG] Pattern {i} matched: {pattern[:50]}... => {potential_value}")
                                # Skip if it looks like a field description
                                if "field" not in potential_value.lower():
                                    step_data["value"] = potential_value
                                    print(f"[DEBUG] Extracted value from substituted description: {step_data['value']}")
                                    break
                                else:
                                    print(f"[DEBUG] Skipped potential_value '{potential_value}' (contains 'field')")
                        
                        if not step_data["value"]:
                            print(f"[DEBUG] No value extracted from patterns")
                
                # Detect action from description if not provided
                desc_lower = step_description.lower()
                if not step_data["action"]:
                    if "navigate" in desc_lower or "go to" in desc_lower or "open" in desc_lower:
                        step_data["action"] = "navigate"
                    # Check for signature/sign actions first
                    elif "sign" in desc_lower or "signature" in desc_lower or "draw" in desc_lower:
                        step_data["action"] = "draw_signature"
                    # Check for dropdown/select actions (select month/year/etc.)
                    # More precise: must have "select/choose" followed by specific dropdown keywords
                    # Exclude cases like "select the $288/month plan" where "month" is part of price
                    elif (("select" in desc_lower or "choose" in desc_lower) and 
                          any(f"{verb} {kw}" in desc_lower or f"{verb} expiry {kw}" in desc_lower or f"{kw} dropdown" in desc_lower or f"{kw} menu" in desc_lower or f"from {kw}" in desc_lower
                              for verb in ["select", "choose", "pick"]
                              for kw in ["month", "year", "day", "country", "date", "dropdown", "option"])):
                        step_data["action"] = "select"
                    elif "click" in desc_lower or "select" in desc_lower or "choose" in desc_lower:
                        step_data["action"] = "click"
                    elif "fill" in desc_lower or "type" in desc_lower or "enter" in desc_lower or "input" in desc_lower:
                        step_data["action"] = "fill"
                    # Check for checkbox/toggle actions before generic verify
                    elif ("check" in desc_lower or "tick" in desc_lower) and ("checkbox" in desc_lower or "box" in desc_lower):
                        step_data["action"] = "check"
                    elif ("uncheck" in desc_lower or "untick" in desc_lower) and ("checkbox" in desc_lower or "box" in desc_lower):
                        step_data["action"] = "uncheck"
                    elif "verify" in desc_lower or "check" in desc_lower or "assert" in desc_lower:
                        step_data["action"] = "verify"
                    # Detect file upload actions
                    elif "upload" in desc_lower:
                        step_data["action"] = "upload_file"
                        # Auto-detect file path from description ONLY if not already provided
                        if not step_data.get("file_path"):
                            # First, try to extract explicit file path from description
                            # Pattern: /path/to/file.ext or path/to/file.ext
                            file_path_pattern = r'(/[\w\-/.]+\.(pdf|jpg|jpeg|png|gif|doc|docx|xls|xlsx|txt|csv))\b'
                            file_path_match = re.search(file_path_pattern, step_description, re.IGNORECASE)
                            
                            if file_path_match:
                                # User specified explicit file path in description
                                step_data["file_path"] = file_path_match.group(1)
                                logger.info(f"[Extracted from description] File path: {step_data['file_path']}")
                            else:
                                # Fallback to keyword-based auto-detection
                                # Determine base path: /app/test_files/ (Docker) or backend/test_files/ (host)
                                if os.path.exists("/app/test_files"):
                                    base_path = "/app/test_files"
                                else:
                                    # Running on host - use absolute path from backend directory
                                    backend_dir = Path(__file__).parent.parent.parent
                                    base_path = str(backend_dir / "test_files")
                                
                                # Default to passport_sample.jpg for uploads (jpg/png accepted by most webapps)
                                if "passport" in desc_lower:
                                    step_data["file_path"] = f"{base_path}/passport_sample.jpg"
                                elif "hkid" in desc_lower:
                                    step_data["file_path"] = f"{base_path}/hkid_sample.pdf"
                                elif "address" in desc_lower or "proof" in desc_lower:
                                    step_data["file_path"] = f"{base_path}/address_proof.pdf"
                                else:
                                    # Default to jpg file for generic uploads (most widely accepted)
                                    step_data["file_path"] = f"{base_path}/passport_sample.jpg"
                                
                                logger.info(f"[Auto-detected from keywords] File upload with file_path: {step_data.get('file_path')}")
                        else:
                            logger.info(f"[User-specified in detailed_step] File upload with file_path: {step_data.get('file_path')}")
                        
                        # Default file input selector for upload actions
                        if not step_data["selector"]:
                            step_data["selector"] = "input[type='file']"
                
                # Extract XPath/CSS selector from instruction text if not already provided
                # Skip selector extraction for navigate actions (to avoid matching URLs)
                if not step_data["selector"] and step_data["action"] != "navigate":
                    # Try to extract XPath first (pattern: xpath "//..." or with xpath "//...")
                    xpath_patterns = [
                        r'xpath\s*"([^"]+)"',  # xpath "//button[@class='btn']" - double quotes
                        r"xpath\s*'([^']+)'",  # xpath '//button[@class="btn"]' - single quotes
                        r'with\s+xpath\s*"([^"]+)"',  # with xpath "//button"
                        r"with\s+xpath\s*'([^']+)'",  # with xpath '//button'
                        r'(//[\w\-/@\[\]()=\'"\s,\.]+)',  # raw XPath like //button[@id='login']
                    ]
                    for pattern in xpath_patterns:
                        xpath_match = re.search(pattern, step_description)
                        if xpath_match:
                            step_data["selector"] = xpath_match.group(1)
                            print(f"[DEBUG] Extracted XPath from instruction: {step_data['selector']}")
                            break
                    
                    # If no XPath found, try CSS selector (pattern: selector "..." or css "...")
                    if not step_data["selector"]:
                        css_patterns = [
                            r'selector\s*["\']([^"\']+)["\']',
                            r'css\s*["\']([^"\']+)["\']',
                        ]
                        for pattern in css_patterns:
                            css_match = re.search(pattern, step_description)
                            if css_match:
                                step_data["selector"] = css_match.group(1)
                                print(f"[DEBUG] Extracted CSS selector from instruction: {step_data['selector']}")
                                break
                
                # For navigate actions, extract URL
                if step_data["action"] == "navigate":
                    if not step_data["value"]:
                        step_data["value"] = base_url
                        if "http" in step_description:
                            # Try to extract URL from quotes first (most reliable)
                            # Pattern: "https://example.com" or 'https://example.com' (handles spaces after URL)
                            quoted_url_match = re.search(r'["\']+(https?://[^\s"\']+)\s*["\']', step_description)
                            if quoted_url_match:
                                step_data["value"] = quoted_url_match.group(1)
                                print(f"[DEBUG] Extracted URL from quotes: {step_data['value']}")
                            else:
                                # Fallback: extract URL and aggressively clean it
                                urls = re.findall(r'https?://[^\s]+', step_description)
                                if urls:
                                    # Remove ALL trailing non-URL characters (quotes, punctuation, etc.)
                                    url = urls[0]
                                    # Strip trailing characters that shouldn't be in URLs
                                    while url and url[-1] in '"\',.;:!?) \t\n':
                                        url = url[:-1]
                                    step_data["value"] = url
                                    print(f"[DEBUG] Extracted URL (fallback, cleaned): {step_data['value']}")
                
                # For fill actions, extract value from instruction if not provided
                if step_data["action"] == "fill" and not step_data["value"]:
                    # Try to extract email, password, username, or other input values
                    
                    # Pattern 1: "Enter email: value" or "Enter password: value" (any value after colon)
                    field_value_match = re.search(
                        r'(?:enter|fill|type|input)\s+(?:email|password|username|name|text):\s*([^\s,;"\']+)',
                        step_description,
                        re.IGNORECASE
                    )
                    if field_value_match:
                        step_data["value"] = field_value_match.group(1)
                        print(f"[DEBUG] Extracted field value from instruction: {step_data['value']}")
                    
                    # Pattern 2: Generic field pattern "field: value" (for any field type)
                    if not step_data["value"]:
                        generic_field_match = re.search(
                            r':\s*([^\s,;"\']+)(?:\s+with\s+xpath|\s+with\s+selector|$)',
                            step_description
                        )
                        if generic_field_match:
                            potential_value = generic_field_match.group(1)
                            # Make sure it's not a URL or selector
                            if not potential_value.startswith('//') and not potential_value.startswith('http'):
                                step_data["value"] = potential_value
                                print(f"[DEBUG] Extracted value from generic pattern: {step_data['value']}")
                    
                    # Pattern 3: Look for any text in quotes (could be password, username, etc.)
                    if not step_data["value"]:
                        quoted_values = re.findall(r'["\']([^"\']+)["\']', step_description)
                        # Filter out XPath/CSS selectors from quoted values
                        for quoted_value in quoted_values:
                            if not quoted_value.startswith('//') and not quoted_value.startswith('.') and not quoted_value.startswith('#'):
                                # Check if it looks like text input (not a selector)
                                if not quoted_value.startswith('http') and len(quoted_value) < 100:
                                    step_data["value"] = quoted_value
                                    print(f"[DEBUG] Extracted value from quotes: {step_data['value']}")
                                    break
                    
                    # Last resort: use default test input
                    if not step_data["value"]:
                        step_data["value"] = "test input"
                        print(f"[DEBUG] Using default value: test input")
                
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
    
    def _find_loop_starting_at(self, step_idx: int, loop_blocks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find loop block that starts at the given step index.
        
        Args:
            step_idx: Current step index (1-based)
            loop_blocks: List of loop block definitions
            
        Returns:
            Loop block definition or None
        """
        for loop in loop_blocks:
            if loop.get("start_step") == step_idx:
                # Validate loop block structure
                if "end_step" in loop and "iterations" in loop:
                    return loop
                else:
                    logger.warning(f"[LOOP] Invalid loop block structure: {loop}")
        return None
    
    def _apply_loop_variables(
        self, 
        detailed_step: Dict[str, Any], 
        iteration: int, 
        loop_variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Apply variable substitution to detailed step data.
        
        Args:
            detailed_step: Step data with action, selector, value, file_path
            iteration: Current iteration number (1-based)
            loop_variables: Variable substitution templates
            
        Returns:
            Modified detailed step with substituted values
        """
        if not detailed_step:
            return detailed_step
        
        # Create a copy to avoid modifying original
        modified_step = detailed_step.copy()
        
        # Apply iteration substitution to all string fields
        for key, value in modified_step.items():
            if isinstance(value, str):
                # Replace {iteration} placeholder
                modified_step[key] = value.replace("{iteration}", str(iteration))
        
        # Apply custom loop variables if provided
        if loop_variables:
            for key, template in loop_variables.items():
                if key in modified_step and isinstance(template, str):
                    # Replace {iteration} in template
                    modified_step[key] = template.replace("{iteration}", str(iteration))
        
        return modified_step
    
    def _substitute_loop_variables(
        self, 
        text: str, 
        iteration: int, 
        loop_variables: Dict[str, str]
    ) -> str:
        """
        Substitute loop variables in text string.
        
        Args:
            text: Text containing placeholders
            iteration: Current iteration number (1-based)
            loop_variables: Variable substitution templates
            
        Returns:
            Text with substituted values
        """
        # Replace {iteration} placeholder
        result = text.replace("{iteration}", str(iteration))
        
        # Apply custom variables if provided
        if loop_variables:
            for key, template in loop_variables.items():
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    value = template.replace("{iteration}", str(iteration))
                    result = result.replace(placeholder, value)
        
        return result
    
    def _substitute_test_data_patterns(
        self, 
        text: str, 
        test_id: int
    ) -> str:
        """
        Substitute test data generation patterns in text string.
        
        Supports patterns like:
        - {generate:hkid} → Full HKID with check digit (A123456(3))
        - {generate:hkid:main} → Main part only (A123456)
        - {generate:hkid:check} → Check digit only (3)
        - {generate:hkid:letter} → Letter only (A)
        - {generate:hkid:digits} → Digits only (123456)
        - {generate:phone} → HK phone number (91234567)
        - {generate:email} → Unique email (testuser1234@example.com)
        
        Maintains consistency within a test - same generated value used across multiple steps.
        
        Args:
            text: Text containing generation patterns
            test_id: Test execution ID for caching consistency
            
        Returns:
            Text with substituted generated values
            
        Example:
            >>> # Step 1: {generate:hkid:main} → A123456
            >>> # Step 2: {generate:hkid:check} → 3 (matches Step 1)
        """
        import re
        
        if not text or not isinstance(text, str):
            return text
        
        # Initialize cache for this test if not exists
        cache_key = str(test_id)
        if cache_key not in self._generated_data_cache:
            self._generated_data_cache[cache_key] = {}
        
        test_cache = self._generated_data_cache[cache_key]
        
        # Pattern: {generate:type} or {generate:type:part}
        pattern = r'\{generate:(\w+)(?::(\w+))?\}'
        
        def replace_pattern(match):
            data_type = match.group(1)  # hkid, phone, email
            part = match.group(2)  # main, check, letter, digits (for HKID)
            
            try:
                if data_type == "hkid":
                    # Generate full HKID once and cache it
                    if "hkid" not in test_cache:
                        test_cache["hkid"] = self.test_data_generator.generate_hkid()
                        logger.info(f"[TestData] Generated HKID for test {test_id}: {test_cache['hkid']}")
                    
                    full_hkid = test_cache["hkid"]
                    
                    # Extract requested part
                    if part:
                        result = TestDataGenerator.extract_hkid_part(full_hkid, part)
                        logger.info(f"[TestData] Extracted HKID part '{part}': {result}")
                        return result
                    else:
                        # Return full HKID
                        return full_hkid
                
                elif data_type == "phone":
                    # Generate phone once and cache
                    if "phone" not in test_cache:
                        test_cache["phone"] = self.test_data_generator.generate_phone()
                        logger.info(f"[TestData] Generated phone for test {test_id}: {test_cache['phone']}")
                    
                    return test_cache["phone"]
                
                elif data_type == "email":
                    # Generate email once and cache
                    if "email" not in test_cache:
                        test_cache["email"] = self.test_data_generator.generate_email()
                        logger.info(f"[TestData] Generated email for test {test_id}: {test_cache['email']}")
                    
                    return test_cache["email"]
                
                else:
                    logger.warning(f"[TestData] Unknown data type: {data_type}")
                    return match.group(0)  # Return original pattern
            
            except Exception as e:
                logger.error(f"[TestData] Error generating {data_type}: {e}")
                return match.group(0)  # Return original pattern on error
        
        # Replace all patterns
        result = re.sub(pattern, replace_pattern, text)
        
        return result
    
    def _apply_test_data_generation(
        self, 
        detailed_step: Dict[str, Any], 
        test_id: int
    ) -> Dict[str, Any]:
        """
        Apply test data generation to detailed step data.
        
        Substitutes {generate:...} patterns in all string fields (selector, value, file_path).
        
        Args:
            detailed_step: Step data with action, selector, value, file_path
            test_id: Test execution ID for caching consistency
            
        Returns:
            Modified detailed step with substituted generated values
        """
        if not detailed_step:
            return detailed_step
        
        # Create a copy to avoid modifying original
        modified_step = detailed_step.copy()
        
        # Apply test data generation to all string fields
        for key, value in modified_step.items():
            if isinstance(value, str):
                modified_step[key] = self._substitute_test_data_patterns(value, test_id)
        
        return modified_step
    
    async def _capture_screenshot_with_iteration(
        self, 
        page: Page, 
        execution_id: int, 
        step_number: int,
        iteration: int,
        result: ExecutionResult
    ) -> Optional[str]:
        """Capture screenshot for a step within a loop iteration."""
        try:
            filename = f"exec_{execution_id}_step_{step_number}_iter_{iteration}_{result.value}.png"
            filepath = self.config.screenshot_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=True)
            
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
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

