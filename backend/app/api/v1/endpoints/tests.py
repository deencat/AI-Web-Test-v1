"""Test case CRUD API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.test_case import TestType, TestStatus, Priority
from app.schemas.test_case import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseListResponse,
    TestStatistics
)
from app.crud import test_case as crud

router = APIRouter()


def sanitize_test_case_for_response(test_case):
    """
    Sanitize test case data to handle empty strings in description and expected_result.
    This ensures backward compatibility with existing test cases that may have empty strings.
    Converts SQLAlchemy model to Pydantic model with sanitized fields.
    """
    # Create a dict from the SQLAlchemy object without modifying it
    # Handle None and empty strings for description and expected_result
    description = test_case.description
    if not description or (isinstance(description, str) and description.strip() == ''):
        description = 'No description provided'
    
    expected_result = test_case.expected_result
    if not expected_result or (isinstance(expected_result, str) and expected_result.strip() == ''):
        expected_result = 'No expected result specified'
    
    test_case_dict = {
        'id': test_case.id,
        'title': test_case.title,
        'description': description,
        'test_type': test_case.test_type,
        'priority': test_case.priority,
        'status': test_case.status,
        'steps': test_case.steps,
        'expected_result': expected_result,
        'preconditions': test_case.preconditions,
        'test_data': test_case.test_data,
        'category_id': test_case.category_id,
        'tags': test_case.tags,
        'test_metadata': test_case.test_metadata,
        'created_at': test_case.created_at,
        'updated_at': test_case.updated_at,
        'user_id': test_case.user_id,
        'scenario_id': test_case.scenario_id,
        'template_id': test_case.template_id,
    }
    
    # Convert dict to Pydantic model
    return TestCaseResponse.model_validate(test_case_dict)


@router.get("/stats", response_model=TestStatistics)
def get_test_statistics(
    user_id: Optional[int] = Query(None, description="Filter statistics by user ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get test case statistics.
    
    **Authentication Required**
    
    **Query Parameters:**
    - `user_id`: Optional user ID to filter statistics (admin only)
    
    **Response:**
    - `total`: Total number of test cases
    - `by_status`: Count of tests by status
    - `by_type`: Count of tests by type
    - `by_priority`: Count of tests by priority
    
    **Example Response:**
    ```json
    {
        "total": 42,
        "by_status": {"pending": 10, "passed": 25, "failed": 5, "in_progress": 2, "skipped": 0},
        "by_type": {"e2e": 20, "unit": 15, "integration": 5, "api": 2},
        "by_priority": {"high": 15, "medium": 20, "low": 7}
    }
    ```
    """
    # Non-admin users can only see their own stats
    if user_id and current_user.role != "admin":
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view other users' statistics"
            )
    
    # If no user_id specified and not admin, show only current user's stats
    if user_id is None and current_user.role != "admin":
        user_id = current_user.id
    
    stats = crud.get_test_statistics(db=db, user_id=user_id)
    
    return stats


@router.get("", response_model=TestCaseListResponse)
def list_test_cases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    test_type: Optional[TestType] = Query(None, description="Filter by test type"),
    status: Optional[TestStatus] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List test cases with optional filtering and pagination.
    
    **Authentication Required**
    
    **Query Parameters:**
    - `skip`: Number of records to skip (pagination)
    - `limit`: Maximum number of records to return (max 1000)
    - `test_type`: Filter by test type (e2e, unit, integration, api)
    - `status`: Filter by status (pending, in_progress, passed, failed, skipped)
    - `priority`: Filter by priority (high, medium, low)
    - `user_id`: Filter by user ID (requires admin role)
    
    **Response:**
    - `items`: Array of test cases
    - `total`: Total count of test cases matching filters
    - `skip`: Number of records skipped
    - `limit`: Maximum records returned
    """
    # Non-admin users can only see their own tests (unless user_id not specified)
    if user_id and current_user.role != "admin":
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view other users' tests"
            )
    
    # If no user_id specified and not admin, show only current user's tests
    if user_id is None and current_user.role != "admin":
        user_id = current_user.id
    
    test_cases, total = crud.get_test_cases(
        db=db,
        skip=skip,
        limit=limit,
        test_type=test_type,
        status=status,
        priority=priority,
        user_id=user_id
    )
    
    # Sanitize test cases to handle empty strings in description and expected_result
    sanitized_cases = [sanitize_test_case_for_response(test_case) for test_case in test_cases]
    
    return TestCaseListResponse(
        items=sanitized_cases,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def create_test_case(
    test_case: TestCaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new test case.
    
    **Authentication Required**
    
    **Request Body:**
    - `title`: Test case title (1-255 chars)
    - `description`: Test case description
    - `test_type`: Type of test (e2e, unit, integration, api)
    - `priority`: Priority level (high, medium, low)
    - `status`: Initial status (default: pending)
    - `steps`: Array of test steps (at least 1)
    - `expected_result`: Expected test result
    - `preconditions`: Optional preconditions
    - `test_data`: Optional test data (max 10KB)
    
    **Response:**
    - Created test case with ID and timestamps
    """
    try:
        db_test_case = crud.create_test_case(
            db=db,
            test_case=test_case,
            user_id=current_user.id
        )
        return db_test_case
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test case: {str(e)}"
        )


@router.get("/{test_case_id}", response_model=TestCaseResponse)
def get_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific test case by ID.
    
    **Authentication Required**
    
    **Path Parameters:**
    - `test_case_id`: ID of the test case
    
    **Response:**
    - Test case details
    
    **Errors:**
    - 404: Test case not found
    - 403: Not authorized to view this test case
    """
    db_test_case = crud.get_test_case(db=db, test_case_id=test_case_id)
    
    if not db_test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    # Check authorization
    if db_test_case.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this test case"
        )
    
    return db_test_case


@router.put("/{test_case_id}", response_model=TestCaseResponse)
def update_test_case(
    test_case_id: int,
    updates: TestCaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a test case.
    
    **Authentication Required**
    
    **Path Parameters:**
    - `test_case_id`: ID of the test case
    
    **Request Body:**
    - Any fields from TestCaseCreate (all optional)
    - Only provided fields will be updated
    
    **Response:**
    - Updated test case
    
    **Errors:**
    - 404: Test case not found
    - 403: Not authorized to update this test case
    """
    # Check if test case exists
    db_test_case = crud.get_test_case(db=db, test_case_id=test_case_id)
    
    if not db_test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    # Check authorization
    if db_test_case.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this test case"
        )
    
    # Update test case
    updated_test_case = crud.update_test_case(
        db=db,
        test_case_id=test_case_id,
        updates=updates
    )
    
    return updated_test_case


@router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(
    test_case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a test case.
    
    **Authentication Required**
    
    **Path Parameters:**
    - `test_case_id`: ID of the test case
    
    **Response:**
    - 204 No Content on success
    
    **Errors:**
    - 404: Test case not found
    - 403: Not authorized to delete this test case
    """
    # Check if test case exists
    db_test_case = crud.get_test_case(db=db, test_case_id=test_case_id)
    
    if not db_test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    # Check authorization
    if db_test_case.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this test case"
        )
    
    # Delete test case
    success = crud.delete_test_case(db=db, test_case_id=test_case_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete test case"
        )
    
    return None

