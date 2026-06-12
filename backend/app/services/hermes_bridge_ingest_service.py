"""Ingest Hermes Bridge events into factory_job_events (HF-6.2)."""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.factory_job import FactoryJob, FactoryJobStatus
from app.schemas.hermes_bridge import HermesBridgeEventCreate, HermesBridgeEventResponse
from app.services.factory_job_service import append_job_event, get_factory_job, set_job_status
from app.services.observatory_service import redact_secrets

logger = logging.getLogger(__name__)

_STATUS_EVENTS = {
    "job_started": FactoryJobStatus.RUNNING,
    "job_complete": FactoryJobStatus.COMPLETED,
    "error": FactoryJobStatus.FAILED,
}


def _redact_optional(value: Any) -> Any:
    if value is None:
        return None
    return redact_secrets(copy.deepcopy(value))


def _sync_job_status(db: Session, job: FactoryJob, body: HermesBridgeEventCreate) -> None:
    status = _STATUS_EVENTS.get(body.event_type)
    if not status:
        return

    error_message: Optional[str] = None
    if status == FactoryJobStatus.FAILED:
        if body.message:
            error_message = body.message
        elif body.payload_summary and isinstance(body.payload_summary.get("error"), str):
            error_message = body.payload_summary["error"]
    elif status == FactoryJobStatus.COMPLETED:
        summary_status = (body.payload_summary or {}).get("status")
        if summary_status in ("failed", "error"):
            set_job_status(
                db,
                job,
                FactoryJobStatus.FAILED,
                error_message=body.message or str(summary_status),
            )
            return

    if job.status != status.value:
        set_job_status(db, job, status, error_message=error_message)


def ingest_hermes_bridge_event(
    db: Session,
    body: HermesBridgeEventCreate,
) -> HermesBridgeEventResponse:
    job = get_factory_job(db, body.job_id)
    if not job:
        raise ValueError("job_not_found")

    payload_full = _redact_optional(body.payload_full)
    llm_turns = _redact_optional(body.llm_turns)
    payload_summary = _redact_optional(body.payload_summary)

    event = append_job_event(
        db,
        body.job_id,
        event_type=body.event_type,
        profile=body.profile,
        parent_profile=body.parent_profile,
        message=body.message,
        payload_summary=payload_summary,
        payload_full=payload_full,
        llm_turns=llm_turns,
        hermes_session_id=body.hermes_session_id,
    )

    try:
        _sync_job_status(db, job, body)
    except Exception as exc:
        logger.warning("[HermesBridge] status sync failed for job %s: %s", body.job_id, exc)

    return HermesBridgeEventResponse(
        event_id=event.id,
        job_id=body.job_id,
        event_type=event.event_type,
        created_at=event.created_at,
    )
