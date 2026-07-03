"""Extract human-readable orchestrator replies from factory job events."""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.models.factory_job import FactoryJob
from app.utils.hermes_session import clean_hermes_resume_session

_SUMMARY_FIELD_RE = re.compile(r'"summary"\s*:\s*"([\s\S]*?)"\s*,', re.MULTILINE)

_BOILERPLATE_MESSAGES = frozenset(
    {
        "orchestrator cli finished",
        "open chat completed",
        "orchestrator reply",
    }
)


def _is_boilerplate(message: str) -> bool:
    lower = message.strip().lower()
    if not lower:
        return True
    if lower in _BOILERPLATE_MESSAGES:
        return True
    if lower.startswith("orchestrator cli started"):
        return True
    if lower.startswith("bridge completed"):
        return True
    if lower.startswith("job queued:"):
        return True
    if lower.startswith("job accepted"):
        return True
    if lower.startswith("open chat:"):
        return True
    if "initializing agent" in lower:
        return True
    if lower.startswith("query:"):
        return True
    return False


def _summary_from_text(text: str) -> Optional[str]:
    stripped = text.strip()
    if not stripped:
        return None

    candidates = [stripped]
    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        candidates.append(stripped[first_brace : last_brace + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        summary = parsed.get("summary")
        if isinstance(summary, str) and summary.strip():
            return " ".join(summary.split())

    match = _SUMMARY_FIELD_RE.search(stripped)
    if match:
        return " ".join(match.group(1).split())
    return None


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


def _summary_from_payload(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    summary = payload.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    return None


def _hermes_cli_reply(raw: str) -> Optional[str]:
    """Surface Hermes CLI errors when no JSON summary is present."""
    stripped = raw.strip()
    if not stripped:
        return None

    lines: list[str] = []
    for line in stripped.splitlines():
        ln = line.strip()
        if not ln:
            continue
        lower = ln.lower()
        if lower.startswith("query:"):
            continue
        if lower == "initializing agent...":
            continue
        if lower.startswith("goodbye"):
            continue
        lines.append(ln)

    if not lines:
        return None

    message = " ".join(lines)
    lower = message.lower()
    if any(
        token in lower
        for token in (
            "session not found",
            "error:",
            "failed",
            "unavailable",
            "could not",
        )
    ):
        return message
    return None


def extract_orchestrator_reply(job: FactoryJob) -> Optional[str]:
    """Best-effort assistant reply for open chat and delegate completions."""
    events = list(job.events or [])

    for event in reversed(events):
        raw = _assistant_from_llm_turns(event.llm_turns)
        if not raw:
            continue
        summary = _summary_from_text(raw)
        if summary:
            return summary
        cli_reply = _hermes_cli_reply(raw)
        if cli_reply:
            return cli_reply
        if not _is_boilerplate(raw):
            return raw

    for event in reversed(events):
        summary = _summary_from_payload(event.payload_summary)
        if summary:
            return summary

    if job.status == "failed" and job.error_message:
        return job.error_message

    return None
