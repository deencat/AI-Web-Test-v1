"""Compaction and conversion for observed flow_steps."""
from app.utils.flow_steps_to_test_strings import (
    compact_observed_flow_steps,
    flow_steps_to_natural_language_steps,
)


def test_compact_observed_flow_steps_drops_consecutive_duplicates():
    steps = [
        {"order": 1, "action": "click", "target": "OK", "page_url": "https://x.com"},
        {"order": 2, "action": "click", "target": "OK", "page_url": "https://x.com"},
        {"order": 3, "action": "input", "target": "email", "page_url": "https://x.com"},
    ]
    out = compact_observed_flow_steps(steps)
    assert len(out) == 2
    assert out[0]["order"] == 1
    assert out[1]["order"] == 3


def test_flow_steps_to_natural_language_steps_dedupe_flag():
    steps = [
        {"order": 1, "action": "navigate", "target": "https://a.com", "page_url": "https://a.com"},
        {"order": 2, "action": "navigate", "target": "https://a.com", "page_url": "https://a.com"},
        {"order": 3, "action": "click", "target": "Go", "page_url": "https://a.com"},
    ]
    nl = flow_steps_to_natural_language_steps(steps, {}, dedupe_consecutive=True)
    assert nl is not None
    assert len(nl) == 2
    assert "Navigate" in nl[0]
    assert "Go" in nl[1]

