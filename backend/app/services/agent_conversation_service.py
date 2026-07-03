"""Persist and restore Agent Console chat threads."""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.agent_conversation import AgentConversation, AgentConversationMessage
from app.models.factory_job import FactoryJob
from app.services.factory_job_reply_service import extract_orchestrator_reply
from app.utils.hermes_session import clean_hermes_resume_session

_HERMES_SESSION_RE = (
    re.compile(r"Session:\s*(\S+)"),
    re.compile(r"hermes --resume (\S+)"),
)


def _hermes_resume_from_job(job: FactoryJob) -> Optional[str]:
    for event in reversed(job.events or []):
        payload = event.payload_summary
        if isinstance(payload, dict):
            session = clean_hermes_resume_session(payload.get("hermes_resume_session"))
            if session:
                return session
        if event.llm_turns:
            for turn in reversed(event.llm_turns):
                if not isinstance(turn, dict):
                    continue
                content = turn.get("content")
                if not content:
                    continue
                text = str(content)
                for pattern in _HERMES_SESSION_RE:
                    match = pattern.search(text)
                    if match:
                        return match.group(1).strip()
    return None


def get_conversation_for_user(
    db: Session,
    conversation_id: str,
    user_id: int,
) -> Optional[AgentConversation]:
    return (
        db.query(AgentConversation)
        .filter(
            AgentConversation.id == conversation_id,
            AgentConversation.user_id == user_id,
        )
        .first()
    )


def get_active_conversation(db: Session, user_id: int) -> Optional[AgentConversation]:
    return (
        db.query(AgentConversation)
        .filter(
            AgentConversation.user_id == user_id,
            AgentConversation.is_active.is_(True),
        )
        .order_by(AgentConversation.updated_at.desc())
        .first()
    )


def get_or_create_active_conversation(
    db: Session,
    user_id: int,
    project: Optional[str] = None,
) -> AgentConversation:
    conversation = get_active_conversation(db, user_id)
    if conversation:
        if project and conversation.project != project:
            conversation.project = project
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
        return conversation
    return create_new_conversation(db, user_id, project)


def create_new_conversation(
    db: Session,
    user_id: int,
    project: Optional[str] = None,
) -> AgentConversation:
    db.query(AgentConversation).filter(
        AgentConversation.user_id == user_id,
        AgentConversation.is_active.is_(True),
    ).update({"is_active": False})

    conversation = AgentConversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        project=project,
        is_active=True,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def append_message(
    db: Session,
    conversation: AgentConversation,
    *,
    role: str,
    text: str,
    job_id: Optional[str] = None,
) -> AgentConversationMessage:
    message = AgentConversationMessage(
        conversation_id=conversation.id,
        role=role,
        text=text.strip(),
        job_id=job_id,
    )
    conversation.updated_at = datetime.utcnow()
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def _assistant_message_for_job(
    db: Session,
    conversation_id: str,
    job_id: str,
) -> Optional[AgentConversationMessage]:
    return (
        db.query(AgentConversationMessage)
        .filter(
            AgentConversationMessage.conversation_id == conversation_id,
            AgentConversationMessage.job_id == job_id,
            AgentConversationMessage.role == "assistant",
        )
        .first()
    )


def finalize_conversation_from_job(db: Session, job: FactoryJob) -> None:
    """Append assistant reply and Hermes session after a factory job completes."""
    from sqlalchemy.orm import joinedload

    job = (
        db.query(FactoryJob)
        .options(joinedload(FactoryJob.events))
        .filter(FactoryJob.id == job.id)
        .first()
    )
    if not job:
        return

    params = job.params or {}
    conversation_id = params.get("conversation_id")
    if not conversation_id or not isinstance(conversation_id, str):
        return

    conversation = (
        db.query(AgentConversation)
        .filter(AgentConversation.id == conversation_id)
        .first()
    )
    if not conversation:
        return

    if _assistant_message_for_job(db, conversation.id, job.id):
        resume = _hermes_resume_from_job(job)
        if resume:
            conversation.hermes_resume_session = clean_hermes_resume_session(resume)
            conversation.updated_at = datetime.utcnow()
            db.commit()
        return

    reply = extract_orchestrator_reply(job)
    if not reply and job.status == "failed":
        reply = (job.error_message or "").strip() or None

    if reply:
        append_message(
            db,
            conversation,
            role="assistant",
            text=reply,
            job_id=job.id,
        )

    resume = _hermes_resume_from_job(job)
    if resume:
        conversation.hermes_resume_session = clean_hermes_resume_session(resume)
        conversation.updated_at = datetime.utcnow()
        db.commit()


def list_messages(db: Session, conversation: AgentConversation) -> List[AgentConversationMessage]:
    return (
        db.query(AgentConversationMessage)
        .filter(AgentConversationMessage.conversation_id == conversation.id)
        .order_by(AgentConversationMessage.id.asc())
        .all()
    )
