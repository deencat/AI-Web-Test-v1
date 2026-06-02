"""CRUD operations for test schedules."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.test_schedule import TestSchedule
from app.schemas.test_schedule import TestScheduleCreate, TestScheduleUpdate


def create_schedule(db: Session, data: TestScheduleCreate, user_id: int) -> TestSchedule:
    schedule = TestSchedule(
        user_id=user_id,
        test_case_id=data.test_case_id,
        name=data.name,
        schedule_type=data.schedule_type,
        interval_minutes=data.interval_minutes,
        cron_expression=data.cron_expression,
        browser=data.browser,
        environment=data.environment,
        base_url=data.base_url,
        enabled=data.enabled,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def get_schedule(db: Session, schedule_id: int) -> Optional[TestSchedule]:
    return db.query(TestSchedule).filter(TestSchedule.id == schedule_id).first()


def list_schedules_for_user(db: Session, user_id: int) -> List[TestSchedule]:
    return db.query(TestSchedule).filter(TestSchedule.user_id == user_id).all()


def list_schedules_for_test(db: Session, test_case_id: int, user_id: int) -> List[TestSchedule]:
    return (
        db.query(TestSchedule)
        .filter(TestSchedule.test_case_id == test_case_id, TestSchedule.user_id == user_id)
        .all()
    )


def list_all_enabled_schedules(db: Session) -> List[TestSchedule]:
    return db.query(TestSchedule).filter(TestSchedule.enabled == True).all()  # noqa: E712


def update_schedule(db: Session, schedule: TestSchedule, data: TestScheduleUpdate) -> TestSchedule:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    schedule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, schedule: TestSchedule) -> None:
    db.delete(schedule)
    db.commit()


def mark_triggered(db: Session, schedule_id: int) -> None:
    schedule = db.query(TestSchedule).filter(TestSchedule.id == schedule_id).first()
    if schedule:
        schedule.last_triggered_at = datetime.utcnow()
        db.commit()
