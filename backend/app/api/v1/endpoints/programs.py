"""Product program manifests API (PG-1 … PG-5)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_factory_operator, require_role, _ROLE_RANK
from app.models.user import User
from app.schemas.program_registry import (
    ProgramDetailResponse,
    ProgramListResponse,
    ProgramManifestRawResponse,
    ProgramManifestSaveRequest,
    ProgramManifestSaveResponse,
    ProgramSeedJourneysResponse,
    ProgramSummary,
    ReqIQOnboardingResponse,
    ReqIQOnboardingItem,
)
from app.services.program_journey_seed import seed_all_program_journeys, seed_journeys_from_manifest
from app.crud import journey_factory as crud_journey
from app.services.program_registry_service import (
    ProgramManifestError,
    build_reqiq_onboarding,
    get_program_detail,
    list_program_summaries,
    load_program_manifest,
    load_program_manifest_raw,
    save_program_manifest_yaml,
)

router = APIRouter()
require_admin = require_role(_ROLE_RANK["admin"], "admin")


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
        upserted, retired = seed_journeys_from_manifest(db, slug)
    except ProgramManifestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProgramSeedJourneysResponse(
        slug=slug,
        journeys_upserted=upserted,
        journeys_retired=retired,
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
