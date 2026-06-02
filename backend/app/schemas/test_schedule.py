"""Pydantic schemas for test schedules."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator


class TestScheduleCreate(BaseModel):
    test_case_id: int
    name: Optional[str] = None

    schedule_type: str = "interval"       # 'interval' | 'cron'
    interval_minutes: Optional[int] = None
    cron_expression: Optional[str] = None

    browser: str = "chromium"
    environment: str = "dev"
    base_url: Optional[str] = None

    enabled: bool = True

    @field_validator("schedule_type")
    @classmethod
    def validate_schedule_type(cls, v: str) -> str:
        if v not in ("interval", "cron"):
            raise ValueError("schedule_type must be 'interval' or 'cron'")
        return v

    @field_validator("interval_minutes")
    @classmethod
    def validate_interval(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("interval_minutes must be at least 1")
        return v

    @model_validator(mode="after")
    def validate_schedule_params(self) -> "TestScheduleCreate":
        if self.schedule_type == "interval" and not self.interval_minutes:
            raise ValueError("interval_minutes is required when schedule_type is 'interval'")
        if self.schedule_type == "cron" and not self.cron_expression:
            raise ValueError("cron_expression is required when schedule_type is 'cron'")
        return self


class TestScheduleUpdate(BaseModel):
    name: Optional[str] = None
    schedule_type: Optional[str] = None
    interval_minutes: Optional[int] = None
    cron_expression: Optional[str] = None
    browser: Optional[str] = None
    environment: Optional[str] = None
    base_url: Optional[str] = None
    enabled: Optional[bool] = None


class TestScheduleResponse(BaseModel):
    id: int
    user_id: int
    test_case_id: int
    name: Optional[str]
    schedule_type: str
    interval_minutes: Optional[int]
    cron_expression: Optional[str]
    browser: str
    environment: str
    base_url: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]

    # Human-readable description of the schedule
    schedule_description: Optional[str] = None

    model_config = {"from_attributes": True}
