"""
Database migration: Add test_versions table for version control

Sprint 4 Day 1 - Phase 2: Learning Foundations
This migration adds the test_versions table that enables test editing with full version history.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base
from app.models.test_version import TestCaseVersion
from app.models.test_case import TestCase


def run_migration():
    """Run the migration to add test_versions table."""
    print("🔄 Starting test_versions table migration...")
    print("=" * 70)
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if table already exists
        result = db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_versions'"
        ))
        table_exists = result.fetchone() is not None
        
        if table_exists:
            print("⚠️  Table 'test_versions' already exists. Skipping migration.")
            return True
        
        # Create test_versions table
        print("📝 Creating test_versions table...")
        TestCaseVersion.__table__.create(engine)
        
        print("✅ test_versions table created successfully!")
        print()
        print("Table schema:")
        print("  - id (PRIMARY KEY)")
        print("  - test_case_id (FOREIGN KEY → test_cases.id)")
        print("  - version_number (INTEGER)")
        print("  - steps (JSON)")
        print("  - expected_result (TEXT, nullable)")
        print("  - test_data (JSON, nullable)")
        print("  - created_at (DATETIME)")
        print("  - created_by (VARCHAR(50))")
        print("  - change_reason (VARCHAR(100), nullable)")
        print("  - parent_version_id (FOREIGN KEY → test_versions.id, nullable)")
        print()
        print("✅ Migration completed successfully!")
        print("=" * 70)
        
        # Create initial versions for existing test cases (optional)
        print("\n🔄 Creating initial versions for existing test cases...")
        test_cases = db.query(TestCase).all()
        
        if test_cases:
            from app.services.version_service import VersionService
            
            created_count = 0
            for test_case in test_cases:
                try:
                    VersionService.save_version(
                        db=db,
                        test_case_id=test_case.id,
                        steps=test_case.steps,
                        expected_result=test_case.expected_result,
                        test_data=test_case.test_data,
                        created_by="system",
                        change_reason="initial_version"
                    )
                    created_count += 1
                except Exception as e:
                    print(f"  ⚠️  Failed to create version for test {test_case.id}: {e}")
            
            print(f"  ✅ Created initial versions for {created_count} test cases")
        else:
            print("  ℹ️  No existing test cases found")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MIGRATION: Add test_versions table")
    print("=" * 70)
    print()
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now use version control features:")
        print("  - Edit test steps in-place")
        print("  - View version history")
        print("  - Rollback to previous versions")
        print("  - Compare versions")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
