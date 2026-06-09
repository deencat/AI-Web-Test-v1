"""Add local_vllm_custom_model and local_vllm_custom_endpoint to user_settings.

Phase 2: custom vLLM model support — lets users specify an arbitrary model
name + endpoint URL instead of choosing from the hardcoded list.

Safe to run multiple times (idempotent column-exists guard).
Picked up automatically by run_all_migrations_auto() on server start.
"""

import os

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
TABLE_NAME = "user_settings"

COLUMNS = [
    ("local_vllm_custom_model",    "TEXT"),
    ("local_vllm_custom_endpoint", "TEXT"),
]


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in [col["name"] for col in inspector.get_columns(table_name)]


def upgrade() -> None:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)

    if TABLE_NAME not in inspector.get_table_names():
        return

    with engine.begin() as conn:
        for col_name, col_type in COLUMNS:
            if not _column_exists(inspector, TABLE_NAME, col_name):
                conn.execute(
                    text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col_name} {col_type}")
                )


def main() -> None:
    upgrade()
