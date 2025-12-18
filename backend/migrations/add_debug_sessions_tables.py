"""
Database migration: Add debug_sessions and debug_step_executions tables
Created: December 17, 2025
Purpose: Support Local Persistent Browser Debug Mode feature
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.base import Base
from app.models import DebugSession, DebugStepExecution

def run_migration():
    """Run the migration to add debug session tables."""
    print("🔄 Starting debug session tables migration...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create tables
        print("📝 Creating debug_sessions and debug_step_executions tables...")
        Base.metadata.create_all(bind=engine, tables=[
            DebugSession.__table__,
            DebugStepExecution.__table__
        ])
        
        print("✅ Migration completed successfully!")
        print("\n📊 Tables created:")
        print("  - debug_sessions")
        print("  - debug_step_executions")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'debug_%'"
            ))
            tables = [row[0] for row in result]
            print(f"\n✅ Verified tables: {', '.join(tables)}")
        
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
