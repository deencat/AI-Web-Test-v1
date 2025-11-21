#!/usr/bin/env python3
"""
Create test execution tables in the database.

This script adds the new execution tracking tables:
- test_executions
- test_execution_steps
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from app.db.base import Base

# Import all models to register them with Base
from app.models import user, test_case, kb_document, test_execution

def create_tables():
    """Create all tables (will skip existing tables)."""
    print("Creating execution tracking tables...")
    
    try:
        # This will create only tables that don't exist
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created successfully!")
        print("\nNew tables:")
        print("  - test_executions")
        print("  - test_execution_steps")
        
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_tables()

