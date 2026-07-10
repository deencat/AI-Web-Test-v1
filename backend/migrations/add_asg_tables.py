"""
Database migration: Add ASG (App State Graph) tables — Feature 3
Created: July 2026
Purpose: Deterministic test generation graph persistence.
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.base import Base
from app.models.asg import ASGGraph, ASGNode, ASGEdge, ASGPath, ASGSynthesizedTest


def run_migration():
    """Create ASG tables if they do not already exist."""
    print("🔄 Starting ASG tables migration...")

    engine = create_engine(settings.DATABASE_URL)
    tables = [
        ASGGraph.__table__,
        ASGNode.__table__,
        ASGEdge.__table__,
        ASGPath.__table__,
        ASGSynthesizedTest.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=tables)

    inspector = inspect(engine)
    created = [t.name for t in tables if t.name in inspector.get_table_names()]
    print("✅ Migration completed successfully!")
    print(f"\n📊 Tables ensured: {', '.join(created)}")


if __name__ == "__main__":
    run_migration()
