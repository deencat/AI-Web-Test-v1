"""
Add selector tracking to test_execution_steps table.

This migration adds selector_used and action_method columns to track
which XPath/CSS selectors were used and which execution method (playwright, stagehand_ai, etc.)
was employed for each test step.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, Table, Column, String, text
from app.core.config import settings as app_settings

def upgrade():
    """Add selector_used and action_method columns to test_execution_steps table."""
    engine = create_engine(app_settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Add selector_used column
        try:
            connection.execute(text(
                "ALTER TABLE test_execution_steps ADD COLUMN selector_used VARCHAR(1000)"
            ))
            connection.commit()
            print("✅ Added selector_used column to test_execution_steps")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("⏭️  selector_used column already exists, skipping")
            else:
                raise
        
        # Add action_method column
        try:
            connection.execute(text(
                "ALTER TABLE test_execution_steps ADD COLUMN action_method VARCHAR(50)"
            ))
            connection.commit()
            print("✅ Added action_method column to test_execution_steps")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("⏭️  action_method column already exists, skipping")
            else:
                raise
    
    print("✅ Migration completed successfully!")

def downgrade():
    """Remove selector_used and action_method columns from test_execution_steps table."""
    engine = create_engine(app_settings.DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            connection.execute(text(
                "ALTER TABLE test_execution_steps DROP COLUMN IF EXISTS selector_used"
            ))
            connection.execute(text(
                "ALTER TABLE test_execution_steps DROP COLUMN IF EXISTS action_method"
            ))
            connection.commit()
            print("✅ Removed selector tracking columns from test_execution_steps")
        except Exception as e:
            print(f"⚠️  Error during downgrade: {e}")
            raise

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Migration: Add Selector Tracking to Test Execution Steps")
    print("="*60 + "\n")
    
    choice = input("Run upgrade? (y/n): ").strip().lower()
    if choice == 'y':
        upgrade()
    else:
        print("Migration cancelled")
