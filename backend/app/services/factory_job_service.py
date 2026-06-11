"""CRUD and event helpers for factory jobs (HF-1)."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.factory_job import FactoryJob, FactoryJobEvent, FactoryJobStatus
from app.schemas.factory_job import FactoryJobCreate


def create_factory_job(
    db: Session,
    body: FactoryJobCreate,
    created_by_user_id: Optional[int],
) -> FactoryJob:
    job = FactoryJob(
        id=str(uuid.uuid4()),
        job_type=body.job_type,
        project=body.project,
        params=body.params or {},
        status=FactoryJobStatus.QUEUED.value,
        created_by_user_id=created_by_user_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    append_job_event(
        db,
        job.id,
        event_type="job_queued",
        profile="factory_worker",
        message=f"Job queued: {body.job_type}",
        payload_summary={"job_type": body.job_type, "params": body.params or {}},
    )
    return job


def get_factory_job(db: Session, job_id: str) -> Optional[FactoryJob]:
    return db.query(FactoryJob).filter(FactoryJob.id == job_id).first()


def list_job_events(db: Session, job_id: str, after_id: int = 0) -> List[FactoryJobEvent]:
    q = db.query(FactoryJobEvent).filter(FactoryJobEvent.job_id == job_id)
    if after_id:
        q = q.filter(FactoryJobEvent.id > after_id)
    return q.order_by(FactoryJobEvent.id.asc()).all()


def append_job_event(
    db: Session,
    job_id: str,
    *,
    event_type: str,
    profile: Optional[str] = None,
    message: Optional[str] = None,
    payload_summary: Optional[Dict[str, Any]] = None,
) -> FactoryJobEvent:
    event = FactoryJobEvent(
        job_id=job_id,
        event_type=event_type,
        profile=profile,
        message=message,
        payload_summary=payload_summary,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def set_job_status(
    db: Session,
    job: FactoryJob,
    status: FactoryJobStatus,
    *,
    error_message: Optional[str] = None,
) -> FactoryJob:
    job.status = status.value
    if status == FactoryJobStatus.RUNNING and not job.started_at:
        job.started_at = datetime.utcnow()
    if status in (FactoryJobStatus.COMPLETED, FactoryJobStatus.FAILED, FactoryJobStatus.CANCELLED):
        job.completed_at = datetime.utcnow()
    if error_message is not None:
        job.error_message = error_message
    db.commit()
    db.refresh(job)
    return job
