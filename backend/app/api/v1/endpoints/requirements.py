"""
ReqIQ proxy endpoints — transparent pass-through to ReqIQ (port 3001).

All routes require a valid AI Web Test Bearer token.
The server calls ReqIQ using a service account stored in .env — callers
never need to know ReqIQ exists or what port it runs on.

Routes:
  GET  /api/v1/requirements/projects
  GET  /api/v1/requirements/{projectId}/requirements
  POST /api/v1/requirements/{projectId}/query
  POST /api/v1/requirements/{projectId}/sources/upload
  GET  /api/v1/requirements/{projectId}/sources
  POST /api/v1/requirements/{projectId}/requirements/{requirementId}/suggest-tests
  GET  /api/v1/requirements/{projectId}/requirements/{requirementId}/latest-iq
  GET  /api/v1/requirements/{projectId}/readiness
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.models.user import User
import app.services.reqiq_client as reqiq

logger = logging.getLogger(__name__)
router = APIRouter()


def _reqiq_unavailable() -> None:
    """Check that ReqIQ credentials are configured."""
    from app.core.config import settings
    if not settings.REQIQ_SERVICE_EMAIL or not settings.REQIQ_SERVICE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ReqIQ integration is not configured on this server.",
        )


async def _proxy(coro):
    """Run a reqiq_client coroutine and convert errors to HTTP exceptions."""
    try:
        return await coro
    except Exception as exc:
        logger.error("ReqIQ proxy error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ReqIQ returned an error: {exc}",
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
# 2. List requirements for a project
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

class RagQueryBody(object):
    pass


from pydantic import BaseModel


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
    # If reqiq_client detected a 429, surface it properly
    if isinstance(result, dict) and result.get("_status") == 429:
        return JSONResponse(
            status_code=429,
            content={"detail": "ReqIQ rate limit exceeded — try again later"},
            headers={"Retry-After": str(result.get("_retry_after", "60"))},
        )
    return result


# ---------------------------------------------------------------------------
# 4. Upload source documents (multipart — stream directly to ReqIQ)
# ---------------------------------------------------------------------------

@router.post("/{project_id}/sources/upload", summary="Upload source documents to ReqIQ")
async def upload_sources(
    project_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    _reqiq_unavailable()

    files_payload = []
    for upload in files:
        content = await upload.read()
        files_payload.append(
            ("file", (upload.filename, content, upload.content_type or "application/octet-stream"))
        )

    return await _proxy(reqiq.upload_sources(project_id, files_payload))


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


# ---------------------------------------------------------------------------
# 6. Generate suggested tests for a requirement
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
# 7. Get latest IQ score for a requirement
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
# 8. Project readiness check
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
