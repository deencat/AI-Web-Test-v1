"""Unit tests for orchestrator reply extraction."""
import json
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

    def test_extracts_summary_from_json_llm_turn(self):
        payload = json.dumps(
            {
                "status": "success",
                "job_type": "ad_hoc",
                "summary": "AI Web Test MCP is reachable (healthy).",
                "test_case_ids": [],
                "delegates": [],
                "errors": [],
            }
        )
        job = SimpleNamespace(
            status="completed",
            error_message=None,
            events=[
                SimpleNamespace(
                    event_type="delegate_complete",
                    profile="qa-orchestrator",
                    message="Orchestrator reply",
                    llm_turns=[
                        {"role": "user", "content": "hi there"},
                        {"role": "assistant", "content": payload},
                    ],
                    payload_summary=None,
                ),
                SimpleNamespace(
                    event_type="job_complete",
                    profile="qa-orchestrator",
                    message="Orchestrator CLI finished",
                    llm_turns=None,
                    payload_summary={"status": "success"},
                ),
            ],
        )
        assert extract_orchestrator_reply(job) == "AI Web Test MCP is reachable (healthy)."

    def test_falls_back_to_failed_error_message(self):
        job = SimpleNamespace(
            status="failed",
            error_message="Bridge unreachable",
            events=[],
        )
        assert extract_orchestrator_reply(job) == "Bridge unreachable"
