"""Sync program manifest from compiled ReqIQ wiki (UF-5)."""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Optional

import yaml
from sqlalchemy.orm import Session

from app.services.product_workspace_service import ProductWorkspaceError, get_product
from app.services.program_journey_seed import seed_journeys_from_manifest
from app.services.program_registry_service import (
    ProgramManifestError,
    load_program_manifest,
    save_program_manifest_yaml,
)

_DATE_RE = re.compile(
    r"(20\d{2}-\d{2}-\d{2})\s*(?:to|–|-|—)\s*(20\d{2}-\d{2}-\d{2}|open-ended|null)",
    re.IGNORECASE,
)
_ISO_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or "promo"


def _parse_promo_section(block: str) -> dict[str, Any]:
    dates = _DATE_RE.search(block)
    effective_from = "2026-01-01"
    effective_to: Optional[str] = None
    if dates:
        effective_from = dates.group(1)
        end = dates.group(2)
        if end and end.lower() not in {"open-ended", "null"}:
            effective_to = end

    rel = "stack"
    if re.search(r"\breplaces\b", block, re.IGNORECASE):
        rel = "replace"
    elif re.search(r"\boverlays\b|\bstack\b", block, re.IGNORECASE):
        rel = "stack"

    audience = "all"
    if re.search(r"new_signups|new signups|new customers", block, re.IGNORECASE):
        audience = "new_signups"
    elif re.search(r"existing_only|existing customers", block, re.IGNORECASE):
        audience = "existing_only"

    return {
        "effective_from": effective_from,
        "effective_to": effective_to,
        "relationship": rel,
        "audience": audience,
    }


def _split_wiki_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: Optional[str] = None
    buf: list[str] = []
    for line in (markdown or "").splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip().lower()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _parse_active_promotions(section: str) -> list[dict[str, Any]]:
    promos: list[dict[str, Any]] = []
    chunks = re.split(r"\n###\s+", section)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        meta = _parse_promo_section(body)
        promos.append({"title": title, **meta})
    return promos


def _parse_ended_promotions(section: str) -> list[str]:
    titles: list[str] = []
    for line in section.splitlines():
        line = line.strip().lstrip("-").strip()
        if line and not line.startswith("#"):
            titles.append(line.split("(")[0].strip())
    return titles


def build_initiatives_from_wiki(
    wiki_markdown: str,
    *,
    program_slug: str,
    today: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Derive initiative list from compiled wiki headings."""
    today = today or date.today()
    sections = _split_wiki_sections(wiki_markdown)
    initiatives: list[dict[str, Any]] = []

    base_id = f"{program_slug}-base"
    initiatives.append(
        {
            "id": base_id,
            "kind": "base_offer",
            "title": "Base offer",
            "effective_from": "2020-01-01",
            "effective_to": None,
            "audience": "all",
            "capability_keys": [],
            "platform_components": ["DT_WEBAPP", "DT_CRM"],
            "regression_tags": [program_slug, f"initiative:{base_id}"],
        }
    )

    active = _parse_active_promotions(sections.get("active promotions", ""))
    prev_id = base_id
    for promo in active:
        pid = f"{_slugify(promo['title'])}-{promo['effective_from'].replace('-', '')}"
        end = promo.get("effective_to")
        if end:
            try:
                if today > date.fromisoformat(end):
                    continue
            except ValueError:
                pass
        init: dict[str, Any] = {
            "id": pid,
            "kind": "promotion",
            "title": promo["title"],
            "effective_from": promo["effective_from"],
            "effective_to": end,
            "audience": promo.get("audience") or "all",
            "capability_keys": [],
            "platform_components": ["DT_WEBAPP", "DT_CRM"],
            "regression_tags": [program_slug, f"initiative:{pid}"],
        }
        rel = promo.get("relationship")
        if rel in {"stack", "replace"}:
            init["relationship"] = rel
            init["relates_to"] = [prev_id if rel == "replace" else base_id]
        initiatives.append(init)
        if rel == "replace":
            prev_id = pid

    return initiatives


def sync_program_from_wiki(
    db: Session,
    *,
    product_id: str,
    wiki_markdown: str,
) -> dict[str, Any]:
    """Update program manifest initiatives from wiki and re-seed journeys."""
    product = get_product(product_id)
    program_slug = product.get("program_slug")
    if not program_slug:
        raise ProductWorkspaceError(f"Product '{product_id}' has no program_slug for sync")

    try:
        manifest = load_program_manifest(program_slug)
    except ProgramManifestError:
        raise ProductWorkspaceError(
            f"Program manifest '{program_slug}' not found — create via admin first"
        ) from None

    new_inits = build_initiatives_from_wiki(wiki_markdown, program_slug=program_slug)
    manifest["initiatives"] = new_inits
    manifest.setdefault("factory", {})["program_tags"] = [program_slug]

    yaml_text = yaml.dump(manifest, allow_unicode=True, sort_keys=False, default_flow_style=False)
    save_program_manifest_yaml(program_slug, yaml_text)
    upserted, journeys_retired, tests_retired = seed_journeys_from_manifest(db, program_slug)

    return {
        "product_id": product_id,
        "program_slug": program_slug,
        "initiatives_synced": len(new_inits),
        "journeys_upserted": upserted,
        "journeys_retired": journeys_retired,
        "tests_retired": tests_retired,
    }
