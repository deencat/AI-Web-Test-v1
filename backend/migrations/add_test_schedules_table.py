"""
Database migration: Add test_schedules table
Created: June 2026
Purpose: Support in-process cross-platform test scheduling (APScheduler).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.core.config import settings
from app.db.base import Base
from app.models.test_schedule import TestSchedule


def run_migration():
    """Create the test_schedules table if it does not already exist."""
    print("🔄 Starting test_schedules migration...")

    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine, tables=[TestSchedule.__table__])

    print("✅ Migration completed successfully!")
    print("\n📊 Table created (or already existed):")
    print("  - test_schedules")
    print("\n🔍 Columns:")
    print("  - id (PRIMARY KEY)")
    print("  - user_id (FOREIGN KEY → users.id, CASCADE DELETE)")
    print("  - test_case_id (FOREIGN KEY → test_cases.id, CASCADE DELETE)")
    print("  - name (VARCHAR 200, nullable)")
    print("  - schedule_type (VARCHAR 20: 'interval' | 'cron')")
    print("  - interval_minutes (INTEGER, nullable)")
    print("  - cron_expression (VARCHAR 100, nullable)")
    print("  - browser (VARCHAR 50)")
    print("  - environment (VARCHAR 50)")
    print("  - base_url (VARCHAR 500, nullable)")
    print("  - enabled (BOOLEAN)")
    print("  - created_at / updated_at (DATETIME)")
    print("  - last_triggered_at (DATETIME, nullable)")


if __name__ == "__main__":
    run_migration()
