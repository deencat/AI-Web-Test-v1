"""CRUD for user notifications (HF-6)."""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.notification import UserNotification


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: Optional[str] = None,
    notification_type: str = "factory_job",
    link: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> UserNotification:
    row = UserNotification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        link=link,
        metadata_json=metadata,
        read=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_notifications(
    db: Session,
    user_id: int,
    *,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[UserNotification], int, int]:
    base = db.query(UserNotification).filter(UserNotification.user_id == user_id)
    total = base.count()
    unread = base.filter(UserNotification.read.is_(False)).count()
    q = base.order_by(UserNotification.created_at.desc())
    if unread_only:
        q = q.filter(UserNotification.read.is_(False))
    items = q.offset(skip).limit(limit).all()
    return items, total, unread


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Optional[UserNotification]:
    row = (
        db.query(UserNotification)
        .filter(UserNotification.id == notification_id, UserNotification.user_id == user_id)
        .first()
    )
    if not row:
        return None
    row.read = True
    db.commit()
    db.refresh(row)
    return row
