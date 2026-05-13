"""
Database migration: Add root_cause_analysis column to execution_feedback table — Sprint 10.12
Created: May 2026
Purpose: Store AI-generated root cause analysis for all_tiers_exhausted failures.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """Add root_cause_analysis TEXT column to execution_feedback if it does not exist."""
    print("🔄 Starting root_cause_analysis migration...")

    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # Check whether the column already exists (SQLite compatible)
        result = conn.execute(text("PRAGMA table_info(execution_feedback)"))
        columns = [row[1] for row in result.fetchall()]

        if "root_cause_analysis" in columns:
            print("✅ Column root_cause_analysis already exists — skipping.")
        else:
            conn.execute(
                text(
                    "ALTER TABLE execution_feedback "
                    "ADD COLUMN root_cause_analysis TEXT"
                )
            )
            conn.commit()
            print("✅ Column root_cause_analysis added to execution_feedback.")

    print("\n📊 Migration completed:")
    print("  Table : execution_feedback")
    print("  Column: root_cause_analysis (TEXT, nullable)")
    print("  Notes : Populated only for error_type=all_tiers_exhausted failures.")


if __name__ == "__main__":
    run_migration()
