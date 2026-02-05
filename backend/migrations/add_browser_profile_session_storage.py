"""
Database migration: Add encrypted session storage fields to browser_profiles
Created: February 5, 2026
Purpose: Store encrypted cookies/localStorage/sessionStorage for server-side profiles
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration() -> bool:
    """Add session storage columns to browser_profiles table."""
    print("🔄 Starting browser profile session storage migration...")
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN cookies_encrypted TEXT
                """
            ))
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN local_storage_encrypted TEXT
                """
            ))
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN session_storage_encrypted TEXT
                """
            ))
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN auto_sync BOOLEAN DEFAULT 0
                """
            ))
            conn.commit()

        print("✅ Migration completed successfully!")
        return True
    except Exception as exc:
        print(f"❌ Migration failed: {exc}")
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
