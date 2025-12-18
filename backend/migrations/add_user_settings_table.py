"""
Add user_settings table for dynamic AI provider configuration.

This migration adds the user_settings table that allows users to configure
their AI provider and model preferences from the Settings page UI.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.config import settings as app_settings

def upgrade():
    """Create user_settings table."""
    engine = create_engine(app_settings.DATABASE_URL)
    metadata = MetaData()
    
    # Define user_settings table
    user_settings = Table(
        'user_settings',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # Test Generation Configuration
        Column('generation_provider', String(50), nullable=False, default='openrouter'),
        Column('generation_model', String(100), nullable=False),
        Column('generation_temperature', Float, default=0.7),
        Column('generation_max_tokens', Integer, default=4096),
        
        # Test Execution Configuration
        Column('execution_provider', String(50), nullable=False, default='openrouter'),
        Column('execution_model', String(100), nullable=False),
        Column('execution_temperature', Float, default=0.7),
        Column('execution_max_tokens', Integer, default=4096),
        
        Column('created_at', DateTime(timezone=True), server_default=func.now()),
        Column('updated_at', DateTime(timezone=True), onupdate=func.now()),
        
        UniqueConstraint('user_id', name='uq_user_settings_user_id')
    )
    
    # Create table
    metadata.create_all(engine)
    print("✅ Created user_settings table")


def downgrade():
    """Drop user_settings table."""
    engine = create_engine(app_settings.DATABASE_URL)
    metadata = MetaData()
    
    # Define table to drop
    user_settings = Table('user_settings', metadata, autoload_with=engine)
    
    # Drop table
    user_settings.drop(engine)
    print("✅ Dropped user_settings table")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python add_user_settings_table.py [upgrade|downgrade]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "upgrade":
        upgrade()
    elif command == "downgrade":
        downgrade()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python add_user_settings_table.py [upgrade|downgrade]")
        sys.exit(1)
