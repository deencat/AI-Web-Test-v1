"""
CRUD operations for Test Suites
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.test_suite import TestSuite, TestSuiteItem, SuiteExecution
from app.schemas.test_suite import TestSuiteCreate, TestSuiteUpdate


def create_test_suite(
    db: Session,
    suite_data: TestSuiteCreate,
    user_id: int
) -> TestSuite:
    """Create a new test suite with test cases"""
    # Create suite
    suite = TestSuite(
        name=suite_data.name,
        description=suite_data.description,
        tags=suite_data.tags,
        user_id=user_id
    )
    db.add(suite)
    db.flush()  # Get suite.id
    
    # Create suite items with execution order
    for order, test_case_id in enumerate(suite_data.test_case_ids, start=1):
        suite_item = TestSuiteItem(
            suite_id=suite.id,
            test_case_id=test_case_id,
            execution_order=order
        )
        db.add(suite_item)
    
    db.commit()
    db.refresh(suite)
    
    # Reload with relationships
    return db.query(TestSuite).options(
        joinedload(TestSuite.items).joinedload(TestSuiteItem.test_case)
    ).filter(TestSuite.id == suite.id).first()


def get_test_suite(db: Session, suite_id: int) -> Optional[TestSuite]:
    """Get a test suite by ID with items"""
    return db.query(TestSuite).options(
        joinedload(TestSuite.items).joinedload(TestSuiteItem.test_case)
    ).filter(TestSuite.id == suite_id).first()


def get_test_suites(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    tags: Optional[List[str]] = None
) -> List[TestSuite]:
    """Get all test suites for a user, optionally filtered by tags"""
    query = db.query(TestSuite).options(
        joinedload(TestSuite.items).joinedload(TestSuiteItem.test_case)
    ).filter(TestSuite.user_id == user_id)
    
    if tags:
        # Filter by tags (JSON contains check)
        for tag in tags:
            query = query.filter(TestSuite.tags.contains(tag))
    
    return query.offset(skip).limit(limit).all()


def update_test_suite(
    db: Session,
    suite_id: int,
    suite_update: TestSuiteUpdate
) -> Optional[TestSuite]:
    """Update a test suite"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        return None
    
    # Update basic fields
    update_data = suite_update.model_dump(exclude_unset=True, exclude={'test_case_ids'})
    for field, value in update_data.items():
        setattr(suite, field, value)
    
    # Update test cases if provided
    if suite_update.test_case_ids is not None:
        # Delete existing items
        db.query(TestSuiteItem).filter(TestSuiteItem.suite_id == suite_id).delete()
        
        # Create new items
        for order, test_case_id in enumerate(suite_update.test_case_ids, start=1):
            suite_item = TestSuiteItem(
                suite_id=suite_id,
                test_case_id=test_case_id,
                execution_order=order
            )
            db.add(suite_item)
    
    db.commit()
    
    # Reload with relationships
    return db.query(TestSuite).options(
        joinedload(TestSuite.items).joinedload(TestSuiteItem.test_case)
    ).filter(TestSuite.id == suite_id).first()


def delete_test_suite(db: Session, suite_id: int) -> bool:
    """Delete a test suite (cascade deletes items)"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        return False
    
    db.delete(suite)
    db.commit()
    return True


def create_suite_execution(
    db: Session,
    suite_id: int,
    user_id: int,
    browser: str,
    environment: str,
    triggered_by: str,
    stop_on_failure: bool,
    total_tests: int
) -> SuiteExecution:
    """Create a suite execution record"""
    execution = SuiteExecution(
        suite_id=suite_id,
        user_id=user_id,
        browser=browser,
        environment=environment,
        triggered_by=triggered_by,
        stop_on_failure=stop_on_failure,
        total_tests=total_tests,
        status="pending"
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def update_suite_execution(
    db: Session,
    execution_id: int,
    **kwargs
) -> Optional[SuiteExecution]:
    """Update suite execution status and results"""
    execution = db.query(SuiteExecution).filter(SuiteExecution.id == execution_id).first()
    if not execution:
        return None
    
    for field, value in kwargs.items():
        setattr(execution, field, value)
    
    db.commit()
    db.refresh(execution)
    return execution


def get_suite_execution(db: Session, execution_id: int) -> Optional[SuiteExecution]:
    """Get a suite execution by ID"""
    return db.query(SuiteExecution).filter(SuiteExecution.id == execution_id).first()


def get_suite_executions(
    db: Session,
    suite_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[SuiteExecution]:
    """Get suite executions, optionally filtered by suite_id or user_id"""
    query = db.query(SuiteExecution)
    
    if suite_id:
        query = query.filter(SuiteExecution.suite_id == suite_id)
    if user_id:
        query = query.filter(SuiteExecution.user_id == user_id)
    
    return query.order_by(SuiteExecution.created_at.desc()).offset(skip).limit(limit).all()
