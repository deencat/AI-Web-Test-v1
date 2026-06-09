"""
Database migration: Phase 2 — Custom vLLM Model Support

Adds two nullable columns to user_settings:
  - local_vllm_custom_model    TEXT  — model name (e.g. "Qwen3.6-35B-A3B-MLX-8bit")
  - local_vllm_custom_endpoint TEXT  — endpoint URL (e.g. "http://192.168.206.164:1235/v1")

Safe to run on existing databases; both columns default to NULL so existing rows
are unaffected.  Re-running is also safe — already-present columns are skipped.
"""
import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")
TABLE_NAME = "user_settings"

NEW_COLUMNS = [
    ("local_vllm_custom_model",    "TEXT"),
    ("local_vllm_custom_endpoint", "TEXT"),
]


def column_exists(inspector, table: str, column: str) -> bool:
    return column in [c["name"] for c in inspector.get_columns(table)]


def run_migration():
    print("=" * 60)
    print("Phase 2: Custom vLLM Model Support — DB Migration")
    print("=" * 60)
    print(f"\nDatabase: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    if TABLE_NAME not in inspector.get_table_names():
        print(f"\n❌  Table '{TABLE_NAME}' not found. Run the main DB setup first.")
        sys.exit(1)

    with engine.begin() as conn:
        for col_name, col_type in NEW_COLUMNS:
            if column_exists(inspector, TABLE_NAME, col_name):
                print(f"\n⏭️  '{TABLE_NAME}.{col_name}' already exists — skipping.")
            else:
                print(f"\n➕  Adding '{TABLE_NAME}.{col_name}' ({col_type}) …")
                conn.execute(
                    text(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col_name} {col_type}")
                )
                # Verify
                inspector2 = inspect(engine)
                if column_exists(inspector2, TABLE_NAME, col_name):
                    print(f"✅  '{col_name}' created successfully.")
                else:
                    print(f"❌  Failed to create '{col_name}'.")
                    sys.exit(1)

    print("\n" + "=" * 60)
    print("Migration complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
