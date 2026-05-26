import importlib.util
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def _load_migration_module():
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "add_local_vllm_enable_thinking.py"
    )
    spec = importlib.util.spec_from_file_location("add_local_vllm_enable_thinking", migration_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_upgrade_adds_missing_local_vllm_enable_thinking_column(tmp_path, monkeypatch):
    db_path = tmp_path / "migration_test.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE user_settings (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    generation_provider VARCHAR(50) NOT NULL,
                    generation_model VARCHAR(100) NOT NULL,
                    generation_temperature FLOAT,
                    generation_max_tokens INTEGER,
                    execution_provider VARCHAR(50) NOT NULL,
                    execution_model VARCHAR(100) NOT NULL,
                    execution_temperature FLOAT,
                    execution_max_tokens INTEGER,
                    stagehand_provider VARCHAR(20) NOT NULL DEFAULT 'python',
                    observation_provider VARCHAR(100),
                    observation_model VARCHAR(100),
                    requirements_provider VARCHAR(100),
                    requirements_model VARCHAR(100),
                    analysis_provider VARCHAR(100),
                    analysis_model VARCHAR(100),
                    evolution_provider VARCHAR(100),
                    evolution_model VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
                """
            )
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    migration = _load_migration_module()

    migration.upgrade()

    columns = [column["name"] for column in inspect(engine).get_columns("user_settings")]
    assert "local_vllm_enable_thinking" in columns


def test_upgrade_is_idempotent_when_column_already_exists(tmp_path, monkeypatch):
    db_path = tmp_path / "migration_idempotent.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE user_settings (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    generation_provider VARCHAR(50) NOT NULL,
                    generation_model VARCHAR(100) NOT NULL,
                    execution_provider VARCHAR(50) NOT NULL,
                    execution_model VARCHAR(100) NOT NULL,
                    stagehand_provider VARCHAR(20) NOT NULL DEFAULT 'python',
                    local_vllm_enable_thinking BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    migration = _load_migration_module()

    migration.upgrade()
    migration.upgrade()

    columns = [column["name"] for column in inspect(engine).get_columns("user_settings")]
    assert columns.count("local_vllm_enable_thinking") == 1