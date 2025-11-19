"""Check database contents."""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print("=" * 60)
    print("Database Users:")
    print("=" * 60)
    for user in users:
        print(f"\nID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")
        print(f"Created: {user.created_at}")
    print("\n" + "=" * 60)
finally:
    db.close()

