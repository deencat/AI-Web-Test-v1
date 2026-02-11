"""
Workflow Schemas for API v2 - Agent Workflow Management

These schemas define the request/response models for the agent workflow API.
Used for triggering workflows, tracking progress, and retrieving results.

Reference: Sprint 10 - Frontend Integration & Real-time Agent Progress
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class GenerateTestsRequest(BaseModel):
    """Request to generate tests using 4-agent workflow."""
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
        description="Optional login credentials: {'username': '...', 'password': '...'}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/login",
                "user_instruction": "Test login flow with invalid credentials",
                "depth": 1,
                "login_credentials": {
                    "username": "test@example.com",
                    "password": "password123"
                }
            }
        }


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

    class Config:
        json_schema_extra = {
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


class AgentProgressEvent(BaseModel):
    """SSE event for agent progress updates."""
    event: str = Field(..., description="Event type: agent_started, agent_progress, agent_completed, workflow_completed, workflow_failed")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


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

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf-abc123",
                "status": "completed",
                "test_case_ids": [123, 124, 125],
                "test_count": 17,
                "completed_at": "2026-03-06T10:02:15Z",
                "total_duration_seconds": 135.5
            }
        }


class WorkflowErrorResponse(BaseModel):
    """Error response for workflow operations."""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    workflow_id: Optional[str] = Field(None, description="Workflow ID if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

