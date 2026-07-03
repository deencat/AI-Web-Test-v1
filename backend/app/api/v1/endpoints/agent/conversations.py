"""Agent conversation persistence endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_factory_operator
from app.models.user import User
from app.schemas.agent_conversation import (
    AgentConversationListItem,
    AgentConversationListResponse,
    AgentConversationResponse,
    AgentConversationMessageResponse,
)
from app.services.agent_conversation_service import (
    activate_conversation,
    create_new_conversation,
    get_conversation_for_user,
    get_or_create_active_conversation,
    list_conversations_for_user,
    list_messages,
)

router = APIRouter()


def _to_response(db: Session, conversation) -> AgentConversationResponse:
    return AgentConversationResponse(
        conversation_id=conversation.id,
        project=conversation.project,
        hermes_resume_session=conversation.hermes_resume_session,
        is_active=conversation.is_active,
        messages=[
            AgentConversationMessageResponse.model_validate(m)
            for m in list_messages(db, conversation)
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/conversations",
    response_model=AgentConversationListResponse,
    summary="List saved chat conversations for the current user",
)
def list_conversations(
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentConversationListResponse:
    items = [
        AgentConversationListItem.model_validate(item)
        for item in list_conversations_for_user(db, current_user.id, limit=limit)
    ]
    return AgentConversationListResponse(items=items)


@router.get(
    "/conversations/active",
    response_model=AgentConversationResponse,
    summary="Get or create the active chat conversation for the current user",
)
def get_active(
    project: str = Query("Three-HK"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentConversationResponse:
    conversation = get_or_create_active_conversation(db, current_user.id, project)
    return _to_response(db, conversation)


@router.get(
    "/conversations/{conversation_id}",
    response_model=AgentConversationResponse,
    summary="Get a conversation with messages",
)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentConversationResponse:
    conversation = get_conversation_for_user(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return _to_response(db, conversation)


@router.post(
    "/conversations/{conversation_id}/activate",
    response_model=AgentConversationResponse,
    summary="Set a conversation as the active thread to resume later",
)
def activate_conversation_endpoint(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentConversationResponse:
    conversation = activate_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return _to_response(db, conversation)


@router.post(
    "/conversations/new",
    response_model=AgentConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new chat conversation",
)
def new_conversation(
    project: str = Query("Three-HK"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentConversationResponse:
    conversation = create_new_conversation(db, current_user.id, project)
    return _to_response(db, conversation)


@router.post(
    "/conversations/{conversation_id}/sync-job/{job_id}",
    response_model=AgentConversationResponse,
    summary="Finalize assistant reply from a completed job into the conversation",
)
def sync_job_to_conversation(
    conversation_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_factory_operator),
) -> AgentConversationResponse:
    from app.services.agent_conversation_service import finalize_conversation_from_job
    from app.services.factory_job_service import get_factory_job

    conversation = get_conversation_for_user(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    job = get_factory_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    finalize_conversation_from_job(db, job)
    db.refresh(conversation)
    return _to_response(db, conversation)
