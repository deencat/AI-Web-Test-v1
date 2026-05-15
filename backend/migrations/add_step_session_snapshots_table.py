"""
Database migration: Add step_session_snapshots table — Sprint 10.12 Feature B
Created: May 2026
Purpose: Persist browser session state after each passing step so executions
         can be resumed from any safe point (Re-Run from Failed Step feature).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """Create step_session_snapshots table if it does not exist."""
    print("🔄 Starting step_session_snapshots migration...")

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # Check whether the table already exists (SQLite compatible)
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='step_session_snapshots'")
        )
        if result.fetchone():
            print("✅ Table step_session_snapshots already exists — skipping.")
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE step_session_snapshots (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        execution_id INTEGER NOT NULL,
                        step_number  INTEGER NOT NULL,
                        page_url     TEXT,
                        session_data TEXT,
                        created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_step_session_snapshots_execution_id "
                    "ON step_session_snapshots (execution_id)"
                )
            )
            conn.commit()
            print("✅ Table step_session_snapshots created.")

    print("\n📊 Migration completed:")
    print("  Table  : step_session_snapshots")
    print("  Columns: id, execution_id, step_number, page_url, session_data, created_at")
    print("  Notes  : execution_id is NOT a FK — snapshots from prior completed runs")
    print("           must remain accessible after the execution row is retained/deleted.")


if __name__ == "__main__":
    run_migration()
