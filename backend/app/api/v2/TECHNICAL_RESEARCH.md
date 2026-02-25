# Technical Research - Sprint 10 Implementation

**Developer:** Developer A  
**Date:** February 11, 2026  
**Purpose:** Technical research and implementation patterns for Sprint 10

**API reference:** Request/response details and parameters: **[API_SPECIFICATION.md](./API_SPECIFICATION.md)**.

---

## 1. Server-Sent Events (SSE) Implementation

### 1.1 FastAPI SSE Pattern

**Library:** `sse-starlette` (recommended) or `starlette.responses.EventSourceResponse`

**Installation:**
```bash
pip install sse-starlette
```

**Basic Pattern:**
```python
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/stream")
async def stream_events():
    async def event_generator():
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            # Generate event
            event_data = {
                "event": "agent_progress",
                "data": json.dumps({
                    "agent": "observation",
                    "progress": 0.5,
                    "message": "Crawling pages..."
                })
            }
            
            yield event_data
            
            # Wait before next event
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())
```

### 1.2 SSE Event Format

**Standard Format:**
```
event: agent_started
data: {"agent": "observation", "timestamp": "2026-02-11T..."}

event: agent_progress
data: {"agent": "observation", "progress": 0.5, "message": "..."}

event: agent_completed
data: {"agent": "observation", "result": {...}}

event: workflow_completed
data: {"workflow_id": "...", "results": {...}}
```

**Python Implementation:**
```python
async def event_generator():
    # Format: "event: <event_type>\ndata: <json_data>\n\n"
    yield {
        "event": "agent_started",
        "data": json.dumps({
            "agent": "observation",
            "timestamp": datetime.utcnow().isoformat()
        })
    }
```

### 1.3 Client Disconnection Handling

**Critical:** Always check for client disconnection to prevent resource leaks.

```python
async def event_generator(request: Request):
    while True:
        if await request.is_disconnected():
            logger.info("Client disconnected, stopping stream")
            break
        
        # Generate event
        yield event_data
        await asyncio.sleep(0.1)
```

### 1.4 Error Handling in SSE

```python
async def event_generator():
    try:
        # Subscribe to Redis
        async for message in redis_subscriber.listen():
            yield {
                "event": message["event"],
                "data": json.dumps(message["data"])
            }
    except Exception as e:
        # Send error event before closing
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        raise
```

---

## 2. Redis Pub/Sub Implementation

### 2.1 Redis Connection

**Library:** `redis` (async support)

**Installation:**
```bash
pip install redis[hiredis]
```

**Connection Pattern:**
```python
import redis.asyncio as redis

# Create Redis client
redis_client = redis.from_url(
    "redis://localhost:6379",
    encoding="utf-8",
    decode_responses=True
)

# Test connection
await redis_client.ping()
```

### 2.2 Publishing Events

```python
class ProgressTracker:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def emit(
        self,
        workflow_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Publish event to Redis channel."""
        channel = f"workflow:{workflow_id}"
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis.publish(
            channel,
            json.dumps(event)
        )
```

### 2.3 Subscribing to Events

```python
async def subscribe_to_workflow(workflow_id: str):
    """Subscribe to workflow events."""
    redis_client = redis.from_url("redis://localhost:6379")
    pubsub = redis_client.pubsub()
    
    channel = f"workflow:{workflow_id}"
    await pubsub.subscribe(channel)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                yield event
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()
```

### 2.4 Redis Connection Pooling

**Best Practice:** Use connection pooling for production.

```python
import redis.asyncio as redis

# Create connection pool
redis_pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379",
    max_connections=50,
    encoding="utf-8",
    decode_responses=True
)

# Create client from pool
redis_client = redis.Redis(connection_pool=redis_pool)
```

---

## 3. Agent Integration Patterns

### 3.1 Agent Initialization

**Pattern from E2E Test:**
```python
from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from agents.analysis_agent import AnalysisAgent
from agents.evolution_agent import EvolutionAgent

# Create message queue (stub for now)
message_queue = None  # Will be replaced with actual MessageBus

# Initialize agents
observation_agent = ObservationAgent(
    message_queue=message_queue,
    agent_id="observation-agent-1",
    priority=8,
    config={
        "max_depth": 2,
        "max_pages": 10,
        "headless": True,
        "use_llm": True
    }
)

requirements_agent = RequirementsAgent(
    agent_id="requirements-agent-1",
    agent_type="requirements",
    priority=7,
    message_queue=message_queue,
    config={
        "use_llm": True
    }
)

analysis_agent = AnalysisAgent(
    agent_id="analysis-agent-1",
    agent_type="analysis",
    priority=6,
    message_queue=message_queue,
    config={
        "use_llm": True,
        "enable_real_time_execution": False  # Set to True for real execution
    }
)

evolution_agent = EvolutionAgent(
    agent_id="evolution-agent-1",
    agent_type="evolution",
    priority=5,
    message_queue=message_queue,
    config={
        "use_llm": True,
        "db": db_session  # Database session for storing test cases
    }
)
```

### 3.2 Agent Execution Pattern

**Sequential Workflow:**
```python
async def run_workflow(workflow_id: str, request: Dict[str, Any]):
    """Run 4-agent workflow sequentially."""
    
    # Stage 1: Observation
    await progress_tracker.emit(workflow_id, "agent_started", {
        "agent": "observation"
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
    
    observation_result = await observation_agent.execute_task(observation_task)
    
    await progress_tracker.emit(workflow_id, "agent_completed", {
        "agent": "observation",
        "result": observation_result.result
    })
    
    # Stage 2: Requirements
    await progress_tracker.emit(workflow_id, "agent_started", {
        "agent": "requirements"
    })
    
    requirements_task = TaskContext(
        task_id=f"{workflow_id}-req-1",
        task_type="requirement_extraction",
        payload={
            "observation_data": observation_result.result,
            "user_instruction": request.get("user_instruction")
        }
    )
    
    requirements_result = await requirements_agent.execute_task(requirements_task)
    
    await progress_tracker.emit(workflow_id, "agent_completed", {
        "agent": "requirements",
        "result": requirements_result.result
    })
    
    # Stage 3: Analysis
    # ... similar pattern
    
    # Stage 4: Evolution
    # ... similar pattern
    
    # Final
    await progress_tracker.emit(workflow_id, "workflow_completed", {
        "workflow_id": workflow_id,
        "results": {
            "observation": observation_result.result,
            "requirements": requirements_result.result,
            "analysis": analysis_result.result,
            "evolution": evolution_result.result
        }
    })
```

### 3.3 Error Handling

```python
async def run_workflow(workflow_id: str, request: Dict[str, Any]):
    """Run workflow with error handling."""
    try:
        # Stage 1: Observation
        try:
            observation_result = await observation_agent.execute_task(observation_task)
        except Exception as e:
            await progress_tracker.emit(workflow_id, "agent_failed", {
                "agent": "observation",
                "error": str(e)
            })
            raise
        
        # ... continue with other stages
        
    except Exception as e:
        await progress_tracker.emit(workflow_id, "workflow_failed", {
            "workflow_id": workflow_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise
```

---

## 4. Background Task Pattern

### 4.1 FastAPI BackgroundTasks

**Pattern:**
```python
from fastapi import BackgroundTasks

@router.post("/generate-tests")
async def generate_tests(
    request: GenerateTestsRequest,
    background_tasks: BackgroundTasks
) -> WorkflowStatusResponse:
    """Generate tests - returns immediately, runs in background."""
    workflow_id = str(uuid.uuid4())
    
    # Add background task
    background_tasks.add_task(
        run_workflow,
        workflow_id=workflow_id,
        request=request.dict()
    )
    
    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        status="pending",
        created_at=datetime.utcnow()
    )
```

### 4.2 Alternative: Celery (For Production)

**For production, consider Celery for long-running tasks:**
```python
from celery import Celery

celery_app = Celery(
    "agent_workflow",
    broker="redis://localhost:6379/0"
)

@celery_app.task
def run_workflow_task(workflow_id: str, request: Dict[str, Any]):
    """Celery task for workflow execution."""
    # Run workflow
    pass
```

**Note:** For Sprint 10, FastAPI BackgroundTasks is sufficient. Celery can be added in Sprint 11 if needed.

---

## 5. Database Integration

### 5.1 Workflow Status Storage

**Model (to be created):**
```python
# backend/app/models/workflow.py
from sqlalchemy import Column, String, DateTime, JSON, Enum
from app.db.base_class import Base
import enum

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

### 5.2 CRUD Operations

```python
# backend/app/crud/workflow.py
from app.models.workflow import Workflow, WorkflowStatus
from sqlalchemy.orm import Session

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

---

## 6. Testing Patterns

### 6.1 Unit Test for SSE

```python
import pytest
from fastapi.testclient import TestClient

def test_sse_stream(client: TestClient):
    """Test SSE stream endpoint."""
    workflow_id = "test-workflow-1"
    
    response = client.get(
        f"/api/v2/workflows/{workflow_id}/stream",
        headers={"Accept": "text/event-stream"}
    )
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/event-stream"
    
    # Parse SSE events
    events = []
    for line in response.iter_lines():
        if line.startswith(b"event:"):
            event_type = line.split(b":", 1)[1].strip().decode()
        elif line.startswith(b"data:"):
            data = json.loads(line.split(b":", 1)[1].strip())
            events.append({"event": event_type, "data": data})
    
    assert len(events) > 0
```

### 6.2 Integration Test for Workflow

```python
@pytest.mark.asyncio
async def test_workflow_execution():
    """Test full workflow execution."""
    workflow_id = "test-workflow-1"
    request = {
        "url": "https://example.com",
        "max_depth": 1
    }
    
    # Start workflow
    orchestration_service = OrchestrationService(progress_tracker)
    result = await orchestration_service.run_workflow(workflow_id, request)
    
    assert result["status"] == "completed"
    assert "observation" in result["results"]
    assert "requirements" in result["results"]
```

---

## 7. Performance Considerations

### 7.1 SSE Connection Limits

**Issue:** Browsers limit concurrent SSE connections (typically 6 per domain).

**Solution:** Use connection pooling or WebSocket for high concurrency.

### 7.2 Redis Pub/Sub Scalability

**Best Practice:** Use Redis Cluster for production scale.

**Current:** Single Redis instance is sufficient for Sprint 10.

### 7.3 Agent Execution Time

**Expected Duration:**
- ObservationAgent: 10-30 seconds
- RequirementsAgent: 5-15 seconds
- AnalysisAgent: 10-20 seconds
- EvolutionAgent: 15-30 seconds
- **Total: 40-95 seconds**

**Optimization:** Already implemented (OPT-1, OPT-2, OPT-3, OPT-4 from Sprint 9).

---

## 8. Security Considerations

### 8.1 Workflow ID Validation

**Always validate workflow_id belongs to requesting user:**
```python
@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_progress(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    # Verify workflow belongs to user
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(404, "Workflow not found")
    
    # Stream events
    ...
```

### 8.2 SSE Authentication

**Option 1: Query Parameter Token**
```python
@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_progress(
    workflow_id: str,
    token: str = Query(...)
):
    # Validate token
    if not validate_token(token):
        raise HTTPException(401, "Invalid token")
    ...
```

**Option 2: Cookie-based Auth**
```python
# FastAPI automatically includes cookies in SSE requests
@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_progress(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    ...
```

---

## 9. References

### Documentation
- FastAPI SSE: https://fastapi.tiangolo.com/advanced/server-sent-events/
- Starlette EventSourceResponse: https://www.starlette.io/responses/#eventsourceresponse
- sse-starlette: https://github.com/sysid/sse-starlette
- Redis Pub/Sub: https://redis.io/docs/manual/pubsub/
- Redis Python: https://redis.readthedocs.io/

### Code Examples
- Existing E2E Test: `backend/tests/integration/test_four_agent_e2e_real.py`
- Agent Base Class: `backend/agents/base_agent.py`
- Existing API Patterns: `backend/app/api/v1/`

---

## 10. Implementation Checklist

### Day 1: API Contract Definition
- [ ] Review Pydantic schemas with Developer B
- [ ] Lock API contracts
- [ ] Verify TypeScript types match

### Days 2-3: `/api/v2/generate-tests`
- [ ] Implement endpoint
- [ ] Integrate OrchestrationService
- [ ] Add error handling
- [ ] Write unit tests

### Days 4-5: SSE Streaming
- [ ] Install `sse-starlette`
- [ ] Implement ProgressTracker with Redis
- [ ] Create SSE endpoint
- [ ] Test event streaming
- [ ] Write unit tests

### Days 6-7: OrchestrationService
- [ ] Initialize agents
- [ ] Implement workflow coordination
- [ ] Add progress tracking
- [ ] Write unit tests

### Day 8: Workflow Status Endpoints
- [ ] Implement GET `/workflows/{id}`
- [ ] Implement GET `/workflows/{id}/results`
- [ ] Implement DELETE `/workflows/{id}`
- [ ] Write unit tests

### Day 9: Unit Tests
- [ ] Comprehensive test coverage
- [ ] Integration tests
- [ ] 90%+ code coverage

---

**Status:** ✅ **RESEARCH COMPLETE**  
**Next:** Day 1 API Contract Definition (Mar 6, 2026)

