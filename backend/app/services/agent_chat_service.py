"""Natural-language → factory job mapping for Agent Chat (HF-1, HF-3)."""
import re
from typing import Any, Dict, Tuple

from app.core.config import settings
from app.schemas.factory_job import FactoryJobCreate

_REGRESSION_PATTERN = re.compile(
    r"\b(run|start|trigger|execute)\b.*\b(regression|regress)\b",
    re.IGNORECASE,
)
_DRAIN_PATTERN = re.compile(
    r"\b(drain|process|empty)\b.*\b(backlog|queue)\b",
    re.IGNORECASE,
)
_SCAN_PATTERN = re.compile(
    r"\b(scan|check|detect)\b.*\b(change|changes|snapshot)\b",
    re.IGNORECASE,
)
_FULL_CYCLE_PATTERN = re.compile(
    r"\b(full[_\s-]?cycle|end[_\s-]?to[_\s-]?end|e2e\s+factory)\b",
    re.IGNORECASE,
)
_GENERATE_PATTERN = re.compile(
    r"\b(generate|create|build)\b.*\b(journey|test)\b",
    re.IGNORECASE,
)
_HEAL_PATTERN = re.compile(
    r"\b(heal|fix|repair)\b.*\b(fail|failure|feedback)\b",
    re.IGNORECASE,
)


def _open_chat_params(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    params: Dict[str, Any] = {"message": message}
    resume_session = str(context.get("hermes_resume_session", "")).strip()
    if resume_session:
        params["hermes_resume_session"] = resume_session
    conversation_id = str(context.get("conversation_id", "")).strip()
    if conversation_id:
        params["conversation_id"] = conversation_id
    return params


def parse_chat_to_job(
    message: str,
    context: Dict[str, Any],
    *,
    allow_open_chat: bool = False,
    prefer_open_chat: bool = False,
) -> Tuple[FactoryJobCreate, str]:
    """Map user message to a structured factory job. HF-1/3: keyword rules; superadmin may use open chat."""
    text = (message or "").strip()
    if not text:
        raise ValueError("Message cannot be empty")

    # Superadmin escape hatch:
    # - Prefix with "!" to force structured command parsing (e.g. "!drain backlog")
    # - Otherwise remain in open-chat mode when prefer_open_chat is enabled.
    force_command = False
    if allow_open_chat and text.startswith("!"):
        force_command = True
        text = text[1:].strip()
        if not text:
            raise ValueError("Command cannot be empty after '!'.")

    project = context.get("project") or "Three-HK"
    lower = text.lower()

    if allow_open_chat and prefer_open_chat and not force_command:
        job = FactoryJobCreate(
            job_type="orchestrator_chat",
            project=project,
            params=_open_chat_params(text, context),
        )
        return job, "Sent to QA Orchestrator (open chat)."

    if _HEAL_PATTERN.search(text) or "heal failures" in lower:
        job = FactoryJobCreate(
            job_type="heal_failures",
            project=project,
            params={"limit": context.get("limit", settings.FACTORY_HEAL_MAX_ITEMS)},
        )
        return job, "Queued heal_failures for recent failed executions."

    if _SCAN_PATTERN.search(text) or "scan changes" in lower:
        job = FactoryJobCreate(
            job_type="scan_changes",
            project=project,
            params={},
        )
        return job, "Queued scan_changes for journey registry URLs."

    if _FULL_CYCLE_PATTERN.search(text):
        job = FactoryJobCreate(
            job_type="full_cycle",
            project=project,
            params={
                "max_items": context.get("max_items", settings.FACTORY_LOOP_A_MAX_ITEMS),
                "tags": context.get("tags") or ["regression"],
            },
        )
        return job, "Queued full_cycle: drain backlog then run regression."

    if _DRAIN_PATTERN.search(text) or "drain backlog" in lower:
        max_items = context.get("max_items", settings.FACTORY_LOOP_A_MAX_ITEMS)
        job = FactoryJobCreate(
            job_type="drain_backlog",
            project=project,
            params={"max_items": max_items},
        )
        return job, f"Queued drain_backlog (max {max_items} items)."

    if _GENERATE_PATTERN.search(text):
        slug = context.get("journey_slug")
        if not slug:
            for token in ("diy-dashboard", "postpaid-preprod4-entry"):
                if token in lower:
                    slug = token
                    break
        if not slug:
            raise ValueError(
                "Specify journey_slug in context or mention a known slug (e.g. diy-dashboard)."
            )
        job = FactoryJobCreate(
            job_type="generate_journey",
            project=project,
            params={"journey_slug": slug},
        )
        return job, f"Queued generate_journey for slug: {slug}."

    if _REGRESSION_PATTERN.search(text) or "regression" in lower:
        tags = context.get("tags") or ["regression"]
        if isinstance(tags, str):
            tags = [tags]
        job = FactoryJobCreate(
            job_type="run_regression",
            project=project,
            params={"tags": tags},
        )
        return job, f"Queued run_regression for tags: {', '.join(tags)}."

    if allow_open_chat:
        job = FactoryJobCreate(
            job_type="orchestrator_chat",
            project=project,
            params=_open_chat_params(text, context),
        )
        return job, "Sent to QA Orchestrator (open chat)."

    raise ValueError(
        "Could not interpret request. Try: 'Run regression', 'Drain backlog', "
        "'Scan changes', 'Heal failures', or 'Full cycle'."
    )
