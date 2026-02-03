"""
Database migration: Add browser_profiles table
Created: February 3, 2026
Purpose: Support Browser Profile Session Persistence feature (Enhancement 5)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.base import Base
from app.models import BrowserProfile

def run_migration():
    """Run the migration to add browser_profiles table."""
    print("🔄 Starting browser profiles table migration...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create table
        print("📝 Creating browser_profiles table...")
        Base.metadata.create_all(bind=engine, tables=[
            BrowserProfile.__table__
        ])
        
        print("✅ Migration completed successfully!")
        print("\n📊 Table created:")
        print("  - browser_profiles")
        print("\n🔍 Columns:")
        print("  - id (PRIMARY KEY)")
        print("  - user_id (FOREIGN KEY → users.id, CASCADE DELETE)")
        print("  - profile_name (VARCHAR 100)")
        print("  - os_type (VARCHAR 20) - windows/linux/macos")
        print("  - browser_type (VARCHAR 20) - chromium/firefox/webkit")
        print("  - description (TEXT)")
        print("  - created_at (DATETIME)")
        print("  - updated_at (DATETIME)")
        print("  - last_sync_at (DATETIME, nullable)")
        
        # Verify table exists
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='browser_profiles'"
            ))
            tables = [row[0] for row in result]
            if tables:
                print(f"\n✅ Verified table: {', '.join(tables)}")
            else:
                print("\n⚠️ Warning: Table verification failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
