"""Extract human-readable orchestrator replies from factory job events."""
from __future__ import annotations

from typing import Any, Optional

from app.models.factory_job import FactoryJob


def _assistant_from_llm_turns(turns: Any) -> Optional[str]:
    if not isinstance(turns, list):
        return None
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        if turn.get("role") == "assistant":
            content = turn.get("content")
            if content and str(content).strip():
                return str(content).strip()
    return None


def extract_orchestrator_reply(job: FactoryJob) -> Optional[str]:
    """Best-effort assistant reply for open chat and delegate completions."""
    events = list(job.events or [])
    for event in reversed(events):
        reply = _assistant_from_llm_turns(event.llm_turns)
        if reply:
            return reply

        if event.event_type == "error" and event.message:
            return event.message

        if event.event_type in ("delegate_complete", "job_complete"):
            profile = (event.profile or "").lower()
            if profile in ("qa-orchestrator", "factory_bridge", "hermes_bridge"):
                msg = (event.message or "").strip()
                if msg and not msg.startswith("Bridge completed"):
                    return msg

    if job.status == "failed" and job.error_message:
        return job.error_message

    return None
