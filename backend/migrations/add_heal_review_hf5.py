"""Create factory_heal_attempts and heal_review_items tables (HF-5)."""

import os

from sqlalchemy import create_engine, inspect

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aiwebtest.db")


def upgrade() -> None:
    from app.db.base import Base
    from app.models.heal_review import FactoryHealAttempt, HealReviewItem  # noqa: F401

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    to_create = []
    if "factory_heal_attempts" not in tables:
        to_create.append(FactoryHealAttempt.__table__)
    if "heal_review_items" not in tables:
        to_create.append(HealReviewItem.__table__)
    if to_create:
        Base.metadata.create_all(bind=engine, tables=to_create)


def main() -> None:
    upgrade()


if __name__ == "__main__":
    main()
