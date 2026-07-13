"""Merge extracted purchase journeys into compiled wiki markdown (UF-3.6)."""
from __future__ import annotations

import re

PURCHASE_JOURNEYS_HEADING = "## Purchase journeys"
CUSTOMER_JOURNEYS_HEADING = "## Customer journeys (summary)"


def has_purchase_journeys_section(markdown: str) -> bool:
    return PURCHASE_JOURNEYS_HEADING.lower() in (markdown or "").lower()


def merge_purchase_journeys(wiki_markdown: str, journeys_markdown: str) -> str:
    """Insert or replace ## Purchase journeys in wiki body."""
    journeys = (journeys_markdown or "").strip()
    if not journeys:
        return wiki_markdown or ""

    wiki = (wiki_markdown or "").strip()
    if not wiki:
        return journeys

    pattern = re.compile(
        rf"^{re.escape(PURCHASE_JOURNEYS_HEADING)}.*?(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if pattern.search(wiki):
        return pattern.sub(journeys + "\n\n", wiki, count=1)

    insert_before = [
        "## UX and UI (SMCD)",
        "## Notifications",
        "## Terms and conditions",
        "## Open questions / gaps",
    ]
    for heading in insert_before:
        idx = wiki.find(heading)
        if idx >= 0:
            return wiki[:idx].rstrip() + "\n\n" + journeys + "\n\n" + wiki[idx:]

    return wiki.rstrip() + "\n\n" + journeys + "\n"


def extract_purchase_journeys_section(markdown: str) -> str:
    """Return body under ## Purchase journeys for test-hint generation."""
    if not markdown:
        return ""
    pattern = re.compile(
        rf"^{re.escape(PURCHASE_JOURNEYS_HEADING)}\s*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    return match.group(1).strip() if match else ""
