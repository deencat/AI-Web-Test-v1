"""REST API endpoints for test schedules."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.test_schedule import TestScheduleCreate, TestScheduleUpdate, TestScheduleResponse
from app.crud import test_schedule as crud_schedules
from app.crud import test_case as crud_tests
from app.services.scheduler_service import scheduler_service

router = APIRouter()


def _to_response(schedule, svc=scheduler_service) -> TestScheduleResponse:
    resp = TestScheduleResponse.model_validate(schedule)
    resp.schedule_description = svc.describe(
        schedule.schedule_type,
        schedule.interval_minutes,
        schedule.cron_expression,
    )
    return resp


@router.get("/schedules/", response_model=List[TestScheduleResponse], tags=["schedules"])
def list_schedules(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """List all schedules owned by the current user."""
    schedules = crud_schedules.list_schedules_for_user(db, current_user.id)
    return [_to_response(s) for s in schedules]


@router.get("/schedules/tests/{test_case_id}", response_model=List[TestScheduleResponse], tags=["schedules"])
def list_schedules_for_test(
    test_case_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """List all schedules for a specific test case."""
    schedules = crud_schedules.list_schedules_for_test(db, test_case_id, current_user.id)
    return [_to_response(s) for s in schedules]


@router.post("/schedules/", response_model=TestScheduleResponse, status_code=status.HTTP_201_CREATED, tags=["schedules"])
def create_schedule(
    data: TestScheduleCreate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Create a new test schedule."""
    # Verify test case exists and is accessible
    test_case = crud_tests.get_test_case(db, data.test_case_id)
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    if current_user.role != "admin" and test_case.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    schedule = crud_schedules.create_schedule(db, data, current_user.id)

    # Register with APScheduler
    scheduler_service.add_schedule(schedule)

    return _to_response(schedule)


@router.get("/schedules/{schedule_id}", response_model=TestScheduleResponse, tags=["schedules"])
def get_schedule(
    schedule_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    schedule = crud_schedules.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    if schedule.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _to_response(schedule)


@router.put("/schedules/{schedule_id}", response_model=TestScheduleResponse, tags=["schedules"])
def update_schedule(
    schedule_id: int,
    data: TestScheduleUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Update an existing schedule (any field). Re-registers the APScheduler job."""
    schedule = crud_schedules.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    if schedule.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updated = crud_schedules.update_schedule(db, schedule, data)

    # Re-register (or remove if now disabled)
    if updated.enabled:
        scheduler_service.add_schedule(updated)
    else:
        scheduler_service.remove_schedule(schedule_id)

    return _to_response(updated)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["schedules"])
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Delete a schedule and stop its timer."""
    schedule = crud_schedules.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    if schedule.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    scheduler_service.remove_schedule(schedule_id)
    crud_schedules.delete_schedule(db, schedule)


@router.post("/schedules/{schedule_id}/toggle", response_model=TestScheduleResponse, tags=["schedules"])
def toggle_schedule(
    schedule_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """Toggle a schedule on or off without deleting it."""
    schedule = crud_schedules.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    if schedule.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    updated = crud_schedules.update_schedule(
        db, schedule, TestScheduleUpdate(enabled=not schedule.enabled)
    )

    if updated.enabled:
        scheduler_service.add_schedule(updated)
    else:
        scheduler_service.remove_schedule(schedule_id)

    return _to_response(updated)
