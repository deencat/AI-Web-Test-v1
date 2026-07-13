"""Product workspace API — business-friendly upload → wiki → tests (UF)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import app.services.reqiq_client as reqiq
from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints.requirements import _proxy, _reqiq_unavailable
from app.models.user import User
from app.schemas.product_workspace import (
    AllowedFormatsResponse,
    ProductCompileWikiResponse,
    ProductCreateRequest,
    ProductCreateResponse,
    ProductDetailResponse,
    ProductGenerateTestsResponse,
    ProductListResponse,
    ProductStatusResponse,
    ProductSummary,
    ProductSyncResponse,
    ProductUpdateRequest,
    ProductWorkspaceStatus,
)
from app.services.document_ingest import (
    ALLOWED_SOURCE_EXTENSIONS,
    SOURCE_TYPE_HINTS,
    infer_source_type,
    validate_filename,
)
from app.services.journey_test_hints import build_suggest_from_wiki_payload
from app.services.product_document_store import save_upload
from app.services.program_sync_agent import sync_program_from_wiki
from app.services.program_registry_service import ProgramManifestError, create_program_manifest
from app.services.product_workspace_service import (
    ProductWorkspaceError,
    create_product_entry,
    get_product,
    list_products,
    product_summary,
    slug_from_title,
    update_product_entry,
)
from app.services.wiki_compile_profile import WikiProfileError, get_compile_feature
from app.services.wiki_journey_merge import merge_purchase_journeys
from app.services.ux_flow_extractor import build_compile_feature_supplement, extract_journeys_for_product

logger = logging.getLogger(__name__)
router = APIRouter()


async def _auto_sync_from_wiki(db: Session, product_id: str) -> Optional[ProductSyncResponse]:
    """Keep automation in sync with wiki — no separate user step."""
    try:
        product = get_product(product_id)
    except ProductWorkspaceError:
        return None
    if not product.get("program_slug"):
        return None
    try:
        wiki = await _proxy(reqiq.get_wiki(product["reqiq_project_id"]))
    except Exception:
        return None
    markdown = wiki.get("markdown") or wiki.get("content") or ""
    if not markdown.strip():
        return None
    try:
        data = sync_program_from_wiki(db, product_id=product_id, wiki_markdown=markdown)
        return ProductSyncResponse(**data)
    except ProductWorkspaceError as exc:
        logger.warning("Auto-sync skipped for %s: %s", product_id, exc)
        return None


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


@router.post("", response_model=ProductCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_product_workspace(
    body: ProductCreateRequest,
    _: User = Depends(get_current_active_user),
) -> ProductCreateResponse:
    """Create product: ReqIQ workspace + config + program shell — one step for any user."""
    _reqiq_unavailable()
    product_id = body.id or slug_from_title(body.title)
    try:
        existing = get_product(product_id)
        title = existing.get("title") or product_id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product already exists: {product_id} (listed as "{title}")',
        )
    except ProductWorkspaceError:
        pass

    try:
        reqiq_project = await _proxy(reqiq.create_project(body.title))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    project_id = reqiq_project.get("id")
    if not project_id:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ReqIQ did not return a project id")

    try:
        entry = create_product_entry(
            product_id=product_id,
            title=body.title,
            title_zh=body.title_zh,
            reqiq_project_id=project_id,
            webapp_url=body.webapp_url,
        )
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        create_program_manifest(
            slug=product_id,
            title=body.title,
            kind="pilot",
            platform_profile="dt-telecom-default",
            initiative_title=f"{body.title} — base offer",
        )
    except ProgramManifestError as exc:
        if "already exists" not in str(exc).lower():
            logger.warning("Program manifest for %s: %s", product_id, exc)

    return ProductCreateResponse(
        product=_to_detail(entry),
        message="Product created. Upload marketing, SSCO, SMCD, and T&C documents whenever they are ready.",
    )


@router.patch("/{product_id}", response_model=ProductDetailResponse)
def update_product_workspace(
    product_id: str,
    body: ProductUpdateRequest,
    _: User = Depends(get_current_active_user),
) -> ProductDetailResponse:
    try:
        updated = update_product_entry(
            product_id,
            title=body.title,
            title_zh=body.title_zh,
            webapp_url=body.webapp_url,
        )
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_detail(updated)


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
        save_upload(
            product_id,
            upload.filename or "upload",
            content,
            source_type=hint,
        )
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


@router.post("/{product_id}/compile-wiki", response_model=ProductCompileWikiResponse)
async def compile_product_wiki(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ProductCompileWikiResponse:
    """Compile wiki from all documents, then auto-sync offers and test automation."""
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

    extraction = await extract_journeys_for_product(product_id)
    compile_feature = feature
    supplement = build_compile_feature_supplement(extraction.journeys_markdown)
    if supplement:
        compile_feature = supplement + compile_feature

    wiki = await _proxy(reqiq.compile_wiki(product["reqiq_project_id"], compile_feature))

    wiki_md = ""
    if isinstance(wiki, dict):
        wiki_md = str(wiki.get("markdown") or wiki.get("content") or "")

    if extraction.journeys_markdown:
        merged = merge_purchase_journeys(wiki_md, extraction.journeys_markdown)
        if merged != wiki_md:
            patch_resp = await reqiq.patch_wiki(product["reqiq_project_id"], merged)
            if patch_resp.is_success:
                wiki_md = merged
                if isinstance(wiki, dict):
                    wiki["markdown"] = merged
                    wiki["content"] = merged
            else:
                logger.warning(
                    "Wiki journey merge patch failed for %s: %s",
                    product_id,
                    patch_resp.status_code,
                )

    sync = await _auto_sync_from_wiki(db, product_id)
    msg = "Summary updated from your documents."
    if extraction.images_processed:
        msg += f" {extraction.images_processed} UX/UI flow image(s) analysed."
        if extraction.journey_names:
            msg += f" Journeys: {', '.join(extraction.journey_names[:5])}."
    if sync and sync.tests_retired:
        msg += f" Ended {sync.tests_retired} outdated test(s) from previous offers."
    return ProductCompileWikiResponse(
        wiki=wiki if isinstance(wiki, dict) else {},
        sync=sync,
        message=msg,
        journeys_extracted=len(extraction.journey_names),
        ux_sources_processed=extraction.images_processed,
        vision_used=extraction.vision_used,
    )


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

    wiki_md = ""
    journey_guided = False
    try:
        wiki = await _proxy(reqiq.get_wiki(product["reqiq_project_id"]))
        wiki_md = str(wiki.get("markdown") or wiki.get("content") or "")
        journey_guided = "## Purchase journeys" in wiki_md
    except Exception:
        logger.warning("Could not load wiki for journey-guided test generation: %s", product_id)

    webapp_url = str((product.get("default_urls") or {}).get("webapp") or "")
    payload = build_suggest_from_wiki_payload(wiki_md, webapp_url=webapp_url, max_scenarios=10)
    result = await _proxy(reqiq.suggest_from_wiki(product["reqiq_project_id"], **payload))
    msg = "Test scenarios created from your summary"
    if journey_guided:
        msg += " (guided by Purchase journeys steps)"
    return ProductGenerateTestsResponse(
        created=int(result.get("created") or result.get("createdCount") or 0),
        dedupe_dropped=int(result.get("dedupeDropped") or 0),
        batch_id=result.get("batchId"),
        message=msg,
        journey_guided=journey_guided,
    )


@router.post("/{product_id}/sync-program", response_model=ProductSyncResponse)
async def sync_product_program(
    product_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ProductSyncResponse:
    """Re-apply wiki → automation (usually automatic after Update summary)."""
    _reqiq_unavailable()
    sync = await _auto_sync_from_wiki(db, product_id)
    if not sync:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wiki summary yet — upload documents and click Update summary",
        )
    return sync


@router.post("/{product_id}/run-overnight")
async def run_overnight_regression(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Queue automated test runs; syncs from wiki first if needed."""
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
        await _auto_sync_from_wiki(db, product_id)
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
            detail="Upload documents and click Update summary first, then Create tests",
        )

    job = create_factory_job(
        db,
        FactoryJobCreate(job_type="run_regression", project=project, params={"journey_slugs": slugs}),
        created_by_user_id=current_user.id,
    )
    submit_factory_job_async(job.id)
    return {"job_id": job.id, "status": job.status, "journey_count": len(slugs)}
