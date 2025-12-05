"""Debug script to check what CRUD returns"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import SessionLocal
from app.crud import test_case as crud

def debug_crud():
    db = SessionLocal()
    try:
        print("\n" + "="*60)
        print("Testing CRUD get_test_cases function")
        print("="*60)
        
        test_cases, total = crud.get_test_cases(db, skip=0, limit=10)
        
        print(f"\nTotal test cases: {total}")
        print(f"Returned: {len(test_cases)} test cases\n")
        
        for tc in test_cases:
            print(f"\n--- Test Case ID: {tc.id} ---")
            print(f"Title: {tc.title}")
            print(f"Steps type: {type(tc.steps).__name__}")
            if isinstance(tc.steps, str):
                print(f"⚠️  Steps is still a STRING!")
                print(f"Steps value: {tc.steps[:100]}...")
            elif isinstance(tc.steps, list):
                print(f"✅ Steps is a LIST!")
                print(f"Steps value: {tc.steps[:2]}...")
            else:
                print(f"❌ Steps is {type(tc.steps)}: {tc.steps}")
            
            print(f"Tags type: {type(tc.tags).__name__}")
            if isinstance(tc.tags, str):
                print(f"⚠️  Tags is still a STRING!")
                print(f"Tags value: {tc.tags}")
            elif isinstance(tc.tags, list):
                print(f"✅ Tags is a LIST!")
                print(f"Tags value: {tc.tags}")
            elif tc.tags is None:
                print(f"Tags value: None")
            else:
                print(f"❌ Tags is {type(tc.tags)}: {tc.tags}")
                
    finally:
        db.close()

if __name__ == "__main__":
    debug_crud()
