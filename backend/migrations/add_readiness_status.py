"""
Migration: add readiness_status column to test_cases.

Feature 4 — Test Readiness Status (draft | ready_to_test | blocked).
Distinct from execution lifecycle TestCase.status.
Existing rows backfilled to 'draft' via column DEFAULT.
Safe to run multiple times (idempotent upgrade).
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings


def upgrade() -> None:
    """Add readiness_status to test_cases with default draft."""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    if "test_cases" not in inspector.get_table_names():
        print("⚠️  Table test_cases does not exist — skipping")
        return

    test_case_columns = {
        column["name"] for column in inspector.get_columns("test_cases")
    }
    if "readiness_status" not in test_case_columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE test_cases "
                    "ADD COLUMN readiness_status VARCHAR(32) "
                    "NOT NULL DEFAULT 'draft'"
                )
            )
            # Index for list filter (SQLite / Postgres)
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_test_cases_readiness_status "
                    "ON test_cases (readiness_status)"
                )
            )
        print("✅ Added column: test_cases.readiness_status (default draft)")
    else:
        print("ℹ️  Column already exists: test_cases.readiness_status")
        # Ensure any unexpected NULLs are backfilled
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE test_cases SET readiness_status = 'draft' "
                    "WHERE readiness_status IS NULL OR readiness_status = ''"
                )
            )


def downgrade() -> None:
    """Drop readiness_status column (best-effort; SQLite may not support DROP COLUMN on older versions)."""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    test_case_columns = {
        column["name"] for column in inspector.get_columns("test_cases")
    }
    if "readiness_status" not in test_case_columns:
        print("ℹ️  Column already absent: test_cases.readiness_status")
        return
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS ix_test_cases_readiness_status"))
        try:
            conn.execute(text("ALTER TABLE test_cases DROP COLUMN readiness_status"))
            print("✅ Dropped column: test_cases.readiness_status")
        except Exception as exc:
            print(f"⚠️  Could not drop readiness_status: {exc}")


def run_migration() -> None:
    upgrade()


if __name__ == "__main__":
    run_migration()
