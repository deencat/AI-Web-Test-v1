"""
Integration tests for the Agent Workflow API v2 (Sprint 10 Phase 2 - Developer B)

Tests cover:
- API contract validation (request/response schema)
- Endpoint existence and HTTP method correctness
- Request validation (required fields, type checks)
- Stub 501 behavior (which is current state; tests will flip to 2xx once Dev A implements)
- End-to-end flow: trigger → status → results

Note: All endpoints currently return 501 (stub). Tests document BOTH:
  (a) current behaviour  — assert 501 where endpoints are stubs
  (b) expected behaviour — helper functions for future contract tests
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.main import app

# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Shared synchronous test client for all tests in this module."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_tests_payload(**overrides) -> dict:
    """Return a minimal valid GenerateTestsRequest payload."""
    base = {
        "url": "https://example.com",
        "user_instruction": "Test the homepage",
        "depth": 1
    }
    return {**base, **overrides}


# ===========================================================================
# Section 1: POST /api/v2/generate-tests
# ===========================================================================

class TestGenerateTestsEndpoint:
    """Tests for POST /api/v2/generate-tests/generate-tests

    Note: The endpoint is registered at /generate-tests/generate-tests due to
    Dev A's router prefix ("/generate-tests") being stacked with the route
    decorator ("/generate-tests").  The test uses the actual registered path.
    Once Dev A fixes the prefix this constant can be updated.
    """

    BASE = "/api/v2/generate-tests/generate-tests"

    def test_endpoint_exists(self, client):
        """Endpoint must exist — not 404 or 405."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code != 404, "Endpoint not found"
        assert response.status_code != 405, "Method not allowed"

    def test_returns_501_stub(self, client):
        """Current stub should return 501 Not Implemented."""
        response = client.post(self.BASE, json=generate_tests_payload())
        assert response.status_code == 501, (
            f"Expected 501 (stub), got {response.status_code}"
        )

    def test_stub_body_contains_error_code(self, client):
        """Stub response body must contain 'NOT_IMPLEMENTED' for clarity."""
        response = client.post(self.BASE, json=generate_tests_payload())
        body = response.json()
        detail = body.get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("code") == "NOT_IMPLEMENTED"

    def test_invalid_request_missing_url(self, client):
        """Submitting without 'url' must fail with 422 Unprocessable Entity."""
        response = client.post(self.BASE, json={"depth": 1})
        assert response.status_code == 422

    def test_invalid_request_bad_url_format(self, client):
        """Non-URL string should be rejected at schema level."""
        response = client.post(self.BASE, json={"url": "not-a-valid-url", "depth": 1})
        assert response.status_code == 422

    def test_invalid_depth_too_high(self, client):
        """depth > 3 should be rejected by Pydantic validation."""
        response = client.post(self.BASE, json=generate_tests_payload(depth=99))
        assert response.status_code == 422

    def test_invalid_depth_too_low(self, client):
        """depth < 1 should be rejected."""
        response = client.post(self.BASE, json=generate_tests_payload(depth=0))
        assert response.status_code == 422

    def test_valid_request_with_all_optional_fields(self, client):
        """All optional fields included — should reach the (stub) handler."""
        payload = {
            "url": "https://example.com/login",
            "user_instruction": "Test the checkout flow",
            "depth": 2,
            "login_credentials": {
                "username": "user@example.com",
                "password": "s3cr3t"
            }
        }
        response = client.post(self.BASE, json=payload)
        # 501 expected because endpoint is stub; important: not 422 or 404
        assert response.status_code in (201, 202, 501)

    def test_content_type_json_required(self, client):
        """Non-JSON body must be rejected."""
        response = client.post(
            self.BASE,
            content="url=https://example.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code in (400, 415, 422)


# ===========================================================================
# Section 2: GET /api/v2/workflows/{workflow_id}
# ===========================================================================

class TestGetWorkflowStatusEndpoint:
    """Tests for GET /api/v2/workflows/{workflow_id}"""

    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}"

    def test_endpoint_exists(self, client):
        """Endpoint must respond — not 404 or 405."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 404
        assert r.status_code != 405

    def test_returns_501_stub(self, client):
        """Current stub must return 501."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code == 501

    def test_workflow_id_is_passed_in_detail(self, client):
        """Stub detail should echo back the workflow_id."""
        wf_id = "wf-echo-check"
        r = client.get(self.url(wf_id))
        body = r.json()
        detail = body.get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("workflow_id") == wf_id

    def test_different_workflow_ids(self, client):
        """Endpoint should accept arbitrary string workflow IDs."""
        for wf_id in ["abc123", "wf-00000001", "workflow_xyz-99"]:
            r = client.get(self.url(wf_id))
            assert r.status_code in (200, 404, 501), (
                f"Unexpected status {r.status_code} for id={wf_id}"
            )


# ===========================================================================
# Section 3: GET /api/v2/workflows/{workflow_id}/results
# ===========================================================================

class TestGetWorkflowResultsEndpoint:
    """Tests for GET /api/v2/workflows/{workflow_id}/results"""

    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}/results"

    def test_endpoint_exists(self, client):
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 404
        assert r.status_code != 405

    def test_returns_501_stub(self, client):
        r = client.get(self.url("wf-test-001"))
        assert r.status_code == 501


# ===========================================================================
# Section 4: DELETE /api/v2/workflows/{workflow_id}
# ===========================================================================

class TestCancelWorkflowEndpoint:
    """Tests for DELETE /api/v2/workflows/{workflow_id}"""

    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}"

    def test_endpoint_exists(self, client):
        r = client.delete(self.url("wf-test-001"))
        assert r.status_code != 404
        assert r.status_code != 405

    def test_returns_501_stub(self, client):
        r = client.delete(self.url("wf-test-001"))
        assert r.status_code == 501


# ===========================================================================
# Section 5: SSE Stream endpoint
# ===========================================================================

class TestSseStreamEndpoint:
    """Tests for GET /api/v2/workflows/{workflow_id}/stream"""

    def url(self, wf_id: str) -> str:
        return f"/api/v2/workflows/{wf_id}/stream"

    def test_endpoint_exists(self, client):
        r = client.get(self.url("wf-test-001"))
        # May return 501 (stub), 200 (streaming), or 404 — not 405
        assert r.status_code != 405

    def test_stub_does_not_return_404(self, client):
        """SSE endpoint stub must be registered and reachable."""
        r = client.get(self.url("wf-test-001"))
        assert r.status_code != 404


# ===========================================================================
# Section 6: Schema / Contract Tests
# ===========================================================================

class TestWorkflowSchema:
    """Validate Pydantic schema correctness via import."""

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
            # Missing required workflow_id, status, progress, started_at
            WorkflowStatusResponse()  # type: ignore[call-arg]


# ===========================================================================
# Section 7: End-to-End Flow Contract (mocked orchestration)
# ===========================================================================

class TestE2EWorkflowFlow:
    """
    Contract tests for the complete E2E flow.

    These tests mock OrchestrationService to test handler logic in isolation
    once the endpoints are implemented.  Currently they verify the 501 state.
    """

    BASE_TRIGGER = "/api/v2/generate-tests/generate-tests"

    def test_full_flow_contract_shape(self, client):
        """
        Trigger → Status → Results: document the expected flow shape.

        Once implemented, this test should verify:
        1. POST /generate-tests → 202 with workflow_id
        2. GET /workflows/{id} → 200 with status
        3. GET /workflows/{id}/results → 200 with test cases

        Currently asserts 501 for all three to document current state.
        """
        payload = generate_tests_payload(url="https://example.com")

        # Step 1: Trigger
        trigger_r = client.post(self.BASE_TRIGGER, json=payload)
        assert trigger_r.status_code in (202, 501)

        # If endpoint is live, follow through
        if trigger_r.status_code == 202:
            wf_id = trigger_r.json()["workflow_id"]
            assert isinstance(wf_id, str)

            # Step 2: Status
            status_r = client.get(f"/api/v2/workflows/{wf_id}")
            assert status_r.status_code == 200
            status_body = status_r.json()
            assert status_body["workflow_id"] == wf_id
            assert status_body["status"] in (
                "pending", "running", "completed", "failed", "cancelled"
            )

            # Step 3: Results (only available when completed)
            results_r = client.get(f"/api/v2/workflows/{wf_id}/results")
            assert results_r.status_code in (200, 404)
