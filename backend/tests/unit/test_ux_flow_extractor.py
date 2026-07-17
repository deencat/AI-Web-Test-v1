"""Unit tests for UX flow journey extraction (UF-2.7 … UF-4.6)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.journey_test_hints import build_suggest_from_wiki_payload
from app.services.product_document_store import list_ux_ui_image_paths, save_upload
from app.services.ux_flow_extractor import _split_image_tiles, assemble_journeys_markdown
from app.services.wiki_journey_merge import extract_purchase_journeys_section, merge_purchase_journeys


SAMPLE_WIKI = """## Base offer
5G broadband base plan.

## Purchase journeys

### Wi-Fi 7 Unlimited
| Step | Screen | User action | Expected | UI labels |
|------|--------|-------------|----------|-----------|
| 1 | Banner | Tap promo banner | Flow starts | 選擇 |

## UX and UI (SMCD)
Field list.
"""


def test_merge_purchase_journeys_inserts_before_ux_section():
    journeys = "## Purchase journeys\n\n### Test flow\nStep 1"
    wiki = "## Base offer\nBase.\n\n## UX and UI (SMCD)\nFields."
    merged = merge_purchase_journeys(wiki, journeys)
    assert "## Purchase journeys" in merged
    assert merged.index("## Purchase journeys") < merged.index("## UX and UI")


def test_merge_purchase_journeys_replaces_existing_section():
    wiki = SAMPLE_WIKI
    new_j = "## Purchase journeys\n\n### New journey\nUpdated"
    merged = merge_purchase_journeys(wiki, new_j)
    assert "### New journey" in merged
    assert "### Wi-Fi 7 Unlimited" not in merged


def test_extract_purchase_journeys_section():
    body = extract_purchase_journeys_section(SAMPLE_WIKI)
    assert "### Wi-Fi 7 Unlimited" in body
    assert "Banner" in body


def test_build_suggest_from_wiki_payload_includes_journey_hints():
    payload = build_suggest_from_wiki_payload(
        SAMPLE_WIKI,
        webapp_url="https://example.com/5gbb",
        max_scenarios=5,
    )
    assert payload["maxScenarios"] == 5
    assert payload["capabilityKey"] == "purchase_journey"
    assert "Purchase journeys" in payload["hints"]
    assert "https://example.com/5gbb" in payload["hints"]


def test_assemble_journeys_markdown_includes_customer_summary():
    md = assemble_journeys_markdown(["### Flow A\nStep 1"], "Narrative summary.")
    assert "## Purchase journeys" in md
    assert "## Customer journeys (summary)" in md
    assert "Narrative summary" in md


def test_save_upload_and_list_ux_ui_images(tmp_path, monkeypatch):
    import app.services.product_document_store as store

    monkeypatch.setattr(store, "_STORE_ROOT", tmp_path)
    save_upload("prod-1", "flow.png", b"\x89PNG", source_type="ux_ui")
    save_upload("prod-1", "urs.pdf", b"%PDF", source_type="marketing_deck")
    paths = list_ux_ui_image_paths("prod-1")
    assert len(paths) == 1
    assert paths[0].name == "flow.png"


def test_split_image_tiles_small_image_unchanged():
    # 1x1 PNG
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    tiles = _split_image_tiles(png)
    assert len(tiles) == 1


def test_split_image_tiles_wide_board():
    pytest.importorskip("PIL")
    from PIL import Image
    import io

    img = Image.new("RGB", (5000, 400), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    tiles = _split_image_tiles(buf.getvalue())
    assert len(tiles) >= 2


def test_parse_response_text_openai_choices():
    from app.services.ux_flow_extractor import _parse_response_text

    azure_style = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "### Wi-Fi 7\n| Step | Screen |\n| 1 | Banner |",
                }
            }
        ]
    }
    text = _parse_response_text(azure_style)
    assert "### Wi-Fi 7" in text
    assert "Banner" in text


def test_parse_response_text_empty_choices():
    from app.services.ux_flow_extractor import _parse_response_text

    assert _parse_response_text({"choices": [{"message": {"content": ""}}]}) == ""
    from app.services.wiki_assembly import is_low_quality_reqiq_wiki

    assert is_low_quality_reqiq_wiki("## QA Summary: flow\nGeneric happy path.")
    assert not is_low_quality_reqiq_wiki(SAMPLE_WIKI)


def test_merge_reqiq_replaces_qa_summary_with_journeys():
    from app.services.wiki_assembly import merge_reqiq_with_journeys

    journeys = "## Purchase journeys\n\n### Wi-Fi 7\n| Step | Screen | User action | Expected | UI labels |\n| 1 | Banner | Tap | Start | 選擇 |"
    merged = merge_reqiq_with_journeys(
        "## QA Summary\nGeneric overview only.",
        journeys,
        product_title="5G BB",
    )
    assert "## Purchase journeys" in merged
    assert "QA Summary" not in merged
    assert "| 1 | Banner |" in merged
