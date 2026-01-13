#!/usr/bin/env python3
"""
Create execution_feedback table - Sprint 4 Migration
Sprint 4: Execution Feedback System

This script adds the execution_feedback table for collecting learning data
from test execution failures. This is the foundation of the learning system.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Import models to register them
from app.models.execution_feedback import ExecutionFeedback

def create_execution_feedback_table():
    """Create execution_feedback table."""
    print("\n" + "="*70)
    print("Sprint 4: Creating Execution Feedback Table")
    print("="*70 + "\n")
    
    try:
        # Create table using SQLAlchemy (will skip if exists)
        print("📊 Creating execution_feedback table...")
        Base.metadata.create_all(bind=engine, tables=[ExecutionFeedback.__table__])
        print("✅ Table created successfully!\n")
        
        # Verify table exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='execution_feedback'
            """))
            table = result.fetchone()
            
            if table:
                print("✅ Verification: execution_feedback table exists\n")
                
                # Show table structure
                result = conn.execute(text("PRAGMA table_info(execution_feedback)"))
                columns = result.fetchall()
                
                print("📋 Table Structure:")
                print("-" * 70)
                for col in columns:
                    print(f"  {col[1]:30} {col[2]:20} {'NOT NULL' if col[3] else ''}")
                print("-" * 70 + "\n")
                
                # Create indexes for performance
                print("🚀 Creating indexes for performance...")
                
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_feedback_execution_id ON execution_feedback(execution_id)",
                    "CREATE INDEX IF NOT EXISTS idx_feedback_failure_type ON execution_feedback(failure_type)",
                    "CREATE INDEX IF NOT EXISTS idx_feedback_page_url ON execution_feedback(page_url)",
                    "CREATE INDEX IF NOT EXISTS idx_feedback_correction_source ON execution_feedback(correction_source)",
                    "CREATE INDEX IF NOT EXISTS idx_feedback_is_anomaly ON execution_feedback(is_anomaly)",
                    "CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON execution_feedback(created_at)"
                ]
                
                for idx_sql in indexes:
                    conn.execute(text(idx_sql))
                    conn.commit()
                
                print("✅ Indexes created successfully!\n")
                
            else:
                print("❌ Table creation failed!")
                return False
        
        print("="*70)
        print("✅ Sprint 4 Migration Complete!")
        print("="*70 + "\n")
        
        print("📝 Next Steps:")
        print("  1. Restart the backend server to load the new model")
        print("  2. Test feedback endpoints at http://127.0.0.1:8000/docs")
        print("  3. Run a test execution to automatically capture feedback")
        print("  4. View feedback in the execution detail page\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_execution_feedback_table()
    sys.exit(0 if success else 1)
