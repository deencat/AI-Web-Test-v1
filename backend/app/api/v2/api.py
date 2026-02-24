"""
API v2 Router - Agent Workflow Endpoints

This module provides the API v2 router for agent workflow management.
Includes endpoints for triggering workflows, streaming progress, and managing workflow state.

Reference: Sprint 10 - Frontend Integration & Real-time Agent Progress
"""
from fastapi import APIRouter

# Import endpoints (will be implemented in Sprint 10)
try:
    from app.api.v2.endpoints import (
        generate_tests,
        workflows,
        sse_stream,
        observation,
        requirements,
        analysis,
        evolution,
        improve_tests,
    )

    api_router = APIRouter()

    # Single-entry (full pipeline) and multi-entry (per-agent) endpoints
    api_router.include_router(generate_tests.router, tags=["agent-workflow"])
    api_router.include_router(observation.router, tags=["agent-workflow"])
    api_router.include_router(requirements.router, tags=["agent-workflow"])
    api_router.include_router(analysis.router, tags=["agent-workflow"])
    api_router.include_router(evolution.router, tags=["agent-workflow"])
    api_router.include_router(improve_tests.router, tags=["agent-workflow"])
    # Workflow resource: status, results, stream, cancel
    api_router.include_router(workflows.router, prefix="/workflows", tags=["agent-workflow"])
    api_router.include_router(sse_stream.router, prefix="/workflows", tags=["agent-workflow"])
except ImportError as e:
    # Fallback if endpoints not yet created
    api_router = APIRouter()
    # Endpoints will be registered as they are implemented

