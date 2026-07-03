"""Unit tests for agent conversation persistence."""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.agent_conversation import AgentConversation, AgentConversationMessage
from app.models.factory_job import FactoryJob, FactoryJobEvent, FactoryJobStatus
from app.models.user import User
from app.services.agent_conversation_service import (
    append_message,
    create_new_conversation,
    finalize_conversation_from_job,
    get_or_create_active_conversation,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            AgentConversation.__table__,
            AgentConversationMessage.__table__,
            FactoryJob.__table__,
            FactoryJobEvent.__table__,
        ],
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def factory_user(db) -> User:
    suffix = uuid.uuid4().hex[:8]
    user = User(
        email=f"conv-{suffix}@test.local",
        username=f"conv_{suffix}",
        hashed_password="x",
        is_active=True,
        role="agent_operator",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_get_or_create_active_conversation(db, factory_user: User) -> None:
    first = get_or_create_active_conversation(db, factory_user.id, "Three-HK")
    second = get_or_create_active_conversation(db, factory_user.id, "Three-HK")
    assert first.id == second.id
    assert first.is_active is True


def test_create_new_conversation_deactivates_previous(db, factory_user: User) -> None:
    old = get_or_create_active_conversation(db, factory_user.id)
    new = create_new_conversation(db, factory_user.id)
    db.refresh(old)
    assert old.is_active is False
    assert new.is_active is True
    assert new.id != old.id


def test_finalize_conversation_from_job_appends_assistant(db, factory_user: User) -> None:
    conversation = create_new_conversation(db, factory_user.id)
    job_id = str(uuid.uuid4())
    job = FactoryJob(
        id=job_id,
        job_type="orchestrator_chat",
        project="Three-HK",
        params={"conversation_id": conversation.id, "message": "hello"},
        status=FactoryJobStatus.COMPLETED.value,
        created_by_user_id=factory_user.id,
    )
    db.add(job)
    db.commit()

    event = FactoryJobEvent(
        job_id=job_id,
        event_type="delegate_complete",
        profile="qa-orchestrator",
        llm_turns=[{"role": "assistant", "content": '{"summary": "Hello back"}'}],
    )
    db.add(event)
    db.commit()

    append_message(db, conversation, role="user", text="hello", job_id=job_id)

    finalize_conversation_from_job(db, job)

    messages = (
        db.query(AgentConversationMessage)
        .filter(AgentConversationMessage.conversation_id == conversation.id)
        .order_by(AgentConversationMessage.id.asc())
        .all()
    )
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].text == "Hello back"

    db.refresh(conversation)
    assert conversation.hermes_resume_session is None


def test_finalize_extracts_hermes_session(db, factory_user: User) -> None:
    conversation = create_new_conversation(db, factory_user.id)
    job_id = str(uuid.uuid4())
    job = FactoryJob(
        id=job_id,
        job_type="orchestrator_chat",
        project="Three-HK",
        params={"conversation_id": conversation.id},
        status=FactoryJobStatus.COMPLETED.value,
        created_by_user_id=factory_user.id,
    )
    db.add(job)
    db.commit()

    event = FactoryJobEvent(
        job_id=job_id,
        event_type="delegate_complete",
        profile="qa-orchestrator",
        payload_summary={"hermes_resume_session": "sess-abc123"},
        llm_turns=[{"role": "assistant", "content": '{"summary": "Done"}'}],
    )
    db.add(event)
    db.commit()

    finalize_conversation_from_job(db, job)

    row = db.query(AgentConversation).filter(AgentConversation.id == conversation.id).first()
    assert row is not None
    assert row.hermes_resume_session == "sess-abc123"
