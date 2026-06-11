"""CRUD for journey registry and backlog (HF-2)."""
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.journey_factory import (
    JourneyBacklogItem,
    JourneyRegistryEntry,
    JourneyRegistryProject,
    BacklogStatus,
)
from app.schemas.journey_factory import (
    JourneyRegistryEntryCreate,
    JourneyRegistryEntryUpdate,
    JourneyBacklogEnqueue,
)


def get_project_meta(db: Session, project: str) -> Optional[JourneyRegistryProject]:
    return db.query(JourneyRegistryProject).filter(JourneyRegistryProject.project == project).first()


def upsert_project_meta(
    db: Session,
    project: str,
    reqiq_project_id: Optional[str],
    default_env_config: Optional[dict],
) -> JourneyRegistryProject:
    row = get_project_meta(db, project)
    if row:
        row.reqiq_project_id = reqiq_project_id
        row.default_env_config = default_env_config
    else:
        row = JourneyRegistryProject(
            project=project,
            reqiq_project_id=reqiq_project_id,
            default_env_config=default_env_config,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_registry_entries(
    db: Session,
    project: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> List[JourneyRegistryEntry]:
    q = db.query(JourneyRegistryEntry)
    if project:
        q = q.filter(JourneyRegistryEntry.project == project)
    return q.order_by(JourneyRegistryEntry.slug).offset(skip).limit(limit).all()


def count_registry_entries(db: Session, project: Optional[str] = None) -> int:
    q = db.query(JourneyRegistryEntry)
    if project:
        q = q.filter(JourneyRegistryEntry.project == project)
    return q.count()


def get_registry_entry(db: Session, entry_id: int) -> Optional[JourneyRegistryEntry]:
    return db.query(JourneyRegistryEntry).filter(JourneyRegistryEntry.id == entry_id).first()


def get_registry_by_slug(db: Session, project: str, slug: str) -> Optional[JourneyRegistryEntry]:
    return (
        db.query(JourneyRegistryEntry)
        .filter(JourneyRegistryEntry.project == project, JourneyRegistryEntry.slug == slug)
        .first()
    )


def create_registry_entry(db: Session, data: JourneyRegistryEntryCreate) -> JourneyRegistryEntry:
    row = JourneyRegistryEntry(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_registry_entry(
    db: Session,
    entry: JourneyRegistryEntry,
    data: JourneyRegistryEntryUpdate,
) -> JourneyRegistryEntry:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_registry_entry(db: Session, entry: JourneyRegistryEntry) -> None:
    db.delete(entry)
    db.commit()


def list_backlog_items(
    db: Session,
    status: Optional[str] = None,
    project: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[JourneyBacklogItem]:
    q = db.query(JourneyBacklogItem)
    if status:
        q = q.filter(JourneyBacklogItem.status == status)
    if project:
        q = q.filter(JourneyBacklogItem.project == project)
    return (
        q.order_by(desc(JourneyBacklogItem.priority), JourneyBacklogItem.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_backlog_items(db: Session, status: Optional[str] = None, project: Optional[str] = None) -> int:
    q = db.query(JourneyBacklogItem)
    if status:
        q = q.filter(JourneyBacklogItem.status == status)
    if project:
        q = q.filter(JourneyBacklogItem.project == project)
    return q.count()


def enqueue_backlog_item(db: Session, data: JourneyBacklogEnqueue) -> JourneyBacklogItem:
    entry = get_registry_by_slug(db, data.project, data.journey_slug)
    if not entry:
        raise ValueError(f"Unknown journey slug '{data.journey_slug}' for project '{data.project}'")

    row = JourneyBacklogItem(
        project=data.project,
        journey_slug=data.journey_slug,
        status=BacklogStatus.PENDING.value,
        priority=data.priority,
        params=data.params,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_backlog_status(
    db: Session,
    item_id: int,
    status: str,
    *,
    factory_job_id: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Optional[JourneyBacklogItem]:
    row = db.query(JourneyBacklogItem).filter(JourneyBacklogItem.id == item_id).first()
    if not row:
        return None
    row.status = status
    if factory_job_id is not None:
        row.factory_job_id = factory_job_id
    if error_message is not None:
        row.error_message = error_message
    db.commit()
    db.refresh(row)
    return row
