"""Add local_vllm_api_key to user_settings.

Allows auth-required OpenAI-compatible local_vllm endpoints to store a per-user
bearer token instead of always falling back to LOCAL_VLLM_API_KEY or "local".

Safe to run multiple times (idempotent column-exists guard).
Picked up automatically by run_all_migrations_auto() on server start.
"""

import os

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
TABLE_NAME = "user_settings"
COLUMN_NAME = "local_vllm_api_key"
COLUMN_TYPE = "TEXT"


def upgrade() -> None:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)

    if TABLE_NAME not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns(TABLE_NAME)}
    if COLUMN_NAME in existing_columns:
        return

    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {COLUMN_NAME} {COLUMN_TYPE}"))


def main() -> None:
    upgrade()