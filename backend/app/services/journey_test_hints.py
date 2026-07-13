"""Build suggest-from-wiki hints from purchase journey wiki content (UF-4.6)."""
from __future__ import annotations

from app.services.wiki_journey_merge import extract_purchase_journeys_section

_BASE_HINTS = """Generate browser E2E test scenarios from the compiled wiki.

RULES:
- Use ## Purchase journeys numbered steps as the PRIMARY guideline for each test.
- One scenario per major journey branch (happy path, negative path, payment variant).
- Each scenario title = plain-language user story (not internal codes).
- Steps must follow visible UI labels from the wiki (EN and 繁中 where given).
- STYLE: imperative browser commands (navigate, click, enter, verify).
- Reference the journey name and step numbers in the customerOutcome field.
- Include negative tests: ineligible address, expired promo, validation errors.
- Map offer eligibility to ## Base offer / ## Active promotions when present.
"""


def build_suggest_from_wiki_payload(
    wiki_markdown: str,
    *,
    webapp_url: str = "",
    max_scenarios: int = 10,
) -> dict:
    journeys = extract_purchase_journeys_section(wiki_markdown)
    hints = _BASE_HINTS
    if webapp_url:
        hints += f"\nWEBAPP_START_URL: {webapp_url}\n"
    if journeys:
        excerpt = journeys if len(journeys) <= 6000 else journeys[:6000] + "\n…(truncated)"
        hints += f"\nPURCHASE JOURNEYS (follow these steps):\n{excerpt}\n"
    else:
        hints += (
            "\nNo ## Purchase journeys section found — derive flows from "
            "## UX and UI (SMCD) and offer sections.\n"
        )

    payload: dict = {
        "maxScenarios": max_scenarios,
        "hints": hints,
    }
    if journeys:
        payload["capabilityKey"] = "purchase_journey"
    return payload
