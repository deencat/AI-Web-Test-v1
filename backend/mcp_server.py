"""
AI Web Test — MCP Server for Hermes Agent

Exposes a curated set of MCP tools so that Hermes Agent profiles (qa-test-gen,
qa-dispatcher, qa-reporter) can interact with the AI Web Test REST API without
needing to know individual endpoint URLs or authentication details.

Transport : Streamable HTTP  (MCP 2025 spec)
Port       : AWT_MCP_PORT    (default 8001)
Auth       : Authorization: Bearer <AWT_MCP_SECRET>

Usage
-----
Development (from backend/ folder):
    python mcp_server.py

Production (add to process manager alongside run_server.py / uvicorn):
    python mcp_server.py

Hermes profile config  (~/.hermes/profiles/qa-test-gen/mcp_servers.yaml):
    servers:
      - name: ai-web-test
        transport: http
        url: http://<NODE2_IP>:8001/mcp
        headers:
          Authorization: "Bearer ${AWT_MCP_SECRET}"

Tools exposed
-------------
  crawl_and_save_test        — Start a browser crawl + save as test case (async job)
  get_workflow_status        — Poll crawl-and-save job status by workflow_id
  get_workflow_results       — Get saved test_case_id after job completes
  list_test_cases            — List test cases (paginated, optional title search)
  get_test_case              — Get a single test case with its steps
  execute_test               — Trigger execution of a test case (Playwright/Stagehand)
  get_execution_status       — Get execution status and result
  list_executions            — List recent executions for a test case
  get_execution_stats        — Aggregated pass/fail statistics
  list_step_library_modules  — List reusable Step Library module names
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Bootstrap: ensure the backend package is importable when run standalone.
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Load .env so settings are available before importing the app config.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(_BACKEND_ROOT / ".env", override=False)

from app.core.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MCP] %(levelname)s %(message)s")
logger = logging.getLogger("awt_mcp")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MCP_SECRET: str = settings.AWT_MCP_SECRET or os.getenv("AWT_MCP_SECRET", "")
MCP_PORT: int = settings.AWT_MCP_PORT
AWT_BASE: str = settings.AWT_BASE_URL.rstrip("/")
AWT_SERVICE_EMAIL: str = settings.AWT_SERVICE_EMAIL or ""
AWT_SERVICE_PASSWORD: str = settings.AWT_SERVICE_PASSWORD or ""
AWT_V2_BASE: str = AWT_BASE.replace("/api/v1", "/api/v2")

if not MCP_SECRET:
    logger.warning(
        "AWT_MCP_SECRET is not set — MCP server will reject all requests. "
        "Set AWT_MCP_SECRET in backend/.env before using Hermes."
    )

# ---------------------------------------------------------------------------
# Internal REST client — authenticates with AI Web Test API using the service
# account and caches the JWT (refreshes on 401).
# ---------------------------------------------------------------------------
_cached_jwt: str | None = None


async def _get_jwt() -> str:
    """Login with the AWT service account and return a JWT. Caches the result."""
    global _cached_jwt
    if _cached_jwt:
        return _cached_jwt
    if not AWT_SERVICE_EMAIL or not AWT_SERVICE_PASSWORD:
        raise RuntimeError(
            "AWT_SERVICE_EMAIL and AWT_SERVICE_PASSWORD must be set in .env for the MCP server."
        )
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{AWT_BASE}/auth/login",
            data={"username": AWT_SERVICE_EMAIL, "password": AWT_SERVICE_PASSWORD},
        )
        r.raise_for_status()
        _cached_jwt = r.json()["access_token"]
        return _cached_jwt


async def _call(
    method: str,
    path: str,
    *,
    json: Any = None,
    params: dict | None = None,
    timeout: float = 600.0,
) -> Any:
    """Authenticated call to the AI Web Test REST API. Retries once on 401."""
    global _cached_jwt
    jwt = await _get_jwt()
    headers = {"Authorization": f"Bearer {jwt}"}
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.request(
            method,
            f"{AWT_BASE}{path}" if path.startswith("/") else path,
            headers=headers,
            json=json,
            params=params,
        )
        if r.status_code == 401:
            # Token expired — refresh once
            _cached_jwt = None
            jwt = await _get_jwt()
            headers["Authorization"] = f"Bearer {jwt}"
            r = await c.request(
                method,
                f"{AWT_BASE}{path}" if path.startswith("/") else path,
                headers=headers,
                json=json,
                params=params,
            )
        r.raise_for_status()
        if r.status_code == 204:
            return {}
        return r.json()


async def _call_v2(
    method: str,
    path: str,
    *,
    json: Any = None,
    params: dict | None = None,
    timeout: float = 30.0,
) -> Any:
    """Same as _call but hits /api/v2 base."""
    global _cached_jwt
    jwt = await _get_jwt()
    headers = {"Authorization": f"Bearer {jwt}"}
    url = f"{AWT_V2_BASE}{path}"
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.request(method, url, headers=headers, json=json, params=params)
        if r.status_code == 401:
            _cached_jwt = None
            jwt = await _get_jwt()
            headers["Authorization"] = f"Bearer {jwt}"
            r = await c.request(method, url, headers=headers, json=json, params=params)
        r.raise_for_status()
        if r.status_code == 204:
            return {}
        return r.json()


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "ai-web-test",
    stateless_http=True,
    instructions=(
        "Tools for driving the AI Web Test automation platform. "
        "Use crawl_and_save_test to generate a new test case via browser crawl, "
        "then poll get_workflow_status until status=='completed', "
        "then get_workflow_results to obtain the saved test_case_id. "
        "Use execute_test to run an existing test case and poll get_execution_status."
    ),
)

# ---------------------------------------------------------------------------
# § 1 — Crawl-and-Save workflow (test generation via browser)
# ---------------------------------------------------------------------------

@mcp.tool()
async def crawl_and_save_test(
    url: str,
    user_instruction: str,
    test_title: str,
    test_description: str,
    stop_at_page_hint: Optional[str] = None,
    login_module: Optional[str] = None,
    existing_subscriber_module: Optional[str] = None,
    new_subscriber_module: Optional[str] = None,
    subscriber_type_hint: Optional[str] = "auto",
    login_email: Optional[str] = None,
    login_password: Optional[str] = None,
    http_auth_username: Optional[str] = None,
    http_auth_password: Optional[str] = None,
    max_browser_steps: Optional[int] = None,
    max_flow_timeout_seconds: Optional[int] = None,
    reference_test_id: Optional[int] = None,
    tags: Optional[list[str]] = None,
) -> dict:
    """Start a browser crawl of a web flow and save the result as a test case.

    This is an **async job** — it returns a workflow_id immediately.
    Poll get_workflow_status(workflow_id) until status is 'completed' or 'failed'.
    Then call get_workflow_results(workflow_id) to get the saved test_case_id.

    Args:
        url: Start URL for the browser (e.g. 'https://wwwuat.three.com.hk/...')
        user_instruction: Step-by-step plain-English instruction for the browser agent.
            Include navigation steps, login, plan selection, and a STOP condition.
            Example: 'Login. Click 5G Monthly Plan. Select $288 Voucher plan.
                      Click Subscribe Now. STOP when SIM Card Setting page appears.'
        test_title: Title for the saved test case.
        test_description: One-line description (shown in test list UI).
        stop_at_page_hint: Substring to match in page title/URL to stop early
            (e.g. 'SIM Card Setting'). Prevents browser from attempting complex forms.
        login_module: Step Library module name for login steps
            (e.g. 'login_my3_andrew'). Replaces crawled login steps with a reusable block.
        existing_subscriber_module: Module appended when existing-subscriber popup is detected
            (e.g. 'plan_subscribe_flow_existing_preprod_andrew').
        new_subscriber_module: Module appended when no existing-subscriber popup
            (e.g. 'plan_subscriber_flow_andrew').
        subscriber_type_hint: 'existing' | 'new' | 'auto' (default).
        login_email: Email address for login (if not using login_module).
        login_password: Password for login (if not using login_module).
        http_auth_username: HTTP Basic auth username for UAT/preprod gate.
        http_auth_password: HTTP Basic auth password for UAT/preprod gate.
        max_browser_steps: Override max browser-use steps (default 120).
        max_flow_timeout_seconds: Override wall-clock timeout in seconds (default 1200).
        reference_test_id: ID of existing test case to use as quality reference for LLM review.
        tags: Optional list of tags for the test case.

    Returns:
        dict with workflow_id (str), status (str), message (str), started_at (str).
    """
    body: dict[str, Any] = {
        "url": url,
        "user_instruction": user_instruction,
        "test_title": test_title,
        "test_description": test_description,
    }
    if stop_at_page_hint:
        body["stop_at_page_hint"] = stop_at_page_hint
    if login_module:
        body["login_module"] = login_module
    if existing_subscriber_module:
        body["existing_subscriber_module"] = existing_subscriber_module
    if new_subscriber_module:
        body["new_subscriber_module"] = new_subscriber_module
    if subscriber_type_hint:
        body["subscriber_type_hint"] = subscriber_type_hint
    if login_email and login_password:
        body["login_credentials"] = {"email": login_email, "password": login_password}
    if http_auth_username and http_auth_password:
        body["http_credentials"] = {"username": http_auth_username, "password": http_auth_password}
    if max_browser_steps is not None:
        body["max_browser_steps"] = max_browser_steps
    if max_flow_timeout_seconds is not None:
        body["max_flow_timeout_seconds"] = max_flow_timeout_seconds
    if reference_test_id is not None:
        body["reference_test_id"] = reference_test_id
    if tags:
        body["tags"] = tags

    return await _call_v2("POST", "/crawl-and-save-test", json=body)


@mcp.tool()
async def get_workflow_status(workflow_id: str) -> dict:
    """Poll the status of a crawl-and-save workflow.

    Args:
        workflow_id: The workflow_id returned by crawl_and_save_test.

    Returns:
        dict with workflow_id, status ('pending'|'running'|'completed'|'failed'),
        current_agent, total_progress (0.0–1.0), error (if failed).

    Poll every 15–30 seconds. Stop when status is 'completed' or 'failed'.
    """
    return await _call_v2("GET", f"/workflows/{workflow_id}")


@mcp.tool()
async def get_workflow_results(workflow_id: str) -> dict:
    """Get the results of a completed crawl-and-save workflow.

    Only call this after get_workflow_status returns status=='completed'.

    Args:
        workflow_id: The workflow_id returned by crawl_and_save_test.

    Returns:
        dict with test_case_ids (list[int]), test_count (int),
        total_duration_seconds (float), completed_at (str).
        The first entry in test_case_ids is the primary saved test case.
    """
    return await _call_v2("GET", f"/workflows/{workflow_id}/results")


# ---------------------------------------------------------------------------
# § 2 — Test case management
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_test_cases(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
) -> dict:
    """List test cases stored in AI Web Test.

    Args:
        limit: Number of results to return (default 20, max 100).
        offset: Pagination offset (default 0).
        search: Optional title search string.

    Returns:
        dict with items (list of test cases), total (int), limit, offset.
        Each item has id, title, description, status, priority, tags, created_at.
    """
    params: dict[str, Any] = {"limit": min(limit, 100), "offset": offset}
    if search:
        params["search"] = search
    return await _call("GET", "/tests", params=params)


@mcp.tool()
async def get_test_case(test_case_id: int) -> dict:
    """Get a single test case including its steps and metadata.

    Args:
        test_case_id: Numeric ID of the test case.

    Returns:
        dict with id, title, description, steps (list), expected_result,
        preconditions, tags, status, priority, created_at, updated_at.
    """
    return await _call("GET", f"/tests/{test_case_id}")


# ---------------------------------------------------------------------------
# § 3 — Test execution
# ---------------------------------------------------------------------------

@mcp.tool()
async def execute_test(
    test_case_id: int,
    browser: str = "chromium",
    environment: str = "staging",
    triggered_by: str = "hermes",
) -> dict:
    """Trigger execution of an existing test case.

    This creates an execution record. The actual Playwright/Stagehand run
    starts asynchronously. Poll get_execution_status(execution_id) until
    status is 'completed' or 'failed'.

    Args:
        test_case_id: ID of the test case to execute.
        browser: 'chromium' | 'firefox' | 'webkit' (default 'chromium').
        environment: 'dev' | 'staging' | 'production' (default 'staging').
        triggered_by: Label for who triggered this (default 'hermes').

    Returns:
        dict with id (execution_id), test_case_id, status, message.
    """
    return await _call(
        "POST",
        f"/executions/tests/{test_case_id}/run",
        json={"browser": browser, "environment": environment, "triggered_by": triggered_by},
    )


@mcp.tool()
async def get_execution_status(execution_id: int) -> dict:
    """Get the current status and result of a test execution.

    Args:
        execution_id: The execution id returned by execute_test.

    Returns:
        dict with id, test_case_id, status ('pending'|'running'|'passed'|'failed'|'error'),
        result ('pass'|'fail'|null), started_at, completed_at, error_message,
        screenshots (list of URLs), duration_seconds.
    """
    return await _call("GET", f"/executions/{execution_id}")


@mcp.tool()
async def list_executions(
    test_case_id: int,
    limit: int = 10,
) -> dict:
    """List recent executions for a test case.

    Args:
        test_case_id: ID of the test case.
        limit: Number of executions to return (default 10).

    Returns:
        dict with items (list), total. Each item has id, status, result,
        started_at, completed_at, triggered_by.
    """
    return await _call(
        "GET",
        f"/executions/tests/{test_case_id}/executions",
        params={"limit": limit},
    )


@mcp.tool()
async def get_execution_stats() -> dict:
    """Get aggregated execution statistics across all test cases.

    Returns:
        dict with total_executions, passed, failed, error, pending,
        pass_rate (0.0–1.0), average_duration_seconds.
        Use to summarise test health in a Telegram report.
    """
    return await _call("GET", "/executions/stats")


# ---------------------------------------------------------------------------
# § 4 — Step Library (reusable modules for crawl-and-save)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_step_library_modules(
    limit: int = 50,
) -> dict:
    """List available Step Library modules that can be referenced in crawl_and_save_test.

    Step Library modules are reusable step sequences (e.g. login flows, subscriber
    selection). Pass a module name as login_module, existing_subscriber_module, or
    new_subscriber_module in crawl_and_save_test.

    Args:
        limit: Max number of modules to return (default 50).

    Returns:
        dict with items (list). Each item has name, description, step_count.
    """
    return await _call("GET", "/step-library", params={"limit": limit})


# ---------------------------------------------------------------------------
# § 5 — Health
# ---------------------------------------------------------------------------

@mcp.tool()
async def health_check() -> dict:
    """Check that the AI Web Test API is reachable and healthy.

    Returns:
        dict with status ('ok'|'error'), version, message.
        Call this first to verify connectivity before starting a pipeline.
    """
    try:
        return await _call("GET", "/health", timeout=10.0)
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


# ---------------------------------------------------------------------------
# Security middleware — validate Bearer token on every request
# ---------------------------------------------------------------------------

class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject requests that don't carry the shared MCP secret."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Allow health/readiness probes without auth
        if request.url.path in ("/health", "/healthz", "/"):
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not MCP_SECRET:
            # Secret not configured — log warning but let through so devs can test locally
            logger.warning("AWT_MCP_SECRET not set; skipping auth check (dev mode)")
            return await call_next(request)

        if not auth.startswith("Bearer ") or auth[7:] != MCP_SECRET:
            return Response(
                content='{"error":"Unauthorized"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)

    logger.info("Starting AI Web Test MCP server on port %d", MCP_PORT)
    logger.info("AWT base URL : %s", AWT_BASE)
    logger.info("Auth         : %s", "ENABLED" if MCP_SECRET else "DISABLED (dev mode)")

    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
