"""
API endpoints for Test Suites
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_test_suite
from app.models.user import User
from app.schemas.test_suite import (
    TestSuiteCreate,
    TestSuiteUpdate,
    TestSuiteResponse,
    SuiteExecutionRequest,
    SuiteExecutionResponse
)
from app.services.suite_execution_service import execute_test_suite

router = APIRouter()


@router.post("/", response_model=TestSuiteResponse, status_code=201)
def create_suite(
    *,
    db: Session = Depends(deps.get_db),
    suite_in: TestSuiteCreate,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new test suite with test cases.
    
    Test cases will be executed in the order specified in test_case_ids.
    """
    # Validate test cases exist (optional - uncomment if needed)
    # from app.crud import crud_test
    # for test_id in suite_in.test_case_ids:
    #     if not crud_test.get_test(db, test_id):
    #         raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
    
    suite = crud_test_suite.create_test_suite(db, suite_in, current_user.id)
    return suite


@router.get("/", response_model=List[TestSuiteResponse])
def list_suites(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tags: Optional[List[str]] = Query(None, description="Filter by tags")
):
    """
    Get all test suites for the current user.
    
    Optionally filter by tags.
    """
    suites = crud_test_suite.get_test_suites(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        tags=tags
    )
    return suites


@router.get("/{suite_id}", response_model=TestSuiteResponse)
def get_suite(
    suite_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get a specific test suite by ID.
    
    Returns suite details with all test cases in execution order.
    """
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    # Check ownership
    if suite.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this suite")
    
    return suite


@router.put("/{suite_id}", response_model=TestSuiteResponse)
def update_suite(
    suite_id: int,
    suite_update: TestSuiteUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update a test suite.
    
    Can update name, description, tags, and/or test_case_ids.
    Updating test_case_ids will replace the entire test list.
    """
    # Check ownership
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    if suite.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this suite")
    
    updated_suite = crud_test_suite.update_test_suite(db, suite_id, suite_update)
    return updated_suite


@router.delete("/{suite_id}", status_code=204)
def delete_suite(
    suite_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a test suite.
    
    This will cascade delete all suite items but NOT the test cases themselves.
    """
    # Check ownership
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    if suite.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this suite")
    
    crud_test_suite.delete_test_suite(db, suite_id)
    return None


@router.post("/{suite_id}/run", response_model=SuiteExecutionResponse)
async def run_suite(
    suite_id: int,
    execution_request: SuiteExecutionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Execute all test cases in a suite.
    
    Tests will run in the order defined in the suite.
    Returns a suite execution ID and list of individual test execution IDs.
    
    Options:
    - stop_on_failure: Stop running subsequent tests if one fails
    - parallel: Run tests in parallel (not yet implemented)
    """
    # Check ownership
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    if suite.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to run this suite")
    
    # Execute suite using merged approach (single browser session)
    # This merges all test cases into ONE execution with shared browser
    from app.services.suite_execution_service import execute_test_suite_merged
    
    result = await execute_test_suite_merged(
        db=db,
        suite_id=suite_id,
        user_id=current_user.id,
        browser=execution_request.browser,
        environment=execution_request.environment
    )
    
    return result


@router.get("/{suite_id}/executions", response_model=List[dict])
def get_suite_execution_history(
    suite_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get execution history for a specific test suite.
    """
    # Check ownership
    suite = crud_test_suite.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    if suite.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this suite")
    
    executions = crud_test_suite.get_suite_executions(
        db,
        suite_id=suite_id,
        skip=skip,
        limit=limit
    )
    return executions
