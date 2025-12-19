"""
Database Seed Script
====================
This script populates the database with seed data for development.

Usage:
  python db_seed.py                    # Seed all data
  python db_seed.py --reset            # Drop all data and reseed
  python db_seed.py --export           # Export current data to seed file
  
How It Works:
  1. Both developers run the same migrations (shared via Git)
  2. Both developers run the same seed script (shared via Git)
  3. Result: Both have identical base data
  4. Each developer can add their own test data locally
  5. When new test cases are needed, export them to seed file and commit

This solves the collaboration problem while keeping databases separate.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models
from app.models.user import User
from app.models.test_case import TestCase
from app.models.kb_document import KBDocument, KBCategory
from app.models.test_suite import TestSuite
from app.db.base import Base

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def reset_database(db: Session):
    """Drop all tables and recreate them"""
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("📝 Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete!")

def seed_users(db: Session):
    """Seed default users"""
    print("\n👤 Seeding users...")
    
    # Check if admin user already exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print(f"  ⏭️  User already exists: admin")
    else:
        # Create admin user (matches actual User model schema)
        admin = User(
            username="admin",
            email="admin@aiwebtest.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNq6L7LXu",  # "admin123"
            role="admin",
            is_active=True
        )
        db.add(admin)
        print(f"  ✅ Created user: admin")
    
    # Check if qa_user already exists
    qa_user = db.query(User).filter(User.username == "qa_user").first()
    if qa_user:
        print(f"  ⏭️  User already exists: qa_user")
    else:
        qa_user = User(
            username="qa_user",
            email="qa@aiwebtest.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNq6L7LXu",  # "admin123"
            role="user",
            is_active=True
        )
        db.add(qa_user)
        print(f"  ✅ Created user: qa_user")
    
    db.commit()

def seed_test_cases(db: Session):
    """Seed sample test cases"""
    print("\n🧪 Seeding test cases...")
    
    test_cases = [
        {
            "name": "Google Search Test",
            "description": "Test Google search functionality",
            "url": "https://www.google.com",
            "steps": [
                {"action": "navigate", "url": "https://www.google.com"},
                {"action": "type", "selector": "textarea[name='q']", "value": "AI Web Testing"},
                {"action": "click", "selector": "input[name='btnK']"},
                {"action": "assert", "selector": "div#search", "exists": True}
            ],
            "expected_result": "Search results should be displayed",
            "status": "active",
            "created_by": "system"
        },
        {
            "name": "GitHub Login Flow",
            "description": "Test GitHub login page elements",
            "url": "https://github.com/login",
            "steps": [
                {"action": "navigate", "url": "https://github.com/login"},
                {"action": "assert", "selector": "input[name='login']", "exists": True},
                {"action": "assert", "selector": "input[name='password']", "exists": True},
                {"action": "assert", "selector": "input[type='submit']", "exists": True}
            ],
            "expected_result": "Login form should be present",
            "status": "active",
            "created_by": "system"
        },
        {
            "name": "Example.com Navigation",
            "description": "Basic navigation test",
            "url": "https://example.com",
            "steps": [
                {"action": "navigate", "url": "https://example.com"},
                {"action": "assert", "selector": "h1", "text": "Example Domain"}
            ],
            "expected_result": "Page should load with title",
            "status": "active",
            "created_by": "system"
        }
    ]
    
    for test_data in test_cases:
        existing = db.query(TestCase).filter(TestCase.name == test_data["name"]).first()
        if not existing:
            test = TestCase(**test_data)
            db.add(test)
            print(f"  ✅ Created test case: {test_data['name']}")
        else:
            print(f"  ⏭️  Test case already exists: {test_data['name']}")
    
    db.commit()

def seed_knowledge_base(db: Session):
    """Seed knowledge base documents"""
    print("\n📚 Seeding knowledge base documents...")
    
    # First ensure we have a category
    category = db.query(KBCategory).filter(KBCategory.name == "best_practices").first()
    if not category:
        category = KBCategory(
            name="best_practices",
            description="Best practices and guidelines",
            color="#3B82F6"
        )
        db.add(category)
        db.commit()
    
    # Get first user
    user = db.query(User).first()
    if not user:
        print("  ⚠️  No users found. Cannot create KB documents without a user.")
        return
    
    kb_docs = [
        {
            "category_id": category.id,
            "title": "Selector Best Practices",
            "description": "Best practices for writing robust selectors",
            "filename": "selector_best_practices.txt",
            "file_path": "/kb/selector_best_practices.txt",
            "file_type": "txt",
            "file_size": 500,
            "content": """# Selector Best Practices

1. Prefer data-testid attributes over CSS classes
2. Use semantic HTML selectors when possible
3. Avoid XPath for simple selections
4. Use stable attributes (id, name, data-*)
5. Avoid nth-child selectors (brittle)

Example:
  ✅ Good: button[data-testid="submit-btn"]
  ❌ Bad: div > div:nth-child(3) > button
""",
            "user_id": user.id
        },
        {
            "category_id": category.id,
            "title": "Login Flow Pattern",
            "description": "Standard login flow pattern",
            "filename": "login_pattern.txt",
            "file_path": "/kb/login_pattern.txt",
            "file_type": "txt",
            "file_size": 400,
            "content": """# Standard Login Flow Pattern

Common pattern for testing login flows:

1. Navigate to login page
2. Verify login form exists
3. Enter username (input[name='username'] or input[type='email'])
4. Enter password (input[name='password'] or input[type='password'])
5. Click submit button
6. Verify redirect to dashboard/home
7. Verify user menu or logout button exists

Success rate: 95%
""",
            "user_id": user.id
        },
        {
            "category_id": category.id,
            "title": "Common Timeout Issues",
            "description": "Common timeout failures and solutions",
            "filename": "timeout_issues.txt",
            "file_path": "/kb/timeout_issues.txt",
            "file_type": "txt",
            "file_size": 600,
            "content": """# Common Timeout Failures

**Problem:** Tests timing out on dynamic content

**Root Causes:**
1. Waiting for wrong selector
2. Element loads late (AJAX)
3. Network issues
4. Heavy JavaScript rendering

**Solutions:**
1. Use explicit waits for dynamic content
2. Wait for network idle before assertions
3. Increase timeout for slow pages
4. Use visibility checks, not just presence

**Example Fix:**
  ❌ Before: assert element exists immediately
  ✅ After: wait for element visible with 10s timeout
""",
            "user_id": user.id
        }
    ]
    
    for doc_data in kb_docs:
        existing = db.query(KBDocument).filter(
            KBDocument.title == doc_data["title"]
        ).first()
        if not existing:
            doc = KBDocument(**doc_data)
            db.add(doc)
            print(f"  ✅ Created KB doc: {doc_data['title']}")
        else:
            print(f"  ⏭️  KB doc already exists: {doc_data['title']}")
    
    db.commit()

def seed_test_suites(db: Session):
    """Seed test suites"""
    print("\n📋 Seeding test suites...")
    
    # Get test cases for suite
    google_test = db.query(TestCase).filter(TestCase.name == "Google Search Test").first()
    github_test = db.query(TestCase).filter(TestCase.name == "GitHub Login Flow").first()
    example_test = db.query(TestCase).filter(TestCase.name == "Example.com Navigation").first()
    
    suites = [
        {
            "name": "Smoke Test Suite",
            "description": "Quick smoke tests for core functionality",
            "status": "active"
        },
        {
            "name": "Regression Suite",
            "description": "Full regression test suite",
            "status": "active"
        }
    ]
    
    for suite_data in suites:
        existing = db.query(TestSuite).filter(TestSuite.name == suite_data["name"]).first()
        if not existing:
            suite = TestSuite(**suite_data)
            
            # Add test cases to smoke suite
            if suite.name == "Smoke Test Suite" and google_test and example_test:
                suite.test_cases.append(google_test)
                suite.test_cases.append(example_test)
            
            # Add all tests to regression suite
            if suite.name == "Regression Suite":
                if google_test:
                    suite.test_cases.append(google_test)
                if github_test:
                    suite.test_cases.append(github_test)
                if example_test:
                    suite.test_cases.append(example_test)
            
            db.add(suite)
            print(f"  ✅ Created test suite: {suite_data['name']}")
        else:
            print(f"  ⏭️  Test suite already exists: {suite_data['name']}")
    
    db.commit()

def export_seed_data(db: Session):
    """Export current test cases to seed file for sharing"""
    print("\n💾 Exporting current data to seed file...")
    
    test_cases = db.query(TestCase).all()
    
    seed_data = []
    for test in test_cases:
        seed_data.append({
            "name": test.name,
            "description": test.description,
            "url": test.url,
            "steps": test.steps,
            "expected_result": test.expected_result,
            "status": test.status,
            "created_by": "system"  # Always set to system for seed data
        })
    
    # Save to JSON file
    with open("seed_test_cases.json", "w") as f:
        json.dump(seed_data, f, indent=2)
    
    print(f"✅ Exported {len(seed_data)} test cases to seed_test_cases.json")
    print("📝 Commit this file to share test cases with other developers!")

def import_seed_file(db: Session):
    """Import test cases from seed file"""
    print("\n📥 Importing test cases from seed file...")
    
    try:
        with open("seed_test_cases.json", "r") as f:
            seed_data = json.load(f)
        
        for test_data in seed_data:
            existing = db.query(TestCase).filter(TestCase.name == test_data["name"]).first()
            if not existing:
                test = TestCase(**test_data)
                db.add(test)
                print(f"  ✅ Imported: {test_data['name']}")
            else:
                print(f"  ⏭️  Already exists: {test_data['name']}")
        
        db.commit()
        print(f"✅ Import complete!")
    
    except FileNotFoundError:
        print("⚠️  No seed_test_cases.json file found. Run with --export first.")

def main():
    """Main seeding function"""
    db = SessionLocal()
    
    try:
        # Parse command line arguments
        reset = "--reset" in sys.argv
        export = "--export" in sys.argv
        import_seeds = "--import" in sys.argv
        
        if reset:
            confirm = input("⚠️  This will DELETE all data. Are you sure? (yes/no): ")
            if confirm.lower() != "yes":
                print("❌ Aborted.")
                return
            reset_database(db)
        
        if export:
            export_seed_data(db)
            return
        
        if import_seeds:
            import_seed_file(db)
            return
        
        # Default: Seed all data
        print("🌱 Starting database seeding...")
        print("=" * 70)
        
        seed_users(db)
        seed_test_cases(db)
        seed_knowledge_base(db)
        seed_test_suites(db)
        
        print("\n" + "=" * 70)
        print("✅ Database seeding complete!")
        print("\n📊 Summary:")
        print(f"  Users: {db.query(User).count()}")
        print(f"  Test Cases: {db.query(TestCase).count()}")
        print(f"  KB Documents: {db.query(KBDocument).count()}")
        print(f"  Test Suites: {db.query(TestSuite).count()}")
        
        print("\n💡 Tips:")
        print("  - Both developers should run this script after migrations")
        print("  - Use --export to share new test cases with team")
        print("  - Use --import to load shared test cases")
        print("  - Use --reset to start fresh (caution: deletes all data)")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
