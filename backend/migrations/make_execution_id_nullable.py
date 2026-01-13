#!/usr/bin/env python3
"""
Migration: Make execution_id nullable for imported feedback
Sprint 4 - Feedback Import/Export Feature

This allows imported feedback from other databases to be stored
without requiring a valid execution_id foreign key reference.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine


def upgrade():
    """Make execution_id nullable in execution_feedback table."""
    print("\n" + "="*70)
    print("Sprint 4 Migration: Make execution_id Nullable for Import")
    print("="*70 + "\n")
    
    try:
        with engine.connect() as conn:
            # SQLite doesn't support ALTER COLUMN directly
            # Need to recreate the table without NOT NULL constraint
            
            print("📊 Modifying execution_feedback table...")
            print("   Step 1: Creating temporary table...")
            
            # Create new table without NOT NULL on execution_id
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS execution_feedback_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER,
                    step_index INTEGER,
                    failure_type VARCHAR(100),
                    error_message TEXT,
                    screenshot_url VARCHAR(500),
                    page_url VARCHAR(2000),
                    page_html_snapshot TEXT,
                    browser_type VARCHAR(50),
                    viewport_width INTEGER,
                    viewport_height INTEGER,
                    failed_selector VARCHAR(2000),
                    selector_type VARCHAR(50),
                    corrected_step JSON,
                    correction_source VARCHAR(50),
                    correction_confidence FLOAT,
                    correction_applied_at TIMESTAMP,
                    corrected_by_user_id INTEGER,
                    step_duration_ms INTEGER,
                    memory_usage_mb FLOAT,
                    network_requests INTEGER,
                    is_anomaly BOOLEAN DEFAULT 0,
                    anomaly_score FLOAT,
                    anomaly_type VARCHAR(100),
                    notes TEXT,
                    tags JSON,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (execution_id) REFERENCES test_executions(id) ON DELETE CASCADE,
                    FOREIGN KEY (corrected_by_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """))
            conn.commit()
            
            print("   Step 2: Copying existing data...")
            conn.execute(text("""
                INSERT INTO execution_feedback_new 
                SELECT * FROM execution_feedback
            """))
            conn.commit()
            
            print("   Step 3: Dropping old table...")
            conn.execute(text("DROP TABLE execution_feedback"))
            conn.commit()
            
            print("   Step 4: Renaming new table...")
            conn.execute(text("""
                ALTER TABLE execution_feedback_new 
                RENAME TO execution_feedback
            """))
            conn.commit()
            
            print("   Step 5: Recreating indexes...")
            indexes = [
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_id ON execution_feedback(id)",
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_execution_id ON execution_feedback(execution_id)",
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_failure_type ON execution_feedback(failure_type)",
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_page_url ON execution_feedback(page_url)",
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_correction_source ON execution_feedback(correction_source)",
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_is_anomaly ON execution_feedback(is_anomaly)",
                "CREATE INDEX IF NOT EXISTS ix_execution_feedback_created_at ON execution_feedback(created_at)"
            ]
            
            for idx_sql in indexes:
                conn.execute(text(idx_sql))
            conn.commit()
            
            print("✅ Migration completed successfully!\n")
            
            # Verify
            result = conn.execute(text("PRAGMA table_info(execution_feedback)"))
            columns = result.fetchall()
            
            execution_id_col = [col for col in columns if col[1] == 'execution_id'][0]
            is_nullable = execution_id_col[3] == 0  # notnull == 0 means nullable
            
            if is_nullable:
                print("✅ Verification: execution_id is now NULLABLE")
            else:
                print("⚠️  Warning: execution_id is still NOT NULL")
            
            print("\n" + "="*70)
            print("Migration complete - Feedback import ready!")
            print("="*70 + "\n")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = upgrade()
    sys.exit(0 if success else 1)
