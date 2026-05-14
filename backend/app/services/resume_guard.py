"""
Resume guard — Sprint 10.12 Feature B.

validate_resume_point raises HTTP 422 for invalid resume requests:
  1. Any step before the resume point FAILED in the source execution.
  2. Any step before the resume point is an OTP step (OTP is consumed, cannot be re-used).
"""
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.test_execution import ExecutionResult, TestExecutionStep
from app.services.email_otp_service import is_otp_step


def validate_resume_point(
    db: Session,
    resume_from_execution_id: int,
    start_from_step: int,
    steps: List,
) -> None:
    """
    Validate that resuming at start_from_step from resume_from_execution_id is safe.

    Args:
        db: SQLAlchemy session
        resume_from_execution_id: The execution whose snapshots + step results to inspect
        start_from_step: 1-based step index to resume from (steps 1..start_from_step-1 are skipped)
        steps: The step list for the incoming run (used for OTP detection)

    Raises:
        HTTPException 422: When a prior step failed OR an OTP step would be skipped
    """
    prior_step_count = start_from_step - 1

    # Fetch step records for the source execution up to start_from_step-1
    prior_results = (
        db.query(TestExecutionStep)
        .filter(
            TestExecutionStep.execution_id == resume_from_execution_id,
            TestExecutionStep.step_number < start_from_step,
        )
        .all()
    )

    # Guard 1: any prior step failed
    for step_record in prior_results:
        if step_record.result in (ExecutionResult.FAIL, ExecutionResult.ERROR):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot resume: step {step_record.step_number} failed in the source execution "
                    f"(execution_id={resume_from_execution_id}). Choose a safe resume point where all "
                    "prior steps passed."
                ),
            )

    # Guard 2: any step in the skipped range is an OTP step
    for step_idx in range(prior_step_count):
        step_desc = steps[step_idx] if step_idx < len(steps) else ""
        step_text = step_desc.get("description", step_desc) if isinstance(step_desc, dict) else str(step_desc)
        if is_otp_step(step_text):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot skip OTP steps — the OTP delivered during step {step_idx + 1} of the "
                    "original run is already consumed. Trigger a new full run from before the OTP step."
                ),
            )
