"""Seed journey registry from YAML (HF-2)."""
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.crud import journey_factory as crud
from app.schemas.journey_factory import JourneyRegistryEntryCreate

_DEFAULT_YAML = Path(__file__).resolve().parents[2] / "config" / "uat-journey-registry.yaml"


def load_registry_yaml(path: Path | None = None) -> dict[str, Any]:
    yaml_path = path or _DEFAULT_YAML
    if not yaml_path.is_file():
        return {}
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def seed_journey_registry(db: Session, path: Path | None = None) -> int:
    """Upsert project meta and journeys from YAML. Returns number of journeys seeded."""
    data = load_registry_yaml(path)
    if not data:
        return 0

    project = data.get("project", "Three-HK")
    crud.upsert_project_meta(
        db,
        project=project,
        reqiq_project_id=data.get("reqiq_project_id"),
        default_env_config=data.get("default_env_config"),
    )

    count = 0
    for j in data.get("journeys") or []:
        slug = j.get("id") or j.get("slug")
        if not slug:
            continue
        existing = crud.get_registry_by_slug(db, project, slug)
        payload = JourneyRegistryEntryCreate(
            slug=slug,
            project=project,
            name=j["name"],
            feature_url=j["feature_url"],
            tags=j.get("tags"),
            capability_keys=j.get("capability_keys"),
            reference_test_id=j.get("reference_test_id"),
            requires_login=bool(j.get("requires_login", False)),
            stop_at_page_hint=j.get("stop_at_page_hint"),
        )
        if existing:
            from app.schemas.journey_factory import JourneyRegistryEntryUpdate

            crud.update_registry_entry(
                db,
                existing,
                JourneyRegistryEntryUpdate(**payload.model_dump(exclude={"slug", "project"})),
            )
        else:
            crud.create_registry_entry(db, payload)
        count += 1
    return count
