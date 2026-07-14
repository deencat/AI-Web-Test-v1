"""
Database migration: Add test_categories table and test_cases.test_category_id.

Sprint 2 — Test Navigator user-defined categories.
Safe to run multiple times (idempotent upgrade).
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.base import Base
from app.models.test_category import TestCategory


def upgrade() -> None:
    """Create test_categories table and add test_category_id to test_cases."""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    if "test_categories" not in inspector.get_table_names():
        Base.metadata.create_all(bind=engine, tables=[TestCategory.__table__])
        print("✅ Created table: test_categories")
    else:
        print("ℹ️  Table already exists: test_categories")

    test_case_columns = {
        column["name"] for column in inspector.get_columns("test_cases")
    }
    if "test_category_id" not in test_case_columns:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE test_cases "
                    "ADD COLUMN test_category_id INTEGER "
                    "REFERENCES test_categories(id) ON DELETE SET NULL"
                )
            )
        print("✅ Added column: test_cases.test_category_id")
    else:
        print("ℹ️  Column already exists: test_cases.test_category_id")


def downgrade() -> None:
    """Drop test_category_id column and test_categories table."""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    test_case_columns = {
        column["name"] for column in inspector.get_columns("test_cases")
    }
    if "test_category_id" in test_case_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE test_cases DROP COLUMN test_category_id"))
        print("✅ Dropped column: test_cases.test_category_id")

    if "test_categories" in inspector.get_table_names():
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE test_categories"))
        print("✅ Dropped table: test_categories")


def run_migration() -> None:
    upgrade()


if __name__ == "__main__":
    run_migration()
