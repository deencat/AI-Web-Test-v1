"""
Unit tests for execution_cancel_store.
"""
import pytest
from concurrent.futures import ThreadPoolExecutor

from app.services.execution_cancel_store import (
    register_cancel,
    request_cancel,
    is_cancel_requested,
    clear_cancel,
)


@pytest.fixture(autouse=True)
def clear_store():
    for eid in [1, 2, 99, 100]:
        clear_cancel(eid)
    yield
    for eid in [1, 2, 99, 100]:
        clear_cancel(eid)


def test_register_cancel_creates_key():
    register_cancel(1)
    assert is_cancel_requested(1) is False


def test_request_cancel_auto_registers_and_sets_flag():
    assert is_cancel_requested(99) is False
    ok = request_cancel(99)
    assert ok is True
    assert is_cancel_requested(99) is True


def test_request_cancel_on_registered_execution():
    register_cancel(2)
    ok = request_cancel(2)
    assert ok is True
    assert is_cancel_requested(2) is True


def test_clear_cancel_removes_key():
    register_cancel(1)
    request_cancel(1)
    assert clear_cancel(1) is True
    assert is_cancel_requested(1) is False
    assert clear_cancel(1) is False


def test_concurrent_request_cancel():
    register_cancel(100)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: request_cancel(100), range(20)))
    assert all(results)
    assert is_cancel_requested(100) is True
