"""
Migration Runner Script
=======================
This script runs all pending database migrations in order.

It tracks which migrations have been applied using a migrations table,
so you can safely run this script multiple times - it only runs new migrations.

Usage:
  python run_migrations.py              # Run all pending migrations
  python run_migrations.py --status     # Show migration status
  python run_migrations.py --rollback   # Rollback last migration (if supported)
"""

import os
import sys
import importlib.util
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Migration tracking table
class MigrationHistory(Base):
    __tablename__ = "migration_history"
    
    id = Column(Integer, primary_key=True)
    migration_name = Column(String(255), unique=True, nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Integer, default=1)  # 1 = success, 0 = failed
    error_message = Column(Text, nullable=True)

def init_migration_table():
    """Create migration tracking table if it doesn't exist"""
    Base.metadata.create_all(bind=engine)

def get_applied_migrations(db):
    """Get list of already-applied migrations"""
    return [m.migration_name for m in db.query(MigrationHistory).filter(MigrationHistory.success == 1).all()]

def get_available_migrations():
    """Scan migrations folder and return list of migration files"""
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    
    if not os.path.exists(migrations_dir):
        print(f"⚠️  Migrations directory not found: {migrations_dir}")
        return []
    
    migration_files = []
    for filename in os.listdir(migrations_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            migration_files.append(filename)
    
    # Sort migrations by name (assumes naming convention: 001_xxx.py, 002_xxx.py, etc.)
    migration_files.sort()
    
    return migration_files

def load_migration_module(migration_file):
    """Dynamically load migration module"""
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    migration_path = os.path.join(migrations_dir, migration_file)
    
    spec = importlib.util.spec_from_file_location(migration_file.replace(".py", ""), migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

def run_migration(migration_file, db):
    """Run a single migration"""
    migration_name = migration_file.replace(".py", "")
    
    print(f"🔄 Running migration: {migration_name}")
    
    try:
        # Load migration module
        module = load_migration_module(migration_file)
        
        # Check if module has main() or upgrade() function
        if hasattr(module, "main"):
            module.main()
        elif hasattr(module, "upgrade"):
            module.upgrade()
        else:
            print(f"  ⚠️  Migration {migration_name} has no main() or upgrade() function")
            return False
        
        # Record successful migration
        history = MigrationHistory(
            migration_name=migration_name,
            applied_at=datetime.utcnow(),
            success=1
        )
        db.add(history)
        db.commit()
        
        print(f"  ✅ Migration {migration_name} completed successfully!")
        return True
    
    except Exception as e:
        print(f"  ❌ Migration {migration_name} FAILED: {str(e)}")
        
        # Record failed migration
        history = MigrationHistory(
            migration_name=migration_name,
            applied_at=datetime.utcnow(),
            success=0,
            error_message=str(e)
        )
        db.add(history)
        db.commit()
        
        return False

def show_migration_status():
    """Show status of all migrations"""
    print("\n📊 Migration Status")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        applied = get_applied_migrations(db)
        available = get_available_migrations()
        
        if not available:
            print("⚠️  No migrations found in migrations/ directory")
            return
        
        print(f"\nTotal migrations: {len(available)}")
        print(f"Applied: {len(applied)}")
        print(f"Pending: {len(available) - len(applied)}")
        
        print("\nMigrations:")
        for migration in available:
            migration_name = migration.replace(".py", "")
            status = "✅ Applied" if migration_name in applied else "⏳ Pending"
            
            if migration_name in applied:
                record = db.query(MigrationHistory).filter(
                    MigrationHistory.migration_name == migration_name
                ).first()
                if record:
                    status += f" ({record.applied_at.strftime('%Y-%m-%d %H:%M')})"
            
            print(f"  {status:30} {migration_name}")
    
    finally:
        db.close()

def run_all_migrations():
    """Run all pending migrations"""
    print("🚀 Starting migration runner...")
    print("=" * 70)
    
    # Initialize migration tracking table
    init_migration_table()
    
    db = SessionLocal()
    try:
        # Get applied and available migrations
        applied = get_applied_migrations(db)
        available = get_available_migrations()
        
        if not available:
            print("⚠️  No migrations found in migrations/ directory")
            return
        
        # Find pending migrations
        pending = [m for m in available if m.replace(".py", "") not in applied]
        
        if not pending:
            print("✅ All migrations already applied. Nothing to do!")
            return
        
        print(f"\n📝 Found {len(pending)} pending migration(s):")
        for migration in pending:
            print(f"  - {migration.replace('.py', '')}")
        
        print("\n" + "=" * 70)
        
        # Run each pending migration
        success_count = 0
        failed_count = 0
        
        for migration in pending:
            if run_migration(migration, db):
                success_count += 1
            else:
                failed_count += 1
                
                # Ask if we should continue on failure
                if failed_count > 0:
                    cont = input("\n⚠️  Migration failed. Continue with remaining migrations? (yes/no): ")
                    if cont.lower() != "yes":
                        break
        
        print("\n" + "=" * 70)
        print(f"✅ Migration run complete!")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {failed_count}")
        
        if failed_count > 0:
            print("\n⚠️  Some migrations failed. Check error messages above.")
            print("💡 Tip: Fix the failed migration and run this script again.")
    
    finally:
        db.close()

def rollback_last_migration():
    """Rollback the last applied migration (if supported)"""
    print("⏪ Rolling back last migration...")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # Get last applied migration
        last_migration = db.query(MigrationHistory).filter(
            MigrationHistory.success == 1
        ).order_by(MigrationHistory.applied_at.desc()).first()
        
        if not last_migration:
            print("⚠️  No migrations to rollback.")
            return
        
        migration_file = f"{last_migration.migration_name}.py"
        print(f"🔄 Rolling back: {last_migration.migration_name}")
        
        # Load migration module
        module = load_migration_module(migration_file)
        
        # Check if module has downgrade() function
        if not hasattr(module, "downgrade"):
            print(f"  ⚠️  Migration {last_migration.migration_name} does not support rollback (no downgrade() function)")
            return
        
        # Run downgrade
        try:
            module.downgrade()
            
            # Mark as rolled back
            last_migration.success = 0
            last_migration.error_message = "Rolled back by user"
            db.commit()
            
            print(f"  ✅ Rollback successful!")
        
        except Exception as e:
            print(f"  ❌ Rollback FAILED: {str(e)}")
    
    finally:
        db.close()

def main():
    """Main entry point"""
    
    if "--status" in sys.argv:
        show_migration_status()
    elif "--rollback" in sys.argv:
        rollback_last_migration()
    else:
        run_all_migrations()
    
    print("\n" + "=" * 70)
    print("💡 Tips:")
    print("  - Run 'python run_migrations.py --status' to see migration status")
    print("  - Run 'python run_migrations.py' again to apply new migrations")
    print("  - Run 'python run_migrations.py --rollback' to undo last migration")
    print("  - Both developers should run this script after pulling new code")

if __name__ == "__main__":
    main()
