"""Agent Observatory superadmin APIs (HF-6)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_superadmin
from app.models.user import User
from app.schemas.observatory import HermesSessionResponse, HermesTraceResponse
from app.services.observatory_service import get_hermes_session, get_hermes_trace

router = APIRouter()


@router.get(
    "/jobs/{job_id}/hermes-trace",
    response_model=HermesTraceResponse,
    summary="Full Hermes delegate trace (superadmin only)",
)
def hermes_trace(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
) -> HermesTraceResponse:
    trace = get_hermes_trace(db, job_id, current_user.id)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return trace


@router.get(
    "/hermes/sessions/{session_id}",
    response_model=HermesSessionResponse,
    summary="Hermes session drill-down (superadmin only)",
)
def hermes_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
) -> HermesSessionResponse:
    return get_hermes_session(db, session_id, current_user.id)
