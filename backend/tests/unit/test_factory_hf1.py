"""Unit tests for Hermes QA Factory HF-1."""
import pytest

from app.services.agent_chat_service import parse_chat_to_job


class TestAgentChatService:
    def test_parse_regression_message(self):
        job, reply = parse_chat_to_job("Run regression", {})
        assert job.job_type == "run_regression"
        assert job.params["tags"] == ["regression"]
        assert "run_regression" in reply

    def test_parse_unknown_message_raises(self):
        with pytest.raises(ValueError):
            parse_chat_to_job("hello there", {})

    def test_open_chat_when_allowed(self):
        job, reply = parse_chat_to_job("What journeys are in the backlog?", {}, allow_open_chat=True)
        assert job.job_type == "orchestrator_chat"
        assert job.params["message"] == "What journeys are in the backlog?"
        assert "open chat" in reply.lower()

    def test_open_chat_preferred_for_superadmin(self):
        job, _ = parse_chat_to_job(
            "please run regression now",
            {},
            allow_open_chat=True,
            prefer_open_chat=True,
        )
        assert job.job_type == "orchestrator_chat"

    def test_superadmin_can_force_structured_command_with_bang_prefix(self):
        job, _ = parse_chat_to_job(
            "!drain backlog",
            {},
            allow_open_chat=True,
            prefer_open_chat=True,
        )
        assert job.job_type == "drain_backlog"

    def test_bang_prefix_requires_nonempty_command(self):
        with pytest.raises(ValueError):
            parse_chat_to_job(
                "!",
                {},
                allow_open_chat=True,
                prefer_open_chat=True,
            )

    def test_keywords_still_work_when_prefer_open_chat_false(self):
        job, _ = parse_chat_to_job(
            "please run regression now",
            {},
            allow_open_chat=True,
            prefer_open_chat=False,
        )
        assert job.job_type == "run_regression"

    def test_parse_drain_backlog_keyword(self):
        job, reply = parse_chat_to_job("Please drain backlog", {})
        assert job.job_type == "drain_backlog"


class TestRoleRank:
    def test_admin_meets_factory_operator(self):
        from app.api.deps import _role_rank, _FACTORY_OPERATOR_MIN_RANK

        assert _role_rank("admin") >= _FACTORY_OPERATOR_MIN_RANK
        assert _role_rank("agent_operator") >= _FACTORY_OPERATOR_MIN_RANK
        assert _role_rank("user") < _FACTORY_OPERATOR_MIN_RANK
