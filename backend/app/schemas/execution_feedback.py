"""Pydantic schemas for execution feedback."""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ============================================================================
# Execution Feedback Schemas
# ============================================================================

class ExecutionFeedbackBase(BaseModel):
    """Base execution feedback schema."""
    execution_id: int = Field(..., description="Test execution ID")
    step_index: Optional[int] = Field(None, description="Failed step index (0-based), null for execution-level feedback")
    failure_type: Optional[str] = Field(None, max_length=100, description="Type of failure: selector_not_found, timeout, assertion_failed, etc.")
    error_message: Optional[str] = Field(None, description="Full error message")
    screenshot_url: Optional[str] = Field(None, max_length=500, description="Screenshot path")
    page_url: Optional[str] = Field(None, max_length=2000, description="URL where failure occurred")
    browser_type: Optional[str] = Field(None, max_length=50, description="Browser: chromium, firefox, webkit")
    failed_selector: Optional[str] = Field(None, max_length=2000, description="Selector that failed")
    selector_type: Optional[str] = Field(None, max_length=50, description="Selector type: css, xpath, text, aria")
    notes: Optional[str] = Field(None, description="Human notes about the failure")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class ExecutionFeedbackCreate(ExecutionFeedbackBase):
    """Schema for creating execution feedback (internal use by execution service)."""
    page_html_snapshot: Optional[str] = Field(None, description="HTML snapshot for pattern analysis")
    viewport_width: Optional[int] = Field(None, description="Viewport width")
    viewport_height: Optional[int] = Field(None, description="Viewport height")
    step_duration_ms: Optional[int] = Field(None, description="Step duration in milliseconds")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    network_requests: Optional[int] = Field(None, description="Number of network requests")


class ExecutionFeedbackUpdate(BaseModel):
    """Schema for updating execution feedback."""
    failure_type: Optional[str] = Field(None, max_length=100)
    error_message: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    anomaly_type: Optional[str] = Field(None, max_length=100)


class CorrectionSubmit(BaseModel):
    """Schema for submitting a correction to a feedback item."""
    corrected_step: Dict[str, Any] = Field(..., description="Corrected step data (JSON)")
    correction_source: str = Field(..., max_length=50, description="Source: human, ai_suggestion, auto_applied")
    correction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    notes: Optional[str] = Field(None, description="Notes about the correction")


class ExecutionFeedbackResponse(ExecutionFeedbackBase):
    """Schema for execution feedback response."""
    id: int
    page_html_snapshot: Optional[str] = None  # Can be large, only return if needed
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    corrected_step: Optional[Dict[str, Any]] = None
    correction_source: Optional[str] = None
    correction_confidence: Optional[float] = None
    correction_applied_at: Optional[datetime] = None
    corrected_by_user_id: Optional[int] = None
    step_duration_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    network_requests: Optional[int] = None
    is_anomaly: bool
    anomaly_score: Optional[float] = None
    anomaly_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionFeedbackListItem(BaseModel):
    """Schema for feedback in list view (without HTML snapshot for performance)."""
    id: int
    execution_id: int
    step_index: Optional[int]
    failure_type: Optional[str]
    error_message: Optional[str]
    screenshot_url: Optional[str]
    page_url: Optional[str]
    browser_type: Optional[str]
    failed_selector: Optional[str]
    selector_type: Optional[str]
    correction_source: Optional[str]
    correction_confidence: Optional[float]
    is_anomaly: bool
    anomaly_score: Optional[float]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionFeedbackListResponse(BaseModel):
    """Schema for paginated feedback list."""
    items: List[ExecutionFeedbackListItem]
    total: int
    skip: int
    limit: int


class ExecutionFeedbackStats(BaseModel):
    """Statistics about execution feedback."""
    total_feedback: int
    total_failures: int
    total_corrected: int
    total_anomalies: int
    correction_rate: float  # Percentage
    top_failure_types: List[Dict[str, Any]]  # List of {type, count}
    top_failed_selectors: List[Dict[str, Any]]  # List of {selector, count}
