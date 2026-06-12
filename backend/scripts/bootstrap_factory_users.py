"""
Bootstrap factory RBAC users: separate admin vs superadmin accounts.

Usage (from backend/):
  python scripts/bootstrap_factory_users.py
  python scripts/bootstrap_factory_users.py --fix-admin-role

Environment (optional):
  FACTORY_SUPERADMIN_PASSWORD  — password for the superadmin account (dev default below)

Accounts created:
  admin       — role admin       (factory + registry; NO Observatory)
  superadmin  — role superadmin  (Observatory + all factory access)

Do NOT promote admin to superadmin; use two logins.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

load_dotenv(backend_dir / ".env", override=False)

from app.crud.user import create_user, get_user_by_username
from app.db.session import SessionLocal
from app.schemas.user import UserCreate

DEFAULT_SUPERADMIN_PASSWORD = "superadmin123"


def bootstrap(*, fix_admin_role: bool = False) -> None:
    db = SessionLocal()
    superadmin_password = os.getenv("FACTORY_SUPERADMIN_PASSWORD", DEFAULT_SUPERADMIN_PASSWORD)

    try:
        admin = get_user_by_username(db, "admin")
        if not admin:
            admin = create_user(
                db,
                UserCreate(
                    email="admin@aiwebtest.com",
                    username="admin",
                    password="admin123",
                    role="admin",
                ),
            )
            print(f"Created admin: {admin.username} (role=admin)")
        elif fix_admin_role and admin.role == "superadmin":
            admin.role = "admin"
            db.commit()
            print("Fixed: admin role restored to 'admin' (was superadmin)")

        superadmin = get_user_by_username(db, "superadmin")
        if not superadmin:
            superadmin = create_user(
                db,
                UserCreate(
                    email="superadmin@aiwebtest.com",
                    username="superadmin",
                    password=superadmin_password,
                    role="superadmin",
                ),
            )
            print(f"Created superadmin: {superadmin.username} (role=superadmin)")
        else:
            if superadmin.role != "superadmin":
                superadmin.role = "superadmin"
                db.commit()
                print("Updated superadmin user role to 'superadmin'")

        print()
        print("Factory login accounts (separate users):")
        print("  admin      — admin / admin123        (no Observatory)")
        print("  superadmin — superadmin / <FACTORY_SUPERADMIN_PASSWORD or superadmin123>")
        print()
        print("Log out and log in as superadmin to use Agent Observatory.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap admin + superadmin factory users")
    parser.add_argument(
        "--fix-admin-role",
        action="store_true",
        help="Demote admin back to role=admin if it was promoted to superadmin",
    )
    args = parser.parse_args()
    bootstrap(fix_admin_role=args.fix_admin_role)
