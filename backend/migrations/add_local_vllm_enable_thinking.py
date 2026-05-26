"""Add local_vllm_enable_thinking to user_settings.

Safe to run multiple times. This migration exists in backend/migrations/ so the
startup auto-migration runner can pick it up for older local databases.
"""

import os

from sqlalchemy import create_engine, inspect, text


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
TABLE_NAME = "user_settings"
COLUMN_NAME = "local_vllm_enable_thinking"


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in [column["name"] for column in inspector.get_columns(table_name)]


def upgrade() -> None:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)

    if TABLE_NAME not in inspector.get_table_names():
        return

    if _column_exists(inspector, TABLE_NAME, COLUMN_NAME):
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                f"ALTER TABLE {TABLE_NAME} "
                f"ADD COLUMN {COLUMN_NAME} BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )


def main() -> None:
    upgrade()