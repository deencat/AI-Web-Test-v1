"""
ReqIQ proxy endpoints -- transparent pass-through to ReqIQ (port 3001).

All routes require a valid AI Web Test Bearer token.
The server calls ReqIQ using a service account stored in .env so callers
never need to know ReqIQ exists or what port it runs on.

Phase 1 routes:
  GET  /api/v1/requirements/projects
  GET  /api/v1/requirements/{project_id}/requirements
  POST /api/v1/requirements/{project_id}/query
  POST /api/v1/requirements/{project_id}/sources/upload
  GET  /api/v1/requirements/{project_id}/sources
  POST /api/v1/requirements/{project_id}/requirements/{requirement_id}/suggest-tests
  GET  /api/v1/requirements/{project_id}/requirements/{requirement_id}/latest-iq
  GET  /api/v1/requirements/{project_id}/readiness

s5.2 extensions:
  POST   /api/v1/requirements/projects
  GET    /api/v1/requirements/projects/{id}
  PATCH  /api/v1/requirements/projects/{id}
  POST   /api/v1/requirements/{project_id}/requirements
  GET    /api/v1/requirements/{project_id}/requirements/{req_id}
  PATCH  /api/v1/requirements/{project_id}/requirements/{req_id}
  POST   .../requirements/{req_id}/transition
  GET    .../requirements/{req_id}/audit
  GET    .../requirements/{req_id}/revisions
  GET    .../requirements/{req_id}/revisions/{index}
  POST   .../requirements/{req_id}/revisions/{index}/stub-iq
  POST   .../requirements/{req_id}/revisions/{index}/llm-iq
  GET    .../requirements/{req_id}/suggested-tests
  POST   .../requirements/{req_id}/suggested-tests/import
"""
import logging
from typing import Any

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
import app.services.reqiq_client as reqiq

logger = logging.getLogger(__name__)
router = APIRouter()


def _reqiq_unavailable() -> None:
    from app.core.config import settings
    if not settings.REQIQ_SERVICE_EMAIL or not settings.REQIQ_SERVICE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ReqIQ integration is not configured on this server.",
        )


async def _proxy(coro: Any) -> Any:
    try:
        return await coro
    except Exception as exc:
        # Include ReqIQ response body in the error detail when available
        body: Any = None
        if hasattr(exc, "response") and exc.response is not None:  # type: ignore[union-attr]
            try:
                body = exc.response.json()  # type: ignore[union-attr]
            except Exception:
                body = exc.response.text  # type: ignore[union-attr]
        detail = body if body else str(exc)
        logger.error("ReqIQ proxy error: %s | body: %s", exc, body)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )


# ---------------------------------------------------------------------------
# 1. List projects
# ---------------------------------------------------------------------------

@router.get("/projects", summary="List ReqIQ projects")
async def list_projects(
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.list_projects())


# ---------------------------------------------------------------------------
# 2. List requirements
# ---------------------------------------------------------------------------

@router.get("/{project_id}/requirements", summary="List requirements for a project")
async def list_requirements(
    project_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.list_requirements(project_id))


# ---------------------------------------------------------------------------
# 3. RAG query
# ---------------------------------------------------------------------------

class RagQueryRequest(BaseModel):
    query: str
    limit: int = 8


@router.post("/{project_id}/query", summary="RAG query over project source documents")
async def rag_query(
    project_id: str,
    body: RagQueryRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    result = await _proxy(reqiq.rag_query(project_id, body.query, body.limit))
    if isinstance(result, dict) and result.get("_status") == 429:
        return JSONResponse(
            status_code=429,
            content={"detail": "ReqIQ rate limit exceeded -- try again later"},
            headers={"Retry-After": str(result.get("_retry_after", "60"))},
        )
    return result


# ---------------------------------------------------------------------------
# 4. Upload source documents
# ---------------------------------------------------------------------------

@router.post("/{project_id}/sources/upload", summary="Upload source documents to ReqIQ")
async def upload_sources(
    project_id: str,
    files: list[UploadFile] = File(...),
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    files_payload = []
    for upload in files:
        content = await upload.read()
        files_payload.append(
            ("file", (upload.filename, content, upload.content_type or "application/octet-stream"))
        )
    result = await _proxy(reqiq.upload_sources(project_id, files_payload))

    # Automatically kick off embedding reindex in the background so RAG and
    # readiness queries use the new documents without the user having to
    # visit ReqIQ advanced manually.
    async def _reindex() -> None:
        try:
            await reqiq.reindex_embeddings(project_id)
            logger.info("ReqIQ reindex triggered for project %s", project_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ReqIQ reindex failed (non-fatal): %s", exc)

    asyncio.create_task(_reindex())

    return result


# ---------------------------------------------------------------------------
# 5. List source documents
# ---------------------------------------------------------------------------

@router.get("/{project_id}/sources", summary="List source documents for a project")
async def list_sources(
    project_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.list_sources(project_id))


@router.delete("/{project_id}/sources/{source_id}", status_code=204, summary="Delete a source document")
async def delete_source(
    project_id: str,
    source_id: str,
    _: User = Depends(get_current_user),
) -> None:
    _reqiq_unavailable()
    await _proxy(reqiq.delete_source(project_id, source_id))


# ---------------------------------------------------------------------------
# 6. Generate suggested tests
# ---------------------------------------------------------------------------

class SuggestTestsRequest(BaseModel):
    maxTests: int = 3
    hints: str = ""


@router.post(
    "/{project_id}/requirements/{requirement_id}/suggest-tests",
    summary="Generate suggested tests from a requirement",
)
async def suggest_tests(
    project_id: str,
    requirement_id: str,
    body: SuggestTestsRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(
        reqiq.suggest_tests(project_id, requirement_id, body.maxTests, body.hints)
    )


# ---------------------------------------------------------------------------
# 7. Latest IQ score
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}/requirements/{requirement_id}/latest-iq",
    summary="Get latest IQ score for a requirement",
)
async def get_latest_iq(
    project_id: str,
    requirement_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_latest_iq(project_id, requirement_id))


# ---------------------------------------------------------------------------
# 8. Project readiness
# ---------------------------------------------------------------------------

@router.get("/{project_id}/readiness", summary="Project readiness check")
async def get_readiness(
    project_id: str,
    query: str = Query(default=""),
    feature: str = Query(default=""),
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_readiness(project_id, query, feature))


# ---------------------------------------------------------------------------
# §5.2 — Workspace CRUD
# ---------------------------------------------------------------------------

class CreateProjectRequest(BaseModel):
    name: str


class UpdateProjectRequest(BaseModel):
    name: str


@router.post("/projects", summary="Create a workspace")
async def create_project(
    body: CreateProjectRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.create_project(body.name))


@router.get("/projects/{project_id}", summary="Get a workspace")
async def get_project(
    project_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_project(project_id))


@router.patch("/projects/{project_id}", summary="Rename a workspace")
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.update_project(project_id, body.name))


# ---------------------------------------------------------------------------
# §5.2 — Requirement CRUD
# ---------------------------------------------------------------------------

class CreateRequirementRequest(BaseModel):
    title: str
    body: str = ""


class UpdateRequirementRequest(BaseModel):
    title: str | None = None
    body: str | None = None


class TransitionRequest(BaseModel):
    state: str


@router.post("/{project_id}/requirements", summary="Create a requirement")
async def create_requirement(
    project_id: str,
    body: CreateRequirementRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.create_requirement(project_id, body.title, body.body))


@router.get("/{project_id}/requirements/{requirement_id}", summary="Get a requirement")
async def get_requirement(
    project_id: str,
    requirement_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_requirement(project_id, requirement_id))


@router.patch("/{project_id}/requirements/{requirement_id}", summary="Update a requirement")
async def update_requirement(
    project_id: str,
    requirement_id: str,
    body: UpdateRequirementRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return await _proxy(reqiq.update_requirement(project_id, requirement_id, **fields))


@router.post(
    "/{project_id}/requirements/{requirement_id}/transition",
    summary="Transition requirement lifecycle state",
)
async def transition_requirement(
    project_id: str,
    requirement_id: str,
    body: TransitionRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.transition_requirement(project_id, requirement_id, body.state))


@router.get(
    "/{project_id}/requirements/{requirement_id}/audit",
    summary="Get requirement audit trail",
)
async def get_requirement_audit(
    project_id: str,
    requirement_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_requirement_audit(project_id, requirement_id))


# ---------------------------------------------------------------------------
# §5.2 — Revisions + IQ
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}/requirements/{requirement_id}/revisions",
    summary="List revisions for a requirement",
)
async def list_revisions(
    project_id: str,
    requirement_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.list_revisions(project_id, requirement_id))


@router.get(
    "/{project_id}/requirements/{requirement_id}/revisions/{revision_index}",
    summary="Get a specific revision",
)
async def get_revision(
    project_id: str,
    requirement_id: str,
    revision_index: int,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_revision(project_id, requirement_id, revision_index))


@router.post(
    "/{project_id}/requirements/{requirement_id}/revisions/{revision_index}/stub-iq",
    summary="Run stub IQ (no LLM) on a revision",
)
async def run_stub_iq(
    project_id: str,
    requirement_id: str,
    revision_index: int,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.run_stub_iq(project_id, requirement_id, revision_index))


@router.post(
    "/{project_id}/requirements/{requirement_id}/revisions/{revision_index}/llm-iq",
    summary="Run LLM IQ on a revision",
)
async def run_llm_iq(
    project_id: str,
    requirement_id: str,
    revision_index: int,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.run_llm_iq(project_id, requirement_id, revision_index))


# ---------------------------------------------------------------------------
# §5.2 — Suggested tests CRUD + import
# ---------------------------------------------------------------------------

class ImportSuggestedTestsRequest(BaseModel):
    tests: list


@router.get(
    "/{project_id}/requirements/{requirement_id}/suggested-tests",
    summary="List suggested tests for a requirement",
)
async def list_suggested_tests(
    project_id: str,
    requirement_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.list_suggested_tests(project_id, requirement_id))


@router.post(
    "/{project_id}/requirements/{requirement_id}/suggested-tests/import",
    summary="Import suggested tests without LLM",
)
async def import_suggested_tests(
    project_id: str,
    requirement_id: str,
    body: ImportSuggestedTestsRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.import_suggested_tests(project_id, requirement_id, body.tests))


class CreateSuggestedTestRequest(BaseModel):
    title: str
    payload: dict | None = None


class UpdateSuggestedTestRequest(BaseModel):
    title: str | None = None
    payload: dict | None = None


@router.post(
    "/{project_id}/requirements/{requirement_id}/suggested-tests",
    summary="Create a single suggested test",
)
async def create_suggested_test(
    project_id: str,
    requirement_id: str,
    body: CreateSuggestedTestRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return await _proxy(reqiq.create_suggested_test(project_id, requirement_id, **fields))


@router.get(
    "/{project_id}/requirements/{requirement_id}/suggested-tests/{suggested_test_id}",
    summary="Get a single suggested test",
)
async def get_suggested_test(
    project_id: str,
    requirement_id: str,
    suggested_test_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    return await _proxy(reqiq.get_suggested_test(project_id, requirement_id, suggested_test_id))


@router.patch(
    "/{project_id}/requirements/{requirement_id}/suggested-tests/{suggested_test_id}",
    summary="Update a suggested test",
)
async def update_suggested_test(
    project_id: str,
    requirement_id: str,
    suggested_test_id: str,
    body: UpdateSuggestedTestRequest,
    _: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    return await _proxy(reqiq.update_suggested_test(project_id, requirement_id, suggested_test_id, **fields))


@router.delete(
    "/{project_id}/requirements/{requirement_id}/suggested-tests/{suggested_test_id}",
    summary="Delete a suggested test",
    status_code=204,
)
async def delete_suggested_test(
    project_id: str,
    requirement_id: str,
    suggested_test_id: str,
    _: User = Depends(get_current_user),
) -> None:
    _reqiq_unavailable()
    await _proxy(reqiq.delete_suggested_test(project_id, requirement_id, suggested_test_id))
