"""Update all user settings to use 4096 max_tokens (Sprint 4 fix)."""
from app.db.session import SessionLocal
from app.models.user_settings import UserSetting

def update_max_tokens():
    """Update max_tokens from 2000 to 4096 for all users."""
    db = SessionLocal()
    try:
        # Get all user settings
        settings = db.query(UserSetting).all()
        
        print(f"Found {len(settings)} user settings to update")
        
        for setting in settings:
            old_gen = setting.generation_max_tokens
            old_exec = setting.execution_max_tokens
            
            # Update max_tokens to 4096 if it's currently 2000
            if setting.generation_max_tokens == 2000:
                setting.generation_max_tokens = 4096
                print(f"✅ User {setting.user_id}: Updated generation_max_tokens from {old_gen} to 4096")
            
            if setting.execution_max_tokens == 2000:
                setting.execution_max_tokens = 4096
                print(f"✅ User {setting.user_id}: Updated execution_max_tokens from {old_exec} to 4096")
        
        db.commit()
        print("\n✅ All user settings updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_max_tokens()
