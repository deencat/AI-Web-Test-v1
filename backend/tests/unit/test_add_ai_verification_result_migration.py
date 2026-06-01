import importlib.util
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def _load_migration_module():
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "add_ai_verification_result_to_test_execution_steps.py"
    )
    spec = importlib.util.spec_from_file_location(
        "add_ai_verification_result_to_test_execution_steps",
        migration_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_upgrade_adds_missing_ai_verification_result_column(tmp_path, monkeypatch):
    db_path = tmp_path / "ai_verification_result.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE test_execution_steps (
                    id INTEGER PRIMARY KEY,
                    execution_id INTEGER NOT NULL,
                    step_index INTEGER NOT NULL,
                    status VARCHAR(50)
                )
                """
            )
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    migration = _load_migration_module()

    migration.upgrade()

    columns = [column["name"] for column in inspect(engine).get_columns("test_execution_steps")]
    assert "ai_verification_result" in columns


def test_upgrade_is_idempotent_when_column_already_exists(tmp_path, monkeypatch):
    db_path = tmp_path / "ai_verification_result_idempotent.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE test_execution_steps (
                    id INTEGER PRIMARY KEY,
                    execution_id INTEGER NOT NULL,
                    step_index INTEGER NOT NULL,
                    status VARCHAR(50),
                    ai_verification_result TEXT
                )
                """
            )
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    migration = _load_migration_module()

    migration.upgrade()
    migration.upgrade()

    columns = [column["name"] for column in inspect(engine).get_columns("test_execution_steps")]
    assert columns.count("ai_verification_result") == 1