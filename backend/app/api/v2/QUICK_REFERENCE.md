# Quick Reference - Sprint 10 API v2

**Developer:** Developer A  
**Quick lookup for common tasks**

---

**Full API reference (parameters, input/output, examples):** [API_SPECIFICATION.md](./API_SPECIFICATION.md). OpenAPI: `/api/v2/docs`.

---

## Entry Points (multi-entry API)

| Endpoint | Purpose |
|----------|---------|
| POST `/api/v2/generate-tests` | Full pipeline from URL |
| POST `/api/v2/observation` | ObservationAgent only; chain with `workflow_id` |
| POST `/api/v2/requirements` | RequirementsAgent; input: `workflow_id` or `observation_result` |
| POST `/api/v2/analysis` | AnalysisAgent; input: `workflow_id` or prior results |
| POST `/api/v2/evolution` | EvolutionAgent; input: `workflow_id` or prior results |
| POST `/api/v2/improve-tests` | Iterative improvement by `test_case_ids` |
| GET `/api/v2/workflows/{id}` | Status |
| GET `/api/v2/workflows/{id}/results` | Results (partial or full) |
| GET `/api/v2/workflows/{id}/stream` | SSE progress |

---

## File Locations

| Component | File Path |
|-----------|-----------|
| API Router | `backend/app/api/v2/api.py` |
| Generate Tests Endpoint | `backend/app/api/v2/endpoints/generate_tests.py` |
| Observation / Requirements / Analysis / Evolution / Improve | `backend/app/api/v2/endpoints/observation.py`, `requirements.py`, `analysis.py`, `evolution.py`, `improve_tests.py` |
| SSE Stream Endpoint | `backend/app/api/v2/endpoints/sse_stream.py` |
| Workflow Status Endpoints | `backend/app/api/v2/endpoints/workflows.py` |
| Pydantic Schemas | `backend/app/schemas/workflow.py` |
| OrchestrationService | `backend/app/services/orchestration_service.py` |
| ProgressTracker | `backend/app/services/progress_tracker.py` |

---

## Agent Initialization Pattern

```python
from agents.observation_agent import ObservationAgent
from agents.requirements_agent import RequirementsAgent
from agents.analysis_agent import AnalysisAgent
from agents.evolution_agent import EvolutionAgent

# Pattern:
agent = AgentClass(
    message_queue=None,  # Stub for now
    agent_id="unique-id",
    agent_type="type",  # For RequirementsAgent, AnalysisAgent, EvolutionAgent
    priority=8,  # 1-10, higher = more important
    config={
        "use_llm": True,
        "max_depth": 2,
        # ... agent-specific config
    }
)
```

---

## TaskContext Pattern

```python
from agents.base_agent import TaskContext

task = TaskContext(
    task_id="unique-task-id",
    task_type="task_type_string",
    payload={
        # Task-specific data
    }
)

result = await agent.execute_task(task)
# result.result contains the agent's output
```

---

## ProgressTracker Pattern

```python
from app.services.progress_tracker import get_progress_tracker

progress_tracker = get_progress_tracker()

# Emit event
await progress_tracker.emit(
    workflow_id="workflow-123",
    event_type="agent_started",
    data={
        "agent": "observation",
        "timestamp": datetime.utcnow().isoformat()
    }
)

# Subscribe to events (for SSE)
async for event in progress_tracker.subscribe(workflow_id):
    # Process event
    pass
```

---

## SSE Event Format

```python
# Event structure
{
    "event": "agent_started",  # Event type
    "data": {                   # Event data
        "agent": "observation",
        "timestamp": "2026-02-11T..."
    },
    "timestamp": "2026-02-11T..."
}

# SSE yield format
yield {
    "event": "agent_started",
    "data": json.dumps({
        "agent": "observation",
        "timestamp": "2026-02-11T..."
    })
}
```

---

## Common Event Types

| Event Type | When Emitted | Data Structure |
|------------|--------------|-----------------|
| `agent_started` | Agent begins execution | `{agent: str, timestamp: str}` |
| `agent_progress` | Agent progress update | `{agent: str, progress: float, message: str}` |
| `agent_completed` | Agent finishes | `{agent: str, result: dict, duration: float}` |
| `workflow_completed` | All agents complete | `{workflow_id: str, results: dict, duration: float}` |
| `workflow_failed` | Workflow fails | `{workflow_id: str, error: str, timestamp: str}` |
| `error` | Any error | `{error: str, workflow_id: str, timestamp: str}` |

---

## Database Session Pattern

```python
from app.db.session import SessionLocal

# Get session
db = SessionLocal()
try:
    # Use db
    pass
finally:
    db.close()

# Or use dependency injection
from fastapi import Depends
from app.db.session import get_db

@router.get("/endpoint")
async def endpoint(db: Session = Depends(get_db)):
    # db is automatically managed
    pass
```

---

## Error Handling Pattern

```python
from fastapi import HTTPException, status

# Validation error
if not valid:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "Error message",
            "code": "ERROR_CODE",
            "message": "Detailed message"
        }
    )

# Not found
if not found:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "Not found",
            "code": "NOT_FOUND",
            "workflow_id": workflow_id
        }
    )
```

---

## Testing Commands

```bash
# Start backend server
cd backend
python -m uvicorn app.main:app --reload

# Test endpoint (should return 501)
curl -X POST http://localhost:8000/api/v2/generate-tests \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test SSE (should return 501)
curl http://localhost:8000/api/v2/workflows/test-id/stream \
  -H "Accept: text/event-stream"

# Run unit tests
pytest backend/tests/unit/test_generate_tests_endpoint.py -v

# Run all tests
pytest backend/tests/ -v
```

---

## Dependencies to Install

```bash
# SSE support
pip install sse-starlette

# Redis pub/sub
pip install redis[hiredis]

# Development
pip install pytest pytest-asyncio httpx
```

---

## Configuration

**Redis URL:** Set in `backend/app/core/config.py`
```python
REDIS_URL: str = "redis://localhost:6379"
```

**Environment Variables:**
- `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379`)
- `HEADLESS_BROWSER` - Browser headless mode (default: `true`)

---

## Common Issues & Solutions

### Issue: Redis Connection Failed
**Solution:** Ensure Redis is running: `redis-server`

### Issue: SSE Not Streaming
**Solution:** Check client disconnection handling, verify Redis pub/sub

### Issue: Agent Not Initializing
**Solution:** Check agent config, verify LLM credentials in `.env`

### Issue: Database Session Error
**Solution:** Ensure database is initialized, check `backend/app/db/session.py`

---

## Next Steps Checklist

- [ ] Day 1: API Contract Definition with Developer B
- [ ] Days 2-3: Implement `/api/v2/generate-tests`
- [ ] Days 4-5: Implement SSE streaming
- [ ] Days 6-7: Implement OrchestrationService
- [ ] Day 8: Implement workflow status endpoints
- [ ] Day 9: Unit tests

---

**Status:** ✅ **QUICK REFERENCE READY**  
**Use this for quick lookups during implementation**

