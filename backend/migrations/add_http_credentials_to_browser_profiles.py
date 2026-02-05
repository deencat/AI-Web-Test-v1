"""
Database migration: Add HTTP credential fields to browser_profiles
Created: February 5, 2026
Purpose: Store encrypted HTTP Basic Auth credentials per browser profile
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration() -> bool:
    """Add HTTP credential columns to browser_profiles table."""
    print("🔄 Starting HTTP credentials migration for browser_profiles...")
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN http_username VARCHAR(255)
                """
            ))
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN http_password_encrypted TEXT
                """
            ))
            conn.execute(text(
                """
                ALTER TABLE browser_profiles
                ADD COLUMN encryption_key_id INTEGER
                """
            ))
            conn.execute(text(
                """
                CREATE INDEX IF NOT EXISTS idx_browser_profiles_http_username
                ON browser_profiles (http_username)
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
