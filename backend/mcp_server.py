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

Hermes profile config  (~/.hermes/profiles/<profile>/config.yaml):
    mcp_servers:
      ai-web-test:
        url: "http://<NODE2_IP>:8001/mcp"
        headers:
          Authorization: "Bearer ${AWT_MCP_SECRET}"
        timeout: 180
        connect_timeout: 30

    Profiles that need this MCP server:
      - qa-manager    (health_check, list_test_cases)
      - qa-test-gen   (crawl_and_save_test, get_workflow_status, get_workflow_results, + all)
      - qa-dispatcher (health_check, execute_test, get_execution_status, list_executions,
                       get_execution_stats) — configure both node2 and node3 entries
    Profiles that do NOT need it:
      - qa-requirements  (calls ReqIQ directly via curl in terminal tool)
      - qa-reporter      (downloads results via terminal/curl from Garage S3)

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
  get_execution_feedback     — Step-level failure feedback for an execution (HF-2)
  list_failed_executions     — Recent failed executions (HF-2)
  create_test_schedule       — Create cron/interval schedule for a test (HF-2)
  list_test_schedules        — List schedules for current service account (HF-2)
  delete_test_schedule       — Delete a schedule by id (HF-2)
  get_coverage_matrix        — ReqIQ coverage matrix via AWT proxy (HF-2)
  get_reqiq_readiness        — ReqIQ wiki readiness check (HF-2)
  suggest_scenarios_from_wiki — Generate DRAFT requirements from wiki (HF-2)
  list_journey_backlog       — Pending journey backlog items (HF-2)
  enqueue_journey            — Add journey to factory backlog (HF-2)
  observe_url_snapshot       — Capture URL snapshot for change detection (HF-4)
  get_url_snapshot           — Get latest snapshot by url_hash (HF-4)
  diff_url_snapshots         — Diff snapshots for material DOM change (HF-4)
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
from mcp.server.fastmcp.server import TransportSecuritySettings
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
AWT_SERVICE_USERNAME: str = settings.AWT_SERVICE_USERNAME or ""
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
    if not AWT_SERVICE_USERNAME or not AWT_SERVICE_PASSWORD:
        raise RuntimeError(
            "AWT_SERVICE_USERNAME and AWT_SERVICE_PASSWORD must be set in .env for the MCP server."
        )
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{AWT_BASE}/auth/login",
            data={"username": AWT_SERVICE_USERNAME, "password": AWT_SERVICE_PASSWORD},
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
    # Use plain JSON responses instead of SSE streams so clients only need
    # Accept: application/json (not text/event-stream).  Hermes Agent sends
    # application/json only, causing 406 with the default SSE mode.
    json_response=True,
    # Disable DNS-rebinding protection so remote LAN clients (e.g. Hermes Agent
    # on a different machine) can connect using the server's IP as the Host header.
    # Bearer-token auth still protects the endpoint.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
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
# § 5 — Execution feedback & schedules (HF-2 factory tools)
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_execution_feedback(execution_id: int) -> list:
    """Get step-level failure feedback for a test execution.

    Args:
        execution_id: Numeric execution id from execute_test or list_failed_executions.

    Returns:
        List of feedback objects with failure_type, step_index, selector, screenshot_url, etc.
    """
    return await _call("GET", f"/executions/{execution_id}/feedback")


@mcp.tool()
async def list_failed_executions(
    since: Optional[str] = None,
    limit: int = 20,
    test_case_id: Optional[int] = None,
) -> dict:
    """List recent failed test executions.

    Args:
        since: ISO-8601 datetime — only failures completed on or after this time.
        limit: Max results (default 20, max 100).
        test_case_id: Optional filter by test case id.

    Returns:
        dict with items, total, skip, limit — same shape as list_executions API.
    """
    params: dict[str, Any] = {"result": "fail", "limit": min(limit, 100)}
    if since:
        params["since"] = since
    if test_case_id is not None:
        params["test_case_id"] = test_case_id
    return await _call("GET", "/executions/", params=params)


@mcp.tool()
async def create_test_schedule(
    test_case_id: int,
    schedule_type: str = "cron",
    cron_expression: Optional[str] = None,
    interval_minutes: Optional[int] = None,
    name: Optional[str] = None,
    browser: str = "chromium",
    environment: str = "staging",
    enabled: bool = True,
) -> dict:
    """Create a recurring test schedule.

    Args:
        test_case_id: Test case to run on schedule.
        schedule_type: 'cron' or 'interval' (default 'cron').
        cron_expression: Required when schedule_type is 'cron' (e.g. '0 2 * * *').
        interval_minutes: Required when schedule_type is 'interval'.
        name: Optional display name.
        browser: Browser target (default chromium).
        environment: dev | staging | production.
        enabled: Whether schedule is active (default True).

    Returns:
        Created schedule object with id, schedule_description, etc.
    """
    body: dict[str, Any] = {
        "test_case_id": test_case_id,
        "schedule_type": schedule_type,
        "browser": browser,
        "environment": environment,
        "enabled": enabled,
    }
    if name:
        body["name"] = name
    if cron_expression:
        body["cron_expression"] = cron_expression
    if interval_minutes is not None:
        body["interval_minutes"] = interval_minutes
    return await _call("POST", "/schedules/", json=body)


@mcp.tool()
async def list_test_schedules() -> list:
    """List all test schedules owned by the service account.

    Returns:
        List of schedule objects with id, test_case_id, cron_expression, enabled, etc.
    """
    return await _call("GET", "/schedules/")


@mcp.tool()
async def delete_test_schedule(schedule_id: int) -> dict:
    """Delete a test schedule and stop its timer.

    Args:
        schedule_id: Schedule id from list_test_schedules or create_test_schedule.

    Returns:
        Empty dict on success (HTTP 204).
    """
    return await _call("DELETE", f"/schedules/{schedule_id}")


# ---------------------------------------------------------------------------
# § 6 — ReqIQ proxy (HF-2)
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_coverage_matrix(project_id: str) -> dict:
    """Get scenario coverage matrix across capabilities from ReqIQ.

    Args:
        project_id: ReqIQ project id (e.g. from journey registry reqiq_project_id).

    Returns:
        Coverage matrix JSON from ReqIQ via AWT proxy.
    """
    return await _call("GET", f"/requirements/{project_id}/coverage-matrix")


@mcp.tool()
async def get_reqiq_readiness(
    project_id: str,
    query: str = "",
    feature: str = "",
) -> dict:
    """Check ReqIQ wiki readiness for a project or feature.

    Args:
        project_id: ReqIQ project id.
        query: Optional search query for wiki context.
        feature: Optional feature name filter.

    Returns:
        dict with readinessScore, wikiContent, and related ReqIQ fields.
    """
    params: dict[str, str] = {}
    if query:
        params["query"] = query
    if feature:
        params["feature"] = feature
    return await _call("GET", f"/requirements/{project_id}/readiness", params=params or None)


@mcp.tool()
async def suggest_scenarios_from_wiki(
    project_id: str,
    capability_keys: Optional[list[str]] = None,
    max_scenarios: Optional[int] = None,
    hints: Optional[str] = None,
) -> dict:
    """Generate DRAFT requirements / scenarios from compiled ReqIQ wiki.

    Args:
        project_id: ReqIQ project id.
        capability_keys: Optional capability keys to focus on.
        max_scenarios: Max scenarios to suggest.
        hints: Optional planner hints for the LLM.

    Returns:
        ReqIQ suggest-from-wiki response with draft requirements.
    """
    body: dict[str, Any] = {}
    if capability_keys:
        body["capabilityKeys"] = capability_keys
    if max_scenarios is not None:
        body["maxScenarios"] = max_scenarios
    if hints:
        body["hints"] = hints
    return await _call(
        "POST",
        f"/requirements/{project_id}/requirements/suggest-from-wiki",
        json=body,
    )


# ---------------------------------------------------------------------------
# § 7 — Journey registry backlog (HF-2)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_journey_backlog(
    status: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """List journey backlog items for the QA factory.

    Args:
        status: Filter by pending | in_progress | done | failed.
        project: Filter by project name (e.g. 'Three-HK').
        limit: Max items (default 50).

    Returns:
        dict with items and total count.
    """
    params: dict[str, Any] = {"limit": min(limit, 200)}
    if status:
        params["status"] = status
    if project:
        params["project"] = project
    return await _call("GET", "/agent/backlog", params=params)


@mcp.tool()
async def enqueue_journey(
    journey_slug: str,
    project: str = "Three-HK",
    priority: int = 0,
    params: Optional[dict] = None,
) -> dict:
    """Enqueue a journey from the registry for test generation.

    Args:
        journey_slug: Registry slug (e.g. 'diy-dashboard').
        project: Project name (default 'Three-HK').
        priority: Higher runs first (default 0).
        params: Optional overrides (user_instruction, tags, etc.).

    Returns:
        Created backlog item with id and status 'pending'.
    """
    body: dict[str, Any] = {
        "journey_slug": journey_slug,
        "project": project,
        "priority": priority,
    }
    if params:
        body["params"] = params
    return await _call("POST", "/agent/backlog", json=body)


# ---------------------------------------------------------------------------
# § 8 — URL snapshots / change detection (HF-4)
# ---------------------------------------------------------------------------

@mcp.tool()
async def observe_url_snapshot(
    url: str,
    http_auth_username: Optional[str] = None,
    http_auth_password: Optional[str] = None,
) -> dict:
    """Capture a lightweight URL snapshot (HTML summary + element fingerprint).

    Args:
        url: Page URL to observe (e.g. journey feature_url).
        http_auth_username: Optional HTTP Basic auth username for UAT gate.
        http_auth_password: Optional HTTP Basic auth password.

    Returns:
        Snapshot record with id, url_hash, element_fingerprint, captured_at.
    """
    body: dict[str, Any] = {"url": url}
    if http_auth_username and http_auth_password:
        body["http_credentials"] = {
            "username": http_auth_username,
            "password": http_auth_password,
        }
    return await _call_v2("POST", "/observe-snapshot", json=body)


@mcp.tool()
async def get_url_snapshot(url_hash: str) -> dict:
    """Get the latest stored snapshot for a URL hash.

    Args:
        url_hash: Hash from observe_url_snapshot response.

    Returns:
        Latest snapshot object or 404 if none stored.
    """
    return await _call_v2("GET", f"/snapshots/{url_hash}")


@mcp.tool()
async def diff_url_snapshots(
    url: str,
    capture_new: bool = True,
    baseline_snapshot_id: Optional[int] = None,
) -> dict:
    """Compare URL snapshots and detect material page changes.

    Args:
        url: URL to diff (captures new snapshot when capture_new=true).
        capture_new: If true, fetch current page before diffing (default true).
        baseline_snapshot_id: Optional explicit baseline snapshot id.

    Returns:
        dict with material_change (bool), summary (str), similarity_score, etc.
    """
    body: dict[str, Any] = {"url": url, "capture_new": capture_new}
    if baseline_snapshot_id is not None:
        body["baseline_snapshot_id"] = baseline_snapshot_id
    return await _call_v2("POST", "/snapshots/diff", json=body)


# ---------------------------------------------------------------------------
# § 9 — Health
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
# Accept-header normaliser — FastMCP validates Accept strictly (no wildcard)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Accept-header normaliser — FastMCP validates Accept strictly (no wildcard)
# ---------------------------------------------------------------------------

class AcceptNormalizerMiddleware:
    """Ensure every MCP request carries Accept: application/json.

    Hermes Agent (and other MCP clients) may send Accept: */* or omit it.
    FastMCP's strict prefix check rejects those with 406.  This raw ASGI
    middleware rewrites the Accept header in the ASGI scope before FastMCP
    sees the request, so any MCP client works regardless of what it sends.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            hdrs = {k: v for k, v in scope["headers"]}
            accept = hdrs.get(b"accept", b"").decode()
            if not any(
                t.strip().startswith("application/json")
                for t in accept.split(",")
            ):
                patched = (
                    "application/json, text/event-stream"
                    if not accept
                    else f"application/json, text/event-stream, {accept}"
                )
                hdrs[b"accept"] = patched.encode()
                scope = {**scope, "headers": list(hdrs.items())}
        await self.app(scope, receive, send)


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
    # Wrap with raw ASGI normaliser so clients sending Accept: */* or no
    # Accept header (e.g. Hermes Agent) are accepted instead of getting 406.
    app = AcceptNormalizerMiddleware(app)

    logger.info("Starting AI Web Test MCP server on port %d", MCP_PORT)
    logger.info("AWT base URL : %s", AWT_BASE)
    logger.info("Auth         : %s", "ENABLED" if MCP_SECRET else "DISABLED (dev mode)")

    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
