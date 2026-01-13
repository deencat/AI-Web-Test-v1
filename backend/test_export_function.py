#!/usr/bin/env python3
"""Quick test of export function"""
import sys
from pathlib import Path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.crud import execution_feedback as crud_feedback

db = SessionLocal()

try:
    print("Testing export_feedback_to_dict...")
    result = crud_feedback.export_feedback_to_dict(db, limit=5)
    print(f"✓ Export returned {len(result)} items")
    if result:
        print(f"First item keys: {list(result[0].keys())}")
except Exception as e:
    print(f"✗ Export failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
