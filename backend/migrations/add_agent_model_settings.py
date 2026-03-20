"""
Migration: Add per-agent model provider/model fields to user_settings table
Sprint 10.6: Per-Agent Model Provider & Model Selection
Date: March 17, 2026

Adds 8 nullable VARCHAR(100) columns so each of the 4 agents
(observation, requirements, analysis, evolution) can have its own
provider and model override stored in the DB.

NULL means "use Azure default" — no data migration required.
"""
import sqlite3
import os
from pathlib import Path


NEW_COLUMNS = [
    ("observation_provider",   "VARCHAR(100)"),
    ("observation_model",      "VARCHAR(100)"),
    ("requirements_provider",  "VARCHAR(100)"),
    ("requirements_model",     "VARCHAR(100)"),
    ("analysis_provider",      "VARCHAR(100)"),
    ("analysis_model",         "VARCHAR(100)"),
    ("evolution_provider",     "VARCHAR(100)"),
    ("evolution_model",        "VARCHAR(100)"),
]


def get_db_path() -> str:
    """Return absolute path to the SQLite database file."""
    backend_dir = Path(__file__).parent.parent
    db_file = backend_dir / "aiwebtest.db"
    if not db_file.exists():
        raise FileNotFoundError(f"Database file not found: {db_file}")
    return str(db_file)


def migrate_up() -> None:
    """Add 8 per-agent columns to user_settings table (idempotent)."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(user_settings)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        added = []
        skipped = []
        for col_name, col_type in NEW_COLUMNS:
            if col_name in existing_columns:
                skipped.append(col_name)
                continue
            cursor.execute(
                f"ALTER TABLE user_settings ADD COLUMN {col_name} {col_type} NULL"
            )
            added.append(col_name)

        conn.commit()

        if added:
            print(f"✅ Added columns to user_settings: {added}")
        if skipped:
            print(f"ℹ️  Already present (skipped): {skipped}")
        if not added and not skipped:
            print("✅ No changes needed.")

    except Exception as exc:
        conn.rollback()
        print(f"❌ Migration failed: {exc}")
        raise
    finally:
        conn.close()


def migrate_down() -> None:
    """Drop the 8 per-agent columns (SQLite does not support DROP COLUMN natively,
    so this recreates the table without those columns)."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(user_settings)")
        all_cols = [row[1] for row in cursor.fetchall()]
        agent_col_names = {c[0] for c in NEW_COLUMNS}
        keep_cols = [c for c in all_cols if c not in agent_col_names]

        # Recreate table without agent columns
        cols_def_query = ", ".join(keep_cols)
        cursor.execute("BEGIN")
        cursor.execute(
            f"CREATE TABLE user_settings_backup AS "
            f"SELECT {cols_def_query} FROM user_settings"
        )
        cursor.execute("DROP TABLE user_settings")
        cursor.execute(
            f"ALTER TABLE user_settings_backup RENAME TO user_settings"
        )
        conn.commit()
        print(f"✅ Rolled back: removed agent columns from user_settings")

    except Exception as exc:
        conn.rollback()
        print(f"❌ Rollback failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    if action == "up":
        migrate_up()
    elif action == "down":
        migrate_down()
    else:
        print(f"Unknown action: {action!r}. Use 'up' or 'down'.")
        sys.exit(1)
