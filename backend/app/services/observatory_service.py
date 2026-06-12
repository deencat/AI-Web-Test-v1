"""Agent Observatory: trace retrieval and secret redaction (HF-6)."""
from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.factory_job import FactoryJob, FactoryJobEvent
from app.models.observatory import ObservatoryAccessLog
from app.schemas.observatory import HermesSessionResponse, HermesTraceEventResponse, HermesTraceResponse

_SECRET_KEY_PATTERN = re.compile(
    r"(secret|password|api[_-]?key|token|authorization|bearer)",
    re.IGNORECASE,
)
_REDACT_VALUE = "***REDACTED***"


def redact_secrets(value: Any) -> Any:
    """Recursively redact sensitive keys in dict/list structures."""
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, val in value.items():
            if _SECRET_KEY_PATTERN.search(str(key)):
                out[key] = _REDACT_VALUE
            else:
                out[key] = redact_secrets(val)
        return out
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        if _SECRET_KEY_PATTERN.search(value) and len(value) > 8:
            return _REDACT_VALUE
        return value
    return value


def _log_access(
    db: Session,
    *,
    user_id: int,
    resource: str,
    job_id: Optional[str] = None,
    hermes_session_id: Optional[str] = None,
) -> None:
    db.add(
        ObservatoryAccessLog(
            user_id=user_id,
            job_id=job_id,
            hermes_session_id=hermes_session_id,
            resource=resource,
        )
    )
    db.commit()


def _event_to_trace(event: FactoryJobEvent) -> HermesTraceEventResponse:
    payload_full = redact_secrets(copy.deepcopy(event.payload_full)) if event.payload_full else None
    llm_turns = redact_secrets(copy.deepcopy(event.llm_turns)) if event.llm_turns else None
    summary = redact_secrets(copy.deepcopy(event.payload_summary)) if event.payload_summary else None
    return HermesTraceEventResponse(
        id=event.id,
        event_type=event.event_type,
        profile=event.profile,
        parent_profile=event.parent_profile,
        message=event.message,
        payload_summary=summary,
        payload_full=payload_full,
        llm_turns=llm_turns,
        hermes_session_id=event.hermes_session_id,
        created_at=event.created_at,
    )


def get_hermes_trace(db: Session, job_id: str, user_id: int) -> Optional[HermesTraceResponse]:
    job = db.query(FactoryJob).filter(FactoryJob.id == job_id).first()
    if not job:
        return None

    _log_access(db, user_id=user_id, resource="hermes-trace", job_id=job_id)

    session_ids = sorted(
        {e.hermes_session_id for e in (job.events or []) if e.hermes_session_id}
    )
    events = [_event_to_trace(e) for e in (job.events or [])]
    return HermesTraceResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        hermes_session_ids=session_ids,
        events=events,
    )


def get_hermes_session(db: Session, session_id: str, user_id: int) -> HermesSessionResponse:
    _log_access(
        db,
        user_id=user_id,
        resource="hermes-session",
        hermes_session_id=session_id,
    )

    events = (
        db.query(FactoryJobEvent)
        .filter(FactoryJobEvent.hermes_session_id == session_id)
        .order_by(FactoryJobEvent.id.asc())
        .all()
    )
    job_ids = sorted({e.job_id for e in events})
    return HermesSessionResponse(
        hermes_session_id=session_id,
        job_ids=job_ids,
        events=[_event_to_trace(e) for e in events],
    )
