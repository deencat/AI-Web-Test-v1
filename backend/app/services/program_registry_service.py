"""Load and validate product program manifests from YAML (PG-1)."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

from app.schemas.program_registry import (
    InitiativeSummary,
    PlatformComponentSummary,
    ProgramDetailResponse,
    ProgramSummary,
    ReferenceLayerSummary,
    InitiativeAmendment,
)

_CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config" / "programs"
_PROFILES_DIR = _CONFIG_ROOT / "_platform-profiles"


class ProgramManifestError(ValueError):
    pass


def programs_config_dir() -> Path:
    return _CONFIG_ROOT


def _is_program_manifest(path: Path) -> bool:
    if not path.is_file() or not path.suffix.lower() in {".yaml", ".yml"}:
        return False
    if path.name.startswith("_"):
        return False
    return path.parent == _CONFIG_ROOT


def list_program_slugs() -> list[str]:
    slugs: list[str] = []
    for path in sorted(_CONFIG_ROOT.glob("*.yaml")):
        if _is_program_manifest(path):
            slugs.append(path.stem)
    for path in sorted(_CONFIG_ROOT.glob("*.yml")):
        if _is_program_manifest(path):
            slugs.append(path.stem)
    return sorted(set(slugs))


def _manifest_path(slug: str) -> Path:
    yaml_path = _CONFIG_ROOT / f"{slug}.yaml"
    if yaml_path.is_file():
        return yaml_path
    yml_path = _CONFIG_ROOT / f"{slug}.yml"
    if yml_path.is_file():
        return yml_path
    raise ProgramManifestError(f"Program manifest not found: {slug}")


def load_platform_profile(profile_name: str) -> dict[str, Any]:
    path = _PROFILES_DIR / f"{profile_name}.yaml"
    if not path.is_file():
        raise ProgramManifestError(f"Unknown platform profile: {profile_name}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def resolve_effective_to(initiative: dict[str, Any]) -> Optional[str]:
    effective_to = initiative.get("effective_to")
    for amendment in initiative.get("amendments") or []:
        if amendment.get("type") == "extend_end_date" and amendment.get("new_effective_to"):
            effective_to = amendment["new_effective_to"]
    return effective_to


def is_initiative_active(initiative: dict[str, Any], on_date: Optional[date] = None) -> bool:
    today = on_date or date.today()
    start = initiative.get("effective_from")
    if start:
        try:
            if today < date.fromisoformat(str(start)):
                return False
        except ValueError:
            pass
    end = resolve_effective_to(initiative)
    if end:
        try:
            if today > date.fromisoformat(str(end)):
                return False
        except ValueError:
            pass
    return True


def merge_platform_components(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    components: dict[str, dict[str, Any]] = {}
    profile_name = manifest.get("platform_profile")
    if profile_name:
        profile = load_platform_profile(profile_name)
        for comp in profile.get("platform_components") or []:
            if comp.get("id"):
                components[comp["id"]] = deepcopy(comp)
    for comp in manifest.get("platform_components") or []:
        if comp.get("id"):
            components[comp["id"]] = {**components.get(comp["id"], {}), **deepcopy(comp)}
    return list(components.values())


def validate_manifest(data: dict[str, Any], *, slug: Optional[str] = None) -> None:
    program = data.get("program") or {}
    program_slug = program.get("slug")
    if not program_slug:
        raise ProgramManifestError("program.slug is required")
    if slug and program_slug != slug:
        raise ProgramManifestError(f"program.slug '{program_slug}' does not match filename '{slug}'")

    platform_ids = {c["id"] for c in merge_platform_components(data) if c.get("id")}
    ref_ids = {r["id"] for r in (data.get("reference_layers") or []) if r.get("id")}

    initiatives = data.get("initiatives") or []
    if not initiatives:
        raise ProgramManifestError("initiatives must contain at least one entry")

    initiative_ids = set()
    for init in initiatives:
        iid = init.get("id")
        if not iid:
            raise ProgramManifestError("Each initiative requires id")
        if iid in initiative_ids:
            raise ProgramManifestError(f"Duplicate initiative id: {iid}")
        initiative_ids.add(iid)

        for pc in init.get("platform_components") or []:
            if pc not in platform_ids:
                raise ProgramManifestError(
                    f"Initiative '{iid}' references unknown platform_component '{pc}'"
                )

        rel = init.get("relationship")
        relates = init.get("relates_to") or []
        if rel in {"replace", "stack"} and not relates:
            raise ProgramManifestError(
                f"Initiative '{iid}' with relationship={rel} requires relates_to"
            )

        audience = init.get("audience")
        if audience and audience not in {"new_signups", "all", "existing_only"}:
            raise ProgramManifestError(f"Initiative '{iid}' has invalid audience: {audience}")

    all_ids = {i.get("id") for i in initiatives}
    for init in initiatives:
        for rid in init.get("relates_to") or []:
            if rid not in all_ids:
                raise ProgramManifestError(
                    f"Initiative '{init.get('id')}' relates_to missing id '{rid}'"
                )

    for tmpl in data.get("journey_templates") or []:
        extra = tmpl.get("extra_config") or {}
        test_kind = extra.get("test_kind", "ui")
        if test_kind not in {"ui", "api", "orchestration"}:
            raise ProgramManifestError(f"Invalid test_kind '{test_kind}' in journey_templates")
        if test_kind == "ui" and not tmpl.get("feature_url") and not tmpl.get("feature_url_tbd"):
            raise ProgramManifestError(
                f"Journey template '{tmpl.get('slug')}' with test_kind=ui needs feature_url or feature_url_tbd"
            )


def load_program_manifest(slug: str, *, validate: bool = True) -> dict[str, Any]:
    path = _manifest_path(slug)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if validate:
        validate_manifest(data, slug=slug)
    data["_manifest_path"] = str(path)
    data["_resolved_platform_components"] = merge_platform_components(data)
    return data


def load_program_manifest_raw(slug: str) -> str:
    path = _manifest_path(slug)
    return path.read_text(encoding="utf-8")


def list_platform_profile_names() -> list[str]:
    if not _PROFILES_DIR.is_dir():
        return []
    names: list[str] = []
    for path in sorted(_PROFILES_DIR.glob("*.yaml")):
        names.append(path.stem)
    return names


def build_new_program_manifest(
    *,
    slug: str,
    title: str,
    kind: str = "pilot",
    test_scope: str = "DT_ONLY",
    platform_profile: Optional[str] = "dt-telecom-default",
    registry_project: str = "Three-HK",
    initiative_title: Optional[str] = None,
) -> str:
    """Render a starter YAML manifest for a new program."""
    today = date.today().isoformat()
    init_id = f"{slug}-base-{today.replace('-', '')}"
    init_title = initiative_title or f"{title} — base"
    lines = [
        f"# Program manifest — {title}",
        "program:",
        f"  slug: {slug}",
        f'  title: "{title}"',
        f"  kind: {kind}",
        f"  test_scope: {test_scope}",
        f"  registry_project: {registry_project}",
        "",
    ]
    if platform_profile:
        if platform_profile not in list_platform_profile_names():
            raise ProgramManifestError(f"Unknown platform profile: {platform_profile}")
        lines.extend([f"platform_profile: {platform_profile}", ""])
    else:
        lines.extend(
            [
                "platform_components:",
                "  - id: DT_WEBAPP",
                "    title: WebApp",
                "    test_surfaces: [ui]",
                "",
            ]
        )

    lines.extend(
        [
            "initiatives:",
            f"  - id: {init_id}",
            "    kind: base_offer",
            f'    title: "{init_title}"',
            f'    effective_from: "{today}"',
            "    effective_to: null",
            "    audience: all",
            "    capability_keys: []",
            "    platform_components: [DT_WEBAPP]",
            f"    regression_tags: [{slug}, initiative:{init_id}]",
            "",
            "journey_templates: []",
            "",
            "factory:",
            f"  program_tags: [{slug}]",
            "",
        ]
    )
    return "\n".join(lines)


def create_program_manifest(
    *,
    slug: str,
    title: str,
    kind: str = "pilot",
    test_scope: str = "DT_ONLY",
    platform_profile: Optional[str] = "dt-telecom-default",
    registry_project: str = "Three-HK",
    initiative_title: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new validated program manifest file."""
    if slug in list_program_slugs():
        raise ProgramManifestError(f"Program already exists: {slug}")
    yaml_content = build_new_program_manifest(
        slug=slug,
        title=title,
        kind=kind,
        test_scope=test_scope,
        platform_profile=platform_profile,
        registry_project=registry_project,
        initiative_title=initiative_title,
    )
    return save_program_manifest_yaml(slug, yaml_content)


def save_program_manifest_yaml(slug: str, yaml_content: str) -> dict[str, Any]:
    data = yaml.safe_load(yaml_content) or {}
    validate_manifest(data, slug=slug)
    path = _CONFIG_ROOT / f"{slug}.yaml"
    path.write_text(yaml_content, encoding="utf-8")
    return load_program_manifest(slug)


def _to_initiative_summary(init: dict[str, Any]) -> InitiativeSummary:
    return InitiativeSummary(
        id=init["id"],
        kind=init.get("kind") or "initiative",
        title=init.get("title") or init["id"],
        effective_from=str(init.get("effective_from") or ""),
        effective_to=init.get("effective_to"),
        resolved_effective_to=resolve_effective_to(init),
        relationship=init.get("relationship"),
        relates_to=list(init.get("relates_to") or []),
        audience=init.get("audience"),
        capability_keys=list(init.get("capability_keys") or []),
        platform_components=list(init.get("platform_components") or []),
        regression_tags=list(init.get("regression_tags") or []),
        amendments=[InitiativeAmendment.model_validate(a) for a in (init.get("amendments") or [])],
    )


def get_program_detail(slug: str) -> ProgramDetailResponse:
    data = load_program_manifest(slug)
    program = data.get("program") or {}
    initiatives = [_to_initiative_summary(i) for i in (data.get("initiatives") or [])]
    refs = [
        ReferenceLayerSummary(
            id=r["id"],
            title=r.get("title") or r["id"],
            capability_key=r.get("capability_key"),
            automate=bool(r.get("automate", False)),
            parity_note=r.get("parity_note") or r.get("note"),
        )
        for r in (data.get("reference_layers") or [])
    ]
    platform = [
        PlatformComponentSummary(
            id=c["id"],
            title=c.get("title") or c["id"],
            modules=list(c.get("modules") or []),
            test_surfaces=list(c.get("test_surfaces") or []),
            aliases=list(c.get("aliases") or []),
            notes=c.get("notes"),
        )
        for c in (data.get("_resolved_platform_components") or [])
    ]
    return ProgramDetailResponse(
        slug=slug,
        program=program,
        platform_components=platform,
        reference_layers=refs,
        initiatives=initiatives,
        hub_gaps=list(data.get("hub_gaps") or []),
        factory=data.get("factory"),
        orchestration_suites=list(data.get("orchestration_suites") or []),
    )


def list_program_summaries() -> list[ProgramSummary]:
    items: list[ProgramSummary] = []
    for slug in list_program_slugs():
        data = load_program_manifest(slug)
        program = data.get("program") or {}
        initiatives = data.get("initiatives") or []
        active = sum(1 for i in initiatives if is_initiative_active(i))
        items.append(
            ProgramSummary(
                slug=slug,
                title=program.get("title") or slug,
                kind=program.get("kind"),
                test_scope=program.get("test_scope"),
                initiative_count=len(initiatives),
                active_initiative_count=active,
            )
        )
    return items


def get_factory_rules(slug: str) -> dict[str, Any]:
    data = load_program_manifest(slug)
    return data.get("factory") or {}


def get_initiative_by_id(slug: str, initiative_id: str) -> Optional[dict[str, Any]]:
    data = load_program_manifest(slug)
    for init in data.get("initiatives") or []:
        if init.get("id") == initiative_id:
            return init
    return None


def build_reqiq_onboarding(slug: str) -> dict[str, Any]:
    data = load_program_manifest(slug)
    program = data.get("program") or {}
    items = []
    for init in data.get("initiatives") or []:
        sources = list(init.get("source_files") or [])
        if not sources:
            continue
        items.append(
            {
                "initiative_id": init["id"],
                "initiative_title": init.get("title") or init["id"],
                "source_files": sources,
                "capability_keys": list(init.get("capability_keys") or []),
            }
        )
    for ref in data.get("reference_layers") or []:
        assets = ref.get("assets") or []
        files = [a.get("file") for a in assets if a.get("file")]
        if not files:
            continue
        items.append(
            {
                "initiative_id": ref["id"],
                "initiative_title": ref.get("title") or ref["id"],
                "source_files": files,
                "capability_keys": [ref.get("capability_key") or ref["id"]],
            }
        )
    steps = [
        "Upload each source_file to ReqIQ workspace via Knowledge Base",
        "Run embedding reindex after each batch",
        "Add requirements with capabilityKey from capability_keys",
        "Check readiness score before factory test-gen",
        "Use reference_layers only for parity assertions (automate: false)",
    ]
    return {
        "program_slug": slug,
        "reqiq_project_id": program.get("reqiq_project_id"),
        "source_folder": program.get("source_folder"),
        "items": items,
        "steps": steps,
    }
