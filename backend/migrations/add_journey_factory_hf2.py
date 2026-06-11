"""Create journey registry and backlog tables; seed from YAML (HF-2)."""

import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def upgrade() -> None:
    from app.db.base import Base
    from app.models.journey_factory import (  # noqa: F401
        JourneyBacklogItem,
        JourneyRegistryEntry,
        JourneyRegistryProject,
    )
    from app.services.journey_registry_seed import seed_journey_registry

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)
    tables = [
        JourneyRegistryProject.__table__,
        JourneyRegistryEntry.__table__,
        JourneyBacklogItem.__table__,
    ]
    if "journey_registry_entries" not in inspector.get_table_names():
        Base.metadata.create_all(bind=engine, tables=tables)

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        seed_journey_registry(db)
    finally:
        db.close()


def main() -> None:
    upgrade()


if __name__ == "__main__":
    main()
