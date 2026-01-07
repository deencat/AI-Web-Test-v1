"""
Migration: Add stagehand_provider field to user_settings table
Sprint 5: Dual Stagehand Provider System
Date: January 7, 2026
"""
import sqlite3
import os
from pathlib import Path


def get_db_path():
    """Get the database file path."""
    backend_dir = Path(__file__).parent.parent
    db_file = backend_dir / "aiwebtest.db"
    
    if not db_file.exists():
        raise FileNotFoundError(f"Database file not found: {db_file}")
    
    return str(db_file)


def migrate_up():
    """Add stagehand_provider column to user_settings table."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'stagehand_provider' in columns:
            print("✅ Column 'stagehand_provider' already exists in user_settings table")
            return
        
        # Add the new column
        cursor.execute("""
            ALTER TABLE user_settings 
            ADD COLUMN stagehand_provider VARCHAR(20) DEFAULT 'python' NOT NULL
        """)
        
        conn.commit()
        print("✅ Successfully added stagehand_provider column to user_settings table")
        print("   Default value: 'python'")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


def migrate_down():
    """Remove stagehand_provider column from user_settings table."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support DROP COLUMN directly
        # We need to recreate the table without that column
        
        print("⚠️  Rollback: Removing stagehand_provider column...")
        print("⚠️  Note: SQLite requires table recreation for column removal")
        
        # Get current schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_settings'")
        create_sql = cursor.fetchone()[0]
        
        # Check if column exists
        if 'stagehand_provider' not in create_sql:
            print("✅ Column 'stagehand_provider' doesn't exist, nothing to rollback")
            return
        
        # Backup data
        cursor.execute("""
            CREATE TEMPORARY TABLE user_settings_backup AS 
            SELECT id, user_id, generation_provider, generation_model, 
                   generation_temperature, generation_max_tokens,
                   execution_provider, execution_model,
                   execution_temperature, execution_max_tokens,
                   created_at, updated_at
            FROM user_settings
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE user_settings")
        
        # Recreate table without stagehand_provider
        cursor.execute("""
            CREATE TABLE user_settings (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                generation_provider VARCHAR(50) NOT NULL DEFAULT 'openrouter',
                generation_model VARCHAR(100) NOT NULL,
                generation_temperature REAL DEFAULT 0.7,
                generation_max_tokens INTEGER DEFAULT 4096,
                execution_provider VARCHAR(50) NOT NULL DEFAULT 'openrouter',
                execution_model VARCHAR(100) NOT NULL,
                execution_temperature REAL DEFAULT 0.7,
                execution_max_tokens INTEGER DEFAULT 4096,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Restore data
        cursor.execute("""
            INSERT INTO user_settings 
            SELECT * FROM user_settings_backup
        """)
        
        # Drop backup
        cursor.execute("DROP TABLE user_settings_backup")
        
        conn.commit()
        print("✅ Successfully rolled back stagehand_provider column")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python add_stagehand_provider_field.py [up|down]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "up":
        migrate_up()
    elif action == "down":
        migrate_down()
    else:
        print(f"Unknown action: {action}")
        print("Usage: python add_stagehand_provider_field.py [up|down]")
        sys.exit(1)
