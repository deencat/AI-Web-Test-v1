"""
Database migration script for Sprint 10.15: vLLM Thinking Mode Toggle

Adds: user_settings.local_vllm_enable_thinking BOOLEAN NOT NULL DEFAULT FALSE

Safe to run on existing databases — DEFAULT FALSE ensures no data loss on
existing rows and the NOT NULL constraint is satisfied from the start.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")

COLUMN_NAME = "local_vllm_enable_thinking"
TABLE_NAME = "user_settings"


def column_exists(inspector, table: str, column: str) -> bool:
    """Return True if the column already exists in the table."""
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def run_migration():
    """Add local_vllm_enable_thinking column to user_settings."""
    print("=" * 60)
    print("Sprint 10.15: vLLM Thinking Mode Toggle — DB Migration")
    print("=" * 60)
    print(f"\nDatabase: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    existing_tables = inspector.get_table_names()
    if TABLE_NAME not in existing_tables:
        print(f"\n❌  Table '{TABLE_NAME}' not found. Run the main DB setup first.")
        sys.exit(1)

    if column_exists(inspector, TABLE_NAME, COLUMN_NAME):
        print(f"\n⏭️  Column '{TABLE_NAME}.{COLUMN_NAME}' already exists — nothing to do.")
        return

    print(f"\n➕  Adding column '{TABLE_NAME}.{COLUMN_NAME}' …")

    with engine.begin() as conn:
        # SQLite does not support NOT NULL without a DEFAULT in ALTER TABLE,
        # so we specify the default value inline.
        conn.execute(
            text(
                f"ALTER TABLE {TABLE_NAME} "
                f"ADD COLUMN {COLUMN_NAME} BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )

    # Verify
    inspector2 = inspect(engine)
    if column_exists(inspector2, TABLE_NAME, COLUMN_NAME):
        print(f"✅  Column '{TABLE_NAME}.{COLUMN_NAME}' created successfully.")
    else:
        print(f"❌  Column creation failed — please check your database.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Migration complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
