"""Pydantic schemas for debug sessions."""
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.debug_session import DebugMode, DebugSessionStatus


# ============================================================================
# Debug Session Request/Response Schemas
# ============================================================================

class DebugSessionStartRequest(BaseModel):
    """Request to start a debug session."""
    execution_id: int = Field(..., description="Test execution ID to debug")
    target_step_number: int = Field(..., ge=1, description="Step number to debug (1-based)")
    mode: DebugMode = Field(..., description="Debug mode: auto (AI setup) or manual (user setup)")
    
    model_config = ConfigDict(use_enum_values=True)


class DebugSessionStartResponse(BaseModel):
    """Response after starting a debug session."""
    session_id: str = Field(..., description="Unique session ID")
    mode: DebugMode
    status: DebugSessionStatus
    target_step_number: int
    prerequisite_steps_count: int
    message: str
    devtools_url: Optional[str] = Field(None, description="DevTools URL for browser inspection (if available)")
    
    model_config = ConfigDict(use_enum_values=True)


class DebugStepExecuteRequest(BaseModel):
    """Request to execute the target step in a debug session."""
    session_id: str = Field(..., description="Debug session ID")


class DebugStepExecuteResponse(BaseModel):
    """Response after executing a debug step."""
    session_id: str
    step_number: int
    success: bool
    error_message: Optional[str]
    screenshot_path: Optional[str]
    duration_seconds: float
    tokens_used: int
    iterations_count: int = Field(..., description="Total iterations of target step so far")
    
    model_config = ConfigDict(from_attributes=True)


class DebugSessionStatusResponse(BaseModel):
    """Debug session status response."""
    session_id: str
    mode: DebugMode
    status: DebugSessionStatus
    target_step_number: int
    prerequisite_steps_count: int
    current_step: Optional[int]
    setup_completed: bool
    tokens_used: int
    iterations_count: int
    started_at: datetime
    setup_completed_at: Optional[datetime]
    last_activity_at: datetime
    ended_at: Optional[datetime]
    error_message: Optional[str]
    devtools_url: Optional[str] = Field(None, description="DevTools URL for browser inspection")
    browser_pid: Optional[int]
    
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class DebugSessionStopRequest(BaseModel):
    """Request to stop a debug session."""
    session_id: str = Field(..., description="Debug session ID")


class DebugSessionStopResponse(BaseModel):
    """Response after stopping a debug session."""
    session_id: str
    status: DebugSessionStatus
    total_tokens_used: int
    total_iterations: int
    duration_seconds: float
    message: str
    
    model_config = ConfigDict(use_enum_values=True)


class ManualSetupInstruction(BaseModel):
    """Single manual setup instruction."""
    step_number: int
    action: str = Field(..., description="Action to perform (e.g., 'click', 'type', 'navigate')")
    description: str = Field(..., description="Human-readable instruction")
    target: Optional[str] = Field(None, description="Target element description")
    value: Optional[str] = Field(None, description="Value to input (for 'type' actions)")


class DebugSessionInstructionsResponse(BaseModel):
    """Manual setup instructions for a debug session."""
    session_id: str
    mode: DebugMode
    target_step_number: int
    prerequisite_steps: List[ManualSetupInstruction]
    instructions_summary: str = Field(..., description="Human-readable summary of setup steps")
    estimated_time_minutes: int = Field(..., description="Estimated time to complete manual setup")
    devtools_url: Optional[str] = Field(None, description="DevTools URL for browser inspection")
    
    model_config = ConfigDict(use_enum_values=True)


class DebugSessionConfirmSetupRequest(BaseModel):
    """Request to confirm manual setup is complete."""
    session_id: str = Field(..., description="Debug session ID")
    setup_completed: bool = Field(..., description="Whether user completed manual setup steps")


class DebugSessionConfirmSetupResponse(BaseModel):
    """Response after confirming manual setup."""
    session_id: str
    status: DebugSessionStatus
    message: str
    ready_for_debug: bool
    
    model_config = ConfigDict(use_enum_values=True)


# ============================================================================
# Debug Session List/Search Schemas
# ============================================================================

class DebugSessionListItem(BaseModel):
    """Debug session list item."""
    id: int
    session_id: str
    mode: DebugMode
    status: DebugSessionStatus
    target_step_number: int
    tokens_used: int
    iterations_count: int
    started_at: datetime
    ended_at: Optional[datetime]
    
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class DebugSessionListResponse(BaseModel):
    """List of debug sessions."""
    total: int
    sessions: List[DebugSessionListItem]
    
    model_config = ConfigDict(from_attributes=True)


class DebugNextStepResponse(BaseModel):
    """Response after executing next step in sequence."""
    session_id: str
    step_number: int = Field(..., description="Current step number that was executed")
    step_description: str = Field(..., description="Description of the executed step")
    success: bool
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    duration_seconds: float
    tokens_used: int
    has_more_steps: bool = Field(..., description="Whether there are more steps to execute")
    next_step_preview: Optional[str] = Field(None, description="Description of next step (if available)")
    total_steps: int = Field(..., description="Total number of steps in test case")
    
    model_config = ConfigDict(from_attributes=True)
