"""Pydantic schemas for test execution."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.test_execution import ExecutionStatus, ExecutionResult


# ============================================================================
# Execution Step Schemas
# ============================================================================

class TestExecutionStepBase(BaseModel):
    """Base execution step schema."""
    step_number: int = Field(..., ge=1, description="Step number (1-based)")
    step_description: str = Field(..., min_length=1, max_length=1000, description="Step description")
    expected_result: Optional[str] = Field(None, description="Expected result")
    is_critical: bool = Field(default=False, description="Whether step failure stops execution")


class TestExecutionStepCreate(TestExecutionStepBase):
    """Schema for creating an execution step (internal use)."""
    execution_id: int
    result: ExecutionResult = ExecutionResult.SKIP
    actual_result: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    screenshot_path: Optional[str] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    retry_count: int = 0


class TestExecutionStepResponse(TestExecutionStepBase):
    """Schema for execution step response."""
    id: int
    execution_id: int
    result: ExecutionResult
    actual_result: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    screenshot_path: Optional[str]
    screenshot_before: Optional[str]
    screenshot_after: Optional[str]
    retry_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Test Execution Schemas
# ============================================================================

class TestExecutionBase(BaseModel):
    """Base test execution schema."""
    test_case_id: int = Field(..., description="Test case ID to execute")
    browser: Optional[str] = Field(None, max_length=50, description="Browser: chromium, firefox, webkit")
    environment: Optional[str] = Field(None, max_length=50, description="Environment: dev, staging, production")
    base_url: Optional[str] = Field(None, max_length=500, description="Base URL for test execution")


class TestExecutionCreate(TestExecutionBase):
    """Schema for creating a test execution."""
    triggered_by: Optional[str] = Field(None, max_length=50, description="Trigger: manual, scheduled, ci_cd, webhook")
    trigger_details: Optional[str] = Field(None, description="Additional trigger details (JSON)")
    browser_profile_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Browser profile data (cookies, localStorage, sessionStorage) for session persistence"
    )


class TestExecutionUpdate(BaseModel):
    """Schema for updating a test execution."""
    status: Optional[ExecutionStatus] = None
    result: Optional[ExecutionResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    total_steps: Optional[int] = None
    passed_steps: Optional[int] = None
    failed_steps: Optional[int] = None
    skipped_steps: Optional[int] = None
    console_log: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None


class TestExecutionResponse(TestExecutionBase):
    """Schema for test execution response."""
    id: int
    status: ExecutionStatus
    result: Optional[ExecutionResult]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    console_log: Optional[str]
    error_message: Optional[str]
    screenshot_path: Optional[str]
    video_path: Optional[str]
    triggered_by: Optional[str]
    trigger_details: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TestExecutionDetailResponse(TestExecutionResponse):
    """Schema for detailed execution response with steps."""
    steps: List[TestExecutionStepResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class TestExecutionListItem(BaseModel):
    """Schema for execution in list view (without logs/steps)."""
    id: int
    test_case_id: int
    status: ExecutionStatus
    result: Optional[ExecutionResult]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    browser: Optional[str]
    environment: Optional[str]
    triggered_by: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TestExecutionListResponse(BaseModel):
    """Schema for paginated execution list."""
    items: List[TestExecutionListItem]
    total: int
    skip: int
    limit: int


# ============================================================================
# Statistics Schemas
# ============================================================================

class ExecutionStatistics(BaseModel):
    """Schema for execution statistics."""
    total_executions: int
    by_status: dict  # status: count
    by_result: dict  # result: count
    by_browser: dict  # browser: count
    by_environment: dict  # environment: count
    pass_rate: float  # Percentage of passed executions
    average_duration_seconds: Optional[float]
    total_duration_hours: float
    executions_last_24h: int
    executions_last_7d: int
    executions_last_30d: int
    most_executed_tests: Optional[List[dict]]  # Top 5 most executed test cases


# ============================================================================
# Execution Request Schemas
# ============================================================================

class ExecutionStartRequest(BaseModel):
    """Schema for starting a test execution."""
    browser: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$", description="Browser to use")
    environment: str = Field(default="dev", max_length=50, description="Target environment")
    base_url: Optional[str] = Field(None, max_length=500, description="Base URL (overrides test case URL)")
    triggered_by: str = Field(default="manual", max_length=50, description="Execution trigger")
    browser_profile_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Browser profile data (cookies, localStorage, sessionStorage) for session persistence"
    )


class ExecutionStartResponse(BaseModel):
    """Schema for execution start response."""
    id: int
    test_case_id: int
    status: ExecutionStatus
    message: str = "Execution started"
    
    model_config = ConfigDict(from_attributes=True)

