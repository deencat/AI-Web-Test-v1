"""
Create test user for API testing
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from app.models.user import User
from app.core.security import get_password_hash

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_user():
    """Create test user if it doesn't exist"""
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if existing_user:
            # Update password to ensure it's correct
            existing_user.hashed_password = get_password_hash("testpassword123")
            db.commit()
            
            print("✅ Test user password updated")
            print(f"  - Email: {existing_user.email}")
            print(f"  - Username: {existing_user.username}")
            print(f"  - Password: testpassword123")
            print(f"  - ID: {existing_user.id}")
            return existing_user
        
        # Create new user
        hashed_password = get_password_hash("testpassword123")
        
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            role="user",
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("✅ Test user created successfully!")
        print(f"  - Email: {user.email}")
        print(f"  - Username: {user.username}")
        print(f"  - Password: testpassword123")
        print(f"  - ID: {user.id}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
