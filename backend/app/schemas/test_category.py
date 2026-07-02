"""Pydantic schemas for test category API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TestCategoryBase(BaseModel):
    """Shared fields for test categories."""

    name: str = Field(..., min_length=1, max_length=100, description="Category display name")
    description: Optional[str] = Field(None, description="Optional category description")
    color: str = Field(default="#3B82F6", max_length=20, description="Hex color for UI badge")
    sort_order: int = Field(default=0, description="Sort order in sidebar")


class TestCategoryCreate(TestCategoryBase):
    """Schema for creating a test category."""


class TestCategoryUpdate(BaseModel):
    """Schema for updating a test category — all fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    sort_order: Optional[int] = None


class TestCategoryResponse(TestCategoryBase):
    """Schema for a single test category."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TestCategoryListItem(TestCategoryResponse):
    """Category in list responses with assigned test count."""

    test_count: int = 0


class TestCategoryListResponse(BaseModel):
    """List of categories for the current user."""

    items: List[TestCategoryListItem]


class TestCategorySummary(BaseModel):
    """Nested category summary on test case responses."""

    id: int
    name: str
    color: str
    model_config = ConfigDict(from_attributes=True)
