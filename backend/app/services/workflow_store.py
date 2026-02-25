"""
In-memory workflow state store for API v2.

Stores workflow status and results so GET /workflows/{id} and GET /workflows/{id}/results
can return current state. Uses a simple dict; can be replaced with Redis/DB later.

Reference: Sprint 10 - Agent Workflow API
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import threading

_lock = threading.Lock()
_store: Dict[str, Dict[str, Any]] = {}


def get_state(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Return current workflow state or None if not found."""
    with _lock:
        return _store.get(workflow_id)


def set_state(workflow_id: str, state: Dict[str, Any]) -> None:
    """Set full workflow state."""
    with _lock:
        _store[workflow_id] = {**state, "updated_at": datetime.now(timezone.utc).isoformat()}


def update_state(workflow_id: str, **kwargs: Any) -> None:
    """Update specific fields of workflow state."""
    with _lock:
        if workflow_id not in _store:
            _store[workflow_id] = {"workflow_id": workflow_id}
        _store[workflow_id].update(kwargs)
        _store[workflow_id]["updated_at"] = datetime.now(timezone.utc).isoformat()


def delete_state(workflow_id: str) -> bool:
    """Remove workflow state. Returns True if existed."""
    with _lock:
        if workflow_id in _store:
            del _store[workflow_id]
            return True
        return False


def request_cancel(workflow_id: str) -> bool:
    """
    Request cancellation of a workflow. Sets cancel_requested=True.
    Orchestration checks this between stages and stops cleanly.
    Returns True if the workflow existed (state was updated).
    """
    with _lock:
        if workflow_id not in _store:
            return False
        _store[workflow_id]["cancel_requested"] = True
        _store[workflow_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        return True


def is_cancel_requested(workflow_id: str) -> bool:
    """Return True if cancellation was requested for this workflow."""
    with _lock:
        state = _store.get(workflow_id)
        return bool(state and state.get("cancel_requested"))
