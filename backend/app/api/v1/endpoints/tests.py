"""Test case CRUD API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.test_case import TestType, TestStatus, Priority, ReadinessStatus
from app.schemas.test_case import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseListResponse,
    TestStatistics,
    BatchDeleteRequest,
    BatchDeleteResponse,
    BatchCategoryRequest,
    BatchCategoryResponse,
    BatchReadinessRequest,
    BatchReadinessResponse,
    TestCaseCloneRequest,
)
from app.crud import test_case as crud
from app.crud import test_category as category_crud

router = APIRouter()


def _coerce_readiness_status(value) -> ReadinessStatus:
    """Normalize readiness to a valid enum; default draft for missing/invalid."""
    if isinstance(value, ReadinessStatus):
        return value
    if isinstance(value, str):
        try:
            return ReadinessStatus(value)
        except ValueError:
            return ReadinessStatus.DRAFT
    return ReadinessStatus.DRAFT


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
        'readiness_status': _coerce_readiness_status(
            getattr(test_case, 'readiness_status', None)
        ),
        'steps': test_case.steps,
        'expected_result': expected_result,
        'preconditions': test_case.preconditions,
        'test_data': test_case.test_data,
        'category_id': test_case.category_id,
        'test_category_id': test_case.test_category_id,
        'tags': test_case.tags,
        'test_metadata': test_case.test_metadata,
        'created_at': test_case.created_at,
        'updated_at': test_case.updated_at,
        'user_id': test_case.user_id,
        'scenario_id': test_case.scenario_id,
        'template_id': test_case.template_id,
        'requires_runtime_credentials': getattr(test_case, 'requires_runtime_credentials', False),
    }

    if getattr(test_case, 'test_category', None):
        test_case_dict['test_category'] = {
            'id': test_case.test_category.id,
            'name': test_case.test_category.name,
            'color': test_case.test_category.color,
        }
    
    # Convert dict to Pydantic model
    return TestCaseResponse.model_validate(test_case_dict)


def _validate_test_category_ownership(
    db: Session,
    test_category_id: Optional[int],
    user_id: int,
) -> None:
    """Ensure test_category_id belongs to the current user when provided."""
    if test_category_id is None:
        return

    category = category_crud.get_test_category(
        db=db,
        category_id=test_category_id,
        user_id=user_id,
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid test_category_id for current user",
        )


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
    test_category_id: Optional[int] = Query(
        None,
        description=(
            "Filter by user-defined category ID. "
            "Use 0 to return only uncategorized tests (test_category_id IS NULL)."
        ),
    ),
    uncategorized: bool = Query(
        False,
        description="When true, return only uncategorized tests (test_category_id IS NULL)",
    ),
    readiness_status: Optional[ReadinessStatus] = Query(
        None,
        description="Filter by workflow readiness (draft, ready_to_test, blocked)",
    ),
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
    - `status`: Filter by execution status (pending, in_progress, passed, failed, skipped)
    - `priority`: Filter by priority (high, medium, low)
    - `test_category_id`: Filter by user-defined category; use `0` for uncategorized only
    - `uncategorized`: When true, return only tests without a user-defined category
    - `readiness_status`: Filter by readiness tag (draft, ready_to_test, blocked)
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
        user_id=user_id,
        test_category_id=test_category_id,
        uncategorized=uncategorized,
        readiness_status=readiness_status,
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
        _validate_test_category_ownership(
            db=db,
            test_category_id=test_case.test_category_id,
            user_id=current_user.id,
        )
        db_test_case = crud.create_test_case(
            db=db,
            test_case=test_case,
            user_id=current_user.id
        )
        return sanitize_test_case_for_response(db_test_case)
    except HTTPException:
        raise
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
    
    return sanitize_test_case_for_response(db_test_case)


@router.post("/{test_case_id}/clone", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def clone_test_case_endpoint(
    test_case_id: int,
    body: TestCaseCloneRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Clone an existing test case.

    Creates an independent copy with a smart title suffix, fresh timestamps,
    and all step content preserved. Does not copy executions or schedules.
    """
    original = crud.get_test_case(db=db, test_case_id=test_case_id)

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found",
        )

    if original.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to clone this test case",
        )

    if body and body.new_title:
        new_title = body.new_title
        if crud.title_exists_for_user(db, current_user.id, new_title):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A test case with this title already exists",
            )
    else:
        new_title = crud._generate_clone_title(db, current_user.id, original.title)

    cloned = crud.clone_test_case(
        db=db,
        original=original,
        user_id=current_user.id,
        new_title=new_title,
    )
    return sanitize_test_case_for_response(cloned)


@router.patch("/batch/category", response_model=BatchCategoryResponse)
def batch_assign_test_category(
    body: BatchCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Bulk assign or clear user-defined category on test cases.

    **Authentication Required**

    **Request Body:**
    - `test_ids`: List of test case IDs (1–100)
    - `test_category_id`: Category to assign, or null to uncategorize

    **Response:**
    - `updated`: Number of tests updated
    - `failed`: IDs not updated (not found or not owned)
    """
    _validate_test_category_ownership(
        db=db,
        test_category_id=body.test_category_id,
        user_id=current_user.id,
    )

    updated, failed = category_crud.batch_assign_test_category(
        db=db,
        test_ids=body.test_ids,
        test_category_id=body.test_category_id,
        user_id=current_user.id,
    )
    return BatchCategoryResponse(updated=updated, failed=failed)


@router.patch("/batch/readiness", response_model=BatchReadinessResponse)
def batch_assign_readiness(
    body: BatchReadinessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Bulk assign readiness_status on test cases.

    **Authentication Required**

    **Request Body:**
    - `test_ids`: List of test case IDs (1–100)
    - `readiness_status`: draft | ready_to_test | blocked

    **Response:**
    - `updated`: Number of tests updated
    - `failed`: IDs not updated (not found or not owned)
    """
    updated, failed = crud.batch_assign_readiness(
        db=db,
        test_ids=body.test_ids,
        readiness_status=body.readiness_status,
        user_id=current_user.id,
    )
    return BatchReadinessResponse(updated=updated, failed=failed)


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

    if updates.test_category_id is not None:
        _validate_test_category_ownership(
            db=db,
            test_category_id=updates.test_category_id,
            user_id=current_user.id,
        )
    
    # Update test case
    updated_test_case = crud.update_test_case(
        db=db,
        test_case_id=test_case_id,
        updates=updates
    )
    
    return sanitize_test_case_for_response(updated_test_case)


@router.delete("/batch", response_model=BatchDeleteResponse)
def batch_delete_test_cases(
    body: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Batch delete test cases.

    **Authentication Required**

    **Request Body:**
    - `ids`: List of test case IDs to delete (1–100 items)

    **Response:**
    - `deleted`: Number of successfully deleted test cases
    - `failed`: List of IDs that could not be deleted (not found, not owned, or DB error)

    **Errors:**
    - 400: ids is empty or exceeds 100
    """
    ids = body.ids

    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids list must not be empty"
        )

    if len(ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete more than 100 test cases in a single request"
        )

    deleted_count = 0
    failed_ids: list[int] = []

    for test_id in ids:
        db_test_case = crud.get_test_case(db=db, test_case_id=test_id)

        if not db_test_case:
            failed_ids.append(test_id)
            continue

        # Ownership check — admins can delete any test
        if db_test_case.user_id != current_user.id and current_user.role != "admin":
            failed_ids.append(test_id)
            continue

        success = crud.delete_test_case(db=db, test_case_id=test_id)
        if success:
            deleted_count += 1
        else:
            failed_ids.append(test_id)

    return BatchDeleteResponse(deleted=deleted_count, failed=failed_ids)


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

