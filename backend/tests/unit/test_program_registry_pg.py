"""Unit tests for product program registry (PG-1 … PG-4)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud import journey_factory as crud
from app.db.base import Base
from app.models.journey_factory import JourneyBacklogItem, JourneyRegistryEntry, JourneyRegistryProject
from app.schemas.journey_factory import JourneyRegistryEntryCreate
from app.services.program_factory_scope import should_skip_factory_entry
from app.services.program_journey_seed import retire_journeys_for_initiative, seed_journeys_from_manifest
from app.services.program_registry_service import (
    ProgramManifestError,
    get_program_detail,
    list_program_slugs,
    load_program_manifest,
    resolve_effective_to,
    validate_manifest,
)


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


def test_list_program_slugs_includes_examples():
    slugs = list_program_slugs()
    assert "5g-mobile-broadband" in slugs
    assert "postpaid-browse" in slugs


def test_load_5g_manifest_merges_platform_profile():
    data = load_program_manifest("5g-mobile-broadband")
    ids = {c["id"] for c in data["_resolved_platform_components"]}
    assert "DT_WEBAPP" in ids
    assert "DT_CRM" in ids


def test_initiative_amendment_resolves_end_date():
    init = {
        "effective_to": "2026-06-30",
        "amendments": [{"type": "extend_end_date", "new_effective_to": "2026-07-15"}],
    }
    assert resolve_effective_to(init) == "2026-07-15"


def test_audience_validation():
    with pytest.raises(ProgramManifestError, match="audience"):
        validate_manifest(
            {
                "program": {"slug": "x"},
                "initiatives": [
                    {
                        "id": "a",
                        "kind": "offer",
                        "title": "A",
                        "effective_from": "2026-01-01",
                        "audience": "invalid",
                        "capability_keys": ["K"],
                        "platform_components": ["DT_WEBAPP"],
                    }
                ],
                "platform_components": [{"id": "DT_WEBAPP", "title": "W"}],
            },
            slug="x",
        )


def test_retire_journeys_for_initiative(db):
    crud.create_registry_entry(
        db,
        JourneyRegistryEntryCreate(
            slug="old-journey",
            project="Three-HK",
            name="Old",
            feature_url="https://example.com",
            tags=["regression"],
            extra_config={
                "program_slug": "postpaid-browse",
                "initiative_id": "abc-base-20260530",
            },
        ),
    )
    n = retire_journeys_for_initiative(
        db,
        program_slug="postpaid-browse",
        initiative_id="abc-base-20260530",
        retired_by_initiative_id="new-offer",
        project="Three-HK",
    )
    assert n == 1
    entry = crud.get_registry_by_slug(db, "Three-HK", "old-journey")
    assert entry.extra_config["retired"] is True
    assert "retired" in entry.tags
    assert "regression" not in entry.tags


def test_should_skip_retired_entry(db):
    entry = crud.create_registry_entry(
        db,
        JourneyRegistryEntryCreate(
            slug="retired-j",
            project="Three-HK",
            name="R",
            feature_url="https://example.com",
            extra_config={"program_slug": "postpaid-browse", "retired": True},
        ),
    )
    assert should_skip_factory_entry(entry) is True


def test_seed_postpaid_journeys(db):
    upserted, retired = seed_journeys_from_manifest(db, "postpaid-browse")
    assert upserted >= 1
    entry = crud.get_registry_by_slug(db, "Three-HK", "postpaid-abc-browse")
    assert entry is not None
    assert entry.extra_config.get("program_slug") == "postpaid-browse"


def test_get_program_detail_has_initiatives():
    detail = get_program_detail("postpaid-browse")
    assert detail.slug == "postpaid-browse"
    assert len(detail.initiatives) >= 2
    june = next(i for i in detail.initiatives if i.id == "june-marketing-20260605")
    assert june.audience == "new_signups"
    assert june.relationship == "stack"
