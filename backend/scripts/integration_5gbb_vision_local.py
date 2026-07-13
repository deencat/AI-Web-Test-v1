"""Integration test: vision journey extraction on cached 5GBB UX images (no ReqIQ)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


async def main() -> int:
    from app.services.product_document_store import list_ux_ui_image_paths
    from app.services.ux_flow_extractor import extract_journeys_for_product
    from app.services.wiki_journey_merge import PURCHASE_JOURNEYS_HEADING, merge_purchase_journeys
    from app.services.journey_test_hints import build_suggest_from_wiki_payload

    product_id = "5g-mobile-broadband"
    paths = list_ux_ui_image_paths(product_id)
    print(f"Cached UX images: {len(paths)}")
    for p in paths:
        print(f"  - {p.name} ({p.stat().st_size // 1024} KB)")

    if not paths:
        print("FAIL: seed images first (run e2e script upload or save_upload)")
        return 1

    result = await extract_journeys_for_product(product_id)
    print(f"images_processed: {result.images_processed}")
    print(f"tiles_processed: {result.tiles_processed}")
    print(f"vision_used: {result.vision_used}")
    print(f"journey_names: {result.journey_names}")
    if result.errors:
        print(f"errors: {result.errors}")

    md = result.journeys_markdown
    assert PURCHASE_JOURNEYS_HEADING in md or md.startswith("##"), "expected journey markdown"
    print(f"\nJourney markdown length: {len(md)}")
    print(md[:800], "\n...")

    merged = merge_purchase_journeys("# Wiki\n\n## Base offer\n", md)
    assert PURCHASE_JOURNEYS_HEADING in merged

    payload = build_suggest_from_wiki_payload(merged, webapp_url="https://example.com", max_scenarios=5)
    assert payload.get("capabilityKey") == "purchase_journey" or payload.get("hints")
    print(f"\nTest hints payload keys: {list(payload.keys())}")
    print("PASS: local journey pipeline")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
