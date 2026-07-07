"""Seed journey registry from program manifests; auto-retire on initiative replace (PG-3)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.crud import journey_factory as crud
from app.schemas.journey_factory import JourneyRegistryEntryCreate, JourneyRegistryEntryUpdate
from app.services.program_test_retire import retire_test_cases_for_initiative
from app.services.program_registry_service import (
    ProgramManifestError,
    list_program_slugs,
    load_program_manifest,
)


def _registry_project_for_manifest(manifest: dict[str, Any]) -> str:
    program = manifest.get("program") or {}
    return program.get("registry_project") or program.get("slug") or "Three-HK"


def is_journey_retired(extra_config: Optional[dict[str, Any]]) -> bool:
    if not extra_config:
        return False
    return bool(extra_config.get("retired"))


def retire_journeys_for_initiative(
    db: Session,
    *,
    program_slug: str,
    initiative_id: str,
    retired_by_initiative_id: str,
    project: Optional[str] = None,
) -> tuple[int, int]:
    """Mark registry journeys for a superseded initiative as retired. Returns (journeys, tests)."""
    count = 0
    reference_test_ids: set[int] = set()
    entries = crud.list_registry_entries(db, project=project, limit=500)
    now = datetime.now(timezone.utc).isoformat()
    for entry in entries:
        extra = dict(entry.extra_config or {})
        if extra.get("program_slug") != program_slug:
            continue
        if extra.get("initiative_id") != initiative_id:
            continue
        if extra.get("retired"):
            continue
        if entry.reference_test_id:
            reference_test_ids.add(entry.reference_test_id)
        extra["retired"] = True
        extra["retired_at"] = now
        extra["retired_by_initiative_id"] = retired_by_initiative_id
        extra["retired_reason"] = f"Superseded by initiative {retired_by_initiative_id} (relationship=replace)"
        tags = [t for t in (entry.tags or []) if t != "regression"]
        if "retired" not in tags:
            tags.append("retired")
        crud.update_registry_entry(
            db,
            entry,
            JourneyRegistryEntryUpdate(tags=tags, extra_config=extra),
        )
        count += 1

    tests_retired = retire_test_cases_for_initiative(
        db,
        program_slug=program_slug,
        initiative_id=initiative_id,
        retired_by_initiative_id=retired_by_initiative_id,
        reference_test_ids=reference_test_ids,
    )
    return count, tests_retired


def apply_replace_retirements(db: Session, manifest: dict[str, Any]) -> tuple[int, int]:
    program_slug = (manifest.get("program") or {}).get("slug")
    if not program_slug:
        return 0, 0
    project = _registry_project_for_manifest(manifest)
    journeys_total = 0
    tests_total = 0
    for init in manifest.get("initiatives") or []:
        if init.get("relationship") != "replace":
            continue
        for old_id in init.get("relates_to") or []:
            j, t = retire_journeys_for_initiative(
                db,
                program_slug=program_slug,
                initiative_id=old_id,
                retired_by_initiative_id=init["id"],
                project=project,
            )
            journeys_total += j
            tests_total += t
    return journeys_total, tests_total


def seed_journeys_from_manifest(db: Session, slug: str) -> tuple[int, int, int]:
    """Upsert journey_templates from a program manifest. Returns (upserted, journeys_retired, tests_retired)."""
    manifest = load_program_manifest(slug)
    program = manifest.get("program") or {}
    project = _registry_project_for_manifest(manifest)

    if program.get("reqiq_project_id"):
        crud.upsert_project_meta(
            db,
            project=project,
            reqiq_project_id=program.get("reqiq_project_id"),
            default_env_config=program.get("default_env_config"),
        )

    journeys_retired, tests_retired = apply_replace_retirements(db, manifest)

    count = 0
    for tmpl in manifest.get("journey_templates") or []:
        journey_slug = tmpl.get("slug")
        if not journey_slug:
            continue
        extra = dict(tmpl.get("extra_config") or {})
        extra.setdefault("program_slug", slug)
        initiative_id = tmpl.get("initiative_id") or extra.get("initiative_id")
        if initiative_id:
            extra["initiative_id"] = initiative_id

        feature_url = tmpl.get("feature_url") or "about:blank"
        if tmpl.get("feature_url_tbd"):
            feature_url = extra.get("placeholder_url") or "about:blank"
            extra["feature_url_tbd"] = True

        payload = JourneyRegistryEntryCreate(
            slug=journey_slug,
            project=project,
            name=tmpl["name"],
            feature_url=feature_url,
            tags=tmpl.get("tags"),
            capability_keys=tmpl.get("capability_keys"),
            requires_login=bool(extra.get("requires_runtime_credentials", False)),
            stop_at_page_hint=tmpl.get("stop_at_page_hint"),
            extra_config=extra,
        )
        existing = crud.get_registry_by_slug(db, project, journey_slug)
        if existing:
            crud.update_registry_entry(
                db,
                existing,
                JourneyRegistryEntryUpdate(**payload.model_dump(exclude={"slug", "project"})),
            )
        else:
            crud.create_registry_entry(db, payload)
        count += 1
    return count, journeys_retired, tests_retired


def seed_all_program_journeys(db: Session) -> dict[str, dict[str, int]]:
    results: dict[str, dict[str, int]] = {}
    for slug in list_program_slugs():
        try:
            upserted, journeys_retired, tests_retired = seed_journeys_from_manifest(db, slug)
            results[slug] = {
                "journeys_upserted": upserted,
                "journeys_retired": journeys_retired,
                "tests_retired": tests_retired,
            }
        except ProgramManifestError as exc:
            results[slug] = {"error": str(exc)}
    return results
