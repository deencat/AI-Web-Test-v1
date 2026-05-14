"""
CRUD helpers for step_session_snapshots — Sprint 10.12 Feature B.

Provides save_step_session_snapshot and get_step_session_snapshot.
"""
import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.test_execution import StepSessionSnapshot


def save_step_session_snapshot(
    db: Session,
    execution_id: int,
    step_number: int,
    page_url: str,
    session_data: Dict[str, Any],
) -> StepSessionSnapshot:
    """
    Persist a browser session snapshot taken after a passing step.

    Args:
        db: SQLAlchemy session
        execution_id: ID of the current test execution
        step_number: 1-based step number that just passed
        page_url: URL of the page when the snapshot was taken
        session_data: Dict with keys cookies, localStorage, sessionStorage, exported_at

    Returns:
        The saved StepSessionSnapshot ORM object
    """
    snap = StepSessionSnapshot(
        execution_id=execution_id,
        step_number=step_number,
        page_url=page_url,
        session_data=json.dumps(session_data) if isinstance(session_data, dict) else session_data,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def get_step_session_snapshot(
    db: Session,
    execution_id: int,
    step_number: int,
) -> Optional[StepSessionSnapshot]:
    """
    Retrieve the session snapshot saved after the given step number.

    Args:
        db: SQLAlchemy session
        execution_id: Execution from which to retrieve the snapshot
        step_number: 1-based step number

    Returns:
        StepSessionSnapshot if found, else None
    """
    return (
        db.query(StepSessionSnapshot)
        .filter(
            StepSessionSnapshot.execution_id == execution_id,
            StepSessionSnapshot.step_number == step_number,
        )
        .first()
    )
