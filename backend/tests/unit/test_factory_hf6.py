"""Unit tests for HF-6 notifications and observatory."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.observatory_service import redact_secrets


class TestRedactSecrets:
    def test_redacts_api_key_fields(self):
        data = {"AWT_MCP_SECRET": "super-secret", "test_case_id": 42}
        out = redact_secrets(data)
        assert out["AWT_MCP_SECRET"] == "***REDACTED***"
        assert out["test_case_id"] == 42

    def test_nested_password(self):
        data = {"auth": {"password": "x", "user": "admin"}}
        out = redact_secrets(data)
        assert out["auth"]["password"] == "***REDACTED***"
        assert out["auth"]["user"] == "admin"


class TestObservatoryAccess:
    def test_get_hermes_trace_logs_access(self):
        from app.services.observatory_service import get_hermes_trace

        db = MagicMock()
        event = SimpleNamespace(
            id=1,
            event_type="delegate_complete",
            profile="qa-test-gen",
            parent_profile="qa-orchestrator",
            message="done",
            payload_summary={"ok": True},
            payload_full={"api_key": "hidden"},
            llm_turns=None,
            hermes_session_id="sess_abc",
            created_at=datetime(2026, 6, 8, 0, 0, 0),
        )
        job = SimpleNamespace(
            id="job-1",
            job_type="full_cycle",
            status="completed",
            events=[event],
        )
        db.query.return_value.filter.return_value.first.return_value = job

        trace = get_hermes_trace(db, "job-1", user_id=99)
        assert trace is not None
        assert trace.job_id == "job-1"
        assert trace.hermes_session_ids == ["sess_abc"]
        assert db.add.called
        assert db.commit.called
