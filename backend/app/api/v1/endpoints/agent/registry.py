"""Journey registry CRUD API (HF-2)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_factory_operator, require_role, _ROLE_RANK
from app.crud import journey_factory as crud
from app.services.factory_change_scan_service import snapshot_status_for_url
from app.models.user import User
from app.schemas.journey_factory import (
    JourneyRegistryEntryCreate,
    JourneyRegistryEntryResponse,
    JourneyRegistryEntryUpdate,
    JourneyRegistryListResponse,
    JourneyRegistryProjectResponse,
)

router = APIRouter()
require_admin = require_role(_ROLE_RANK["admin"], "admin")


@router.get("/registry", response_model=JourneyRegistryListResponse)
def list_registry(
    project: Optional[str] = Query(None, description="Filter by project name"),
    db: Session = Depends(get_db),
    _: User = Depends(require_factory_operator),
) -> JourneyRegistryListResponse:
    items = crud.list_registry_entries(db, project=project)
    meta = crud.get_project_meta(db, project) if project else None
    return JourneyRegistryListResponse(
        project_meta=JourneyRegistryProjectResponse.model_validate(meta) if meta else None,
        items=[JourneyRegistryEntryResponse.model_validate(i) for i in items],
        total=crud.count_registry_entries(db, project=project),
    )


@router.post(
    "/registry",
    response_model=JourneyRegistryEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_registry_entry(
    body: JourneyRegistryEntryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> JourneyRegistryEntryResponse:
    if crud.get_registry_by_slug(db, body.project, body.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Journey '{body.slug}' already exists for project '{body.project}'",
        )
    row = crud.create_registry_entry(db, body)
    return JourneyRegistryEntryResponse.model_validate(row)


@router.get("/registry/snapshot-status")
def registry_snapshot_status(
    project: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_factory_operator),
) -> dict:
    """Per-journey change-detection status for registry UI badges (HF-4)."""
    items = crud.list_registry_entries(db, project=project)
    return {
        row.slug: snapshot_status_for_url(db, row.feature_url)
        for row in items
    }


@router.patch("/registry/{entry_id}", response_model=JourneyRegistryEntryResponse)
def update_registry_entry(
    entry_id: int,
    body: JourneyRegistryEntryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> JourneyRegistryEntryResponse:
    entry = crud.get_registry_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registry entry not found")
    updated = crud.update_registry_entry(db, entry, body)
    return JourneyRegistryEntryResponse.model_validate(updated)


@router.delete("/registry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registry_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    entry = crud.get_registry_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registry entry not found")
    crud.delete_registry_entry(db, entry)
