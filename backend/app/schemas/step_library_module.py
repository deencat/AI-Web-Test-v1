"""
Pydantic schemas for StepLibraryModule — Sprint 10.11.
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class StepLibraryModuleCreate(BaseModel):
    """Request body for creating a new step library module."""

    name: str = Field(..., min_length=1, max_length=100, description="Slug identifier, e.g. 'login_three_hk'")
    display_name: str = Field(..., min_length=1, max_length=255, description="Human-readable label")
    description: Optional[str] = Field(None, description="Optional description of the module")
    steps: List[Any] = Field(..., min_length=1, description="List of step strings or step dicts")
    parameters: Optional[List[str]] = Field(None, description="Declared parameter names for substitution")
    tags: Optional[List[str]] = Field(None, description="Searchable tags")


class StepLibraryModuleUpdate(BaseModel):
    """Request body for updating an existing module — all fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[Any]] = Field(None, min_length=1)
    parameters: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class StepLibraryModuleResponse(BaseModel):
    """Response body for a step library module."""

    id: int
    user_id: int
    name: str
    display_name: str
    description: Optional[str]
    steps: List[Any]
    parameters: Optional[List[str]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    usage_count: Optional[int] = None

    model_config = {"from_attributes": True}
