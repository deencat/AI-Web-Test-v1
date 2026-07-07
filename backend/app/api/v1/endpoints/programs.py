"""Product program manifests API (PG-1 … PG-5)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_factory_operator, require_role, _ROLE_RANK
from app.models.user import User
from app.schemas.program_registry import (
    ProgramCreateRequest,
    ProgramCreateResponse,
    ProgramDetailResponse,
    ProgramListResponse,
    ProgramManifestRawResponse,
    ProgramManifestSaveRequest,
    ProgramManifestSaveResponse,
    ProgramSeedJourneysResponse,
    ProgramSummary,
    PlatformProfileSummary,
    ReqIQOnboardingResponse,
    ReqIQOnboardingItem,
)
from app.services.program_journey_seed import seed_all_program_journeys, seed_journeys_from_manifest
from app.crud import journey_factory as crud_journey
from app.services.program_registry_service import (
    ProgramManifestError,
    build_reqiq_onboarding,
    create_program_manifest,
    get_program_detail,
    list_platform_profile_names,
    list_program_summaries,
    load_program_manifest,
    load_program_manifest_raw,
    load_platform_profile,
    save_program_manifest_yaml,
)

router = APIRouter()
require_admin = require_role(_ROLE_RANK["admin"], "admin")


@router.get("/platform-profiles")
def list_platform_profiles(
    _: User = Depends(require_factory_operator),
) -> dict:
    items = []
    for name in list_platform_profile_names():
        try:
            profile = load_platform_profile(name)
            items.append(
                PlatformProfileSummary(
                    name=name,
                    title=(profile.get("title") or name),
                ).model_dump()
            )
        except ProgramManifestError:
            items.append(PlatformProfileSummary(name=name).model_dump())
    return {"items": items}


@router.post("", response_model=ProgramCreateResponse, status_code=status.HTTP_201_CREATED)
def create_program(
    body: ProgramCreateRequest,
    _: User = Depends(require_admin),
) -> ProgramCreateResponse:
    try:
        create_program_manifest(
            slug=body.slug,
            title=body.title,
            kind=body.kind,
            test_scope=body.test_scope,
            platform_profile=body.platform_profile or None,
            registry_project=body.registry_project,
            initiative_title=body.initiative_title,
        )
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProgramCreateResponse(slug=body.slug, message="Program manifest created")


@router.get("", response_model=ProgramListResponse)
def list_programs(
    _: User = Depends(get_current_active_user),
) -> ProgramListResponse:
    items = list_program_summaries()
    return ProgramListResponse(items=items, total=len(items))


@router.get("/{slug}", response_model=ProgramDetailResponse)
def get_program(
    slug: str,
    _: User = Depends(get_current_active_user),
) -> ProgramDetailResponse:
    try:
        return get_program_detail(slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{slug}/initiatives/{initiative_id}")
def get_initiative(
    slug: str,
    initiative_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict:
    try:
        detail = get_program_detail(slug)
        manifest = load_program_manifest(slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    initiative = next((i for i in detail.initiatives if i.id == initiative_id), None)
    if not initiative:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Initiative not found")

    raw = next((i for i in (manifest.get("initiatives") or []) if i.get("id") == initiative_id), None)
    project = (manifest.get("program") or {}).get("registry_project") or slug
    entries = crud_journey.list_registry_entries(db, project=project, limit=500)
    journeys = []
    for e in entries:
        extra = e.extra_config or {}
        if extra.get("program_slug") == slug and extra.get("initiative_id") == initiative_id:
            journeys.append(
                {
                    "id": e.id,
                    "slug": e.slug,
                    "name": e.name,
                    "feature_url": e.feature_url,
                    "tags": e.tags,
                    "retired": bool(extra.get("retired")),
                }
            )

    return {
        "program_slug": slug,
        "initiative": initiative.model_dump(),
        "raw": raw,
        "journeys": journeys,
    }


@router.get("/{slug}/manifest", response_model=ProgramManifestRawResponse)
def get_program_manifest_raw(
    slug: str,
    _: User = Depends(require_factory_operator),
) -> ProgramManifestRawResponse:
    try:
        content = load_program_manifest_raw(slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ProgramManifestRawResponse(slug=slug, yaml_content=content)


@router.put("/{slug}/manifest", response_model=ProgramManifestSaveResponse)
def save_program_manifest(
    slug: str,
    body: ProgramManifestSaveRequest,
    _: User = Depends(require_admin),
) -> ProgramManifestSaveResponse:
    try:
        save_program_manifest_yaml(slug, body.yaml_content)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProgramManifestSaveResponse(slug=slug, message="Manifest saved and validated")


@router.post("/{slug}/seed-journeys", response_model=ProgramSeedJourneysResponse)
def seed_program_journeys(
    slug: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProgramSeedJourneysResponse:
    try:
        upserted, journeys_retired, tests_retired = seed_journeys_from_manifest(db, slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProgramSeedJourneysResponse(
        slug=slug,
        journeys_upserted=upserted,
        journeys_retired=journeys_retired,
        tests_retired=tests_retired,
    )


@router.post("/seed-journeys/all")
def seed_all_journeys(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    return seed_all_program_journeys(db)


@router.get("/{slug}/reqiq-onboarding", response_model=ReqIQOnboardingResponse)
def get_reqiq_onboarding(
    slug: str,
    _: User = Depends(require_factory_operator),
) -> ReqIQOnboardingResponse:
    try:
        data = build_reqiq_onboarding(slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ReqIQOnboardingResponse(
        program_slug=data["program_slug"],
        reqiq_project_id=data.get("reqiq_project_id"),
        items=[ReqIQOnboardingItem.model_validate(i) for i in data["items"]],
        steps=data["steps"],
    )


@router.get("/{slug}/orchestration-suites")
def list_orchestration_suites(
    slug: str,
    _: User = Depends(get_current_active_user),
) -> dict:
    try:
        manifest = load_program_manifest(slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "program_slug": slug,
        "suites": list(manifest.get("orchestration_suites") or []),
    }
