"""Hermes Bridge event ingestion (HF-6.2)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_hermes_bridge_secret
from app.schemas.hermes_bridge import HermesBridgeEventCreate, HermesBridgeEventResponse
from app.services.hermes_bridge_ingest_service import ingest_hermes_bridge_event

router = APIRouter()


@router.post(
    "/hermes/events",
    response_model=HermesBridgeEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Hermes Bridge delegate / LLM events",
)
def post_hermes_event(
    body: HermesBridgeEventCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_hermes_bridge_secret),
) -> HermesBridgeEventResponse:
    try:
        return ingest_hermes_bridge_event(db, body)
    except ValueError as exc:
        if str(exc) == "job_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            ) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
