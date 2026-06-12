"""Heal review queue API (HF-5)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_factory_operator
from app.crud import heal_review as crud
from app.models.heal_review import HealReviewStatus
from app.models.user import User
from app.schemas.heal_review import (
    HealReviewItemResponse,
    HealReviewListResponse,
    HealReviewPatch,
)

router = APIRouter()


@router.get("/heal-review", response_model=HealReviewListResponse)
def list_heal_review(
    status: Optional[str] = Query(None, description="open | resolved"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_factory_operator),
) -> HealReviewListResponse:
    items = crud.list_heal_review_items(db, status=status, skip=skip, limit=limit)
    return HealReviewListResponse(
        items=[HealReviewItemResponse.model_validate(i) for i in items],
        total=crud.count_heal_review_items(db, status=status),
    )


@router.patch("/heal-review/{item_id}", response_model=HealReviewItemResponse)
def patch_heal_review(
    item_id: int,
    body: HealReviewPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> HealReviewItemResponse:
    if body.status not in (HealReviewStatus.OPEN.value, HealReviewStatus.RESOLVED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be 'open' or 'resolved'",
        )
    resolved_by = current_user.id if body.status == HealReviewStatus.RESOLVED.value else None
    item = crud.update_heal_review_status(db, item_id, body.status, resolved_by_user_id=resolved_by)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Heal review item not found")
    return HealReviewItemResponse.model_validate(item)
