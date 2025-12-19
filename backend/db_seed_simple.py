"""
Simple Database Seed Script - Demonstration
============================================
This is a simplified version to demonstrate the concept.

Both developers run this after migrations to get identical base data.

Usage:
  python db_seed_simple.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.db.base import Base

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_users(db):
    """Seed default users"""
    print("\n👤 Seeding users...")
    
    # Check if admin user already exists
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@aiwebtest.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNq6L7LXu",  # Password: admin123
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"  ✅ Created user: admin (password: admin123)")
    else:
        print(f"  ⏭️  User already exists: admin")
    
    # Check if qa_user already exists
    qa_user = db.query(User).filter(User.username == "qa_user").first()
    if not qa_user:
        qa_user = User(
            username="qa_user",
            email="qa@aiwebtest.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNq6L7LXu",  # Password: admin123
            role="user",
            is_active=True
        )
        db.add(qa_user)
        db.commit()
        print(f"  ✅ Created user: qa_user (password: admin123)")
    else:
        print(f"  ⏭️  User already exists: qa_user")

def main():
    """Main seeding function"""
    db = SessionLocal()
    
    try:
        print("🌱 Starting database seeding (simple version)...")
        print("=" * 70)
        
        seed_users(db)
        
        print("\n" + "=" * 70)
        print("✅ Database seeding complete!")
        print("\n📊 Summary:")
        print(f"  Users: {db.query(User).count()}")
        
        print("\n💡 Login credentials:")
        print("  Admin: admin / admin123")
        print("  QA User: qa_user / admin123")
        
        print("\n💡 Next steps:")
        print("  1. Both developers now have same users")
        print("  2. Create test cases via UI")
        print("  3. When ready to share: python db_seed.py --export")
        print("  4. Commit seed_test_cases.json to share with team")
        print("  5. Other developer: python db_seed.py --import")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
