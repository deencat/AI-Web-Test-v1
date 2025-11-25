"""
Add queue fields to test_executions table.

Sprint 3 Day 2 - Queue System Migration
"""
from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_queue_fields():
    """Add queue-related fields to test_executions table."""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            logger.info("Adding queue fields to test_executions table...")
            
            # Add queued_at column
            try:
                conn.execute(text("""
                    ALTER TABLE test_executions 
                    ADD COLUMN queued_at TIMESTAMP NULL
                """))
                conn.commit()
                logger.info("✅ Added queued_at column")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.info("⏭️  queued_at column already exists")
                else:
                    raise
            
            # Add priority column
            try:
                conn.execute(text("""
                    ALTER TABLE test_executions 
                    ADD COLUMN priority INTEGER DEFAULT 5
                """))
                conn.commit()
                logger.info("✅ Added priority column")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.info("⏭️  priority column already exists")
                else:
                    raise
            
            # Add queue_position column
            try:
                conn.execute(text("""
                    ALTER TABLE test_executions 
                    ADD COLUMN queue_position INTEGER NULL
                """))
                conn.commit()
                logger.info("✅ Added queue_position column")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.info("⏭️  queue_position column already exists")
                else:
                    raise
            
            logger.info("\n✅ Migration complete! Queue fields added successfully.")
            
            # Verify columns exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'test_executions' 
                AND column_name IN ('queued_at', 'priority', 'queue_position')
                ORDER BY column_name
            """))
            
            columns = [row[0] for row in result]
            logger.info(f"\nVerified columns: {columns}")
            
            if len(columns) == 3:
                logger.info("✅ All queue fields verified!")
            else:
                logger.warning(f"⚠️  Expected 3 columns, found {len(columns)}")
    
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 3 Day 2 - Queue Fields Migration")
    print("=" * 60)
    add_queue_fields()
    print("=" * 60)

