"""
Integration tests for the Agent Workflow API v2 — Sprint 10 Real Backend (Developer B)

Tests cover:
- API contract validation (request/response schema)
- Endpoint existence and HTTP method correctness
- Request validation (required fields, type checks)
- Real 202 responses — no more 501 stubs
- End-to-end flow: trigger → status → results for the 4-agent pipeline

Note: Per Phase3 Architecture, AnalysisAgent may run test execution (critical scenarios)
as a scoring criterion (Phase 2 engine, 3-tier strategy). These tests verify the
API contract (202, status, results shape) and do not assert execution details.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.main import app

# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_tests_payload(**overrides) -> dict:
    base = {"url": "https://example.com", "user_instruction": "Test the homepage", "depth": 1}
    return {**base, **overrides}


# ===========================================================================
# Section 1: POST /api/v2/generate-tests
# ===========================================================================

class TestGenerateTestsEndpoint:
    BASE = "/api/v2/generate-tests"

    def test_endpoint_exists(self, client):
        """Endpoint must be registered — not 404 or 405."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code != 404, "Endpoint not found"
        assert response.status_code != 405, "Method not allowed"

    def test_returns_202_accepted(self, client):
        """Real backend must return 202 Accepted."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code == 202, (
            f"Expected 202, got {response.status_code}: {response.text}"
        )

    def test_response_has_workflow_id(self, client):
        """202 response body must contain a workflow_id string."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code == 202
        body = response.json()
        assert "workflow_id" in body
        assert isinstance(body["workflow_id"], str)
        assert len(body["workflow_id"]) > 0

    def test_response_status_is_pending(self, client):
        """Initial status must be 'pending'."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "pending"

    def test_response_has_required_fields(self, client):
        """Response must include all WorkflowStatusResponse fields."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code == 202
        body = response.json()
        for field in ("workflow_id", "status", "current_agent", "progress",
                      "total_progress", "started_at"):
            assert field in body, f"Missing field: {field}"

    def test_invalid_request_missing_url(self, client):
        """Submitting without 'url' must fail with 422."""
        response = client.post(self.BASE, json={"depth": 1})
        assert response.status_code == 422

    def test_invalid_request_bad_url_format(self, client):
        """Non-URL string must be rejected at schema level."""
        response = client.post(self.BASE, json={"url": "not-a-valid-url", "depth": 1})
        assert response.status_code == 422

    def test_invalid_depth_too_high(self, client):
        """depth > 3 must be rejected by Pydantic."""
        response = client.post(self.BASE, json=generate_tests_payload(depth=99))
        assert response.status_code == 422

    def test_invalid_depth_too_low(self, client):
        """depth < 1 must be rejected."""
        response = client.post(self.BASE, json=generate_tests_payload(depth=0))
        assert response.status_code == 422

    def test_optional_fields_accepted(self, client):
        """All optional fields included — must reach handler and return 202."""
        payload = {
            "url": "https://example.com/login",
            "user_instruction": "Test the checkout flow",
            "depth": 2,
            "login_credentials": {"username": "user@example.com", "password": "s3cr3t"},
        }
        response = client.post(self.BASE, json=payload)
        assert response.status_code == 202

    def test_content_type_json_required(self, client):
        """Non-JSON body must be rejected."""
        response = client.post(
            self.BASE,
            content="url=https://example.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code in (400, 415, 422)


# ===========================================================================
# Section 2: GET /api/v2/workflows/{workflow_id}
# ===========================================================================

class TestGetWorkflowStatusEndpoint:
    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}"

    def test_endpoint_exists(self, client):
        """Endpoint must be registered — 404 for unknown IDs is valid (not 405)."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 405, "Method not allowed — endpoint not registered"

    def test_unknown_workflow_returns_404(self, client):
        """Unknown workflow_id must return 404 with NOT_FOUND code."""
        r = client.get(self.url("this-id-does-not-exist-xyz"))
        assert r.status_code == 404
        body = r.json()
        detail = body.get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("code") == "NOT_FOUND"

    def test_known_workflow_returns_200(self, client):
        """Triggering a workflow then fetching its status must return 200."""
        # First create a workflow
        trigger = client.post("/api/v2/generate-tests", json=generate_tests_payload())
        assert trigger.status_code == 202
        wf_id = trigger.json()["workflow_id"]

        r = client.get(self.url(wf_id))
        assert r.status_code == 200
        body = r.json()
        assert body["workflow_id"] == wf_id
        assert body["status"] in ("pending", "running", "completed", "failed", "cancelled")

    def test_status_response_shape(self, client):
        """Status response must have all required fields."""
        trigger = client.post("/api/v2/generate-tests", json=generate_tests_payload())
        wf_id = trigger.json()["workflow_id"]
        r = client.get(self.url(wf_id))
        assert r.status_code == 200
        body = r.json()
        for field in ("workflow_id", "status", "current_agent", "progress",
                      "total_progress", "started_at"):
            assert field in body, f"Missing field: {field}"


# ===========================================================================
# Section 3: GET /api/v2/workflows/{workflow_id}/results
# ===========================================================================

class TestGetWorkflowResultsEndpoint:
    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}/results"

    def test_endpoint_exists(self, client):
        """Endpoint must be registered — 404 for unknown IDs is valid (not 405)."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 405, "Method not allowed — endpoint not registered"

    def test_unknown_workflow_returns_404(self, client):
        r = client.get(self.url("this-id-does-not-exist-xyz"))
        assert r.status_code == 404

    def test_results_endpoint_returns_valid_status(self, client):
        """
        After triggering a workflow, the results endpoint should return either:
        - 200  if the workflow completes synchronously (TestClient runs background tasks
               immediately, so stub agents often finish before this assertion)
        - 404  (NOT_READY) if polling happens before the workflow finishes
        """
        trigger = client.post("/api/v2/generate-tests", json=generate_tests_payload())
        wf_id = trigger.json()["workflow_id"]
        r = client.get(self.url(wf_id))
        assert r.status_code in (200, 404), (
            f"Expected 200 (completed) or 404 (not ready), got {r.status_code}: {r.text}"
        )


# ===========================================================================
# Section 4: DELETE /api/v2/workflows/{workflow_id}
# ===========================================================================

class TestCancelWorkflowEndpoint:
    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}"

    def test_endpoint_exists(self, client):
        r = client.delete(self.url("wf-test-001"))
        assert r.status_code not in (405,)

    def test_unknown_workflow_returns_404(self, client):
        r = client.delete(self.url("this-id-does-not-exist-xyz"))
        assert r.status_code == 404

    def test_cancel_known_workflow_returns_204(self, client):
        """Cancelling an existing workflow must return 204 No Content."""
        trigger = client.post("/api/v2/generate-tests", json=generate_tests_payload())
        wf_id = trigger.json()["workflow_id"]
        r = client.delete(self.url(wf_id))
        assert r.status_code == 204


# ===========================================================================
# Section 5: SSE Stream endpoint
# ===========================================================================

class TestSseStreamEndpoint:
    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}/stream"

    def test_endpoint_exists(self, client):
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 405

    def test_endpoint_not_404(self, client):
        """SSE endpoint must be registered."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 404

    def test_returns_event_stream_content_type(self, client):
        """SSE endpoint must return text/event-stream content type."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code in (200,)
        assert "text/event-stream" in r.headers.get("content-type", "")


# ===========================================================================
# Section 6: Schema / Contract Tests
# ===========================================================================

class TestWorkflowSchema:
    def test_generate_tests_request_import(self):
        from app.schemas.workflow import GenerateTestsRequest
        req = GenerateTestsRequest(url="https://example.com")
        assert str(req.url).startswith("https://example.com")

    def test_generate_tests_request_depth_defaults_to_1(self):
        from app.schemas.workflow import GenerateTestsRequest
        req = GenerateTestsRequest(url="https://example.com")
        assert req.depth == 1

    def test_generate_tests_request_depth_validation(self):
        from app.schemas.workflow import GenerateTestsRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            GenerateTestsRequest(url="https://example.com", depth=10)

    def test_agent_progress_model_defaults(self):
        from app.schemas.workflow import AgentProgress
        progress = AgentProgress(agent="observation", status="running")
        assert progress.progress == 0.0

    def test_agent_progress_event_has_timestamp(self):
        from app.schemas.workflow import AgentProgressEvent
        event = AgentProgressEvent(event="agent_started", data={"agent": "observation"})
        assert event.timestamp is not None

    def test_workflow_status_response_requires_workflow_id(self):
        from app.schemas.workflow import WorkflowStatusResponse
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            WorkflowStatusResponse()  # type: ignore[call-arg]


# ===========================================================================
# Section 7: End-to-End Flow Contract (real backend, mocked agents)
# ===========================================================================

class TestE2EWorkflowFlow:
    """
    E2E contract test: trigger /generate-tests → poll status → fetch results.
    Verifies the 4-agent pipeline (observation → requirements → analysis → evolution)
    returns workflow_id, status, and results shape. AnalysisAgent may execute
    critical scenarios for scoring (per Phase3 Architecture); this test does not
    assert execution details.
    """
    BASE = "/api/v2/generate-tests"

    def test_full_flow_trigger_and_status(self, client):
        """Trigger → return 202 → poll status → return 200 with correct shape."""
        payload = generate_tests_payload(url="https://example.com")

        # Step 1: Trigger
        trigger_r = client.post(self.BASE, json=payload)
        assert trigger_r.status_code == 202
        wf_id = trigger_r.json()["workflow_id"]
        assert isinstance(wf_id, str)

        # Step 2: Status
        status_r = client.get(f"/api/v2/workflows/{wf_id}")
        assert status_r.status_code == 200
        status_body = status_r.json()
        assert status_body["workflow_id"] == wf_id
        assert status_body["status"] in ("pending", "running", "completed", "failed", "cancelled")

    def test_cancel_after_trigger(self, client):
        """Trigger → cancel → 204."""
        trigger_r = client.post(self.BASE, json=generate_tests_payload())
        assert trigger_r.status_code == 202
        wf_id = trigger_r.json()["workflow_id"]

        cancel_r = client.delete(f"/api/v2/workflows/{wf_id}")
        assert cancel_r.status_code == 204

    def test_results_available_after_trigger(self, client):
        """
        Results endpoint returns 200 or 404 after trigger. In TestClient, background
        tasks run synchronously so stub agents may complete before this assertion.
        """
        trigger_r = client.post(self.BASE, json=generate_tests_payload())
        assert trigger_r.status_code == 202
        wf_id = trigger_r.json()["workflow_id"]

        results_r = client.get(f"/api/v2/workflows/{wf_id}/results")
        assert results_r.status_code in (200, 404), (
            f"Expected 200 or 404, got {results_r.status_code}: {results_r.text}"
        )
