"""Create agent_conversations and agent_conversation_messages tables."""

import os

from sqlalchemy import create_engine, inspect

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def upgrade() -> None:
    from app.db.base import Base
    from app.models.agent_conversation import AgentConversation, AgentConversationMessage  # noqa: F401

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)
    if "agent_conversations" in inspector.get_table_names():
        return
    Base.metadata.create_all(
        bind=engine,
        tables=[AgentConversation.__table__, AgentConversationMessage.__table__],
    )


def main() -> None:
    upgrade()


if __name__ == "__main__":
    main()
