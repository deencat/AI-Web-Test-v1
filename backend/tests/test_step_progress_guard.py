"""Unit tests for confirm-step progress detection."""

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.step_progress_guard import StepProgressSnapshot, has_confirm_step_progress


def test_has_confirm_step_progress_returns_false_when_modal_state_is_unchanged():
    before = StepProgressSnapshot(
        url="https://web.three.com.hk/subscribe",
        modal_signature="enter the referrer mobile number to earn rewards next",
        body_signature="",
    )
    after = StepProgressSnapshot(
        url="https://web.three.com.hk/subscribe",
        modal_signature="enter the referrer mobile number to earn rewards next",
        body_signature="",
    )

    assert has_confirm_step_progress(
        before,
        after,
        "Step 14: Click the 'Confirm' button to confirm the subscription again",
    ) is False


def test_has_confirm_step_progress_returns_true_when_modal_changes():
    before = StepProgressSnapshot(
        url="https://web.three.com.hk/subscribe",
        modal_signature="select mobile number confirm",
        body_signature="",
    )
    after = StepProgressSnapshot(
        url="https://web.three.com.hk/subscribe",
        modal_signature="enter the referrer mobile number to earn rewards next",
        body_signature="",
    )

    assert has_confirm_step_progress(
        before,
        after,
        "Step 13: Click the 'Confirm' button to confirm the subscription details",
    ) is True