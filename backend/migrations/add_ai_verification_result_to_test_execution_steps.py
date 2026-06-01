"""Add ai_verification_result to test_execution_steps.

Safe to run multiple times. This migration exists in backend/migrations/ so the
startup auto-migration runner applies Sprint 10.17 schema changes on server
restart for older local databases.
"""

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from migrate_sprint10_17 import run_migration as legacy_run_migration


def upgrade() -> None:
    legacy_run_migration()


def main() -> None:
    upgrade()