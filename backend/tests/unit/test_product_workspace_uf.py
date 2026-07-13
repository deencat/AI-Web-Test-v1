"""Unit tests for Product workspace (UF-1 … UF-6)."""
import pytest

from app.services.document_ingest import infer_source_type, validate_filename
from app.services.product_workspace_service import create_product_entry, get_product, list_products
from app.services.program_sync_agent import build_initiatives_from_wiki
from app.services.wiki_compile_profile import get_compile_feature, list_wiki_profiles


def test_list_products_includes_pilot_entries():
    items = list_products()
    ids = [p["id"] for p in items]
    assert "voucher-plan-dns-5gbb" in ids
    assert "5g-voucher-monthly-plan" in ids


def test_get_voucher_monthly_plan_product():
    p = get_product("5g-voucher-monthly-plan")
    assert p["reqiq_project_id"] == "cmp9en6hv000nte01qnbs8jic"
    assert p["title"] == "5G Voucher Monthly Plan"


def test_create_product_entry_roundtrip(tmp_path, monkeypatch):
    import app.services.product_workspace_service as svc

    monkeypatch.setattr(svc, "_CONFIG_PATH", tmp_path / "product-workspaces.yaml")
    entry = create_product_entry(
        product_id="new-offer",
        title="New Offer",
        reqiq_project_id="reqiq123",
        title_zh="新優惠",
        webapp_url="https://example.com/",
    )
    assert entry["id"] == "new-offer"
    assert get_product("new-offer")["title_zh"] == "新優惠"


def test_get_voucher_plan_dns_product():
    p = get_product("voucher-plan-dns-5gbb")
    assert p["reqiq_project_id"] == "cmp0zdx4g0004alp8z77ess7a"
    assert p["title"] == "Voucher Plan (DNS / 5GBB bundle)"
    assert p["program_slug"] == "voucher-plan-dns-5gbb"


def test_validate_pptx_allowed():
    validate_filename("june-promo.pptx")


def test_validate_exe_rejected():
    with pytest.raises(ValueError, match="not supported"):
        validate_filename("virus.exe")


def test_infer_source_type_marketing():
    assert infer_source_type("deck.pptx") == "marketing_deck"
    assert infer_source_type("screen.png") == "ux_ui"


def test_wiki_telecom_profile_loads():
    assert "telecom-promo" in list_wiki_profiles()
    feature = get_compile_feature("telecom-promo")
    assert "Active promotions" in feature
    assert "Purchase journeys" in feature


SAMPLE_WIKI = """
## Base offer
ABC 5G plan from SSCO URS.

## Active promotions
### June 2026 marketing
Effective dates: 2026-06-01 to 2026-06-30
Relationship: overlays base
Audience: new_signups

## Ended promotions
- May flash sale (ended 2026-05-31)

## UX and UI (SMCD)
Checkout banner layout.

## Notifications
SMS welcome template EN and 繁中.
"""


def test_build_initiatives_from_wiki_parses_june_promo():
    inits = build_initiatives_from_wiki(
        SAMPLE_WIKI,
        program_slug="5g-mobile-broadband",
        today=__import__("datetime").date(2026, 6, 15),
    )
    assert any(i["kind"] == "base_offer" for i in inits)
    june = next(i for i in inits if "june" in i["title"].lower())
    assert june["effective_from"] == "2026-06-01"
    assert june["effective_to"] == "2026-06-30"
    assert june["audience"] == "new_signups"
    assert june["relationship"] == "stack"


def test_build_initiatives_skips_ended_june_after_july():
    inits = build_initiatives_from_wiki(
        SAMPLE_WIKI,
        program_slug="5g-mobile-broadband",
        today=__import__("datetime").date(2026, 7, 2),
    )
    assert not any("june" in i["title"].lower() for i in inits if i["kind"] == "promotion")
