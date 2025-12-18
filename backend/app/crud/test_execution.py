"""CRUD operations for test executions."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.models.test_execution import TestExecution, TestExecutionStep, ExecutionStatus, ExecutionResult
from app.schemas.test_execution import (
    TestExecutionCreate,
    TestExecutionUpdate,
    TestExecutionStepCreate
)


# ============================================================================
# Execution CRUD
# ============================================================================

def create_execution(
    db: Session,
    test_case_id: int,
    user_id: int,
    browser: str = "chromium",
    environment: str = "dev",
    base_url: Optional[str] = None
) -> TestExecution:
    """Create a new test execution."""
    db_execution = TestExecution(
        test_case_id=test_case_id,
        user_id=user_id,
        browser=browser,
        environment=environment,
        base_url=base_url,
        status=ExecutionStatus.PENDING,
        total_steps=0,
        passed_steps=0,
        failed_steps=0,
        skipped_steps=0
    )
    db.add(db_execution)
    db.commit()
    db.refresh(db_execution)
    return db_execution


def start_execution(db: Session, execution_id: int) -> TestExecution:
    """Mark execution as started and record start time."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if execution:
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        db.commit()
        db.refresh(execution)
        print(f"[DEBUG] Updated execution {execution_id} to RUNNING status")
    return execution


def complete_execution(
    db: Session,
    execution_id: int,
    result: ExecutionResult,
    total_steps: int = 0,
    passed_steps: int = 0,
    failed_steps: int = 0,
    screenshot_path: Optional[str] = None,
    video_path: Optional[str] = None
) -> TestExecution:
    """Mark execution as completed with results."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if execution:
        execution.status = ExecutionStatus.COMPLETED
        execution.result = result
        execution.completed_at = datetime.utcnow()
        execution.total_steps = total_steps
        execution.passed_steps = passed_steps
        execution.failed_steps = failed_steps
        execution.screenshot_path = screenshot_path
        execution.video_path = video_path
        
        # Calculate duration
        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.duration_seconds = duration
        
        db.commit()
        db.refresh(execution)
        print(f"[DEBUG] Completed execution {execution_id} with result {result}, {passed_steps}/{total_steps} passed")
    return execution


def fail_execution(
    db: Session,
    execution_id: int,
    error_message: str
) -> TestExecution:
    """Mark execution as failed with error message."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if execution:
        execution.status = ExecutionStatus.FAILED
        execution.result = ExecutionResult.ERROR
        execution.completed_at = datetime.utcnow()
        execution.error_message = error_message
        
        # Calculate duration if started
        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.duration_seconds = duration
        
        db.commit()
        db.refresh(execution)
    return execution


def get_execution(db: Session, execution_id: int) -> Optional[TestExecution]:
    """Get execution by ID."""
    return db.query(TestExecution).filter(TestExecution.id == execution_id).first()


def get_executions(
    db: Session,
    test_case_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[ExecutionStatus] = None,
    result: Optional[ExecutionResult] = None,
    browser: Optional[str] = None,
    environment: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TestExecution]:
    """
    Get executions with optional filters.
    
    Args:
        db: Database session
        test_case_id: Filter by test case
        user_id: Filter by user
        status: Filter by status
        result: Filter by result
        browser: Filter by browser
        environment: Filter by environment
        skip: Number of records to skip
        limit: Maximum records to return
    """
    query = db.query(TestExecution)
    
    if test_case_id is not None:
        query = query.filter(TestExecution.test_case_id == test_case_id)
    
    if user_id is not None:
        query = query.filter(TestExecution.user_id == user_id)
    
    if status is not None:
        query = query.filter(TestExecution.status == status)
    
    if result is not None:
        query = query.filter(TestExecution.result == result)
    
    if browser:
        query = query.filter(TestExecution.browser == browser)
    
    if environment:
        query = query.filter(TestExecution.environment == environment)
    
    return query.order_by(desc(TestExecution.created_at)).offset(skip).limit(limit).all()


def get_execution_count(
    db: Session,
    test_case_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[ExecutionStatus] = None,
    result: Optional[ExecutionResult] = None,
    browser: Optional[str] = None,
    environment: Optional[str] = None
) -> int:
    """Get count of executions matching filters."""
    query = db.query(func.count(TestExecution.id))
    
    if test_case_id is not None:
        query = query.filter(TestExecution.test_case_id == test_case_id)
    
    if user_id is not None:
        query = query.filter(TestExecution.user_id == user_id)
    
    if status is not None:
        query = query.filter(TestExecution.status == status)
    
    if result is not None:
        query = query.filter(TestExecution.result == result)
    
    if browser:
        query = query.filter(TestExecution.browser == browser)
    
    if environment:
        query = query.filter(TestExecution.environment == environment)
    
    return query.scalar()


def update_execution(db: Session, execution_id: int, updates: TestExecutionUpdate) -> Optional[TestExecution]:
    """Update an execution."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    
    if execution:
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(execution, field, value)
        
        db.commit()
        db.refresh(execution)
    
    return execution


def delete_execution(db: Session, execution_id: int) -> bool:
    """Delete an execution."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    
    if execution:
        db.delete(execution)
        db.commit()
        return True
    
    return False


# ============================================================================
# Execution Step CRUD
# ============================================================================

def create_execution_step(
    db: Session,
    execution_id: int,
    step_number: int,
    step_description: str,
    expected_result: Optional[str] = None,
    result: ExecutionResult = ExecutionResult.PASS,
    actual_result: Optional[str] = None,
    error_message: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    selector_used: Optional[str] = None,
    action_method: Optional[str] = None
) -> TestExecutionStep:
    """Create an execution step."""
    db_step = TestExecutionStep(
        execution_id=execution_id,
        step_number=step_number,
        step_description=step_description,
        expected_result=expected_result,
        result=result,
        actual_result=actual_result,
        error_message=error_message,
        screenshot_path=screenshot_path,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        duration_seconds=duration_seconds,
        selector_used=selector_used,
        action_method=action_method
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


def get_execution_steps(db: Session, execution_id: int) -> List[TestExecutionStep]:
    """Get all steps for an execution."""
    return db.query(TestExecutionStep).filter(
        TestExecutionStep.execution_id == execution_id
    ).order_by(TestExecutionStep.step_number).all()


def update_execution_step(
    db: Session,
    step_id: int,
    result: ExecutionResult,
    actual_result: Optional[str] = None,
    error_message: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    screenshot_path: Optional[str] = None
) -> Optional[TestExecutionStep]:
    """Update an execution step."""
    step = db.query(TestExecutionStep).filter(TestExecutionStep.id == step_id).first()
    
    if step:
        step.result = result
        if actual_result is not None:
            step.actual_result = actual_result
        if error_message is not None:
            step.error_message = error_message
        if duration_seconds is not None:
            step.duration_seconds = duration_seconds
        if screenshot_path is not None:
            step.screenshot_path = screenshot_path
        
        db.commit()
        db.refresh(step)
    
    return step


# ============================================================================
# Statistics
# ============================================================================

def get_execution_statistics(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get execution statistics.
    
    Args:
        db: Database session
        user_id: Filter by user (None for all users, requires admin)
    """
    query = db.query(TestExecution)
    
    if user_id is not None:
        query = query.filter(TestExecution.user_id == user_id)
    
    # Total executions
    total_executions = query.count()
    
    # By status
    by_status = {}
    for status in ExecutionStatus:
        count = query.filter(TestExecution.status == status).count()
        by_status[status.value] = count
    
    # By result
    by_result = {}
    for result in ExecutionResult:
        count = query.filter(TestExecution.result == result).count()
        by_result[result.value] = count
    
    # By browser
    browsers = db.query(TestExecution.browser, func.count(TestExecution.id)).filter(
        TestExecution.browser.isnot(None)
    )
    if user_id is not None:
        browsers = browsers.filter(TestExecution.user_id == user_id)
    by_browser = dict(browsers.group_by(TestExecution.browser).all())
    
    # By environment
    environments = db.query(TestExecution.environment, func.count(TestExecution.id)).filter(
        TestExecution.environment.isnot(None)
    )
    if user_id is not None:
        environments = environments.filter(TestExecution.user_id == user_id)
    by_environment = dict(environments.group_by(TestExecution.environment).all())
    
    # Pass rate (completed executions with pass result)
    completed_count = query.filter(TestExecution.status == ExecutionStatus.COMPLETED).count()
    passed_count = query.filter(TestExecution.result == ExecutionResult.PASS).count()
    pass_rate = (passed_count / completed_count * 100) if completed_count > 0 else 0.0
    
    # Average duration
    avg_duration = db.query(func.avg(TestExecution.duration_seconds)).filter(
        TestExecution.duration_seconds.isnot(None)
    )
    if user_id is not None:
        avg_duration = avg_duration.filter(TestExecution.user_id == user_id)
    avg_duration = avg_duration.scalar() or 0.0
    
    # Total duration in hours
    total_duration = db.query(func.sum(TestExecution.duration_seconds)).filter(
        TestExecution.duration_seconds.isnot(None)
    )
    if user_id is not None:
        total_duration = total_duration.filter(TestExecution.user_id == user_id)
    total_duration_seconds = total_duration.scalar() or 0.0
    total_duration_hours = total_duration_seconds / 3600
    
    # Executions by time period
    now = datetime.utcnow()
    executions_last_24h = query.filter(TestExecution.created_at >= now - timedelta(hours=24)).count()
    executions_last_7d = query.filter(TestExecution.created_at >= now - timedelta(days=7)).count()
    executions_last_30d = query.filter(TestExecution.created_at >= now - timedelta(days=30)).count()
    
    # Most executed tests (top 5)
    most_executed = db.query(
        TestExecution.test_case_id,
        func.count(TestExecution.id).label('execution_count')
    )
    if user_id is not None:
        most_executed = most_executed.filter(TestExecution.user_id == user_id)
    
    most_executed = most_executed.group_by(TestExecution.test_case_id).order_by(
        desc('execution_count')
    ).limit(5).all()
    
    most_executed_tests = [
        {"test_case_id": test_id, "execution_count": count}
        for test_id, count in most_executed
    ]
    
    return {
        "total_executions": total_executions,
        "by_status": by_status,
        "by_result": by_result,
        "by_browser": by_browser,
        "by_environment": by_environment,
        "pass_rate": round(pass_rate, 2),
        "average_duration_seconds": round(avg_duration, 2) if avg_duration else None,
        "total_duration_hours": round(total_duration_hours, 2),
        "executions_last_24h": executions_last_24h,
        "executions_last_7d": executions_last_7d,
        "executions_last_30d": executions_last_30d,
        "most_executed_tests": most_executed_tests
    }


# ============================================================================
# Utility Functions
# ============================================================================

def update_execution_summary(db: Session, execution_id: int) -> Optional[TestExecution]:
    """
    Update execution summary (counts, result) based on steps.
    Call this after steps are added/updated.
    """
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    
    if not execution:
        return None
    
    steps = db.query(TestExecutionStep).filter(TestExecutionStep.execution_id == execution_id).all()
    
    execution.total_steps = len(steps)
    execution.passed_steps = sum(1 for s in steps if s.result == ExecutionResult.PASS)
    execution.failed_steps = sum(1 for s in steps if s.result == ExecutionResult.FAIL)
    execution.skipped_steps = sum(1 for s in steps if s.result == ExecutionResult.SKIP)
    
    # Determine overall result
    if execution.status == ExecutionStatus.COMPLETED:
        if execution.failed_steps > 0:
            execution.result = ExecutionResult.FAIL
        elif execution.passed_steps > 0:
            execution.result = ExecutionResult.PASS
        else:
            execution.result = ExecutionResult.SKIP
    
    db.commit()
    db.refresh(execution)
    
    return execution

