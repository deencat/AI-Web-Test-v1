"""Retire generated test cases when an initiative is superseded (replace)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.crud.test_case import get_test_case, update_test_case
from app.models.test_case import TestCase, TestStatus
from app.models.test_schedule import TestSchedule
from app.schemas.test_case import TestCaseUpdate


def is_test_case_retired(test_metadata: Optional[dict[str, Any]]) -> bool:
    if not test_metadata or not isinstance(test_metadata, dict):
        return False
    return bool(test_metadata.get("retired"))


def retire_test_case(
    db: Session,
    test_case_id: int,
    *,
    program_slug: str,
    initiative_id: str,
    retired_by_initiative_id: str,
    reason: Optional[str] = None,
) -> bool:
    """Mark a test case retired and disable its schedules. Returns True if updated."""
    tc = get_test_case(db, test_case_id)
    if not tc:
        return False

    meta = dict(tc.test_metadata) if isinstance(tc.test_metadata, dict) else {}
    if is_test_case_retired(meta):
        return False

    now = datetime.now(timezone.utc).isoformat()
    meta.update(
        {
            "retired": True,
            "retired_at": now,
            "retired_by_initiative_id": retired_by_initiative_id,
            "retired_reason": reason
            or f"Superseded by initiative {retired_by_initiative_id} (relationship=replace)",
            "program_slug": program_slug,
            "initiative_id": initiative_id,
        }
    )
    tags = [t for t in (tc.tags or []) if t != "regression"]
    if "retired" not in tags:
        tags.append("retired")

    update_test_case(
        db,
        test_case_id,
        TestCaseUpdate(status=TestStatus.SKIPPED, tags=tags, test_metadata=meta),
    )

    db.query(TestSchedule).filter(
        TestSchedule.test_case_id == test_case_id,
        TestSchedule.enabled.is_(True),
    ).update({"enabled": False})
    db.commit()
    return True


def retire_test_cases_for_initiative(
    db: Session,
    *,
    program_slug: str,
    initiative_id: str,
    retired_by_initiative_id: str,
    reference_test_ids: Optional[set[int]] = None,
) -> int:
    """Retire test cases linked to a superseded initiative."""
    retired_ids: set[int] = set()
    reason = f"Superseded by initiative {retired_by_initiative_id} (relationship=replace)"

    for test_id in reference_test_ids or set():
        if retire_test_case(
            db,
            test_id,
            program_slug=program_slug,
            initiative_id=initiative_id,
            retired_by_initiative_id=retired_by_initiative_id,
            reason=reason,
        ):
            retired_ids.add(test_id)

    rows = db.query(TestCase).filter(TestCase.test_metadata.isnot(None)).all()
    for tc in rows:
        if tc.id in retired_ids:
            continue
        meta = tc.test_metadata if isinstance(tc.test_metadata, dict) else {}
        if meta.get("program_slug") != program_slug:
            continue
        if meta.get("initiative_id") != initiative_id:
            continue
        if is_test_case_retired(meta):
            continue
        if retire_test_case(
            db,
            tc.id,
            program_slug=program_slug,
            initiative_id=initiative_id,
            retired_by_initiative_id=retired_by_initiative_id,
            reason=reason,
        ):
            retired_ids.add(tc.id)

    return len(retired_ids)
