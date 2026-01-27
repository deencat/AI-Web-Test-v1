"""
Database migration: Add debug range selection fields to debug_sessions
Created: January 27, 2026
Purpose: Support Phase 4 Debug Range Selection feature
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the migration to add debug range selection fields."""
    print("🔄 Starting debug range selection migration...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            print("📝 Checking existing columns...")
            result = conn.execute(text("PRAGMA table_info(debug_sessions)"))
            existing_columns = {row[1] for row in result}
            
            migrations_needed = []
            
            if 'end_step_number' not in existing_columns:
                migrations_needed.append("end_step_number")
            
            if 'skip_prerequisites' not in existing_columns:
                migrations_needed.append("skip_prerequisites")
            
            if not migrations_needed:
                print("✅ All columns already exist, no migration needed")
                return True
            
            print(f"📝 Adding columns: {', '.join(migrations_needed)}")
            
            # Add end_step_number column (nullable integer)
            if 'end_step_number' in migrations_needed:
                print("  - Adding end_step_number column...")
                conn.execute(text(
                    "ALTER TABLE debug_sessions ADD COLUMN end_step_number INTEGER"
                ))
                conn.commit()
            
            # Add skip_prerequisites column (boolean, default False)
            if 'skip_prerequisites' in migrations_needed:
                print("  - Adding skip_prerequisites column...")
                conn.execute(text(
                    "ALTER TABLE debug_sessions ADD COLUMN skip_prerequisites BOOLEAN DEFAULT 0"
                ))
                conn.commit()
            
            print("✅ Migration completed successfully!")
            
            # Verify columns were added
            print("\n📊 Verifying new columns...")
            result = conn.execute(text("PRAGMA table_info(debug_sessions)"))
            all_columns = [row[1] for row in result]
            
            for col in migrations_needed:
                if col in all_columns:
                    print(f"  ✅ {col}")
                else:
                    print(f"  ❌ {col} - NOT FOUND!")
            
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
