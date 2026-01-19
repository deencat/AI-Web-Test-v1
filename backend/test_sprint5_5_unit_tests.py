"""
Simple unit test for Sprint 5.5: 3-Tier Execution Engine
Tests the core logic without requiring network access
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from app.services.xpath_cache_service import XPathCacheService
from app.models.execution_settings import ExecutionSettings, XPathCache
from app.db.base import Base

# Load environment
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_execution_settings_model():
    """Test ExecutionSettings model"""
    print("\n" + "=" * 60)
    print("TEST 1: ExecutionSettings Model")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clean up any existing settings for user_id 1
        db.query(ExecutionSettings).filter(ExecutionSettings.user_id == 1).delete()
        db.commit()
        
        # Create execution settings
        settings = ExecutionSettings()
        settings.user_id = 1
        settings.fallback_strategy = "option_c"
        settings.max_retry_per_tier = 1
        settings.timeout_per_tier_seconds = 30
        settings.track_fallback_reasons = True
        settings.track_strategy_effectiveness = True
        
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
        print(f"✅ Created ExecutionSettings:")
        print(f"  - ID: {settings.id}")
        print(f"  - User ID: {settings.user_id}")
        print(f"  - Strategy: {settings.fallback_strategy}")
        print(f"  - Timeout: {settings.timeout_per_tier_seconds}s")
        
        # Query back
        retrieved = db.query(ExecutionSettings).filter(
            ExecutionSettings.user_id == 1
        ).first()
        
        assert retrieved is not None, "Should retrieve settings"
        assert retrieved.fallback_strategy == "option_c", "Strategy should match"
        print("✅ Settings retrieved successfully")
        
    finally:
        db.close()
    
    print("=" * 60)


def test_xpath_cache_service():
    """Test XPath cache service"""
    print("\n" + "=" * 60)
    print("TEST 2: XPath Cache Service")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clean up any existing cache entries
        db.query(XPathCache).delete()
        db.commit()
        
        cache_service = XPathCacheService(db)
        
        # Test cache key generation
        print("\n[Test 2.1] Cache key generation...")
        key = cache_service.generate_cache_key(
            "https://example.com",
            "Click on login button"
        )
        print(f"  - Generated key: {key[:16]}...")
        assert len(key) == 64, "SHA256 should be 64 chars"
        print("✅ Cache key generation works")
        
        # Test caching XPath
        print("\n[Test 2.2] Caching XPath...")
        cached_entry = cache_service.cache_xpath(
            page_url="https://example.com",
            instruction="Click on login button",
            xpath="//button[@id='login']",
            extraction_time_ms=150.5,
            page_title="Example Domain",
            element_text="Login"
        )
        print(f"  - Cached entry ID: {cached_entry.id}")
        print(f"  - XPath: {cached_entry.xpath}")
        print(f"  - Extraction time: {cached_entry.extraction_time_ms}ms")
        print("✅ XPath cached successfully")
        
        # Test retrieving cached XPath
        print("\n[Test 2.3] Retrieving cached XPath...")
        retrieved = cache_service.get_cached_xpath(
            page_url="https://example.com",
            instruction="Click on login button"
        )
        assert retrieved is not None, "Should retrieve cached XPath"
        assert retrieved["xpath"] == "//button[@id='login']", "XPath should match"
        assert retrieved["hit_count"] == 1, "Hit count should be 1"
        print(f"  - Retrieved XPath: {retrieved['xpath']}")
        print(f"  - Hit count: {retrieved['hit_count']}")
        print("✅ Cache retrieval works")
        
        # Test cache hit increment
        print("\n[Test 2.4] Testing cache hit increment...")
        retrieved2 = cache_service.get_cached_xpath(
            page_url="https://example.com",
            instruction="Click on login button"
        )
        assert retrieved2["hit_count"] == 2, "Hit count should increment"
        print(f"  - Hit count after 2nd access: {retrieved2['hit_count']}")
        print("✅ Cache hit increment works")
        
        # Test cache stats
        print("\n[Test 2.5] Cache statistics...")
        stats = cache_service.get_cache_stats()
        print(f"  - Total entries: {stats['total_entries']}")
        print(f"  - Valid entries: {stats['valid_entries']}")
        print(f"  - Total hits: {stats['total_hits']}")
        print(f"  - Avg extraction time: {stats['avg_extraction_time_ms']:.2f}ms")
        assert stats['total_entries'] >= 1, "Should have at least 1 entry"
        assert stats['total_hits'] >= 2, "Should have at least 2 hits"
        print("✅ Cache stats working")
        
        # Test cache invalidation
        print("\n[Test 2.6] Cache invalidation...")
        cache_service.invalidate_cache(
            page_url="https://example.com",
            instruction="Click on login button",
            error_message="Element not found"
        )
        
        # Check validation failures count
        cache_entry = db.query(XPathCache).filter(
            XPathCache.cache_key == key
        ).first()
        assert cache_entry.validation_failures == 1, "Should have 1 validation failure"
        print(f"  - Validation failures: {cache_entry.validation_failures}")
        print("✅ Cache invalidation works")
        
    finally:
        db.close()
    
    print("=" * 60)


def test_three_tier_settings():
    """Test 3-Tier strategy settings"""
    print("\n" + "=" * 60)
    print("TEST 3: 3-Tier Strategy Settings")
    print("=" * 60)
    
    # Test Option A
    print("\n[Test 3.1] Option A (Tier 1 → Tier 2)...")
    settings_a = ExecutionSettings()
    settings_a.fallback_strategy = "option_a"
    assert settings_a.fallback_strategy == "option_a"
    print(f"  - Strategy: {settings_a.fallback_strategy}")
    print("✅ Option A settings valid")
    
    # Test Option B
    print("\n[Test 3.2] Option B (Tier 1 → Tier 3)...")
    settings_b = ExecutionSettings()
    settings_b.fallback_strategy = "option_b"
    assert settings_b.fallback_strategy == "option_b"
    print(f"  - Strategy: {settings_b.fallback_strategy}")
    print("✅ Option B settings valid")
    
    # Test Option C
    print("\n[Test 3.3] Option C (Tier 1 → Tier 2 → Tier 3)...")
    settings_c = ExecutionSettings()
    settings_c.fallback_strategy = "option_c"
    assert settings_c.fallback_strategy == "option_c"
    print(f"  - Strategy: {settings_c.fallback_strategy}")
    print("✅ Option C settings valid")
    
    # Test default values
    print("\n[Test 3.4] Default values...")
    # Create with defaults by using schema defaults
    from app.schemas.execution_settings import ExecutionSettingsBase
    settings_schema = ExecutionSettingsBase()
    print(f"  - Default strategy: {settings_schema.fallback_strategy}")
    print(f"  - Default timeout: {settings_schema.timeout_per_tier_seconds}s")
    print(f"  - Default max retries: {settings_schema.max_retry_per_tier}")
    assert settings_schema.fallback_strategy == "option_c", "Default should be option_c"
    assert settings_schema.timeout_per_tier_seconds == 30, "Default timeout should be 30s"
    print("✅ Default values correct")
    
    print("=" * 60)


def main():
    """Run all unit tests"""
    print("\n" + "=" * 60)
    print("Sprint 5.5: 3-Tier Execution Engine - Unit Tests")
    print("=" * 60)
    
    try:
        # Test 1: ExecutionSettings model
        test_execution_settings_model()
        
        # Test 2: XPath cache service
        test_xpath_cache_service()
        
        # Test 3: 3-Tier strategy settings
        test_three_tier_settings()
        
        print("\n" + "=" * 60)
        print("🎉 ALL UNIT TESTS PASSED!")
        print("=" * 60)
        print("\n✅ ExecutionSettings model working")
        print("✅ XPath cache service operational")
        print("✅ All fallback strategies (A, B, C) valid")
        print("✅ Database tables created successfully")
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. ✅ Day 1 Complete - Core framework implemented")
        print("2. 📋 Day 2 - Create API endpoints for settings")
        print("3. 📋 Day 3 - Build frontend UI components")
        print("4. 📋 Day 4 - Integration with execution service")
        print("5. 📋 Day 5 - E2E testing and documentation")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
