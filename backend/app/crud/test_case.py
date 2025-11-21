"""CRUD operations for test cases."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.test_case import TestCase, TestType, TestStatus, Priority
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate


def create_test_case(db: Session, test_case: TestCaseCreate, user_id: int) -> TestCase:
    """
    Create a new test case.
    
    Args:
        db: Database session
        test_case: Test case data
        user_id: ID of user creating the test
        
    Returns:
        Created test case
    """
    db_test_case = TestCase(
        title=test_case.title,
        description=test_case.description,
        test_type=test_case.test_type,
        priority=test_case.priority,
        status=test_case.status,
        steps=test_case.steps,
        expected_result=test_case.expected_result,
        preconditions=test_case.preconditions,
        test_data=test_case.test_data,
        user_id=user_id
    )
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


def get_test_case(db: Session, test_case_id: int) -> Optional[TestCase]:
    """
    Get a test case by ID.
    
    Args:
        db: Database session
        test_case_id: Test case ID
        
    Returns:
        Test case or None if not found
    """
    return db.query(TestCase).filter(TestCase.id == test_case_id).first()


def get_test_cases(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    test_type: Optional[TestType] = None,
    status: Optional[TestStatus] = None,
    priority: Optional[Priority] = None,
    user_id: Optional[int] = None
) -> tuple[List[TestCase], int]:
    """
    Get test cases with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        test_type: Filter by test type
        status: Filter by status
        priority: Filter by priority
        user_id: Filter by user ID
        
    Returns:
        Tuple of (test cases list, total count)
    """
    query = db.query(TestCase)
    
    # Apply filters
    if test_type:
        query = query.filter(TestCase.test_type == test_type)
    if status:
        query = query.filter(TestCase.status == status)
    if priority:
        query = query.filter(TestCase.priority == priority)
    if user_id:
        query = query.filter(TestCase.user_id == user_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    test_cases = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    
    return test_cases, total


def update_test_case(
    db: Session,
    test_case_id: int,
    updates: TestCaseUpdate
) -> Optional[TestCase]:
    """
    Update a test case.
    
    Args:
        db: Database session
        test_case_id: Test case ID
        updates: Fields to update
        
    Returns:
        Updated test case or None if not found
    """
    db_test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not db_test_case:
        return None
    
    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_test_case, field, value)
    
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


def delete_test_case(db: Session, test_case_id: int) -> bool:
    """
    Delete a test case.
    
    Args:
        db: Database session
        test_case_id: Test case ID
        
    Returns:
        True if deleted, False if not found
    """
    db_test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not db_test_case:
        return False
    
    db.delete(db_test_case)
    db.commit()
    return True


def get_test_cases_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[TestCase], int]:
    """
    Get all test cases created by a specific user.
    
    Args:
        db: Database session
        user_id: User ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (test cases list, total count)
    """
    query = db.query(TestCase).filter(TestCase.user_id == user_id)
    total = query.count()
    test_cases = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    return test_cases, total


def get_test_cases_by_type(
    db: Session,
    test_type: TestType,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[TestCase], int]:
    """
    Get all test cases of a specific type.
    
    Args:
        db: Database session
        test_type: Test type to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (test cases list, total count)
    """
    query = db.query(TestCase).filter(TestCase.test_type == test_type)
    total = query.count()
    test_cases = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    return test_cases, total


def get_test_cases_by_status(
    db: Session,
    status: TestStatus,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[TestCase], int]:
    """
    Get all test cases with a specific status.
    
    Args:
        db: Database session
        status: Status to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (test cases list, total count)
    """
    query = db.query(TestCase).filter(TestCase.status == status)
    total = query.count()
    test_cases = query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    return test_cases, total


def get_test_statistics(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get test case statistics.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter statistics
        
    Returns:
        Dictionary with statistics
    """
    query = db.query(TestCase)
    if user_id:
        query = query.filter(TestCase.user_id == user_id)
    
    total = query.count()
    
    # Count by status
    by_status = {}
    for status in TestStatus:
        count = query.filter(TestCase.status == status).count()
        by_status[status.value] = count
    
    # Count by type
    by_type = {}
    for test_type in TestType:
        count = query.filter(TestCase.test_type == test_type).count()
        by_type[test_type.value] = count
    
    # Count by priority
    by_priority = {}
    for priority in Priority:
        count = query.filter(TestCase.priority == priority).count()
        by_priority[priority.value] = count
    
    return {
        "total": total,
        "by_status": by_status,
        "by_type": by_type,
        "by_priority": by_priority
    }


def search_test_cases(
    db: Session,
    query: str,
    user_id: Optional[int] = None,
    test_type: Optional[TestType] = None,
    status: Optional[TestStatus] = None,
    priority: Optional[Priority] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[TestCase], int]:
    """
    Search test cases across multiple fields.
    
    Args:
        db: Database session
        query: Search query string
        user_id: Optional user ID to filter by
        test_type: Optional test type to filter by
        status: Optional status to filter by
        priority: Optional priority to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (test cases list, total count)
    """
    # Build base query
    db_query = db.query(TestCase)
    
    # Apply user filter
    if user_id:
        db_query = db_query.filter(TestCase.user_id == user_id)
    
    # Apply search across multiple fields
    if query:
        search_pattern = f"%{query}%"
        db_query = db_query.filter(
            or_(
                TestCase.title.ilike(search_pattern),
                TestCase.description.ilike(search_pattern),
                TestCase.expected_result.ilike(search_pattern),
                TestCase.preconditions.ilike(search_pattern)
            )
        )
    
    # Apply additional filters
    if test_type:
        db_query = db_query.filter(TestCase.test_type == test_type)
    
    if status:
        db_query = db_query.filter(TestCase.status == status)
    
    if priority:
        db_query = db_query.filter(TestCase.priority == priority)
    
    # Get total count
    total = db_query.count()
    
    # Get paginated results
    test_cases = db_query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    
    return test_cases, total

