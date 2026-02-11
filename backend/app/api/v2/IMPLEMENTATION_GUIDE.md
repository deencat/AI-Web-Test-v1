# Implementation Guide - Sprint 10 API v2

**Developer:** Developer A  
**Date:** February 11, 2026  
**Purpose:** Step-by-step implementation guide with code examples

---

## Overview

This guide provides concrete code examples for implementing Sprint 10 API v2 endpoints, based on existing codebase patterns.

---

## Phase 1: Days 2-3 - `/api/v2/generate-tests` Endpoint

### Step 1: Update Endpoint Implementation

**File:** `backend/app/api/v2/endpoints/generate_tests.py`

```python
"""
API v2: Generate Tests Endpoint - IMPLEMENTATION
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from app.schemas.workflow import GenerateTestsRequest, WorkflowStatusResponse, WorkflowErrorResponse
from app.services.orchestration_service import get_orchestration_service, OrchestrationService
from app.db.session import get_db
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/generate-tests",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": WorkflowErrorResponse, "description": "Invalid request"},
        500: {"model": WorkflowErrorResponse, "description": "Internal server error"},
    },
    summary="Generate tests using 4-agent workflow",
    description="""
    Triggers the 4-agent workflow to analyze a URL and generate test cases.
    
    **Workflow Stages:**
    1. **ObservationAgent**: Crawls the URL and extracts UI elements
    2. **RequirementsAgent**: Generates BDD test scenarios
    3. **AnalysisAgent**: Analyzes risks, ROI, and dependencies
    4. **EvolutionAgent**: Generates executable test code
    
    **Returns:** workflow_id immediately (workflow runs in background)
    **Progress:** Track via SSE stream at `/api/v2/workflows/{workflow_id}/stream`
    """
)
async def generate_tests(
    request: GenerateTestsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service)
) -> WorkflowStatusResponse:
    """
    Generate tests using 4-agent workflow.
    
    Returns workflow_id immediately and starts workflow in background.
    """
    try:
        # Validate request
        if not request.url or not request.url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid URL",
                    "code": "INVALID_URL",
                    "message": "URL must start with http:// or https://"
                }
            )
        
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        logger.info(f"Creating workflow {workflow_id} for URL: {request.url}")
        
        # TODO: Create workflow record in database (Day 8)
        # from app.crud.workflow import create_workflow
        # workflow = create_workflow(db, workflow_id)
        
        # Start workflow in background
        background_tasks.add_task(
            run_workflow_background,
            workflow_id=workflow_id,
            request=request.dict(),
            orchestration_service=orchestration_service
        )
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status="pending",
            created_at=datetime.utcnow(),
            estimated_duration=120  # seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "message": str(e),
                "workflow_id": None,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


async def run_workflow_background(
    workflow_id: str,
    request: dict,
    orchestration_service: OrchestrationService
):
    """
    Background task to run the workflow.
    
    This function is called by FastAPI BackgroundTasks.
    """
    try:
        logger.info(f"Starting workflow {workflow_id}")
        result = await orchestration_service.run_workflow(workflow_id, request)
        logger.info(f"Workflow {workflow_id} completed: {result['status']}")
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
        # Error is already emitted via ProgressTracker
```

### Step 2: Test the Endpoint

**File:** `backend/tests/unit/test_generate_tests_endpoint.py` (create new)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generate_tests_endpoint_success():
    """Test successful workflow creation."""
    response = client.post(
        "/api/v2/generate-tests",
        json={
            "url": "https://example.com",
            "max_depth": 1,
            "user_instruction": "Test login flow"
        }
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "workflow_id" in data
    assert data["status"] == "pending"
    assert "created_at" in data


def test_generate_tests_endpoint_invalid_url():
    """Test invalid URL handling."""
    response = client.post(
        "/api/v2/generate-tests",
        json={
            "url": "not-a-url",
            "max_depth": 1
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_URL"
```

---

## Phase 2: Days 4-5 - SSE Streaming

### Step 1: Install Dependencies

```bash
cd backend
pip install sse-starlette redis[hiredis]
```

### Step 2: Update ProgressTracker

**File:** `backend/app/services/progress_tracker.py`

```python
"""
Progress Tracker - IMPLEMENTATION
"""
from typing import Dict, Any, AsyncIterator
from datetime import datetime
import json
import logging
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Emits real-time progress events via Redis pub/sub.
    """
    
    def __init__(self, redis_client: redis.Redis = None):
        """
        Initialize ProgressTracker.
        
        Args:
            redis_client: Redis async client (optional, will create if None)
        """
        self.redis = redis_client
        if not self.redis:
            # Create Redis client from settings
            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")
            self.redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        logger.info("ProgressTracker initialized")
    
    async def emit(
        self,
        workflow_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Emit a progress event to Redis pub/sub.
        
        Args:
            workflow_id: Workflow identifier
            event_type: Event type (agent_started, agent_progress, etc.)
            data: Event data payload
        """
        channel = f"workflow:{workflow_id}"
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await self.redis.publish(channel, json.dumps(event))
            logger.debug(f"Emitted event {event_type} to {channel}")
        except Exception as e:
            logger.error(f"Failed to emit event to Redis: {e}", exc_info=True)
    
    async def subscribe(self, workflow_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to workflow events (for SSE endpoint).
        
        Args:
            workflow_id: Workflow identifier
        
        Yields:
            Event dictionaries as they arrive
        """
        channel = f"workflow:{workflow_id}"
        pubsub = self.redis.pubsub()
        
        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        yield event
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse event: {e}")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"Unsubscribed from {channel}")


# Singleton instance
_progress_tracker: ProgressTracker = None


def get_progress_tracker() -> ProgressTracker:
    """
    Dependency injection function for ProgressTracker.
    
    Returns:
        ProgressTracker instance (singleton)
    """
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
```

### Step 3: Update SSE Endpoint

**File:** `backend/app/api/v2/endpoints/sse_stream.py`

```python
"""
API v2: Server-Sent Events (SSE) Stream Endpoint - IMPLEMENTATION
"""
from fastapi import APIRouter, HTTPException, status, Path, Request
from app.schemas.workflow import WorkflowErrorResponse
from app.services.progress_tracker import get_progress_tracker
from sse_starlette.sse import EventSourceResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{workflow_id}/stream",
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Stream workflow progress (SSE)",
    description="""
    Stream real-time progress events for a workflow using Server-Sent Events (SSE).
    
    **Event Types:**
    - `agent_started`: Agent begins execution
    - `agent_progress`: Agent progress update
    - `agent_completed`: Agent finishes execution
    - `workflow_completed`: All agents complete
    - `workflow_failed`: Workflow failed with error
    """
)
async def stream_workflow_progress(
    request: Request,
    workflow_id: str = Path(..., description="Workflow identifier"),
    progress_tracker = None  # Will be injected via Depends
):
    """
    Stream workflow progress via Server-Sent Events.
    """
    if progress_tracker is None:
        progress_tracker = get_progress_tracker()
    
    async def event_generator():
        """Generate SSE events from Redis pub/sub."""
        try:
            logger.info(f"Starting SSE stream for workflow {workflow_id}")
            
            async for event in progress_tracker.subscribe(workflow_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected for workflow {workflow_id}")
                    break
                
                # Format SSE event
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"])
                }
                
        except Exception as e:
            logger.error(f"Error in SSE stream for workflow {workflow_id}: {e}", exc_info=True)
            # Send error event
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        finally:
            logger.info(f"SSE stream ended for workflow {workflow_id}")
    
    return EventSourceResponse(event_generator())
```

### Step 4: Test SSE Endpoint

**File:** `backend/tests/unit/test_sse_stream.py` (create new)

```python
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sse_stream_endpoint():
    """Test SSE stream endpoint."""
    workflow_id = "test-workflow-1"
    
    response = client.get(
        f"/api/v2/workflows/{workflow_id}/stream",
        headers={"Accept": "text/event-stream"}
    )
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]
    
    # Parse SSE events (simplified - real test would need async client)
    # This is a basic structure test
    assert response.headers["Cache-Control"] == "no-cache"
```

---

## Phase 3: Days 6-7 - OrchestrationService

### Step 1: Update OrchestrationService

**File:** `backend/app/services/orchestration_service.py`

```python
"""
Orchestration Service - IMPLEMENTATION
"""
from typing import Dict, Any
from datetime import datetime
import logging
import asyncio

from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from agents.analysis_agent import AnalysisAgent
from agents.evolution_agent import EvolutionAgent
from agents.base_agent import TaskContext
from app.services.progress_tracker import ProgressTracker
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Coordinates the 4-agent workflow with progress tracking.
    """
    
    def __init__(self, progress_tracker: ProgressTracker = None, db_session=None):
        """
        Initialize OrchestrationService.
        
        Args:
            progress_tracker: ProgressTracker instance for emitting progress events
            db_session: Database session (optional, will create if None)
        """
        from app.services.progress_tracker import get_progress_tracker
        
        self.progress_tracker = progress_tracker or get_progress_tracker()
        self.db_session = db_session
        
        # Initialize agents (message_queue is None for now - agents work standalone)
        # TODO: Integrate with MessageBus in future sprint
        message_queue = None
        
        self.observation_agent = ObservationAgent(
            message_queue=message_queue,
            agent_id="orchestration-observation",
            priority=8,
            config={
                "use_llm": True,
                "max_depth": 2,
                "max_pages": 10,
                "headless": True
            }
        )
        
        self.requirements_agent = RequirementsAgent(
            agent_id="orchestration-requirements",
            agent_type="requirements",
            priority=7,
            message_queue=message_queue,
            config={
                "use_llm": True
            }
        )
        
        self.analysis_agent = AnalysisAgent(
            agent_id="orchestration-analysis",
            agent_type="analysis",
            priority=6,
            message_queue=message_queue,
            config={
                "use_llm": True,
                "enable_realtime_execution": False,  # Disable for workflow
                "db": self.db_session
            }
        )
        
        self.evolution_agent = EvolutionAgent(
            agent_id="orchestration-evolution",
            agent_type="evolution",
            priority=5,
            message_queue=message_queue,
            config={
                "use_llm": True,
                "db": self.db_session
            }
        )
        
        logger.info("OrchestrationService initialized with 4 agents")
    
    async def run_workflow(
        self,
        workflow_id: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the 4-agent workflow.
        
        Args:
            workflow_id: Unique workflow identifier
            request: GenerateTestsRequest data (url, user_instruction, etc.)
        
        Returns:
            Dict containing workflow results
        """
        start_time = datetime.utcnow()
        
        try:
            # Stage 1: Observation
            await self.progress_tracker.emit(workflow_id, "agent_started", {
                "agent": "observation",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            observation_task = TaskContext(
                task_id=f"{workflow_id}-obs-1",
                task_type="web_crawling",
                payload={
                    "url": request["url"],
                    "max_depth": request.get("max_depth", 2),
                    "auth": request.get("login_credentials")
                }
            )
            
            observation_result = await self.observation_agent.execute_task(observation_task)
            
            await self.progress_tracker.emit(workflow_id, "agent_completed", {
                "agent": "observation",
                "result": observation_result.result,
                "duration": (datetime.utcnow() - start_time).total_seconds()
            })
            
            # Stage 2: Requirements
            await self.progress_tracker.emit(workflow_id, "agent_started", {
                "agent": "requirements",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            requirements_task = TaskContext(
                task_id=f"{workflow_id}-req-1",
                task_type="requirement_extraction",
                payload={
                    "observation_data": observation_result.result,
                    "user_instruction": request.get("user_instruction")
                }
            )
            
            requirements_result = await self.requirements_agent.execute_task(requirements_task)
            
            await self.progress_tracker.emit(workflow_id, "agent_completed", {
                "agent": "requirements",
                "result": requirements_result.result,
                "duration": (datetime.utcnow() - start_time).total_seconds()
            })
            
            # Stage 3: Analysis
            await self.progress_tracker.emit(workflow_id, "agent_started", {
                "agent": "analysis",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            analysis_task = TaskContext(
                task_id=f"{workflow_id}-ana-1",
                task_type="risk_analysis",
                payload={
                    "scenarios": requirements_result.result.get("scenarios", []),
                    "observation_data": observation_result.result
                }
            )
            
            analysis_result = await self.analysis_agent.execute_task(analysis_task)
            
            await self.progress_tracker.emit(workflow_id, "agent_completed", {
                "agent": "analysis",
                "result": analysis_result.result,
                "duration": (datetime.utcnow() - start_time).total_seconds()
            })
            
            # Stage 4: Evolution
            await self.progress_tracker.emit(workflow_id, "agent_started", {
                "agent": "evolution",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            evolution_task = TaskContext(
                task_id=f"{workflow_id}-evo-1",
                task_type="test_generation",
                payload={
                    "scenarios": analysis_result.result.get("prioritized_scenarios", []),
                    "observation_data": observation_result.result
                }
            )
            
            evolution_result = await self.evolution_agent.execute_task(evolution_task)
            
            await self.progress_tracker.emit(workflow_id, "agent_completed", {
                "agent": "evolution",
                "result": evolution_result.result,
                "duration": (datetime.utcnow() - start_time).total_seconds()
            })
            
            # Final: Workflow completed
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            
            results = {
                "workflow_id": workflow_id,
                "status": "completed",
                "duration": total_duration,
                "observation": observation_result.result,
                "requirements": requirements_result.result,
                "analysis": analysis_result.result,
                "evolution": evolution_result.result
            }
            
            await self.progress_tracker.emit(workflow_id, "workflow_completed", results)
            
            logger.info(f"Workflow {workflow_id} completed in {total_duration:.2f}s")
            
            return results
            
        except Exception as e:
            error_data = {
                "workflow_id": workflow_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.progress_tracker.emit(workflow_id, "workflow_failed", error_data)
            
            logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            raise


def get_orchestration_service(
    progress_tracker=None,
    db_session=None
) -> OrchestrationService:
    """
    Dependency injection function for OrchestrationService.
    
    Returns:
        OrchestrationService instance
    """
    return OrchestrationService(
        progress_tracker=progress_tracker,
        db_session=db_session
    )
```

---

## Phase 4: Day 8 - Workflow Status Endpoints

### Step 1: Create Workflow Model

**File:** `backend/app/models/workflow.py` (create new)

```python
"""
Workflow Model - Database schema for workflow tracking
"""
from sqlalchemy import Column, String, DateTime, JSON, Enum
from app.db.base_class import Base
import enum
from datetime import datetime

class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    results = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
```

### Step 2: Create CRUD Operations

**File:** `backend/app/crud/workflow.py` (create new)

```python
"""
Workflow CRUD Operations
"""
from app.models.workflow import Workflow, WorkflowStatus
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Optional

def create_workflow(db: Session, workflow_id: str) -> Workflow:
    """Create new workflow record."""
    workflow = Workflow(
        id=workflow_id,
        status=WorkflowStatus.PENDING
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow

def get_workflow(db: Session, workflow_id: str) -> Optional[Workflow]:
    """Get workflow by ID."""
    return db.query(Workflow).filter(Workflow.id == workflow_id).first()

def update_workflow_status(
    db: Session,
    workflow_id: str,
    status: WorkflowStatus,
    results: Dict = None,
    error: str = None
) -> Workflow:
    """Update workflow status."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if workflow:
        workflow.status = status
        workflow.results = results
        workflow.error = error
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
    return workflow
```

### Step 3: Update Workflows Endpoint

**File:** `backend/app/api/v2/endpoints/workflows.py`

```python
"""
API v2: Workflow Status Endpoints - IMPLEMENTATION
"""
from fastapi import APIRouter, HTTPException, status, Path, Depends
from app.schemas.workflow import WorkflowStatusResponse, WorkflowResultsResponse, WorkflowErrorResponse
from app.db.session import get_db
from app.crud.workflow import get_workflow, update_workflow_status
from app.models.workflow import WorkflowStatus
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{workflow_id}",
    response_model=WorkflowStatusResponse,
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Get workflow status",
    description="Get the current status of a workflow."
)
async def get_workflow_status(
    workflow_id: str = Path(..., description="Workflow identifier"),
    db: Session = Depends(get_db)
) -> WorkflowStatusResponse:
    """Get workflow status."""
    workflow = get_workflow(db, workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow not found",
                "code": "WORKFLOW_NOT_FOUND",
                "workflow_id": workflow_id
            }
        )
    
    return WorkflowStatusResponse(
        workflow_id=workflow.id,
        status=workflow.status.value,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at
    )


@router.get(
    "/{workflow_id}/results",
    response_model=WorkflowResultsResponse,
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Get workflow results",
    description="Get the results of a completed workflow."
)
async def get_workflow_results(
    workflow_id: str = Path(..., description="Workflow identifier"),
    db: Session = Depends(get_db)
) -> WorkflowResultsResponse:
    """Get workflow results."""
    workflow = get_workflow(db, workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow not found",
                "code": "WORKFLOW_NOT_FOUND",
                "workflow_id": workflow_id
            }
        )
    
    if workflow.status != WorkflowStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Workflow not completed",
                "code": "WORKFLOW_NOT_COMPLETED",
                "workflow_id": workflow_id,
                "status": workflow.status.value
            }
        )
    
    return WorkflowResultsResponse(
        workflow_id=workflow.id,
        results=workflow.results or {}
    )


@router.delete(
    "/{workflow_id}",
    responses={
        404: {"model": WorkflowErrorResponse, "description": "Workflow not found"},
    },
    summary="Cancel workflow",
    description="Cancel a running workflow."
)
async def cancel_workflow(
    workflow_id: str = Path(..., description="Workflow identifier"),
    db: Session = Depends(get_db)
):
    """Cancel a workflow."""
    workflow = get_workflow(db, workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow not found",
                "code": "WORKFLOW_NOT_FOUND",
                "workflow_id": workflow_id
            }
        )
    
    if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Cannot cancel completed or failed workflow",
                "code": "WORKFLOW_ALREADY_FINISHED",
                "workflow_id": workflow_id,
                "status": workflow.status.value
            }
        )
    
    # Update status
    update_workflow_status(db, workflow_id, WorkflowStatus.CANCELLED)
    
    # TODO: Actually stop the workflow execution (Day 8)
    # orchestration_service.cancel_workflow(workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "status": "cancelled",
        "message": "Workflow cancellation requested"
    }
```

---

## Testing Checklist

### Unit Tests
- [ ] `test_generate_tests_endpoint.py` - Test POST endpoint
- [ ] `test_sse_stream.py` - Test SSE streaming
- [ ] `test_orchestration_service.py` - Test workflow coordination
- [ ] `test_workflows_endpoint.py` - Test status/results/cancel

### Integration Tests
- [ ] `test_workflow_e2e.py` - Full workflow from POST to results

### Manual Testing
- [ ] Start backend server
- [ ] POST `/api/v2/generate-tests`
- [ ] Connect to SSE stream
- [ ] Verify events arrive
- [ ] GET `/api/v2/workflows/{id}/results`
- [ ] Verify results

---

**Status:** ✅ **IMPLEMENTATION GUIDE COMPLETE**  
**Next:** Follow this guide during Sprint 10 Days 2-9

