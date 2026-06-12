"""Factory job REST + SSE endpoints (HF-1)."""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_factory_operator
from app.models.user import User
from app.schemas.factory_job import (
    FactoryJobCreate,
    FactoryJobCreatedResponse,
    FactoryJobEventResponse,
    FactoryJobResponse,
)
from app.services.factory_job_service import create_factory_job, get_factory_job, list_job_events
from app.services.factory_scheduler_service import submit_factory_job_async

router = APIRouter()


def _job_to_response(job) -> FactoryJobResponse:
    return FactoryJobResponse(
        job_id=job.id,
        job_type=job.job_type,
        project=job.project,
        params=job.params,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        events=[FactoryJobEventResponse.model_validate(e) for e in (job.events or [])],
    )


@router.post(
    "/jobs",
    response_model=FactoryJobCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a factory job",
)
def create_job(
    body: FactoryJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> FactoryJobCreatedResponse:
    job = create_factory_job(db, body, created_by_user_id=current_user.id)
    submit_factory_job_async(job.id)
    return FactoryJobCreatedResponse(job_id=job.id, status=job.status)


@router.get(
    "/jobs/{job_id}",
    response_model=FactoryJobResponse,
    summary="Get factory job status and events",
)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> FactoryJobResponse:
    job = get_factory_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _job_to_response(job)


@router.get(
    "/jobs/{job_id}/events",
    response_model=list[FactoryJobEventResponse],
    summary="List factory job events",
)
def get_job_events(
    job_id: str,
    after_id: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> list[FactoryJobEventResponse]:
    job = get_factory_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    events = list_job_events(db, job_id, after_id=after_id)
    return [FactoryJobEventResponse.model_validate(e) for e in events]


async def _job_sse_generator(
    job_id: str,
    request: Request,
    poll_interval: float = 1.0,
) -> AsyncGenerator[bytes, None]:
    from app.db.session import SessionLocal

    last_id = 0
    terminal_statuses = {"completed", "failed", "cancelled"}

    while True:
        if await request.is_disconnected():
            break

        db = SessionLocal()
        try:
            job = get_factory_job(db, job_id)
            if not job:
                payload = {"error": "Job not found"}
                yield f"event: error\ndata: {json.dumps(payload)}\n\n".encode()
                break

            events = list_job_events(db, job_id, after_id=last_id)
            for event in events:
                data = FactoryJobEventResponse.model_validate(event).model_dump(mode="json")
                yield f"event: job_event\ndata: {json.dumps(data)}\n\n".encode()
                last_id = event.id

            if job.status in terminal_statuses:
                payload = {"status": job.status, "job_id": job_id}
                yield f"event: job_complete\ndata: {json.dumps(payload)}\n\n".encode()
                break
        finally:
            db.close()

        await asyncio.sleep(poll_interval)


@router.get(
    "/jobs/{job_id}/stream",
    response_class=StreamingResponse,
    summary="Stream factory job events (SSE)",
)
async def stream_job(
    request: Request,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> StreamingResponse:
    job = get_factory_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return StreamingResponse(
        _job_sse_generator(job_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

