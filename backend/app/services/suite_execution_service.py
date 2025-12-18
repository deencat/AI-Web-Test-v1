"""
Service for executing test suites
"""
import asyncio
import json
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.crud import crud_test_suite
from app.crud import test_case as crud_test_case
from app.crud import test_execution as crud_executions
from app.services.execution_queue import get_execution_queue
from app.models.test_execution import ExecutionStatus
from app.schemas.test_suite import SuiteExecutionResponse


async def execute_test_suite(
    db: Session,
    suite_id: int,
    user_id: int,
    browser: str,
    environment: str,
    stop_on_failure: bool,
    parallel: bool
) -> SuiteExecutionResponse:
    """
    Execute all tests in a suite.
    
    Args:
        db: Database session
        suite_id: Test suite ID
        user_id: User ID
        browser: Browser to use (chromium, firefox, webkit)
        environment: Environment (dev, staging, prod)
        stop_on_failure: Stop executing if a test fails
        parallel: Run tests in parallel (not yet implemented)
    
    Returns:
        SuiteExecutionResponse with suite_execution_id and list of test_execution_ids
    """
    # Get suite with items
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise ValueError(f"Suite {suite_id} not found")
    
    # Create suite execution record
    suite_execution = crud_test_suite.create_suite_execution(
        db=db,
        suite_id=suite_id,
        user_id=user_id,
        browser=browser,
        environment=environment,
        triggered_by="manual",
        stop_on_failure=stop_on_failure,
        total_tests=len(suite.items)
    )
    
    # Get test cases in execution order
    ordered_items = sorted(suite.items, key=lambda x: x.execution_order)
    test_case_ids = [item.test_case_id for item in ordered_items]
    
    # Start executing tests
    queued_executions: List[int] = []
    
    try:
        # Update suite execution status
        crud_test_suite.update_suite_execution(
            db, suite_execution.id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        if parallel:
            # TODO: Implement parallel execution
            # For now, fall back to sequential
            queued_executions = await _execute_sequential(
                db, test_case_ids, browser, environment, stop_on_failure, user_id
            )
        else:
            # Sequential execution
            queued_executions = await _execute_sequential(
                db, test_case_ids, browser, environment, stop_on_failure, user_id
            )
        
        # Update suite execution with test results
        # Count passed/failed tests
        passed_count = 0
        failed_count = 0
        
        for exec_id in queued_executions:
            execution = crud_executions.get_execution(db, exec_id)
            if execution:
                if execution.status == ExecutionStatus.COMPLETED:
                    passed_count += 1
                elif execution.status == ExecutionStatus.FAILED:
                    failed_count += 1
        
        crud_test_suite.update_suite_execution(
            db, suite_execution.id,
            status="completed",
            completed_at=datetime.utcnow(),
            passed_tests=passed_count,
            failed_tests=failed_count
        )
        
    except Exception as e:
        # Mark suite execution as failed
        crud_test_suite.update_suite_execution(
            db, suite_execution.id,
            status="failed",
            completed_at=datetime.utcnow()
        )
        raise e
    
    return SuiteExecutionResponse(
        id=suite_execution.id,
        suite_id=suite_execution.suite_id,
        status=suite_execution.status,
        message=f"Suite execution started. {len(queued_executions)} tests queued.",
        total_tests=suite_execution.total_tests,
        queued_executions=queued_executions
    )


async def _execute_sequential(
    db: Session,
    test_case_ids: List[int],
    browser: str,
    environment: str,
    stop_on_failure: bool,
    user_id: int = 1
) -> List[int]:
    """
    Execute tests sequentially by queuing them one at a time.
    
    Note: Shared browser session approach doesn't work in FastAPI main thread
    due to Windows subprocess limitations. Using queue-based approach instead.
    """
    from app.crud import test_case as crud_test_case
    
    queued_executions = []
    queue = get_execution_queue()
    
    for index, test_case_id in enumerate(test_case_ids):
        try:
            # Get the test case
            test_case = crud_test_case.get_test_case(db, test_case_id)
            if not test_case:
                print(f"[SUITE] Warning: Test case {test_case_id} not found, skipping")
                continue
            
            # Extract base_url from test case
            base_url = _extract_base_url(test_case)
            print(f"[SUITE] Test {index + 1}/{len(test_case_ids)}: #{test_case_id} - {test_case.title}")
            
            # Create execution record
            execution = crud_executions.create_execution(
                db=db,
                test_case_id=test_case_id,
                user_id=user_id,
                browser=browser,
                environment=environment,
                base_url=base_url
            )
            
            # Set queued status
            execution.queued_at = datetime.utcnow()
            execution.priority = 5  # Medium priority
            execution.status = ExecutionStatus.PENDING
            db.commit()
            db.refresh(execution)
            
            # Add to execution queue
            queue_position = queue.add_to_queue(
                execution_id=execution.id,
                test_case_id=test_case_id,
                user_id=user_id,
                priority=execution.priority
            )
            
            # Update queue position
            execution.queue_position = queue_position
            db.commit()
            
            queued_executions.append(execution.id)
            
            # For sequential execution, wait for this test to complete before queuing the next
            is_last_test = (index == len(test_case_ids) - 1)
            
            if not is_last_test:
                print(f"[SUITE] Waiting for execution {execution.id} (test {index + 1}/{len(test_case_ids)}) to complete...")
                max_wait_time = 600  # 10 minutes max per test
                wait_interval = 2  # Check every 2 seconds
                elapsed = 0
                
                while elapsed < max_wait_time:
                    await asyncio.sleep(wait_interval)
                    elapsed += wait_interval
                    
                    # Refresh execution status
                    db.refresh(execution)
                    
                    if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                        print(f"[SUITE] Execution {execution.id} finished with status: {execution.status}")
                        
                        # If stop_on_failure is True and test failed, stop queuing more tests
                        if stop_on_failure and execution.status != ExecutionStatus.COMPLETED:
                            print(f"[SUITE] Stopping suite execution due to test failure (stop_on_failure=True)")
                            break
                        
                        # Continue to next test
                        break
                
                if elapsed >= max_wait_time:
                    print(f"[SUITE] Execution {execution.id} timed out after {max_wait_time}s")
                    if stop_on_failure:
                        break
                    
        except Exception as e:
            print(f"[SUITE] Error executing test {test_case_id}: {e}")
            if stop_on_failure:
                break
    
    return queued_executions


def _extract_base_url(test_case) -> str:
    """Extract base URL from test case description or steps."""
    base_url = "https://example.com"  # Default fallback
    
    # Try to extract URL from description
    if test_case.description:
        import re
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, test_case.description)
        if urls:
            return urls[0]
    
    # Also check in steps if available
    if test_case.steps:
        try:
            import json
            import re
            steps_data = test_case.steps if isinstance(test_case.steps, list) else json.loads(test_case.steps)
            if isinstance(steps_data, list) and len(steps_data) > 0:
                first_step = steps_data[0]
                if isinstance(first_step, dict):
                    step_desc = first_step.get('description', '') or first_step.get('action', '') or first_step.get('step', '')
                    urls = re.findall(r'https?://[^\s<>"]+', str(step_desc))
                    if urls:
                        return urls[0]
                elif isinstance(first_step, str):
                    urls = re.findall(r'https?://[^\s<>"]+', first_step)
                    if urls:
                        return urls[0]
        except Exception:
            pass
    
    return base_url


async def _execute_parallel(
    db: Session,
    test_case_ids: List[int],
    browser: str,
    environment: str
) -> List[int]:
    """Execute tests in parallel (future feature)"""
    # For now, just call sequential execution
    # TODO: Implement true parallel execution
    return await _execute_sequential(db, test_case_ids, browser, environment, False)


async def execute_test_suite_merged(
    db: Session,
    suite_id: int,
    user_id: int,
    browser: str,
    environment: str
) -> SuiteExecutionResponse:
    """
    Execute test suite by merging all test cases into ONE test with shared browser.
    
    This approach:
    - Combines all test steps into a single execution
    - Uses ONE browser session throughout (works around Windows limitation)
    - Maintains state between tests
    - Executes as continuous flow
    
    Args:
        db: Database session
        suite_id: Test suite ID
        user_id: User ID
        browser: Browser to use
        environment: Environment
    
    Returns:
        SuiteExecutionResponse with merged execution
    """
    from app.crud import test_case as crud_test_case
    
    # Get suite with items
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise ValueError(f"Suite {suite_id} not found")
    
    # Create suite execution record
    suite_execution = crud_test_suite.create_suite_execution(
        db=db,
        suite_id=suite_id,
        user_id=user_id,
        browser=browser,
        environment=environment,
        triggered_by="manual",
        stop_on_failure=False,
        total_tests=len(suite.items)
    )
    
    try:
        # Update suite execution status
        crud_test_suite.update_suite_execution(
            db, suite_execution.id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        # Get test cases in execution order
        ordered_items = sorted(suite.items, key=lambda x: x.execution_order)
        
        # Merge all test steps into one
        merged_steps = []
        merged_title_parts = []
        base_url = None
        
        print(f"[SUITE-MERGED] Merging {len(ordered_items)} test cases into single execution")
        
        for idx, item in enumerate(ordered_items, 1):
            test_case = crud_test_case.get_test_case(db, item.test_case_id)
            if not test_case:
                print(f"[SUITE-MERGED] Warning: Test case {item.test_case_id} not found, skipping")
                continue
            
            merged_title_parts.append(test_case.title)
            
            # Extract base_url from first test or from test with URL
            if not base_url:
                base_url = _extract_base_url(test_case)
            
            # Get steps from test case
            test_steps = test_case.steps
            if isinstance(test_steps, str):
                try:
                    test_steps = json.loads(test_steps)
                except:
                    test_steps = [test_steps]
            
            if not isinstance(test_steps, list):
                test_steps = [str(test_steps)]
            
            # Add steps with test case context
            print(f"[SUITE-MERGED] Test {idx}/{len(ordered_items)}: '{test_case.title}' - {len(test_steps)} steps")
            for step in test_steps:
                merged_steps.append(step)
        
        if not base_url:
            base_url = "https://example.com"
        
        print(f"[SUITE-MERGED] Total merged steps: {len(merged_steps)}")
        print(f"[SUITE-MERGED] Base URL: {base_url}")
        
        # Create a temporary merged test case in database
        merged_title = f"[MERGED] Suite: {suite.name}"
        merged_description = f"Merged from suite #{suite_id}: " + " → ".join(merged_title_parts)
        
        from app.models.test_case import TestCase
        merged_test = TestCase(
            title=merged_title,
            description=merged_description,
            test_type="e2e",
            priority="medium",
            steps=json.dumps(merged_steps),
            expected_result=f"All {len(ordered_items)} tests pass",
            user_id=user_id,
            tags=f"suite,merged,suite_{suite_id}"
        )
        db.add(merged_test)
        db.commit()
        db.refresh(merged_test)
        
        print(f"[SUITE-MERGED] Created temporary merged test case #{merged_test.id}")
        
        # Create execution for the merged test
        execution = crud_executions.create_execution(
            db=db,
            test_case_id=merged_test.id,
            user_id=user_id,
            browser=browser,
            environment=environment,
            base_url=base_url
        )
        
        # Override execution with merged data
        execution.test_data = json.dumps({
            "merged_from_suite": suite_id,
            "original_tests": [item.test_case_id for item in ordered_items],
            "merged_steps_count": len(merged_steps)
        })
        db.commit()
        
        # Set queued status
        execution.queued_at = datetime.utcnow()
        execution.priority = 5
        execution.status = ExecutionStatus.PENDING
        db.commit()
        db.refresh(execution)
        
        # Add to execution queue
        queue = get_execution_queue()
        queue_position = queue.add_to_queue(
            execution_id=execution.id,
            test_case_id=merged_test.id,
            user_id=user_id,
            priority=execution.priority
        )
        
        execution.queue_position = queue_position
        db.commit()
        
        print(f"[SUITE-MERGED] Queued merged execution {execution.id} with {len(merged_steps)} steps")
        
        # Wait for execution to complete
        print(f"[SUITE-MERGED] Waiting for merged execution to complete...")
        max_wait_time = 600  # 10 minutes
        wait_interval = 2
        elapsed = 0
        
        while elapsed < max_wait_time:
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
            
            db.refresh(execution)
            
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                print(f"[SUITE-MERGED] Execution {execution.id} finished with status: {execution.status}")
                break
        
        # Update suite execution with results
        if execution.status == ExecutionStatus.COMPLETED:
            passed_count = len(ordered_items)  # All tests passed
            failed_count = 0
        else:
            passed_count = 0
            failed_count = len(ordered_items)  # All tests failed
        
        crud_test_suite.update_suite_execution(
            db, suite_execution.id,
            status="completed",
            completed_at=datetime.utcnow(),
            passed_tests=passed_count,
            failed_tests=failed_count
        )
        
    except Exception as e:
        print(f"[SUITE-MERGED] Error: {e}")
        crud_test_suite.update_suite_execution(
            db, suite_execution.id,
            status="failed",
            completed_at=datetime.utcnow()
        )
        raise e
    
    return SuiteExecutionResponse(
        id=suite_execution.id,
        suite_id=suite_execution.suite_id,
        status=suite_execution.status,
        message=f"Suite executed as merged test. {len(merged_steps)} total steps.",
        total_tests=suite_execution.total_tests,
        queued_executions=[execution.id]
    )
