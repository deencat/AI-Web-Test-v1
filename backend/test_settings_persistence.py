"""
Test Script: Verify Execution Settings Persistence
Tests that settings are saved, loaded, and used correctly
"""
import sys
import asyncio
from app.db.session import SessionLocal
from app.models.execution_settings import ExecutionSettings
from app.models.user import User
from app.services.execution_service import ExecutionService

def test_settings_persistence():
    """Test that settings persist and are loaded correctly"""
    print("🧪 Testing Execution Settings Persistence\n")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Step 1: Check current settings for user 1
        print("\n📋 Step 1: Check Current Settings for User 1")
        settings = db.query(ExecutionSettings).filter(
            ExecutionSettings.user_id == 1
        ).first()
        
        if settings:
            print(f"✅ Found settings:")
            print(f"   ID: {settings.id}")
            print(f"   Strategy: {settings.fallback_strategy}")
            print(f"   Timeout: {settings.timeout_per_tier_seconds}s")
            print(f"   Max Retry: {settings.max_retry_per_tier}")
        else:
            print("❌ No settings found for user 1")
            print("   (This is expected if you haven't saved settings yet)")
        
        # Step 2: Test what execution_service.py will use
        print("\n🔍 Step 2: Test What Execution Service Will Use")
        
        from app.services.execution_service import ExecutionService
        
        exec_service = ExecutionService()
        loaded_settings = exec_service._get_user_execution_settings(db, user_id=1)
        
        print(f"   Execution Service will use:")
        print(f"   Strategy: {loaded_settings.fallback_strategy}")
        print(f"   Timeout: {loaded_settings.timeout_per_tier_seconds}s")
        print(f"   Max Retry: {loaded_settings.max_retry_per_tier}")
        print(f"   Track fallback: {loaded_settings.track_fallback_reasons}")
        print(f"   Track effectiveness: {loaded_settings.track_strategy_effectiveness}")
        
        if settings:
            if settings.fallback_strategy == loaded_settings.fallback_strategy:
                print("\n✅ SUCCESS: Execution service loads saved settings correctly!")
            else:
                print(f"\n❌ MISMATCH: DB has {settings.fallback_strategy}, "
                      f"but service will use {loaded_settings.fallback_strategy}")
        else:
            print("\n⚠️  Note: No saved settings, execution service using defaults")
        
        # Step 3: Simulate updating settings
        print("\n📝 Step 3: Simulate Updating Settings to option_a")
        
        if settings:
            # Update existing
            settings.fallback_strategy = "option_a"
            settings.timeout_per_tier_seconds = 45
            db.commit()
            print("✅ Updated existing settings")
        else:
            # Create new
            new_settings = ExecutionSettings(
                user_id=1,
                fallback_strategy="option_a",
                max_retry_per_tier=2,
                timeout_per_tier_seconds=45,
                track_fallback_reasons=True,
                track_strategy_effectiveness=True
            )
            db.add(new_settings)
            db.commit()
            print("✅ Created new settings")
        
        # Step 4: Verify the change persisted
        print("\n🔄 Step 4: Reload and Verify Persistence")
        db.expire_all()  # Clear cache
        
        reloaded_settings = db.query(ExecutionSettings).filter(
            ExecutionSettings.user_id == 1
        ).first()
        
        if reloaded_settings:
            print(f"✅ Reloaded settings:")
            print(f"   Strategy: {reloaded_settings.fallback_strategy}")
            print(f"   Timeout: {reloaded_settings.timeout_per_tier_seconds}s")
            
            if reloaded_settings.fallback_strategy == "option_a":
                print("\n✅ SUCCESS: Settings persisted correctly!")
            else:
                print(f"\n❌ FAIL: Expected option_a, got {reloaded_settings.fallback_strategy}")
        
        # Step 5: Reset to original
        print("\n🔄 Step 5: Reset to Original Settings")
        if settings:
            reloaded_settings.fallback_strategy = settings.fallback_strategy if hasattr(settings, 'fallback_strategy') else "option_c"
            reloaded_settings.timeout_per_tier_seconds = 30
            db.commit()
            print("✅ Reset complete")
        
        print("\n" + "=" * 60)
        print("✅ Test Complete!\n")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_settings_persistence()
