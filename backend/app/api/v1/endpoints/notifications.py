"""In-app notifications API (HF-6)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud import notification as crud
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationResponse

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
def list_my_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationListResponse:
    items, total, unread = crud.list_notifications(
        db,
        current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(i) for i in items],
        total=total,
        unread=unread,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationResponse:
    row = crud.mark_notification_read(db, notification_id, current_user.id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse.model_validate(row)
