"""Unit tests for orchestrator reply extraction."""
from types import SimpleNamespace

from app.services.factory_job_reply_service import extract_orchestrator_reply


class TestExtractOrchestratorReply:
    def test_prefers_assistant_llm_turn(self):
        job = SimpleNamespace(
            status="completed",
            error_message=None,
            events=[
                SimpleNamespace(
                    event_type="delegate_complete",
                    profile="qa-orchestrator",
                    message="ignored echo",
                    llm_turns=[
                        {"role": "user", "content": "hi"},
                        {"role": "assistant", "content": "Hello! How can I help?"},
                    ],
                )
            ],
        )
        assert extract_orchestrator_reply(job) == "Hello! How can I help?"

    def test_falls_back_to_failed_error_message(self):
        job = SimpleNamespace(
            status="failed",
            error_message="Bridge unreachable",
            events=[],
        )
        assert extract_orchestrator_reply(job) == "Bridge unreachable"
