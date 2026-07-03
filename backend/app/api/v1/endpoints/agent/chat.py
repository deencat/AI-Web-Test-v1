"""Agent chat endpoint (HF-1)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import _FACTORY_OPERATOR_MIN_RANK, _role_rank, get_db, require_factory_operator
from app.models.user import User
from app.schemas.factory_job import AgentChatRequest, AgentChatResponse
from app.services.agent_chat_service import parse_chat_to_job
from app.services.agent_conversation_service import (
    append_message,
    get_conversation_for_user,
    get_or_create_active_conversation,
)
from app.services.factory_job_service import create_factory_job
from app.services.factory_bridge_client import submit_job_to_bridge_async
from app.services.factory_scheduler_service import submit_factory_job_async
from app.utils.hermes_session import clean_hermes_resume_session

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
    rank = _role_rank(current_user.role)
    allow_open_chat = rank >= _FACTORY_OPERATOR_MIN_RANK
    prefer_open_chat = allow_open_chat

    project = str(body.context.get("project") or "Three-HK")
    conversation_id = str(body.context.get("conversation_id") or "").strip()

    if conversation_id:
        conversation = get_conversation_for_user(db, conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conversation = get_or_create_active_conversation(db, current_user.id, project)

    resume_session = clean_hermes_resume_session(
        conversation.hermes_resume_session or body.context.get("hermes_resume_session")
    )
    chat_context = {
        **body.context,
        "project": project,
        "conversation_id": conversation.id,
    }
    if resume_session:
        chat_context["hermes_resume_session"] = resume_session

    try:
        job_body, reply = parse_chat_to_job(
            body.message,
            chat_context,
            allow_open_chat=allow_open_chat,
            prefer_open_chat=prefer_open_chat,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job = create_factory_job(db, job_body, created_by_user_id=current_user.id)
    append_message(
        db,
        conversation,
        role="user",
        text=body.message.strip(),
        job_id=job.id,
    )

    if submit_job_to_bridge_async(job.id):
        reply = f"{reply} Routed to QA Orchestrator node."
    else:
        submit_factory_job_async(job.id)

    return AgentChatResponse(
        job_id=job.id,
        conversation_id=conversation.id,
        reply=reply,
    )
