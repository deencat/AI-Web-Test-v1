"""
In-memory execution cancel flags for cooperative stop during test runs.

Mirrors workflow_store.py pattern: thread-safe dict keyed by execution_id.
"""
from typing import Dict, Any
from datetime import datetime, timezone
import threading

_lock = threading.Lock()
_store: Dict[int, Dict[str, Any]] = {}


def register_cancel(execution_id: int) -> None:
    """Ensure execution_id key exists in store (called when worker starts)."""
    with _lock:
        if execution_id not in _store:
            _store[execution_id] = {"execution_id": execution_id}


def request_cancel(execution_id: int) -> bool:
    """
    Set cancel_requested=True. Auto-registers key if missing.
    Returns True when the flag was set.
    """
    with _lock:
        if execution_id not in _store:
            _store[execution_id] = {"execution_id": execution_id}
        _store[execution_id]["cancel_requested"] = True
        _store[execution_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        return True


def is_cancel_requested(execution_id: int) -> bool:
    """Return True if cancellation was requested for this execution."""
    with _lock:
        state = _store.get(execution_id)
        return bool(state and state.get("cancel_requested"))


def clear_cancel(execution_id: int) -> bool:
    """Remove entry. Returns True if existed. Call in worker finally."""
    with _lock:
        if execution_id in _store:
            del _store[execution_id]
            return True
        return False
