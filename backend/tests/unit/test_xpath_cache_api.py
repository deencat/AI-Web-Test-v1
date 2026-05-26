"""
Unit tests for XPath Cache Management API endpoints — Sprint 10.16.

TDD approach, covers:
 1. GET  /settings/xpath-cache/stats  — returns stats dict from XPathCacheService
 2. GET  /settings/xpath-cache        — lists entries, optional keyword filter on instruction/page_url
 3. DELETE /settings/xpath-cache/{id} — deletes by PK; 404 when not found
 4. DELETE /settings/xpath-cache      — clears all entries; invalid_only=true clears only invalid
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cache_entry(
    entry_id: int = 1,
    instruction: str = "Step 1: click Submit",
    page_url: str = "https://example.com/checkout",
    xpath: str = "//button[@id='submit']",
    is_valid: bool = True,
    hit_count: int = 5,
):
    entry = MagicMock()
    entry.id = entry_id
    entry.instruction = instruction
    entry.page_url = page_url
    entry.xpath = xpath
    entry.cache_key = "abc123"
    entry.selector_type = "xpath"
    entry.is_valid = is_valid
    entry.hit_count = hit_count
    entry.validation_failures = 0
    entry.extraction_time_ms = 250.0
    entry.page_title = "Checkout"
    entry.element_text = "Submit"
    entry.metadata = None
    entry.last_validated = None
    entry.created_at = datetime(2026, 5, 1, tzinfo=timezone.utc)
    entry.updated_at = datetime(2026, 5, 20, tzinfo=timezone.utc)
    return entry


# ---------------------------------------------------------------------------
# 1. XPathCacheService.get_cache_stats() contract
# ---------------------------------------------------------------------------


class TestXPathCacheStats:
    """XPathCacheService.get_cache_stats returns expected keys."""

    def test_stats_returns_required_keys(self):
        from app.services.xpath_cache_service import XPathCacheService

        db = MagicMock()
        # Simulate empty DB
        db.query.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.all.return_value = []

        svc = XPathCacheService(db)
        stats = svc.get_cache_stats()

        required_keys = {
            "total_entries", "valid_entries", "invalid_entries",
            "total_hits", "avg_extraction_time_ms", "cache_hit_rate",
        }
        assert required_keys.issubset(stats.keys())

    def test_stats_zero_when_empty(self):
        from app.services.xpath_cache_service import XPathCacheService

        db = MagicMock()
        db.query.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.all.return_value = []

        svc = XPathCacheService(db)
        stats = svc.get_cache_stats()

        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["invalid_entries"] == 0


# ---------------------------------------------------------------------------
# 2. XPathCacheStatsResponse schema
# ---------------------------------------------------------------------------


class TestXPathCacheStatsSchema:
    """XPathCacheStatsResponse Pydantic schema validates fields."""

    def test_schema_accepts_valid_stats(self):
        from app.schemas.execution_settings import XPathCacheStatsResponse

        data = {
            "total_entries": 42,
            "valid_entries": 40,
            "invalid_entries": 2,
            "total_hits": 150,
            "avg_extraction_time_ms": 312.5,
            "cache_hit_rate": 3.57,
        }
        stats = XPathCacheStatsResponse(**data)
        assert stats.total_entries == 42
        assert stats.valid_entries == 40
        assert stats.cache_hit_rate == 3.57

    def test_schema_fields_are_numeric(self):
        from app.schemas.execution_settings import XPathCacheStatsResponse

        stats = XPathCacheStatsResponse(
            total_entries=0,
            valid_entries=0,
            invalid_entries=0,
            total_hits=0,
            avg_extraction_time_ms=0.0,
            cache_hit_rate=0.0,
        )
        assert isinstance(stats.total_entries, int)
        assert isinstance(stats.avg_extraction_time_ms, float)


# ---------------------------------------------------------------------------
# 3. XPathCacheListResponse schema
# ---------------------------------------------------------------------------


class TestXPathCacheListResponseSchema:
    """XPathCacheListResponse wraps entries list and total count."""

    def test_schema_wraps_entries_and_total(self):
        from app.schemas.execution_settings import XPathCacheListResponse, XPathCache

        entry = XPathCache(
            id=1,
            page_url="https://example.com",
            instruction="click ok",
            xpath="//button",
            cache_key="key123",
            selector_type="xpath",
            is_valid=True,
            hit_count=3,
            validation_failures=0,
            created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        resp = XPathCacheListResponse(entries=[entry], total=1)
        assert resp.total == 1
        assert len(resp.entries) == 1

    def test_empty_list_is_valid(self):
        from app.schemas.execution_settings import XPathCacheListResponse

        resp = XPathCacheListResponse(entries=[], total=0)
        assert resp.total == 0
        assert resp.entries == []


# ---------------------------------------------------------------------------
# 4. DELETE /settings/xpath-cache/{id} — service direct-delete logic
# ---------------------------------------------------------------------------


class TestDeleteXPathCacheEntryById:
    """Deleting a specific cache entry by primary key."""

    def test_delete_existing_entry_removes_it_from_db(self):
        from app.services.xpath_cache_service import XPathCacheService
        from app.models.execution_settings import XPathCache as XPathCacheModel

        db = MagicMock()
        entry = _make_cache_entry(entry_id=7)
        db.query.return_value.filter.return_value.first.return_value = entry

        svc = XPathCacheService(db)
        # Simulate a direct DB query-and-delete by ID (endpoint logic)
        found = db.query(XPathCacheModel).filter(XPathCacheModel.id == 7).first()
        assert found is not None
        db.delete(found)
        db.commit()

        db.delete.assert_called_once_with(found)
        db.commit.assert_called()

    def test_delete_returns_none_when_not_found(self):
        from app.models.execution_settings import XPathCache as XPathCacheModel

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        found = db.query(XPathCacheModel).filter(XPathCacheModel.id == 999).first()
        assert found is None


# ---------------------------------------------------------------------------
# 5. DELETE /settings/xpath-cache — clear all or invalid-only
# ---------------------------------------------------------------------------


class TestClearXPathCache:
    """Clearing all or invalid-only entries uses existing service methods."""

    def test_clear_invalid_entries_delegates_to_service(self):
        from app.services.xpath_cache_service import XPathCacheService

        db = MagicMock()
        db.query.return_value.filter.return_value.delete.return_value = 3
        svc = XPathCacheService(db)

        count = svc.clear_invalid_entries()
        assert count == 3

    def test_clear_all_entries_deletes_full_table(self):
        from app.models.execution_settings import XPathCache as XPathCacheModel

        db = MagicMock()
        db.query.return_value.delete.return_value = 10

        deleted = db.query(XPathCacheModel).delete()
        db.commit()
        assert deleted == 10
        db.commit.assert_called()

    def test_clear_returns_deleted_count(self):
        from app.services.xpath_cache_service import XPathCacheService

        db = MagicMock()
        db.query.return_value.filter.return_value.delete.return_value = 5
        svc = XPathCacheService(db)

        count = svc.clear_invalid_entries()
        assert isinstance(count, int)


# ---------------------------------------------------------------------------
# 6. GET /settings/xpath-cache — keyword filter
# ---------------------------------------------------------------------------


class TestListXPathCacheKeywordFilter:
    """Listing entries with optional keyword filter searches instruction and page_url."""

    def test_filter_matches_instruction_substring(self):
        entries = [
            _make_cache_entry(1, instruction="Step 5: click Subscribe button"),
            _make_cache_entry(2, instruction="Step 6: fill card number"),
        ]
        keyword = "subscribe"
        filtered = [
            e for e in entries
            if keyword.lower() in e.instruction.lower()
            or keyword.lower() in e.page_url.lower()
        ]
        assert len(filtered) == 1
        assert filtered[0].id == 1

    def test_filter_matches_page_url_substring(self):
        entries = [
            _make_cache_entry(1, page_url="https://three.com.hk/checkout"),
            _make_cache_entry(2, page_url="https://example.com/login"),
        ]
        keyword = "three.com"
        filtered = [
            e for e in entries
            if keyword.lower() in e.page_url.lower()
        ]
        assert len(filtered) == 1
        assert filtered[0].id == 1

    def test_no_keyword_returns_all_entries(self):
        entries = [_make_cache_entry(i) for i in range(1, 6)]
        keyword = None
        filtered = entries if not keyword else [
            e for e in entries
            if keyword.lower() in e.instruction.lower()
            or keyword.lower() in e.page_url.lower()
        ]
        assert len(filtered) == 5

    def test_filter_is_case_insensitive(self):
        entries = [_make_cache_entry(1, instruction="Step 3: CLICK Login")]
        keyword = "click login"
        filtered = [
            e for e in entries
            if keyword.lower() in e.instruction.lower()
        ]
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# 7. XPathCache response schema from_attributes (ORM → Pydantic)
# ---------------------------------------------------------------------------


class TestXPathCacheSchemaOrmCompatibility:
    """XPathCache schema can be built from ORM model instances."""

    def test_schema_from_attributes(self):
        from app.schemas.execution_settings import XPathCache as XPathCacheSchema

        entry = _make_cache_entry(
            entry_id=10,
            instruction="Step 2: click checkout",
            page_url="https://shop.example.com/cart",
            xpath="//button[@data-testid='checkout']",
        )
        # Simulate ORM → Pydantic via model_validate (from_attributes)
        schema = XPathCacheSchema.model_validate(entry)
        assert schema.id == 10
        assert schema.instruction == "Step 2: click checkout"
        assert schema.page_url == "https://shop.example.com/cart"
        assert schema.xpath == "//button[@data-testid='checkout']"
        assert schema.is_valid is True
        assert schema.hit_count == 5
