"""Create system_settings table for QA Factory UI overrides."""

import os

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def upgrade() -> None:
    from app.db.base import Base
    from app.models.system_settings import SystemSettings  # noqa: F401

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )

    inspector = inspect(engine)
    if "system_settings" not in inspector.get_table_names():
        Base.metadata.create_all(bind=engine, tables=[SystemSettings.__table__])
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO system_settings (id) VALUES (1)")
            )


def downgrade() -> None:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS system_settings"))
