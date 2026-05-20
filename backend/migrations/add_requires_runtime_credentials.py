"""
Migration: add requires_runtime_credentials column to test_cases table.

Sprint 10.14 — Ephemeral CRM Login Credentials
Run this script once to apply the migration:
    python migrations/add_requires_runtime_credentials.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

def upgrade():
    with engine.connect() as conn:
        # Check if column already exists (idempotent)
        result = conn.execute(
            text("PRAGMA table_info(test_cases)")
        )
        column_names = [row[1] for row in result.fetchall()]

        if "requires_runtime_credentials" not in column_names:
            conn.execute(
                text(
                    "ALTER TABLE test_cases "
                    "ADD COLUMN requires_runtime_credentials BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            conn.commit()
            print("✅ Added column: test_cases.requires_runtime_credentials")
        else:
            print("ℹ️  Column already exists: test_cases.requires_runtime_credentials")


if __name__ == "__main__":
    upgrade()
