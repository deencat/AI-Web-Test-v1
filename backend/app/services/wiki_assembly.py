"""Assemble test-ready wiki markdown when UX flow images are primary sources."""
from __future__ import annotations

import re

from app.services.product_document_store import list_mvp_config_paths, list_ux_ui_image_paths
from app.services.wiki_journey_merge import CUSTOMER_JOURNEYS_HEADING, PURCHASE_JOURNEYS_HEADING

_STEP_TABLE_RE = re.compile(r"\|\s*Step\s*\|", re.IGNORECASE)
_QA_SUMMARY_RE = re.compile(r"^##\s*QA\s+Summary", re.IGNORECASE | re.MULTILINE)


def journeys_have_step_tables(journeys_markdown: str) -> bool:
    """True when vision output includes actionable step tables."""
    if not journeys_markdown:
        return False
    if _STEP_TABLE_RE.search(journeys_markdown):
        return True
    # Numbered steps without table still useful
    return bool(re.search(r"^\|\s*1\s*\|", journeys_markdown, re.MULTILINE))


def is_low_quality_reqiq_wiki(wiki_markdown: str) -> bool:
    """Detect generic ReqIQ compile from PNG OCR (not usable for E2E tests)."""
    md = wiki_markdown or ""
    if not md.strip():
        return True
    if _QA_SUMMARY_RE.search(md):
        return True
    if PURCHASE_JOURNEYS_HEADING.lower() not in md.lower():
        if "## Base offer" not in md and "happy path" in md.lower():
            return True
    return False


def is_ux_primary_product(product_id: str) -> bool:
    """Product workspace has UX images but no structured offer/config uploads."""
    if not list_ux_ui_image_paths(product_id):
        return False
    return not list_mvp_config_paths(product_id)


def build_ux_first_wiki(
    journeys_markdown: str,
    *,
    product_title: str = "",
    include_offer_stubs: bool = True,
) -> str:
    """Build telecom-promo wiki skeleton centred on vision-extracted Purchase journeys."""
    journeys = (journeys_markdown or "").strip()
    title = product_title.strip() or "Product"

    parts = [f"# {title} — Test context (UX flow sources)\n"]

    if journeys:
        if PURCHASE_JOURNEYS_HEADING not in journeys:
            parts.append(f"{PURCHASE_JOURNEYS_HEADING}\n\n{journeys}")
        else:
            parts.append(journeys)
    else:
        parts.append(
            f"{PURCHASE_JOURNEYS_HEADING}\n\n"
            "_No journeys extracted yet — configure UX_FLOW_VISION_PROVIDER/MODEL or use Edit to paste flow steps._\n"
        )

    if include_offer_stubs:
        parts.append(
            """## Base offer
_Upload SSCO URS / DT Offer Table (xlsx) and click Update summary to fill plan codes, pricing, and eligibility._

## Active promotions
_List timed promos with effective dates when marketing decks or offer tables are uploaded._

## Ended promotions
_Mark ended promos here so they are excluded from regression._

## UX and UI (SMCD)
_Per-screen validation rules and bilingual field labels — extend from Purchase journey step tables above._

## Notifications
_SMS / email / push copy when notification sources are uploaded._

## Terms and conditions
_Key T&C clauses when legal documents are uploaded._

## Open questions / gaps
- Confirm xAPI endpoints per journey step with API spec owners.
- Upload offer Excel to link plan codes ($238 / $191 tracks) to CRM rows.
"""
        )

    return "\n\n".join(parts).strip() + "\n"


def merge_reqiq_with_journeys(
    reqiq_wiki: str,
    journeys_markdown: str,
    *,
    product_title: str = "",
    product_id: str = "",
) -> str:
    """Prefer vision journeys; replace low-quality ReqIQ PNG-OCR output."""
    journeys = (journeys_markdown or "").strip()
    has_ux = bool(list_ux_ui_image_paths(product_id)) if product_id else False

    if has_ux and not (reqiq_wiki or "").strip():
        return build_ux_first_wiki(
            journeys,
            product_title=product_title,
            include_offer_stubs=True,
        )

    if is_ux_primary_product(product_id):
        return build_ux_first_wiki(
            journeys,
            product_title=product_title,
            include_offer_stubs=True,
        )

    if not journeys:
        return reqiq_wiki or ""

    if is_low_quality_reqiq_wiki(reqiq_wiki):
        if journeys_have_step_tables(journeys):
            return build_ux_first_wiki(
                journeys,
                product_title=product_title,
                include_offer_stubs=True,
            )

    from app.services.wiki_journey_merge import merge_purchase_journeys

    return merge_purchase_journeys(reqiq_wiki, journeys)
