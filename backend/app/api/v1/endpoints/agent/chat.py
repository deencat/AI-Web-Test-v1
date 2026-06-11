"""Agent chat endpoint (HF-1)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_factory_operator
from app.models.user import User
from app.schemas.factory_job import AgentChatRequest, AgentChatResponse
from app.services.agent_chat_service import parse_chat_to_job
from app.services.factory_job_service import create_factory_job
from app.services.factory_scheduler_service import submit_factory_job_async

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Conversational factory job trigger",
)
def agent_chat(
    body: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentChatResponse:
    try:
        job_body, reply = parse_chat_to_job(body.message, body.context)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job = create_factory_job(db, job_body, created_by_user_id=current_user.id)
    submit_factory_job_async(job.id)
    return AgentChatResponse(job_id=job.id, reply=reply)
