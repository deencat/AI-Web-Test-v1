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
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.product_workspace import (
    AllowedFormatsResponse,
    ProductCompileWikiProgressResponse,
    ProductCompileWikiResponse,
    ProductCompileWikiStartResponse,
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
from app.services.offer_table_convert import (
    convert_offer_spreadsheet_to_markdown,
    is_offer_spreadsheet,
    reqiq_markdown_filename,
)
from app.services.journey_test_hints import build_suggest_from_wiki_payload
from app.services.compile_progress import CompileProgressStore
from app.services.product_document_store import remove_upload_for_reqiq_source, save_upload
from app.services.product_wiki_compile import compile_product_wiki_with_progress
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

logger = logging.getLogger(__name__)
router = APIRouter()


def _progress_to_response(state) -> ProductCompileWikiProgressResponse:
    result = None
    if state.result:
        result = ProductCompileWikiResponse(**state.result)
    return ProductCompileWikiProgressResponse(
        status=state.status,
        step=state.step,
        percent=state.percent,
        detail=state.detail,
        started_at=state.started_at,
        updated_at=state.updated_at,
        result=result,
        error=state.error,
    )


async def _run_compile_background(product_id: str, user_id: int) -> None:
    db = SessionLocal()
    try:
        result = await compile_product_wiki_with_progress(
            product_id,
            db,
            user_id,
            report=CompileProgressStore.reporter(product_id),
        )
        await CompileProgressStore.complete(product_id, result)
    except ProductWorkspaceError as exc:
        await CompileProgressStore.fail(product_id, str(exc))
    except WikiProfileError as exc:
        await CompileProgressStore.fail(product_id, str(exc))
    except Exception as exc:
        logger.exception("Compile wiki failed for %s", product_id)
        await CompileProgressStore.fail(product_id, str(exc))
    finally:
        db.close()


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
        ws.wiki_compile_status = wiki.get("compileStatus")
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
    locally_cached: list[str] = []
    converted_offer_tables: list[str] = []

    for upload in files:
        try:
            validate_filename(upload.filename or "")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        content = await upload.read()
        original_name = upload.filename or "upload"
        hint = infer_source_type(original_name)
        if hint:
            ingested_types.append(hint)
        save_upload(
            product_id,
            original_name,
            content,
            source_type=hint,
        )
        locally_cached.append(original_name)

        if is_offer_spreadsheet(original_name):
            try:
                md_text = convert_offer_spreadsheet_to_markdown(content, original_name)
                md_name = reqiq_markdown_filename(original_name)
                files_payload.append(
                    ("file", (md_name, md_text.encode("utf-8"), "text/markdown")),
                )
                converted_offer_tables.append(original_name)
            except Exception as exc:
                logger.warning("Offer table convert failed for %s: %s", original_name, exc)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not read offer table '{original_name}': {exc}",
                ) from exc
        else:
            files_payload.append(
                ("file", (original_name, content, upload.content_type or "application/octet-stream"))
            )

    result: dict[str, Any] = {
        "uploadedCount": 0,
        "rejectedCount": 0,
        "uploaded": [],
        "rejected": [],
        "locally_cached": locally_cached,
        "converted_offer_tables": converted_offer_tables,
    }

    if files_payload:
        try:
            result = await _proxy(reqiq.upload_sources(product["reqiq_project_id"], files_payload))
            if not isinstance(result, dict):
                result = {"uploaded": result}
        except HTTPException as exc:
            # Originals are cached locally; surface ReqIQ errors clearly.
            detail = exc.detail
            if locally_cached and converted_offer_tables:
                raise HTTPException(
                    status_code=exc.status_code,
                    detail={
                        "message": (
                            f"Offer table saved locally ({', '.join(locally_cached)}) but "
                            "ReqIQ indexing failed for the converted markdown."
                        ),
                        "reqiq_error": detail,
                        "locally_cached": locally_cached,
                        "converted_offer_tables": converted_offer_tables,
                    },
                ) from exc
            raise

    indexed = False
    try:
        await reqiq.reindex_embeddings(product["reqiq_project_id"])
        indexed = True
    except Exception as exc:
        logger.warning("Reindex after product upload failed: %s", exc)

    if isinstance(result, dict):
        result["ingested_source_types"] = list(set(ingested_types))
        result["embedding_indexed"] = indexed
        result["locally_cached"] = locally_cached
        result["converted_offer_tables"] = converted_offer_tables
        parts: list[str] = []
        uploaded_n = int(result.get("uploadedCount") or len(result.get("uploaded") or []))
        if uploaded_n:
            parts.append(f"{uploaded_n} file(s) indexed in ReqIQ.")
        if converted_offer_tables:
            parts.append(
                "Offer table(s) converted to markdown for ReqIQ: "
                + ", ".join(converted_offer_tables)
                + "."
            )
        elif locally_cached:
            parts.append(f"Cached locally: {', '.join(locally_cached)}.")
        if indexed:
            parts.append("Search index updated — click Update summary when ready.")
        result["message"] = " ".join(parts) if parts else "Upload complete."
    return result


@router.delete("/{product_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_source(
    product_id: str,
    source_id: str,
    _: User = Depends(get_current_active_user),
) -> None:
    """Delete from ReqIQ and remove matching local vision/MVP cache (used on Update summary)."""
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    pid = product["reqiq_project_id"]
    source_filename = ""
    try:
        sources = await _proxy(reqiq.list_sources(pid))
        items = sources if isinstance(sources, list) else (sources.get("items") or sources.get("sources") or [])
        for item in items:
            if str(item.get("id")) == str(source_id):
                source_filename = (
                    item.get("originalFilename")
                    or item.get("filename")
                    or item.get("name")
                    or ""
                )
                break
    except Exception as exc:
        logger.warning("Could not resolve source filename for %s: %s", source_id, exc)

    await _proxy(reqiq.delete_source(pid, source_id))

    if source_filename:
        removed = remove_upload_for_reqiq_source(product_id, source_filename)
        if removed:
            logger.info("Removed local cache for %s / %s", product_id, source_filename)


@router.post("/{product_id}/compile-wiki", response_model=ProductCompileWikiStartResponse)
async def compile_product_wiki(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
) -> ProductCompileWikiStartResponse:
    """Start wiki compile in the background; poll GET …/compile-wiki/progress for status."""
    _reqiq_unavailable()
    try:
        product = get_product(product_id)
    except ProductWorkspaceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    profile = product.get("wiki_profile") or "telecom-promo"
    try:
        get_compile_feature(profile)
    except WikiProfileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    started = await CompileProgressStore.try_start(product_id)
    if not started:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Summary update is already running for this product.",
        )

    asyncio.create_task(_run_compile_background(product_id, current_user.id))
    return ProductCompileWikiStartResponse(
        status="running",
        message="Summary update started. This may take several minutes — progress will appear below.",
    )


@router.get("/{product_id}/compile-wiki/progress", response_model=ProductCompileWikiProgressResponse)
async def compile_product_wiki_progress(
    product_id: str,
    _: User = Depends(get_current_active_user),
) -> ProductCompileWikiProgressResponse:
    """Poll compile progress; when status is done, result contains the final wiki response."""
    state = CompileProgressStore.get(product_id)
    if not state:
        return ProductCompileWikiProgressResponse(status="idle")
    return _progress_to_response(state)


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
    compile_status = ""
    try:
        wiki = await _proxy(reqiq.get_wiki(product["reqiq_project_id"]))
        wiki_md = str(wiki.get("markdown") or wiki.get("content") or "")
        compile_status = str(wiki.get("compileStatus") or "")
        journey_guided = "## Purchase journeys" in wiki_md
    except Exception:
        logger.warning("Could not load wiki for journey-guided test generation: %s", product_id)

    if not wiki_md.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No summary yet. Upload documents and click Update summary first.",
        )

    webapp_url = str((product.get("default_urls") or {}).get("webapp") or "")
    payload = build_suggest_from_wiki_payload(wiki_md, webapp_url=webapp_url, max_scenarios=10)

    # ReqIQ suggest-from-wiki requires compileStatus=ok. After Update summary we PATCH
    # merged markdown (status becomes "edited"). Recompile once here; journey hints above
    # still come from the full summary the user sees.
    if compile_status != "ok":
        profile = product.get("wiki_profile") or "telecom-promo"
        try:
            feature = get_compile_feature(profile)
        except WikiProfileError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info(
            "Recompiling ReqIQ wiki for %s before suggest-from-wiki (was %s)",
            product_id,
            compile_status or "unknown",
        )
        await _proxy(reqiq.compile_wiki(product["reqiq_project_id"], feature))

    try:
        result = await _proxy(reqiq.suggest_from_wiki(product["reqiq_project_id"], **payload))
    except HTTPException as exc:
        detail = exc.detail
        if isinstance(detail, dict) and detail.get("error") == "wiki_not_compiled":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Could not create tests from the summary. "
                    "If you have not run Update summary yet, do that once after uploading documents. "
                    "Otherwise wait a moment and click Create tests again."
                ),
            ) from exc
        raise
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
