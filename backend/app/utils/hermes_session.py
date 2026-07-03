"""Helpers for Hermes CLI session ids passed through factory jobs."""
from __future__ import annotations

from typing import Any, Optional

_INVALID_SESSION_VALUES = frozenset({"", "none", "null", "undefined"})


def clean_hermes_resume_session(value: Any) -> Optional[str]:
    """Normalize resume session; reject None/null-like strings (e.g. str(None) -> 'None')."""
    if value is None:
        return None
    session = str(value).strip()
    if session.lower() in _INVALID_SESSION_VALUES:
        return None
    return session
