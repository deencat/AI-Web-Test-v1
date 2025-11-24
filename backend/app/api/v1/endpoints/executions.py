"""Test execution API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from app.api import deps
from app.models.user import User
from app.models.test_execution import ExecutionStatus, ExecutionResult
from app.schemas.test_execution import (
    ExecutionStartRequest,
    ExecutionStartResponse,
    TestExecutionCreate,
    TestExecutionResponse,
    TestExecutionDetailResponse,
    TestExecutionListItem,
    TestExecutionListResponse,
    ExecutionStatistics
)
from app.crud import test_case as crud_tests
from app.crud import test_execution as crud_executions
from app.services.stagehand_service import get_stagehand_service

router = APIRouter()


# ============================================================================
# Execution Management
# ============================================================================

@router.post("/tests/{test_case_id}/execute", response_model=ExecutionStartResponse, status_code=status.HTTP_201_CREATED)
def start_execution(
    test_case_id: int,
    request: ExecutionStartRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Start a test execution.
    
    **Authentication required**
    
    Creates a new execution record for the specified test case.
    The execution starts in PENDING status and can be updated as it progresses.
    
    **Request Body:**
    - `browser`: Browser to use (chromium, firefox, webkit)
    - `environment`: Target environment (dev, staging, production)
    - `base_url`: Optional base URL override
    - `triggered_by`: Who/what triggered the execution
    """
    # Verify test case exists
    test_case = crud_tests.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with ID {test_case_id} not found"
        )
    
    # Check permissions (can only execute own tests unless admin)
    if current_user.role != "admin" and test_case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to execute this test case"
        )
    
    # Create execution
    execution_data = TestExecutionCreate(
        test_case_id=test_case_id,
        browser=request.browser,
        environment=request.environment,
        base_url=request.base_url,
        triggered_by=request.triggered_by
    )
    
    execution = crud_executions.create_execution(db, execution_data, current_user.id)
    
    return ExecutionStartResponse(
        id=execution.id,
        test_case_id=execution.test_case_id,
        status=execution.status,
        message=f"Execution started for test case {test_case_id}"
    )


@router.post("/tests/{test_case_id}/run", response_model=ExecutionStartResponse, status_code=status.HTTP_201_CREATED)
async def run_test_with_playwright(
    test_case_id: int,
    request: ExecutionStartRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Run a test case with Playwright browser automation.
    
    **Authentication required**
    
    Executes the test case steps using Playwright in a real browser.
    The test runs in the background and returns immediately with execution ID.
    Use GET /executions/{execution_id} to check progress and results.
    
    **Request Body:**
    - `browser`: Browser to use (chromium, firefox, webkit) - default: chromium
    - `environment`: Target environment (dev, staging, production) - default: dev
    - `base_url`: Base URL for the application under test (required)
    - `triggered_by`: Who/what triggered the execution - default: manual
    
    **Response:**
    - `id`: Execution ID for tracking
    - `test_case_id`: Test case being executed
    - `status`: Initial status (PENDING)
    - `message`: Confirmation message
    
    **Example:**
    ```json
    {
      "browser": "chromium",
      "environment": "dev",
      "base_url": "https://example.com",
      "triggered_by": "manual"
    }
    ```
    """
    # Verify test case exists
    test_case = crud_tests.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with ID {test_case_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and test_case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to execute this test case"
        )
    
    # Validate base_url is provided
    if not request.base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="base_url is required for test execution"
        )
    
    # Get Stagehand execution service
    service = get_stagehand_service()
    
    # Create initial execution record FIRST (before thread)
    execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case_id,
        user_id=current_user.id,
        browser=request.browser or "chromium",
        environment=request.environment or "dev",
        base_url=request.base_url
    )
    execution_id = execution.id  # Capture ID for closure
    
    # Run test in background - use executor to run in separate thread with proper event loop
    def run_test_in_thread():
        """
        Run test in a separate thread with its own event loop.
        This ensures ProactorEventLoopPolicy is respected on Windows.
        """
        import asyncio
        import sys
        import signal
        from app.db.session import SessionLocal, engine
        from sqlalchemy.orm import scoped_session, sessionmaker
        
        # Patch signal.signal to be a no-op in threads (Playwright tries to use it)
        original_signal = signal.signal
        def thread_safe_signal(signalnum, handler):
            """No-op signal handler for threads."""
            return None
        signal.signal = thread_safe_signal
        
        try:
            # Set Windows event loop policy in this thread
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create a thread-local database session
                # This ensures the session is properly bound to this thread
                ThreadSession = scoped_session(sessionmaker(bind=engine))
                bg_db = ThreadSession()
                
                try:
                    loop.run_until_complete(
                        service.execute_test(
                            db=bg_db,
                            test_case=test_case,
                            execution_id=execution_id,  # Use captured ID
                            user_id=current_user.id,
                            base_url=request.base_url,
                            environment=request.environment or "dev"
                        )
                    )
                    # Force commit and flush to ensure all changes are written
                    bg_db.commit()
                    bg_db.flush()
                    print(f"[DEBUG] Background thread committed execution updates to database")
                except Exception as e:
                    print(f"[ERROR] Test execution failed: {e}")
                    import traceback
                    traceback.print_exc()
                    bg_db.rollback()
                    raise
                finally:
                    bg_db.close()
                    ThreadSession.remove()
            finally:
                loop.close()
        finally:
            # Restore original signal handler
            signal.signal = original_signal
    
    # Use thread executor to run the test
    from concurrent.futures import ThreadPoolExecutor
    import threading
    
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(run_test_in_thread)
    
    # Don't wait for the result - let it run in background
    # The thread will handle the execution and update the database
    background_tasks.add_task(lambda: future.result())
    
    return ExecutionStartResponse(
        id=execution.id,
        test_case_id=execution.test_case_id,
        status=execution.status,
        message=f"Test execution started in background. Use GET /executions/{execution.id} to check progress."
    )


@router.get("/tests/{test_case_id}/executions", response_model=TestExecutionListResponse)
def get_test_executions(
    test_case_id: int,
    status_filter: Optional[ExecutionStatus] = Query(None, alias="status", description="Filter by status"),
    result_filter: Optional[ExecutionResult] = Query(None, alias="result", description="Filter by result"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get execution history for a test case.
    
    **Authentication required**
    
    Returns paginated list of executions for the specified test case.
    Non-admin users can only see executions for their own test cases.
    
    **Query Parameters:**
    - `status`: Filter by execution status
    - `result`: Filter by execution result
    - `skip`: Pagination offset
    - `limit`: Max results per page
    """
    # Verify test case exists
    test_case = crud_tests.get_test_case(db, test_case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test case with ID {test_case_id} not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and test_case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view these executions"
        )
    
    # Get executions
    executions = crud_executions.get_executions(
        db=db,
        test_case_id=test_case_id,
        status=status_filter,
        result=result_filter,
        skip=skip,
        limit=limit
    )
    
    total = crud_executions.get_execution_count(
        db=db,
        test_case_id=test_case_id,
        status=status_filter,
        result=result_filter
    )
    
    items = [TestExecutionListItem.model_validate(exec) for exec in executions]
    
    return TestExecutionListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/executions", response_model=TestExecutionListResponse)
def list_all_executions(
    test_case_id: Optional[int] = Query(None, description="Filter by test case"),
    status_filter: Optional[ExecutionStatus] = Query(None, alias="status", description="Filter by status"),
    result_filter: Optional[ExecutionResult] = Query(None, alias="result", description="Filter by result"),
    browser: Optional[str] = Query(None, description="Filter by browser"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    List all executions (with filters).
    
    **Authentication required**
    
    Returns paginated list of all executions.
    Non-admin users see only their own executions.
    Admins see all executions.
    
    **Query Parameters:**
    - `test_case_id`: Filter by test case
    - `status`: Filter by execution status
    - `result`: Filter by execution result
    - `browser`: Filter by browser
    - `environment`: Filter by environment
    - `skip`: Pagination offset
    - `limit`: Max results per page
    """
    # Non-admin users can only see their own executions
    user_filter = None if current_user.role == "admin" else current_user.id
    
    executions = crud_executions.get_executions(
        db=db,
        test_case_id=test_case_id,
        user_id=user_filter,
        status=status_filter,
        result=result_filter,
        browser=browser,
        environment=environment,
        skip=skip,
        limit=limit
    )
    
    total = crud_executions.get_execution_count(
        db=db,
        test_case_id=test_case_id,
        user_id=user_filter,
        status=status_filter,
        result=result_filter,
        browser=browser,
        environment=environment
    )
    
    items = [TestExecutionListItem.model_validate(exec) for exec in executions]
    
    return TestExecutionListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


# ============================================================================
# Statistics (MUST be before /executions/{execution_id} to avoid route conflict)
# ============================================================================

@router.get("/executions/stats", response_model=ExecutionStatistics)
def get_execution_statistics(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get execution statistics.
    
    **Authentication required**
    
    Returns comprehensive statistics about test executions.
    Non-admin users see stats for their own executions.
    Admins see stats for all executions.
    """
    user_filter = None if current_user.role == "admin" else current_user.id
    stats = crud_executions.get_execution_statistics(db, user_filter)
    return ExecutionStatistics(**stats)


@router.get("/executions/{execution_id}", response_model=TestExecutionDetailResponse)
def get_execution(
    execution_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get detailed execution information.
    
    **Authentication required**
    
    Returns complete execution details including all steps, logs, and artifacts.
    Non-admin users can only access their own executions.
    """
    execution = crud_executions.get_execution(db, execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and execution.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this execution"
        )
    
    return execution


@router.delete("/executions/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_execution(
    execution_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Delete an execution.
    
    **Authentication required**
    
    Deletes an execution and all its steps.
    Non-admin users can only delete their own executions.
    """
    execution = crud_executions.get_execution(db, execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and execution.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this execution"
        )
    
    crud_executions.delete_execution(db, execution_id)
    return None

