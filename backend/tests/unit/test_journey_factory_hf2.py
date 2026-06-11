"""Unit tests for journey registry and backlog (HF-2)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.crud import journey_factory as crud
from app.schemas.journey_factory import JourneyRegistryEntryCreate, JourneyBacklogEnqueue
from app.models.journey_factory import JourneyRegistryEntry, JourneyRegistryProject, JourneyBacklogItem


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            JourneyRegistryProject.__table__,
            JourneyRegistryEntry.__table__,
            JourneyBacklogItem.__table__,
        ],
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_create_and_list_registry(db):
    crud.create_registry_entry(
        db,
        JourneyRegistryEntryCreate(
            slug="diy-dashboard",
            project="Three-HK",
            name="DIY Dashboard",
            feature_url="https://example.com/diy",
            tags=["diy"],
            capability_keys=["DIY_DASHBOARD"],
        ),
    )
    items = crud.list_registry_entries(db, project="Three-HK")
    assert len(items) == 1
    assert items[0].slug == "diy-dashboard"


def test_enqueue_backlog_requires_registry_slug(db):
    crud.create_registry_entry(
        db,
        JourneyRegistryEntryCreate(
            slug="diy-dashboard",
            project="Three-HK",
            name="DIY Dashboard",
            feature_url="https://example.com/diy",
        ),
    )
    item = crud.enqueue_backlog_item(
        db,
        JourneyBacklogEnqueue(journey_slug="diy-dashboard", project="Three-HK"),
    )
    assert item.status == "pending"
    pending = crud.list_backlog_items(db, status="pending", project="Three-HK")
    assert len(pending) == 1


def test_enqueue_unknown_slug_raises(db):
    with pytest.raises(ValueError, match="Unknown journey slug"):
        crud.enqueue_backlog_item(
            db,
            JourneyBacklogEnqueue(journey_slug="missing", project="Three-HK"),
        )
