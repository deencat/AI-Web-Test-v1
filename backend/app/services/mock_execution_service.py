"""
Mock Test Execution Service for Windows Development
This provides a working MVP that simulates browser execution without Playwright.
Use this for development/testing on Windows. Real Stagehand service works on Linux/Docker.
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.models.test_execution import ExecutionStatus, ExecutionResult
from app.crud import test_execution as crud_execution
from app.schemas.test_execution import TestExecutionStepCreate


class MockExecutionService:
    """
    Mock execution service that simulates browser automation.
    Perfect for Windows development where Playwright has asyncio issues.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.artifacts_dir = Path("artifacts")
        self.artifacts_dir.mkdir(exist_ok=True)
    
    async def execute_test(
        self,
        db: Session,
        test_case: TestCase,
        user_id: int,
        base_url: Optional[str] = None,
        environment: str = "dev"
    ):
        """
        Execute a test case with mock browser automation.
        
        Args:
            db: Database session
            test_case: Test case to execute
            user_id: User executing the test
            base_url: Base URL for the test
            environment: Environment to run in
        """
        execution_id = None
        
        try:
            # Get the execution record (should have been created by the endpoint)
            executions = db.query(test_case.executions).all()
            if executions:
                execution = executions[-1]  # Get the latest execution
                execution_id = execution.id
            else:
                # Fallback: create execution if not found
                from app.schemas.test_execution import TestExecutionCreate
                execution_data = TestExecutionCreate(
                    test_case_id=test_case.id,
                    browser="chromium",
                    environment=environment,
                    base_url=base_url or "https://example.com",
                    triggered_by="api"
                )
                execution = crud_execution.create_execution(db, execution_data, user_id)
                execution_id = execution.id
            
            # Update status to RUNNING
            crud_execution.update_execution(
                db, execution_id,
                {
                    "status": ExecutionStatus.RUNNING,
                    "started_at": datetime.utcnow()
                }
            )
            
            # Simulate test execution with delays
            test_url = base_url or test_case.test_data.get("base_url", "https://example.com")
            
            # Execute each step with mock results
            for i, step_description in enumerate(test_case.steps):
                step_number = i + 1
                step_start = datetime.utcnow()
                
                # Simulate step execution (add small delay for realism)
                await asyncio.sleep(1.0)
                
                # Mock step result (90% pass rate for demo)
                import random
                step_result = ExecutionResult.PASS if random.random() > 0.1 else ExecutionResult.FAIL
                
                actual_result = f"[MOCK] Step '{step_description}' executed successfully"
                error_message = None
                screenshot_path = None
                
                if step_result == ExecutionResult.FAIL:
                    error_message = f"[MOCK] Simulated failure for demo purposes"
                    actual_result = f"[MOCK] Step '{step_description}' failed"
                    # Create mock screenshot path
                    screenshot_path = f"artifacts/execution_{execution_id}_step_{step_number}_mock.png"
                
                step_end = datetime.utcnow()
                duration = (step_end - step_start).total_seconds()
                
                # Create step record
                step_data = TestExecutionStepCreate(
                    execution_id=execution_id,
                    step_number=step_number,
                    step_description=step_description,
                    expected_result=f"Expected: {step_description}",
                    result=step_result,
                    actual_result=actual_result,
                    error_message=error_message,
                    duration_seconds=duration,
                    screenshot_path=screenshot_path
                )
                crud_execution.create_execution_step(db, step_data)
            
            # Determine final result
            steps = crud_execution.get_execution_steps(db, execution_id)
            final_result = ExecutionResult.PASS
            if any(s.result == ExecutionResult.FAIL for s in steps):
                final_result = ExecutionResult.FAIL
            elif any(s.result == ExecutionResult.ERROR for s in steps):
                final_result = ExecutionResult.ERROR
            
            # Update final execution status
            end_time = datetime.utcnow()
            execution = crud_execution.get_execution(db, execution_id)
            start_time = execution.started_at
            total_duration = (end_time - start_time).total_seconds() if start_time else None
            
            crud_execution.update_execution(
                db,
                execution_id,
                {
                    "status": ExecutionStatus.COMPLETED,
                    "result": final_result,
                    "completed_at": end_time,
                    "duration_seconds": total_duration,
                    "console_log": "[MOCK] Mock execution completed successfully.\nNo actual browser was used.",
                    "browser": "chromium (mock)",
                    "environment": environment,
                    "base_url": test_url
                }
            )
            
            # Update execution summary
            crud_execution.update_execution_summary(db, execution_id)
            
            print(f"[MOCK] Test execution {execution_id} completed with result: {final_result}")
            
        except Exception as e:
            print(f"[MOCK] Error during test execution: {e}")
            if execution_id:
                crud_execution.update_execution(
                    db,
                    execution_id,
                    {
                        "status": ExecutionStatus.FAILED,
                        "result": ExecutionResult.ERROR,
                        "completed_at": datetime.utcnow(),
                        "error_message": f"[MOCK] Execution error: {str(e)}"
                    }
                )


# Singleton instance
_mock_service_instance: Optional[MockExecutionService] = None


def get_mock_execution_service() -> MockExecutionService:
    """Get or create the mock execution service singleton."""
    global _mock_service_instance
    if _mock_service_instance is None:
        _mock_service_instance = MockExecutionService(headless=True)
    return _mock_service_instance

