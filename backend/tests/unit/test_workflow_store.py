"""
Unit tests for workflow_store (API v2).
Tests get_state, set_state, request_cancel, is_cancel_requested.
"""
import pytest
from app.services.workflow_store import (
    get_state,
    set_state,
    update_state,
    delete_state,
    request_cancel,
    is_cancel_requested,
)


@pytest.fixture(autouse=True)
def clear_store():
    """Clear workflow store before each test to avoid cross-test state."""
    # Store is module-level; we clear by deleting known keys used in tests
    for wfid in ["wf-test-1", "wf-test-2", "wf-cancel-me"]:
        delete_state(wfid)
    yield
    for wfid in ["wf-test-1", "wf-test-2", "wf-cancel-me"]:
        delete_state(wfid)


def test_get_state_not_found():
    assert get_state("wf-nonexistent") is None


def test_set_state_and_get_state():
    set_state("wf-test-1", {"workflow_id": "wf-test-1", "status": "running"})
    state = get_state("wf-test-1")
    assert state is not None
    assert state["workflow_id"] == "wf-test-1"
    assert state["status"] == "running"
    assert "updated_at" in state


def test_update_state_creates_if_missing():
    update_state("wf-test-2", status="pending")
    state = get_state("wf-test-2")
    assert state is not None
    assert state["workflow_id"] == "wf-test-2"
    assert state["status"] == "pending"


def test_update_state_merges():
    set_state("wf-test-1", {"workflow_id": "wf-test-1", "status": "pending"})
    update_state("wf-test-1", status="running", current_agent="observation")
    state = get_state("wf-test-1")
    assert state["status"] == "running"
    assert state["current_agent"] == "observation"


def test_delete_state():
    set_state("wf-test-1", {"workflow_id": "wf-test-1"})
    assert get_state("wf-test-1") is not None
    ok = delete_state("wf-test-1")
    assert ok is True
    assert get_state("wf-test-1") is None
    ok2 = delete_state("wf-test-1")
    assert ok2 is False


def test_request_cancel_returns_false_for_unknown():
    assert request_cancel("wf-nonexistent") is False


def test_request_cancel_sets_flag_and_returns_true():
    set_state("wf-cancel-me", {"workflow_id": "wf-cancel-me", "status": "running"})
    assert is_cancel_requested("wf-cancel-me") is False
    ok = request_cancel("wf-cancel-me")
    assert ok is True
    assert is_cancel_requested("wf-cancel-me") is True
    state = get_state("wf-cancel-me")
    assert state.get("cancel_requested") is True


def test_is_cancel_requested_false_for_unknown():
    assert is_cancel_requested("wf-unknown") is False


def test_is_cancel_requested_false_when_not_set():
    set_state("wf-test-1", {"workflow_id": "wf-test-1", "status": "pending"})
    assert is_cancel_requested("wf-test-1") is False
