"""
Test Suite Schema and CRUD Operations
Allows grouping test cases into suites for batch execution
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class TestSuiteBase(BaseModel):
    """Base schema for test suite."""
    name: str = Field(..., min_length=1, max_length=255, description="Suite name")
    description: Optional[str] = Field(None, description="Suite description")
    tags: Optional[List[str]] = Field(None, description="Suite tags for categorization")


class TestSuiteCreate(TestSuiteBase):
    """Schema for creating a test suite."""
    test_case_ids: List[int] = Field(..., min_length=1, description="List of test case IDs in execution order")


class TestSuiteUpdate(BaseModel):
    """Schema for updating a test suite."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    test_case_ids: Optional[List[int]] = Field(None, min_length=1)


class TestSuiteItemResponse(BaseModel):
    """Schema for a test case item in a suite."""
    id: int
    test_case_id: int
    execution_order: int
    
    class Config:
        from_attributes = True


class TestSuiteResponse(TestSuiteBase):
    """Schema for test suite API response."""
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    items: Optional[List[TestSuiteItemResponse]] = None
    
    class Config:
        from_attributes = True


class TestSuiteListResponse(BaseModel):
    """Schema for list of test suites."""
    items: List[TestSuiteResponse]
    total: int
    skip: int
    limit: int


class SuiteExecutionRequest(BaseModel):
    """Schema for executing a test suite."""
    browser: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$")
    environment: str = Field(default="dev", max_length=50)
    triggered_by: str = Field(default="manual", max_length=50)
    stop_on_failure: bool = Field(default=False, description="Stop execution if a test fails")
    parallel: bool = Field(default=False, description="Run tests in parallel (future feature)")


class SuiteExecutionResponse(BaseModel):
    """Schema for suite execution response."""
    id: int
    suite_id: int
    status: str
    message: str
    total_tests: int
    queued_executions: List[int]  # List of execution IDs
    
    class Config:
        from_attributes = True
