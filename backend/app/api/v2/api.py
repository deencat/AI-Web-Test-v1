"""
API v2 Router - Agent Workflow Endpoints

This module provides the API v2 router for agent workflow management.
Includes endpoints for triggering workflows, streaming progress, and managing workflow state.

Reference: Sprint 10 - Frontend Integration & Real-time Agent Progress
"""
from fastapi import APIRouter

# Import endpoints (will be implemented in Sprint 10)
try:
    from app.api.v2.endpoints import generate_tests, workflows, sse_stream
    
    api_router = APIRouter()
    
    # Register all v2 endpoints
    api_router.include_router(generate_tests.router, prefix="/generate-tests", tags=["agent-workflow"])
    api_router.include_router(workflows.router, prefix="/workflows", tags=["agent-workflow"])
    api_router.include_router(sse_stream.router, prefix="/workflows", tags=["agent-workflow"])
except ImportError as e:
    # Fallback if endpoints not yet created
    api_router = APIRouter()
    # Endpoints will be registered as they are implemented

