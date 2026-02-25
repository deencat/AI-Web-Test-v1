"""
Unit tests for API v2 endpoints.
Uses a minimal FastAPI app with only the v2 router (no DB/queue_manager).
Tests: POST generate-tests (202), GET status/results (200/404), DELETE cancel (204/404).
Uses httpx.ASGITransport for compatibility with current httpx/Starlette versions.
"""
import pytest
import pytest_asyncio
from fastapi import FastAPI
import httpx

from app.api.v2.api import api_router
from app.services.workflow_store import set_state, get_state, delete_state, request_cancel


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v2")
    return app


@pytest.fixture
def app():
    return _make_app()


@pytest_asyncio.fixture
async def client(app: FastAPI):
    """Async client using httpx ASGITransport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def clear_workflows():
    """Clear workflow store entries used in tests."""
    for wfid in ["wf-status-test", "wf-results-test", "wf-cancel-test"]:
        delete_state(wfid)
    yield
    for wfid in ["wf-status-test", "wf-results-test", "wf-cancel-test"]:
        delete_state(wfid)


# --- POST /generate-tests ---


@pytest.mark.asyncio
async def test_generate_tests_returns_202_and_workflow_id(client: httpx.AsyncClient):
    response = await client.post(
        "/api/v2/generate-tests",
        json={"url": "https://example.com"},
    )
    assert response.status_code == 202
    data = response.json()
    assert "workflow_id" in data
    assert data["status"] in ("pending", "running")
    assert data["workflow_id"]


@pytest.mark.asyncio
async def test_generate_tests_accepts_optional_fields(client: httpx.AsyncClient):
    response = await client.post(
        "/api/v2/generate-tests",
        json={
            "url": "https://example.com/login",
            "user_instruction": "Test login",
            "depth": 2,
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["workflow_id"]


@pytest.mark.asyncio
async def test_generate_tests_invalid_url(client: httpx.AsyncClient):
    response = await client.post(
        "/api/v2/generate-tests",
        json={"url": "not-a-url"},
    )
    assert response.status_code == 422


# --- GET /workflows/{id} ---


@pytest.mark.asyncio
async def test_get_workflow_status_404_for_unknown(client: httpx.AsyncClient):
    response = await client.get("/api/v2/workflows/wf-nonexistent-12345")
    assert response.status_code == 404
    data = response.json()
    assert data.get("detail", {}).get("code") == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_workflow_status_200_with_state(client: httpx.AsyncClient):
    set_state("wf-status-test", {
        "workflow_id": "wf-status-test",
        "status": "running",
        "current_agent": "observation",
        "progress": {},
        "total_progress": 0.25,
        "started_at": "2026-02-23T10:00:00",
        "error": None,
    })
    response = await client.get("/api/v2/workflows/wf-status-test")
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-status-test"
    assert data["status"] == "running"
    assert data["current_agent"] == "observation"


# --- GET /workflows/{id}/results ---


@pytest.mark.asyncio
async def test_get_workflow_results_404_for_unknown(client: httpx.AsyncClient):
    response = await client.get("/api/v2/workflows/wf-unknown/results")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_workflow_results_404_when_not_ready(client: httpx.AsyncClient):
    set_state("wf-results-test", {
        "workflow_id": "wf-results-test",
        "status": "running",
        "result": None,
    })
    response = await client.get("/api/v2/workflows/wf-results-test/results")
    assert response.status_code == 404
    data = response.json()
    assert data.get("detail", {}).get("code") == "NOT_READY"


@pytest.mark.asyncio
async def test_get_workflow_results_200_when_ready(client: httpx.AsyncClient):
    set_state("wf-results-test", {
        "workflow_id": "wf-results-test",
        "status": "completed",
        "result": {
            "test_case_ids": [1, 2, 3],
            "test_count": 3,
            "observation_result": {},
            "requirements_result": {},
            "analysis_result": {},
            "evolution_result": {},
            "total_duration_seconds": 10.5,
        },
        "completed_at": "2026-02-23T10:05:00",
    })
    response = await client.get("/api/v2/workflows/wf-results-test/results")
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-results-test"
    assert data["status"] == "completed"
    assert data["test_case_ids"] == [1, 2, 3]
    assert data["test_count"] == 3


# --- DELETE /workflows/{id} (cancel) ---


@pytest.mark.asyncio
async def test_cancel_workflow_404_for_unknown(client: httpx.AsyncClient):
    response = await client.delete("/api/v2/workflows/wf-unknown-999")
    assert response.status_code == 404
    data = response.json()
    assert data.get("detail", {}).get("code") == "NOT_FOUND"


@pytest.mark.asyncio
async def test_cancel_workflow_204_for_existing(client: httpx.AsyncClient):
    set_state("wf-cancel-test", {
        "workflow_id": "wf-cancel-test",
        "status": "running",
    })
    response = await client.delete("/api/v2/workflows/wf-cancel-test")
    assert response.status_code == 204
    # Cancel flag should be set in store
    state = get_state("wf-cancel-test")
    assert state is not None
    assert state.get("cancel_requested") is True
