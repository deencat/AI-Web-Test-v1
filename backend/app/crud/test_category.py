"""CRUD operations for user-defined test categories."""
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.test_case import TestCase
from app.models.test_category import TestCategory
from app.schemas.test_category import TestCategoryCreate, TestCategoryUpdate


def get_test_category(
    db: Session,
    category_id: int,
    user_id: int,
) -> Optional[TestCategory]:
    """Return a category by ID scoped to the user."""
    return (
        db.query(TestCategory)
        .filter(
            TestCategory.id == category_id,
            TestCategory.user_id == user_id,
        )
        .first()
    )


def get_test_category_by_name(
    db: Session,
    name: str,
    user_id: int,
) -> Optional[TestCategory]:
    """Return a category by name scoped to the user."""
    return (
        db.query(TestCategory)
        .filter(
            TestCategory.name == name,
            TestCategory.user_id == user_id,
        )
        .first()
    )


def get_test_categories(
    db: Session,
    user_id: int,
) -> List[TestCategory]:
    """List all categories for a user ordered by sort_order then name."""
    return (
        db.query(TestCategory)
        .filter(TestCategory.user_id == user_id)
        .order_by(TestCategory.sort_order, TestCategory.name)
        .all()
    )


def get_test_count_for_category(db: Session, category_id: int) -> int:
    """Count test cases assigned to a category."""
    return (
        db.query(func.count(TestCase.id))
        .filter(TestCase.test_category_id == category_id)
        .scalar()
        or 0
    )


def create_test_category(
    db: Session,
    category: TestCategoryCreate,
    user_id: int,
) -> TestCategory:
    """Create a new test category."""
    db_category = TestCategory(
        name=category.name,
        description=category.description,
        color=category.color,
        sort_order=category.sort_order,
        user_id=user_id,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_test_category(
    db: Session,
    category_id: int,
    user_id: int,
    updates: TestCategoryUpdate,
) -> Optional[TestCategory]:
    """Update a category owned by the user."""
    db_category = get_test_category(db=db, category_id=category_id, user_id=user_id)
    if not db_category:
        return None

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_test_category(
    db: Session,
    category_id: int,
    user_id: int,
) -> bool:
    """
    Delete a category owned by the user.

    Nullifies test_category_id on affected tests before delete so behavior is
    explicit even when DB-level ON DELETE SET NULL is unavailable.
    """
    db_category = get_test_category(db=db, category_id=category_id, user_id=user_id)
    if not db_category:
        return False

    db.query(TestCase).filter(TestCase.test_category_id == category_id).update(
        {TestCase.test_category_id: None},
        synchronize_session=False,
    )
    db.delete(db_category)
    db.commit()
    return True


def batch_assign_test_category(
    db: Session,
    test_ids: List[int],
    test_category_id: Optional[int],
    user_id: int,
) -> tuple[int, List[int]]:
    """
    Bulk assign or clear test_category_id on owned test cases.

    Returns:
        Tuple of (updated_count, failed_ids)
    """
    updated = 0
    failed: List[int] = []

    for test_id in test_ids:
        test_case = (
            db.query(TestCase)
            .filter(TestCase.id == test_id, TestCase.user_id == user_id)
            .first()
        )
        if not test_case:
            failed.append(test_id)
            continue

        test_case.test_category_id = test_category_id
        updated += 1

    if updated:
        db.commit()

    return updated, failed
