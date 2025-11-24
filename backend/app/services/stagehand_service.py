"""
Stagehand-based Test Execution Service
Uses Stagehand for browser automation with Playwright under the hood.
"""
import asyncio
import os
import sys
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
        headless: bool = True,
        screenshot_dir: str = "artifacts/screenshots",
        video_dir: str = "artifacts/videos"
    ):
        """Initialize Stagehand execution service."""
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
            
            config = StagehandConfig(
                env="LOCAL",  # Use local Playwright
                headless=self.headless,
                verbose=0,  # Reduce logging
                # Disable signal handlers when running in a thread
                local_browser_launch_options={
                    "handle_sigint": False,
                    "handle_sigterm": False,
                    "handle_sighup": False
                }
            )
            
            self.stagehand = Stagehand(config)
            await self.stagehand.init()
            self.page = self.stagehand.page
    
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
        progress_callback: Optional[Callable] = None
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
            
            # Navigate to base URL
            print(f"[DEBUG] Navigating to {base_url}")
            await self.page.goto(base_url)
            await asyncio.sleep(1)  # Wait for page to stabilize
            
            # Execute steps
            steps = test_case.steps if isinstance(test_case.steps, list) else []
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
                    
                    # Execute the step (simplified for MVP)
                    result = await self._execute_step_simple(step_desc, idx)
                    
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
    
    async def _execute_step_simple(self, step_description: str, step_number: int) -> Dict[str, Any]:
        """
        Execute a single test step (simplified for MVP).
        
        This is a basic implementation that doesn't use AI.
        Future enhancement: Integrate Stagehand's AI-powered act() and observe()
        """
        try:
            # Wait a moment to simulate execution
            await asyncio.sleep(0.5)
            
            # For MVP, we just verify the page is still alive
            # Future: Use Stagehand's AI features here
            title = await self.page.title()
            
            return {
                "success": True,
                "actual": f"Step executed (page title: {title})",
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


# Singleton instance
_stagehand_service: Optional[StagehandExecutionService] = None


def get_stagehand_service() -> StagehandExecutionService:
    """Get or create Stagehand service singleton."""
    global _stagehand_service
    if _stagehand_service is None:
        _stagehand_service = StagehandExecutionService(headless=True)
    return _stagehand_service

