"""
Database migration script for Sprint 10.17: AI Screenshot Verification

Adds: test_execution_steps.ai_verification_result TEXT NULL

Stores the AI vision verdict as JSON:
  {"verdict": "PASS"|"FAIL", "reason": "...", "provider": "...", "model": "..."}

Safe to run on existing databases — NULL default ensures no data loss on
existing rows.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")

COLUMN_NAME = "ai_verification_result"
TABLE_NAME = "test_execution_steps"


def column_exists(inspector, table: str, column: str) -> bool:
    """Return True if the column already exists in the table."""
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def run_migration():
    """Add ai_verification_result column to test_execution_steps."""
    print("=" * 60)
    print("Sprint 10.17: AI Screenshot Verification — DB Migration")
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
        conn.execute(
            text(
                f"ALTER TABLE {TABLE_NAME} "
                f"ADD COLUMN {COLUMN_NAME} TEXT NULL"
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
