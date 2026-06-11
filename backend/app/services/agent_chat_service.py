"""Natural-language → factory job mapping for Agent Chat (HF-1)."""
import re
from typing import Any, Dict, Tuple

from app.schemas.factory_job import FactoryJobCreate

_REGRESSION_PATTERN = re.compile(
    r"\b(run|start|trigger|execute)\b.*\b(regression|regress)\b",
    re.IGNORECASE,
)


def parse_chat_to_job(message: str, context: Dict[str, Any]) -> Tuple[FactoryJobCreate, str]:
    """Map user message to a structured factory job. HF-1: keyword rules only."""
    text = (message or "").strip()
    if not text:
        raise ValueError("Message cannot be empty")

    project = context.get("project")

    if _REGRESSION_PATTERN.search(text) or "regression" in text.lower():
        tags = context.get("tags") or ["regression"]
        if isinstance(tags, str):
            tags = [tags]
        job = FactoryJobCreate(
            job_type="run_regression",
            project=project,
            params={"tags": tags},
        )
        reply = f"Queued run_regression for tags: {', '.join(tags)}."
        return job, reply

    raise ValueError(
        "Could not interpret request. Try: 'Run regression' or 'Run regression for tag smoke'."
    )
