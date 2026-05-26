from types import SimpleNamespace
from unittest.mock import MagicMock

from run_migrations import run_migration


def test_run_migration_supports_legacy_migrate_up(monkeypatch):
    called = {"migrate_up": False}

    def fake_migrate_up():
        called["migrate_up"] = True

    monkeypatch.setattr(
        "run_migrations.load_migration_module",
        lambda _: SimpleNamespace(migrate_up=fake_migrate_up),
    )

    db = MagicMock()

    result = run_migration("legacy_migration.py", db)

    assert result is True
    assert called["migrate_up"] is True
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_run_migration_supports_legacy_run_migration(monkeypatch):
    called = {"run_migration": False}

    def fake_run_migration():
        called["run_migration"] = True
        return True

    monkeypatch.setattr(
        "run_migrations.load_migration_module",
        lambda _: SimpleNamespace(run_migration=fake_run_migration),
    )

    db = MagicMock()

    result = run_migration("legacy_runner.py", db)

    assert result is True
    assert called["run_migration"] is True
    db.add.assert_called_once()
    db.commit.assert_called_once()