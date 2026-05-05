"""
Database migration: Add step_library_modules table — Sprint 10.11
Created: May 2026
Purpose: Support the Step Library — Reusable Modular Test Steps feature.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.core.config import settings
from app.db.base import Base
from app.models.step_library_module import StepLibraryModule


def run_migration():
    """Create the step_library_modules table if it does not already exist."""
    print("🔄 Starting step_library_modules migration...")

    engine = create_engine(settings.DATABASE_URL)

    Base.metadata.create_all(bind=engine, tables=[StepLibraryModule.__table__])

    print("✅ Migration completed successfully!")
    print("\n📊 Table created (or already existed):")
    print("  - step_library_modules")
    print("\n🔍 Columns:")
    print("  - id (PRIMARY KEY)")
    print("  - user_id (FOREIGN KEY → users.id, CASCADE DELETE)")
    print("  - name (VARCHAR 100, UNIQUE, INDEX)")
    print("  - display_name (VARCHAR 255)")
    print("  - description (TEXT, nullable)")
    print("  - steps (JSON)")
    print("  - parameters (JSON, nullable)")
    print("  - tags (JSON, nullable)")
    print("  - created_at (DATETIME)")
    print("  - updated_at (DATETIME)")


if __name__ == "__main__":
    run_migration()
