"""
ReqIQ server-to-server client.

Handles JWT auth (auto-login, 8-hour token cache, retry on 401) and provides
one async method per ReqIQ API call used by the proxy endpoints.

All HTTP calls use httpx.AsyncClient.  The module keeps a single module-level
token cache so the token survives across requests within the same process.
"""
import logging
import time
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token cache (module-level, survives across requests in the same process)
# ---------------------------------------------------------------------------
_token: Optional[str] = None
_token_expires_at: float = 0.0          # Unix timestamp
_TOKEN_TTL_SECONDS: float = 7 * 3600   # refresh 1 h before the 8-h expiry


def _token_valid() -> bool:
    return bool(_token) and time.time() < _token_expires_at


async def _login(client: httpx.AsyncClient) -> str:
    """Obtain a fresh JWT from ReqIQ and update the cache."""
    global _token, _token_expires_at

    if not settings.REQIQ_SERVICE_EMAIL or not settings.REQIQ_SERVICE_PASSWORD:
        raise RuntimeError(
            "REQIQ_SERVICE_EMAIL and REQIQ_SERVICE_PASSWORD must be set in .env"
        )

    resp = await client.post(
        f"{settings.REQIQ_URL}/api/v1/login",
        json={"email": settings.REQIQ_SERVICE_EMAIL, "password": settings.REQIQ_SERVICE_PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token = data["accessToken"]
    _token_expires_at = time.time() + _TOKEN_TTL_SECONDS
    logger.info("ReqIQ login successful; token cached for %.0f h", _TOKEN_TTL_SECONDS / 3600)
    return _token


async def _get_token(client: httpx.AsyncClient) -> str:
    if _token_valid():
        return _token  # type: ignore[return-value]
    return await _login(client)


async def _request(
    method: str,
    path: str,
    *,
    json: Any = None,
    data: Any = None,
    files: Any = None,
    params: Any = None,
    headers: dict | None = None,
    retry_on_401: bool = True,
) -> httpx.Response:
    """
    Make an authenticated request to ReqIQ.

    Retries once on 401 (token expired mid-request) by re-logging in.
    Passes 429 responses through as-is so callers can forward Retry-After.
    """
    async with httpx.AsyncClient(timeout=60) as client:
        token = await _get_token(client)
        auth_headers = {"Authorization": f"Bearer {token}", **(headers or {})}

        resp = await client.request(
            method,
            f"{settings.REQIQ_URL}{path}",
            json=json,
            data=data,
            files=files,
            params=params,
            headers=auth_headers,
        )

        if resp.status_code == 401 and retry_on_401:
            logger.warning("ReqIQ returned 401 — re-logging in and retrying")
            token = await _login(client)
            auth_headers["Authorization"] = f"Bearer {token}"
            resp = await client.request(
                method,
                f"{settings.REQIQ_URL}{path}",
                json=json,
                data=data,
                files=files,
                params=params,
                headers=auth_headers,
            )

        return resp


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_projects() -> dict:
    resp = await _request("GET", "/api/v1/projects")
    resp.raise_for_status()
    return resp.json()


async def list_requirements(project_id: str) -> dict:
    resp = await _request("GET", f"/api/v1/projects/{project_id}/requirements")
    resp.raise_for_status()
    return resp.json()


async def rag_query(project_id: str, query: str, limit: int = 8) -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/rag/query",
        json={"query": query, "limit": limit},
    )
    # Pass 429 back to caller; raise on everything else
    if resp.status_code == 429:
        return {"_status": 429, "_retry_after": resp.headers.get("Retry-After", "60")}
    resp.raise_for_status()
    return resp.json()


async def upload_sources(project_id: str, files_payload: list[tuple]) -> dict:
    """
    files_payload: list of (field_name, (filename, file_bytes, content_type)) tuples
    ready to pass directly to httpx files=...
    """
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/sources/upload",
        files=files_payload,
    )
    resp.raise_for_status()
    return resp.json()


async def list_sources(project_id: str) -> dict:
    resp = await _request("GET", f"/api/v1/projects/{project_id}/sources")
    resp.raise_for_status()
    return resp.json()


async def suggest_tests(
    project_id: str,
    requirement_id: str,
    max_tests: int = 3,
    hints: str = "",
) -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/suggested-tests/generate",
        json={"requirementId": requirement_id, "maxTests": max_tests, "hints": hints},
    )
    resp.raise_for_status()
    return resp.json()


async def get_latest_iq(project_id: str, requirement_id: str) -> dict:
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/latest-iq",
    )
    resp.raise_for_status()
    return resp.json()


async def get_readiness(project_id: str, query: str = "", feature: str = "") -> dict:
    params: dict = {}
    if query:
        params["query"] = query
    if feature:
        params["feature"] = feature
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/readiness",
        params=params,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# §5.2 extensions — workspace + requirement CRUD, IQ, suggested-test ops
# ---------------------------------------------------------------------------

async def create_project(name: str) -> dict:
    resp = await _request("POST", "/api/v1/projects", json={"name": name})
    resp.raise_for_status()
    return resp.json()


async def get_project(project_id: str) -> dict:
    resp = await _request("GET", f"/api/v1/projects/{project_id}")
    resp.raise_for_status()
    return resp.json()


async def update_project(project_id: str, name: str) -> dict:
    resp = await _request("PATCH", f"/api/v1/projects/{project_id}", json={"name": name})
    resp.raise_for_status()
    return resp.json()


async def create_requirement(project_id: str, title: str, body: str = "") -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": title, "body": body},
    )
    resp.raise_for_status()
    return resp.json()


async def get_requirement(project_id: str, requirement_id: str) -> dict:
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}",
    )
    resp.raise_for_status()
    return resp.json()


async def update_requirement(project_id: str, requirement_id: str, **fields: Any) -> dict:
    resp = await _request(
        "PATCH",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}",
        json=fields,
    )
    resp.raise_for_status()
    return resp.json()


async def transition_requirement(project_id: str, requirement_id: str, state: str) -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/transition",
        json={"state": state},
    )
    resp.raise_for_status()
    return resp.json()


async def get_requirement_audit(project_id: str, requirement_id: str) -> dict:
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/audit",
    )
    resp.raise_for_status()
    return resp.json()


async def list_revisions(project_id: str, requirement_id: str) -> dict:
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/revisions",
    )
    resp.raise_for_status()
    return resp.json()


async def get_revision(project_id: str, requirement_id: str, revision_index: int) -> dict:
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/revisions/{revision_index}",
    )
    resp.raise_for_status()
    return resp.json()


async def run_stub_iq(project_id: str, requirement_id: str, revision_index: int) -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/revisions/{revision_index}/stub-iq",
    )
    resp.raise_for_status()
    return resp.json()


async def run_llm_iq(project_id: str, requirement_id: str, revision_index: int) -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/revisions/{revision_index}/llm-iq",
    )
    resp.raise_for_status()
    return resp.json()


async def list_suggested_tests(project_id: str, requirement_id: str) -> dict:
    resp = await _request(
        "GET",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/suggested-tests",
    )
    resp.raise_for_status()
    return resp.json()


async def import_suggested_tests(project_id: str, requirement_id: str, tests: list) -> dict:
    resp = await _request(
        "POST",
        f"/api/v1/projects/{project_id}/requirements/{requirement_id}/suggested-tests/import",
        json={"tests": tests},
    )
    resp.raise_for_status()
    return resp.json()
