"""
Workflow Schemas for API v2 - Agent Workflow Management

These schemas define the request/response models for the agent workflow API.
Used for triggering workflows, tracking progress, and retrieving results.

Reference: Sprint 10 - Frontend Integration & Real-time Agent Progress
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GenerateTestsRequest(BaseModel):
    """Request to generate tests using full 4-agent workflow (single entry)."""
    url: HttpUrl = Field(..., description="Target URL to analyze and generate tests for")
    user_instruction: Optional[str] = Field(
        None,
        description="Optional user instructions for test generation (e.g., 'Test purchase flow for 5G plan')"
    )
    depth: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Crawl depth (1=current page, 2=include links, 3=deep crawl)"
    )
    login_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="Website login: {'username': '...', 'password': '...'} or {'email': '...', 'password': '...'}"
    )
    gmail_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="Gmail login for OTP verification: {'email': '...', 'password': '...'}. Used when flow requires checking email for OTP."
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/login",
                "user_instruction": "Test login flow with invalid credentials",
                "depth": 1,
                "login_credentials": {
                    "username": "test@example.com",
                    "password": "password123"
                },
                "gmail_credentials": {
                    "email": "myaccount@gmail.com",
                    "password": "gmail-app-password"
                }
            }
        }
    )


# ---- Multi-entry-point: per-agent / per-stage requests ----


class ObservationRequest(BaseModel):
    """Request to run ObservationAgent only (crawl URL, extract UI elements)."""
    url: HttpUrl = Field(..., description="Target URL to observe")
    user_instruction: Optional[str] = Field(None, description="Optional instruction for observation")
    depth: int = Field(default=1, ge=1, le=3, description="Crawl depth")
    login_credentials: Optional[Dict[str, str]] = Field(None, description="Website login (username/email + password)")
    gmail_credentials: Optional[Dict[str, str]] = Field(None, description="Gmail login for OTP verification (email + password)")
    model_config = ConfigDict(json_schema_extra={"example": {"url": "https://example.com/login", "depth": 1}})


class RequirementsRequest(BaseModel):
    """Request to run RequirementsAgent. Provide workflow_id (from observation) or inline observation payload."""
    workflow_id: Optional[str] = Field(None, description="ID of workflow that has observation results")
    observation_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Inline observation result (ui_elements, page_structure, page_context) if no workflow_id"
    )
    user_instruction: Optional[str] = Field(None, description="Optional instruction for scenarios")
    model_config = ConfigDict(json_schema_extra={"example": {"workflow_id": "wf-abc123"}})


class AnalysisRequest(BaseModel):
    """Request to run AnalysisAgent. Provide workflow_id (from requirements) or inline payload."""
    workflow_id: Optional[str] = Field(None, description="ID of workflow that has requirements (and observation) results")
    requirements_result: Optional[Dict[str, Any]] = Field(None, description="Inline requirements result if no workflow_id")
    observation_result: Optional[Dict[str, Any]] = Field(None, description="Inline observation (page_context etc.) if no workflow_id")
    user_instruction: Optional[str] = Field(None, description="Optional instruction")
    model_config = ConfigDict(json_schema_extra={"example": {"workflow_id": "wf-abc123"}})


class EvolutionRequest(BaseModel):
    """Request to run EvolutionAgent (test generation). Provide workflow_id or inline payload."""
    workflow_id: Optional[str] = Field(None, description="ID of workflow that has analysis (and prior) results")
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="Inline analysis result if no workflow_id")
    requirements_result: Optional[Dict[str, Any]] = Field(None, description="Inline requirements if no workflow_id")
    observation_result: Optional[Dict[str, Any]] = Field(None, description="Inline observation (page_context) if no workflow_id")
    user_instruction: Optional[str] = Field(None, description="Optional instruction for test generation")
    login_credentials: Optional[Dict[str, str]] = Field(None, description="Website login for evolution step generation")
    gmail_credentials: Optional[Dict[str, str]] = Field(None, description="Gmail login for OTP (if tests need to reference it)")
    model_config = ConfigDict(json_schema_extra={"example": {"workflow_id": "wf-abc123"}})


class ImproveTestsRequest(BaseModel):
    """Request to improve existing tests (iterative evolution + analysis)."""
    test_case_ids: List[int] = Field(..., min_length=1, description="IDs of test cases to improve")
    user_instruction: Optional[str] = Field(
        None,
        description="Optional instruction (e.g., 'Focus on edge cases', 'Add assertions')"
    )
    max_iterations: int = Field(default=5, ge=1, le=20, description="Max improvement iterations")
    model_config = ConfigDict(
        json_schema_extra={"example": {"test_case_ids": [101, 102], "user_instruction": "Add more assertions", "max_iterations": 3}}
    )


class AgentProgress(BaseModel):
    """Progress information for a single agent."""
    agent: str = Field(..., description="Agent name: observation, requirements, analysis, evolution")
    status: str = Field(..., description="Status: pending, running, completed, failed")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress percentage (0.0 to 1.0)"
    )
    message: Optional[str] = Field(None, description="Current status message")
    started_at: Optional[datetime] = Field(None, description="When agent started")
    completed_at: Optional[datetime] = Field(None, description="When agent completed")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Agent confidence score")
    elements_found: Optional[int] = Field(None, description="Number of UI elements found (ObservationAgent)")
    scenarios_generated: Optional[int] = Field(None, description="Number of scenarios generated (RequirementsAgent)")
    tests_generated: Optional[int] = Field(None, description="Number of tests generated (EvolutionAgent)")


class WorkflowStatusResponse(BaseModel):
    """Response containing workflow status."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    status: str = Field(..., description="Overall status: pending, running, completed, failed, cancelled")
    current_agent: Optional[str] = Field(None, description="Currently executing agent")
    progress: Dict[str, AgentProgress] = Field(..., description="Progress for each agent")
    total_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall progress percentage (0.0 to 1.0)"
    )
    started_at: datetime = Field(..., description="When workflow started")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error: Optional[str] = Field(None, description="Error message if workflow failed")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf-abc123",
                "status": "running",
                "current_agent": "requirements",
                "progress": {
                    "observation": {
                        "agent": "observation",
                        "status": "completed",
                        "progress": 1.0,
                        "message": "38 UI elements found",
                        "confidence": 0.90
                    },
                    "requirements": {
                        "agent": "requirements",
                        "status": "running",
                        "progress": 0.65,
                        "message": "Generating scenarios...",
                        "scenarios_generated": 12
                    }
                },
                "total_progress": 0.41,
                "started_at": "2026-03-06T10:00:00Z",
                "estimated_completion": "2026-03-06T10:02:30Z"
            }
        }
    )


class AgentProgressEvent(BaseModel):
    """SSE event for agent progress updates."""
    event: str = Field(..., description="Event type: agent_started, agent_progress, agent_completed, workflow_completed, workflow_failed")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event timestamp")


class WorkflowResultsResponse(BaseModel):
    """Response containing workflow results (generated tests)."""
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Final status: completed, failed")
    test_case_ids: List[int] = Field(..., description="IDs of generated test cases")
    test_count: int = Field(..., description="Total number of tests generated")
    observation_result: Optional[Dict[str, Any]] = Field(None, description="ObservationAgent results")
    requirements_result: Optional[Dict[str, Any]] = Field(None, description="RequirementsAgent results")
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="AnalysisAgent results")
    evolution_result: Optional[Dict[str, Any]] = Field(None, description="EvolutionAgent results")
    completed_at: datetime = Field(..., description="When workflow completed")
    total_duration_seconds: float = Field(..., description="Total workflow duration")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf-abc123",
                "status": "completed",
                "test_case_ids": [123, 124, 125],
                "test_count": 17,
                "completed_at": "2026-03-06T10:02:15Z",
                "total_duration_seconds": 135.5
            }
        }
    )


class WorkflowErrorResponse(BaseModel):
    """Error response for workflow operations."""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    workflow_id: Optional[str] = Field(None, description="Workflow ID if available")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")

