"""Journey backlog API (HF-2)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_factory_operator
from app.crud import journey_factory as crud
from app.models.user import User
from app.schemas.journey_factory import (
    JourneyBacklogEnqueue,
    JourneyBacklogItemResponse,
    JourneyBacklogListResponse,
)

router = APIRouter()


@router.get("/backlog", response_model=JourneyBacklogListResponse)
def list_backlog(
    status: Optional[str] = Query(None, description="pending | in_progress | done | failed"),
    project: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_factory_operator),
) -> JourneyBacklogListResponse:
    items = crud.list_backlog_items(db, status=status, project=project, skip=skip, limit=limit)
    return JourneyBacklogListResponse(
        items=[JourneyBacklogItemResponse.model_validate(i) for i in items],
        total=crud.count_backlog_items(db, status=status, project=project),
    )


@router.post(
    "/backlog",
    response_model=JourneyBacklogItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def enqueue_backlog(
    body: JourneyBacklogEnqueue,
    db: Session = Depends(get_db),
    _: User = Depends(require_factory_operator),
) -> JourneyBacklogItemResponse:
    try:
        row = crud.enqueue_backlog_item(db, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JourneyBacklogItemResponse.model_validate(row)
