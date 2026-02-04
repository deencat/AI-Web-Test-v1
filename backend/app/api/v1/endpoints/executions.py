"""Test execution API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import json
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
from app.services.stagehand_factory import get_stagehand_adapter
from app.services.stagehand_adapter import StagehandAdapter
from app.services.queue_manager import get_queue_manager
from app.services.execution_queue import get_execution_queue

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
    
    # Create initial execution record with QUEUED status (Sprint 3 Day 2)
    execution = crud_executions.create_execution(
        db=db,
        test_case_id=test_case_id,
        user_id=current_user.id,
        browser=request.browser or "chromium",
        environment=request.environment or "dev",
        base_url=request.base_url
    )
    execution_id = execution.id

    # Store trigger details and optional browser profile data
    if request.triggered_by:
        execution.triggered_by = request.triggered_by

    if request.browser_profile_data:
        execution.trigger_details = json.dumps({
            "browser_profile_data": request.browser_profile_data
        })

    http_credentials = (
        request.http_credentials.model_dump()
        if request.http_credentials
        else None
    )
    
    # Set queued timestamp and priority
    execution.queued_at = datetime.utcnow()
    execution.priority = getattr(request, 'priority', 5)  # Default: medium priority
    execution.status = ExecutionStatus.PENDING  # Will be updated to RUNNING by queue
    db.commit()
    db.refresh(execution)
    
    # Add to execution queue (Sprint 3 Day 2)
    queue = get_execution_queue()
    queue_position = queue.add_to_queue(
        execution_id=execution_id,
        test_case_id=test_case_id,
        user_id=current_user.id,
        priority=execution.priority,
        http_credentials=http_credentials
    )
    
    # Update queue position in database
    execution.queue_position = queue_position
    db.commit()
    db.refresh(execution)
    
    # Queue manager will pick up and execute automatically (Sprint 3 Day 2)
    # No need to manually start execution - it's now handled by the queue
    
    # Determine message based on queue status
    if queue_position == 0 and queue.is_under_limit():
        message = f"Test execution starting now for test case '{test_case.title}'"
    else:
        message = f"Test execution queued (position {queue_position}) for test case '{test_case.title}'"
    
    return ExecutionStartResponse(
        id=execution.id,
        test_case_id=execution.test_case_id,
        status=execution.status,
        message=message
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


@router.get("/", response_model=TestExecutionListResponse)
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

@router.get("/stats", response_model=ExecutionStatistics)
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


@router.get("/{execution_id}", response_model=TestExecutionDetailResponse)
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


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
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


# ============================================================================
# Queue Management (Sprint 3 Day 2)
# ============================================================================

@router.get("/queue/status")
def get_queue_status(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get current queue status.
    
    **Authentication required**
    
    Returns information about active and queued executions.
    
    **Response:**
    - `active_count`: Number of currently running executions
    - `queued_count`: Number of executions waiting in queue
    - `max_concurrent`: Maximum concurrent executions allowed
    - `is_under_limit`: Whether more executions can start
    - `queue`: List of queued executions
    - `active`: List of active executions
    """
    queue = get_execution_queue()
    return queue.get_queue_status()


@router.get("/queue/statistics")
def get_queue_statistics(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get queue manager statistics.
    
    **Authentication required**
    
    Returns statistics about the queue manager and execution queue.
    """
    manager = get_queue_manager()
    return manager.get_statistics()


@router.post("/queue/clear")
def clear_queue(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Clear all queued executions.
    
    **Authentication required** (Admin only)
    
    Removes all queued executions (does not affect running ones).
    Use with caution!
    """
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear the queue"
        )
    
    queue = get_execution_queue()
    count = queue.clear_queue()
    
    return {
        "message": f"Queue cleared successfully",
        "removed_count": count
    }


@router.get("/queue/active")
def get_active_executions(
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get list of active (running) executions.
    
    **Authentication required**
    
    Returns list of executions currently being executed.
    """
    queue = get_execution_queue()
    return {
        "active_count": queue.get_active_count(),
        "max_concurrent": queue.max_concurrent,
        "executions": queue.get_active_executions()
    }

