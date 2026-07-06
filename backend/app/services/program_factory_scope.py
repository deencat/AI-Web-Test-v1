"""Factory planner helpers scoped by program manifest (PG-4)."""
from __future__ import annotations

from typing import Any, Optional

from app.models.journey_factory import JourneyRegistryEntry
from app.services.program_journey_seed import is_journey_retired
from app.services.program_registry_service import (
    ProgramManifestError,
    get_factory_rules,
    load_program_manifest,
)


def program_slug_from_entry(entry: JourneyRegistryEntry) -> Optional[str]:
    extra = entry.extra_config or {}
    return extra.get("program_slug")


def initiative_id_from_entry(entry: JourneyRegistryEntry) -> Optional[str]:
    extra = entry.extra_config or {}
    return extra.get("initiative_id")


def should_skip_factory_entry(entry: JourneyRegistryEntry) -> bool:
    if is_journey_retired(entry.extra_config):
        return True
    slug = program_slug_from_entry(entry)
    if not slug:
        return False
    try:
        rules = get_factory_rules(slug)
    except ProgramManifestError:
        return False
    exclude = set(rules.get("exclude_capability_keys") or [])
    keys = set(entry.capability_keys or [])
    if keys & exclude:
        return True
    return False


def build_planner_context(entry: JourneyRegistryEntry) -> dict[str, Any]:
    slug = program_slug_from_entry(entry)
    if not slug:
        return {}
    try:
        manifest = load_program_manifest(slug)
    except ProgramManifestError:
        return {}
    factory = manifest.get("factory") or {}
    program = manifest.get("program") or {}
    initiative = None
    iid = initiative_id_from_entry(entry)
    if iid:
        for init in manifest.get("initiatives") or []:
            if init.get("id") == iid:
                initiative = init
                break
    return {
        "program_slug": slug,
        "program_title": program.get("title"),
        "test_scope": program.get("test_scope"),
        "initiative_id": iid,
        "initiative": initiative,
        "planner_rules": list(factory.get("planner_rules") or []),
        "program_tags": list(factory.get("program_tags") or []),
    }


def merge_program_regression_tags(tags: list[str], program_slug: Optional[str]) -> list[str]:
    if not program_slug:
        return tags
    try:
        rules = get_factory_rules(program_slug)
    except ProgramManifestError:
        return tags
    merged = list(tags)
    for t in rules.get("program_tags") or []:
        if t not in merged:
            merged.append(t)
    return merged
