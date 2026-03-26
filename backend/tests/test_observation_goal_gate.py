"""Orchestration gate: Requirements only after goal_reached when user_instruction is set."""
from app.services.orchestration_service import observation_goal_required_and_met


def test_no_instruction_skips_gate():
    ok, msg = observation_goal_required_and_met(
        {"page_context": {"goal_reached": False}},
        "",
    )
    assert ok is True
    assert msg == ""


def test_instruction_requires_goal_true():
    ok, msg = observation_goal_required_and_met(
        {
            "user_instruction": "Complete purchase",
            "page_context": {"goal_reached": False},
            "navigation_flow": {"goal_reached": False},
        },
        "Complete purchase",
    )
    assert ok is False
    assert "goal_reached=false" in msg.lower()


def test_goal_true_passes():
    ok, msg = observation_goal_required_and_met(
        {
            "page_context": {"goal_reached": True, "user_instruction": "x"},
        },
        "",
    )
    assert ok is True


def test_instruction_from_page_context_only():
    ok, msg = observation_goal_required_and_met(
        {
            "page_context": {"goal_reached": False, "user_instruction": "Finish flow"},
        },
        "",
    )
    assert ok is False
