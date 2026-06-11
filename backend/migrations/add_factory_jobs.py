"""Create factory_jobs and factory_job_events tables (Hermes QA Factory HF-1)."""

import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def upgrade() -> None:
    from app.db.base import Base
    from app.models.factory_job import FactoryJob, FactoryJobEvent  # noqa: F401

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)
    if "factory_jobs" in inspector.get_table_names():
        return
    Base.metadata.create_all(bind=engine, tables=[FactoryJob.__table__, FactoryJobEvent.__table__])


def main() -> None:
    upgrade()


if __name__ == "__main__":
    main()
