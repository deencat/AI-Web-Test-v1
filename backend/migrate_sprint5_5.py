"""
Database migration script for Sprint 5.5: 3-Tier Execution Engine
Creates tables: execution_settings, xpath_cache, tier_execution_logs
"""
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect
from app.db.base import Base
from app.models import ExecutionSettings, XPathCache, TierExecutionLog

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

def run_migration():
    """Run database migration to create new tables"""
    print("=" * 60)
    print("Sprint 5.5: 3-Tier Execution Engine - Database Migration")
    print("=" * 60)
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Check which tables exist
    existing_tables = inspector.get_table_names()
    
    print(f"\nDatabase: {DATABASE_URL}")
    print(f"Existing tables: {len(existing_tables)}")
    
    # Tables to create
    new_tables = {
        "execution_settings": ExecutionSettings,
        "xpath_cache": XPathCache,
        "tier_execution_logs": TierExecutionLog
    }
    
    print("\n" + "=" * 60)
    print("Tables to create:")
    print("=" * 60)
    
    tables_created = []
    tables_already_exist = []
    
    for table_name, model_class in new_tables.items():
        if table_name in existing_tables:
            print(f"  ⏭️  {table_name} - Already exists, skipping")
            tables_already_exist.append(table_name)
        else:
            print(f"  ➕ {table_name} - Creating...")
            tables_created.append(table_name)
    
    # Create all tables (only new ones will be created)
    print("\n" + "=" * 60)
    print("Creating tables...")
    print("=" * 60)
    
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    print("\n✅ Migration completed successfully!")
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"  • Tables created: {len(tables_created)}")
    for table in tables_created:
        print(f"    - {table}")
    
    if tables_already_exist:
        print(f"\n  • Tables already existed: {len(tables_already_exist)}")
        for table in tables_already_exist:
            print(f"    - {table}")
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("=" * 60)
    print("  1. Restart the backend server")
    print("  2. Test the 3-Tier Execution Engine")
    print("  3. Configure fallback strategy in settings")
    print("=" * 60)

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
