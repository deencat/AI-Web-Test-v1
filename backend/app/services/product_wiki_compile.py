"""Product wiki compile with progress reporting."""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

import app.services.reqiq_client as reqiq
from app.api.v1.endpoints.requirements import _proxy
from app.services.compile_progress import ProgressCallback
from app.schemas.product_workspace import ProductSyncResponse
from app.services.product_workspace_service import ProductWorkspaceError, get_product
from app.services.program_sync_agent import sync_program_from_wiki
from app.services.user_settings_service import user_settings_service
from app.services.product_document_store import list_mvp_config_paths, list_ux_ui_image_paths
from app.services.ux_flow_extractor import extract_journeys_for_product
from app.services.wiki_assembly import merge_reqiq_with_journeys
from app.services.wiki_compile_profile import WikiProfileError, get_compile_feature

logger = logging.getLogger(__name__)


async def _auto_sync_from_wiki(db: Session, product_id: str) -> Optional[ProductSyncResponse]:
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


async def compile_product_wiki_with_progress(
    product_id: str,
    db: Session,
    user_id: int,
    *,
    report: Optional[ProgressCallback] = None,
) -> dict[str, Any]:
    async def _step(step: str, percent: int, detail: str = "") -> None:
        if report:
            await report(step, percent, detail)

    product = get_product(product_id)
    gen_cfg = user_settings_service.get_provider_config(db, user_id, "generation")
    vision_provider = str(gen_cfg.get("provider") or "")
    vision_model = str(gen_cfg.get("model") or "")

    profile = product.get("wiki_profile") or "telecom-promo"
    try:
        feature = get_compile_feature(profile)
    except WikiProfileError:
        raise

    await _step("Indexing documents", 8, "Refreshing ReqIQ search index…")
    try:
        await reqiq.reindex_embeddings(product["reqiq_project_id"])
    except Exception as exc:
        logger.warning("Reindex before compile failed for %s: %s", product_id, exc)

    await _step("Analysing UX/UI flows", 12, "Running vision on flow images (this may take several minutes)…")
    extraction = await extract_journeys_for_product(
        product_id,
        vision_provider=vision_provider,
        vision_model=vision_model,
        progress=report,
        progress_base=12,
        progress_span=58,
    )
    has_ux_images = bool(list_ux_ui_image_paths(product_id))
    has_offer_docs = bool(list_mvp_config_paths(product_id))

    wiki: dict[str, Any] = {}
    wiki_md = ""
    reqiq_md = ""

    if has_ux_images:
        if has_offer_docs:
            await _step("Compiling offer sections", 68, "Extracting base offer and promos from documents…")
            try:
                # Journeys come from vision below — never embed them in the compile URL (431 limit).
                wiki = await _proxy(reqiq.compile_wiki(product["reqiq_project_id"], feature))
                if isinstance(wiki, dict):
                    reqiq_md = str(wiki.get("markdown") or wiki.get("content") or "")
            except Exception as exc:
                logger.warning(
                    "ReqIQ offer compile failed for %s (continuing with vision journeys): %s",
                    product_id,
                    exc,
                )

        await _step("Building summary", 72, "Assembling Purchase journeys wiki…")
        wiki_md = merge_reqiq_with_journeys(
            reqiq_md,
            extraction.journeys_markdown,
            product_title=str(product.get("title") or ""),
            product_id=product_id,
        )
    else:
        await _step("Compiling summary", 72, "ReqIQ is compiling offer and promo sections…")
        wiki = await _proxy(reqiq.compile_wiki(product["reqiq_project_id"], feature))
        if isinstance(wiki, dict):
            wiki_md = str(wiki.get("markdown") or wiki.get("content") or "")
        wiki_md = merge_reqiq_with_journeys(
            wiki_md,
            extraction.journeys_markdown,
            product_title=str(product.get("title") or ""),
            product_id=product_id,
        )

    await _step("Saving summary", 88, "Writing wiki to ReqIQ…")
    if wiki_md:
        patch_resp = await reqiq.patch_wiki(product["reqiq_project_id"], wiki_md)
        if patch_resp.is_success:
            wiki = {"markdown": wiki_md, "content": wiki_md}
        else:
            logger.warning("Wiki patch failed for %s: %s", product_id, patch_resp.status_code)

    await _step("Syncing automation", 94, "Updating program journeys and tests…")
    sync = await _auto_sync_from_wiki(db, product_id)

    msg = "Summary updated from your documents."
    if extraction.images_processed:
        msg += f" {extraction.images_processed} UX/UI flow image(s) analysed."
        if extraction.vision_used:
            msg += " Vision model used for Purchase journeys."
        elif not extraction.journey_names:
            msg += " (Vision did not run — check Settings → generation model supports images.)"
        if extraction.journey_names:
            msg += f" Journeys: {', '.join(extraction.journey_names[:5])}."
    if sync and sync.tests_retired:
        msg += f" Ended {sync.tests_retired} outdated test(s) from previous offers."

    return {
        "wiki": wiki if isinstance(wiki, dict) else {},
        "sync": sync.model_dump() if sync else None,
        "message": msg,
        "journeys_extracted": len(extraction.journey_names),
        "ux_sources_processed": extraction.images_processed,
        "vision_used": extraction.vision_used,
    }
