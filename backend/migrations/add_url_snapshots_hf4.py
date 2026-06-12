"""Create url_snapshots table (HF-4)."""

import os

from sqlalchemy import create_engine, inspect

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def upgrade() -> None:
    from app.db.base import Base
    from app.models.url_snapshot import UrlSnapshot  # noqa: F401

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)
    if "url_snapshots" not in inspector.get_table_names():
        Base.metadata.create_all(bind=engine, tables=[UrlSnapshot.__table__])


def main() -> None:
    upgrade()


if __name__ == "__main__":
    main()
