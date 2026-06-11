"""Pydantic schemas for journey registry and backlog (HF-2)."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JourneyRegistryProjectResponse(BaseModel):
    project: str
    reqiq_project_id: Optional[str] = None
    default_env_config: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class JourneyRegistryEntryBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=128)
    project: str = Field(..., min_length=1, max_length=128)
    name: str
    feature_url: str
    tags: Optional[list[str]] = None
    capability_keys: Optional[list[str]] = None
    reference_test_id: Optional[int] = None
    requires_login: bool = False
    stop_at_page_hint: Optional[str] = None
    extra_config: Optional[dict[str, Any]] = None


class JourneyRegistryEntryCreate(JourneyRegistryEntryBase):
    pass


class JourneyRegistryEntryUpdate(BaseModel):
    name: Optional[str] = None
    feature_url: Optional[str] = None
    tags: Optional[list[str]] = None
    capability_keys: Optional[list[str]] = None
    reference_test_id: Optional[int] = None
    requires_login: Optional[bool] = None
    stop_at_page_hint: Optional[str] = None
    extra_config: Optional[dict[str, Any]] = None


class JourneyRegistryEntryResponse(JourneyRegistryEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JourneyRegistryListResponse(BaseModel):
    project_meta: Optional[JourneyRegistryProjectResponse] = None
    items: list[JourneyRegistryEntryResponse]
    total: int


class JourneyBacklogEnqueue(BaseModel):
    journey_slug: str
    project: str = "Three-HK"
    priority: int = 0
    params: Optional[dict[str, Any]] = None


class JourneyBacklogItemResponse(BaseModel):
    id: int
    project: str
    journey_slug: str
    status: str
    priority: int
    params: Optional[dict[str, Any]] = None
    factory_job_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JourneyBacklogListResponse(BaseModel):
    items: list[JourneyBacklogItemResponse]
    total: int
