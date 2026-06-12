"""HF-6: notifications, observatory columns, access log."""

import os

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def _add_column_if_missing(engine, table: str, column: str, ddl: str) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns(table)}
    if column not in existing:
        with engine.begin() as conn:
            conn.execute(text(ddl))


def upgrade() -> None:
    from app.db.base import Base
    from app.models.notification import UserNotification  # noqa: F401
    from app.models.observatory import ObservatoryAccessLog  # noqa: F401

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )

    _add_column_if_missing(
        engine,
        "factory_job_events",
        "payload_full",
        "ALTER TABLE factory_job_events ADD COLUMN payload_full JSON",
    )
    _add_column_if_missing(
        engine,
        "factory_job_events",
        "llm_turns",
        "ALTER TABLE factory_job_events ADD COLUMN llm_turns JSON",
    )
    _add_column_if_missing(
        engine,
        "factory_job_events",
        "hermes_session_id",
        "ALTER TABLE factory_job_events ADD COLUMN hermes_session_id VARCHAR(128)",
    )
    _add_column_if_missing(
        engine,
        "factory_job_events",
        "parent_profile",
        "ALTER TABLE factory_job_events ADD COLUMN parent_profile VARCHAR(64)",
    )

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    to_create = []
    if "user_notifications" not in tables:
        to_create.append(UserNotification.__table__)
    if "observatory_access_log" not in tables:
        to_create.append(ObservatoryAccessLog.__table__)
    if to_create:
        Base.metadata.create_all(bind=engine, tables=to_create)


def main() -> None:
    upgrade()


if __name__ == "__main__":
    main()
