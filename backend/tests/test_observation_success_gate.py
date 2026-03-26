"""Tests for guided observation strict success gate (browser-use done / goal) and helpers."""
from types import SimpleNamespace

import pytest

from agents.observation_agent import history_has_browser_use_done_success


class _MO:
    """Minimal model_output with a done action."""

    def __init__(self, done_success: bool):
        self.action = SimpleNamespace(done=SimpleNamespace(success=done_success))


def _hist_item(model_output):
    return SimpleNamespace(model_output=model_output)


def test_history_has_browser_use_done_success_true():
    h = SimpleNamespace(
        history=[
            _hist_item(_MO(False)),
            _hist_item(_MO(True)),
        ]
    )
    assert history_has_browser_use_done_success(h) is True


def test_history_has_browser_use_done_success_false():
    h = SimpleNamespace(history=[_hist_item(_MO(False))])
    assert history_has_browser_use_done_success(h) is False


def test_history_has_browser_use_done_success_dict_action():
    mo = SimpleNamespace()
    mo.actions = [{"done": {"success": True, "text": "ok"}}]
    h = SimpleNamespace(history=[SimpleNamespace(model_output=mo)])
    assert history_has_browser_use_done_success(h) is True


def test_history_empty():
    assert history_has_browser_use_done_success(SimpleNamespace(history=[])) is False
    assert history_has_browser_use_done_success(None) is False
