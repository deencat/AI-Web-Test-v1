"""Product workspace API — business-friendly upload → wiki → tests (UF)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import app.services.reqiq_client as reqiq
from app.api.deps import get_current_active_user, get_db, require_role, _ROLE_RANK
from app.api.v1.endpoints.requirements import _proxy, _reqiq_unavailable
from app.models.user import User
from app.schemas.product_workspace import (
    AllowedFormatsResponse,
    ProductDetailResponse,
    ProductGenerateTestsResponse,
    ProductListResponse,
    ProductStatusResponse,
    ProductSummary,
    ProductSyncResponse,
    ProductWorkspaceStatus,
)
from app.services.document_ingest import (
    ALLOWED_SOURCE_EXTENSIONS,
    SOURCE_TYPE_HINTS,
    infer_source_type,
    validate_filename,
)
from app.services.product_workspace_service import (
    ProductWorkspaceError,
    get_product,
    list_products,
    product_summary,
)
from app.services.program_sync_agent import sync_program_from_wiki
from app.services.wiki_compile_profile import WikiProfileError, get_compile_feature

logger = logging.getLogger(__name__)
router = APIRouter()
require_admin = require_role(_ROLE_RANK["admin"], "admin")


def _to_detail(product: dict[str, Any]) -> ProductDetailResponse:
    return ProductDetailResponse(
        id=product["id"],
        title=product.get("title") or product["id"],
        title_zh=product.get("title_zh"),
        locale=product.get("locale"),
        pilot=bool(product.get("pilot")),
        program_slug=product.get("program_slug"),
        wiki_profile=product.get("wiki_profile"),
        default_urls=dict(product.get("default_urls") or {}),
        reqiq_project_id=product["reqiq_project_id"],
    )


@router.get("/formats", response_model=AllowedFormatsResponse)
def allowed_formats(_: User = Depends(get_current_active_user)) -> AllowedFormatsResponse:
    return AllowedFormatsResponse(
        extensions=sorted(ALLOWED_SOURCE_EXTENSIONS),
        source_type_hints=SOURCE_TYPE_HINTS,
    )


@router.get("", response_model=ProductListResponse)
def list_product_workspaces(_: User = Depends(get_current_active_user)) -> ProductListResponse:
    items = [ProductSummary.model_validate(product_summary(p)) for p in list_products()]
    return ProductListResponse(items=items, total=len(items))


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    product_id: str,
    _: User = Depends(get_current_active_user),
) -> ProductDetailResponse:
    try:
        return _to_detail(get_product(product_id))
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{product_id}/status", response_model=ProductStatusResponse)
async def get_product_status(
    product_id: str,
    _: User = Depends(get_current_active_user),
) -> ProductStatusResponse:
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    pid = product["reqiq_project_id"]
    ws = ProductWorkspaceStatus()

    try:
        sources = await _proxy(reqiq.list_sources(pid))
        if isinstance(sources, list):
            ws.source_count = len(sources)
        else:
            items = sources.get("items") or sources.get("sources") or []
            ws.source_count = len(items) if isinstance(items, list) else int(sources.get("total", 0))
    except Exception:
        ws.source_count = 0

    try:
        wiki = await _proxy(reqiq.get_wiki(pid))
        ws.wiki_ready = bool(wiki.get("markdown") or wiki.get("content"))
        ws.wiki_stale = bool(wiki.get("wikiStale"))
        ws.wiki_compiled_at = wiki.get("compiledAt") or wiki.get("wikiCompiledAt")
    except Exception:
        pass

    try:
        reqs = await _proxy(reqiq.list_requirements(pid))
        items = reqs if isinstance(reqs, list) else (reqs.get("items") or reqs.get("requirements") or [])
        if isinstance(items, list):
            ws.requirement_count = len(items)
            ws.draft_requirement_count = sum(1 for r in items if r.get("state") == "DRAFT")
    except Exception:
        pass

    try:
        readiness = await _proxy(reqiq.get_readiness(pid))
        ws.readiness_score = readiness.get("compositeScore") or readiness.get("score")
    except Exception:
        pass

    return ProductStatusResponse(product=_to_detail(product), status=ws)


@router.post("/{product_id}/upload")
async def upload_product_documents(
    product_id: str,
    files: list[UploadFile] = File(...),
    _: User = Depends(get_current_active_user),
) -> Any:
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    files_payload = []
    ingested_types: list[str] = []
    for upload in files:
        try:
            validate_filename(upload.filename or "")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        content = await upload.read()
        hint = infer_source_type(upload.filename or "")
        if hint:
            ingested_types.append(hint)
        files_payload.append(
            ("file", (upload.filename, content, upload.content_type or "application/octet-stream"))
        )

    result = await _proxy(reqiq.upload_sources(product["reqiq_project_id"], files_payload))

    async def _reindex() -> None:
        try:
            await reqiq.reindex_embeddings(product["reqiq_project_id"])
        except Exception as exc:
            logger.warning("Reindex after product upload failed: %s", exc)

    asyncio.create_task(_reindex())
    if isinstance(result, dict):
        result["ingested_source_types"] = list(set(ingested_types))
    return result


@router.post("/{product_id}/compile-wiki")
async def compile_product_wiki(
    product_id: str,
    _: User = Depends(get_current_active_user),
) -> Any:
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    profile = product.get("wiki_profile") or "telecom-promo"
    try:
        feature = get_compile_feature(profile)
    except WikiProfileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return await _proxy(reqiq.compile_wiki(product["reqiq_project_id"], feature))


@router.post("/{product_id}/generate-tests", response_model=ProductGenerateTestsResponse)
async def generate_tests_from_wiki(
    product_id: str,
    _: User = Depends(get_current_active_user),
) -> ProductGenerateTestsResponse:
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    result = await _proxy(
        reqiq.suggest_from_wiki(product["reqiq_project_id"], maxScenarios=10)
    )
    return ProductGenerateTestsResponse(
        created=int(result.get("created") or result.get("createdCount") or 0),
        dedupe_dropped=int(result.get("dedupeDropped") or 0),
        batch_id=result.get("batchId"),
        message="Test scenarios generated — review in Tests section",
    )


@router.post("/{product_id}/sync-program", response_model=ProductSyncResponse)
async def sync_product_program(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProductSyncResponse:
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    wiki = await _proxy(reqiq.get_wiki(product["reqiq_project_id"]))
    markdown = wiki.get("markdown") or wiki.get("content") or ""
    if not markdown.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wiki not compiled — upload documents and compile wiki first",
        )

    try:
        data = sync_program_from_wiki(db, product_id=product_id, wiki_markdown=markdown)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ProductSyncResponse(**data)


@router.post("/{product_id}/run-overnight")
async def run_overnight_regression(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Enqueue factory regression for product journeys (UF-4/5)."""
    from app.crud import journey_factory as crud_journey
    from app.schemas.factory_job import FactoryJobCreate
    from app.services.factory_job_service import create_factory_job
    from app.services.factory_scheduler_service import submit_factory_job_async

    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    program_slug = product.get("program_slug")
    project = "Three-HK"
    entries = crud_journey.list_registry_entries(db, project=project, limit=500)
    slugs = [
        e.slug
        for e in entries
        if (e.extra_config or {}).get("program_slug") == program_slug
        and not (e.extra_config or {}).get("retired")
    ]
    if not slugs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active journeys for this product — sync program from wiki first",
        )

    job = create_factory_job(
        db,
        FactoryJobCreate(job_type="run_regression", project=project, params={"journey_slugs": slugs}),
        created_by_user_id=current_user.id,
    )
    submit_factory_job_async(job.id)
    return {"job_id": job.id, "status": job.status, "journey_count": len(slugs)}
