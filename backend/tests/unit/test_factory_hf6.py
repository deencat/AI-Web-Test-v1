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


class TestHermesBridgeIngest:
    def test_ingest_redacts_secrets_before_store(self):
        from unittest.mock import patch

        from app.schemas.hermes_bridge import HermesBridgeEventCreate
        from app.services.hermes_bridge_ingest_service import ingest_hermes_bridge_event

        db = MagicMock()
        job = SimpleNamespace(id="job-1", status="running")
        stored_event = SimpleNamespace(
            id=99,
            event_type="delegate_complete",
            created_at=datetime(2026, 6, 8, 12, 0, 0),
        )

        with patch(
            "app.services.hermes_bridge_ingest_service.get_factory_job",
            return_value=job,
        ), patch(
            "app.services.hermes_bridge_ingest_service.append_job_event",
            return_value=stored_event,
        ) as append_mock:
            body = HermesBridgeEventCreate(
                job_id="job-1",
                event_type="delegate_complete",
                profile="qa-test-gen",
                payload_full={"api_key": "secret-value"},
            )
            result = ingest_hermes_bridge_event(db, body)

        assert result.event_id == 99
        kwargs = append_mock.call_args.kwargs
        assert kwargs["payload_full"]["api_key"] == "***REDACTED***"

    def test_ingest_unknown_job_raises(self):
        from unittest.mock import patch

        from app.schemas.hermes_bridge import HermesBridgeEventCreate
        from app.services.hermes_bridge_ingest_service import ingest_hermes_bridge_event

        db = MagicMock()
        with patch(
            "app.services.hermes_bridge_ingest_service.get_factory_job",
            return_value=None,
        ):
            try:
                ingest_hermes_bridge_event(
                    db,
                    HermesBridgeEventCreate(job_id="missing", event_type="job_started"),
                )
                assert False, "expected ValueError"
            except ValueError as exc:
                assert str(exc) == "job_not_found"
