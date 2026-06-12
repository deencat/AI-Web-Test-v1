"""CRUD for heal review queue and heal attempts (HF-5)."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.heal_review import FactoryHealAttempt, HealReviewItem, HealReviewStatus


def get_heal_attempt(db: Session, execution_id: int) -> Optional[FactoryHealAttempt]:
    return (
        db.query(FactoryHealAttempt)
        .filter(FactoryHealAttempt.execution_id == execution_id)
        .first()
    )


def increment_heal_attempt(
    db: Session,
    execution_id: int,
    *,
    action: str,
    test_case_id: Optional[int] = None,
    error: Optional[str] = None,
) -> FactoryHealAttempt:
    row = get_heal_attempt(db, execution_id)
    if row:
        row.attempt_count += 1
        row.last_action = action
        row.last_test_case_id = test_case_id
        row.last_error = error
        row.updated_at = datetime.utcnow()
    else:
        row = FactoryHealAttempt(
            execution_id=execution_id,
            attempt_count=1,
            last_action=action,
            last_test_case_id=test_case_id,
            last_error=error,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_heal_review_item(
    db: Session,
    *,
    execution_id: int,
    test_case_id: Optional[int],
    reason: str,
) -> HealReviewItem:
    existing = (
        db.query(HealReviewItem)
        .filter(
            HealReviewItem.execution_id == execution_id,
            HealReviewItem.status == HealReviewStatus.OPEN.value,
        )
        .first()
    )
    if existing:
        return existing

    item = HealReviewItem(
        execution_id=execution_id,
        test_case_id=test_case_id,
        reason=reason,
        status=HealReviewStatus.OPEN.value,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_heal_review_items(
    db: Session,
    *,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[HealReviewItem]:
    query = db.query(HealReviewItem).order_by(HealReviewItem.created_at.desc())
    if status:
        query = query.filter(HealReviewItem.status == status)
    return query.offset(skip).limit(limit).all()


def count_heal_review_items(db: Session, *, status: Optional[str] = None) -> int:
    query = db.query(HealReviewItem)
    if status:
        query = query.filter(HealReviewItem.status == status)
    return query.count()


def update_heal_review_status(
    db: Session,
    item_id: int,
    status: str,
    resolved_by_user_id: Optional[int] = None,
) -> Optional[HealReviewItem]:
    item = db.query(HealReviewItem).filter(HealReviewItem.id == item_id).first()
    if not item:
        return None
    item.status = status
    if status == HealReviewStatus.RESOLVED.value:
        item.resolved_at = datetime.utcnow()
        item.resolved_by_user_id = resolved_by_user_id
    db.commit()
    db.refresh(item)
    return item
