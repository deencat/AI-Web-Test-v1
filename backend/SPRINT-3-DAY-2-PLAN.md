# Sprint 3 Day 2 - Test Execution Queue System

**Branch:** `backend-dev-sprint-3-queue`  
**Started:** November 24, 2025  
**Goal:** Implement queue system for managing multiple test executions

## 🎯 Objectives

### Primary Goal
Enable multiple test executions to be queued and executed concurrently with proper resource management.

### Success Criteria
- [ ] Can queue multiple tests
- [ ] Tests execute concurrently (up to configured limit)
- [ ] Queue status visible via API
- [ ] Priority-based execution supported
- [ ] Resource limits enforced
- [ ] No conflicts or race conditions

## 📋 Requirements

### Functional Requirements
1. **Queue Management**
   - Add execution to queue
   - Remove execution from queue
   - View queue status
   - Clear queue (admin only)

2. **Concurrent Execution**
   - Execute up to N tests simultaneously
   - Default: 5 concurrent executions
   - Configurable via settings

3. **Priority Handling**
   - High/Medium/Low priority
   - High priority executions start first
   - FIFO within same priority

4. **Resource Management**
   - Track active executions
   - Enforce concurrent limit
   - Clean up completed executions
   - Handle failures gracefully

### Non-Functional Requirements
- Thread-safe operations
- No race conditions
- Efficient queue operations (O(1) add/remove)
- Minimal memory overhead
- Proper logging

## 🏗️ Architecture Design

### Components to Build

#### 1. Queue Data Structure
**File:** `backend/app/services/execution_queue.py`

```python
class ExecutionQueue:
    """
    Thread-safe queue for test executions.
    Supports priority-based ordering and concurrent execution limits.
    """
    - add_to_queue(execution_id, priority)
    - remove_from_queue(execution_id)
    - get_next_execution()
    - get_queue_status()
    - get_active_executions()
    - is_under_limit()
```

#### 2. Queue Manager
**File:** `backend/app/services/queue_manager.py`

```python
class QueueManager:
    """
    Manages execution queue and worker pool.
    Handles concurrent execution and resource limits.
    """
    - start_execution(execution_id)
    - process_queue()
    - check_and_start_next()
    - handle_execution_complete(execution_id)
    - get_statistics()
```

#### 3. API Endpoints
**File:** `backend/app/api/v1/endpoints/queue.py`

```python
# New endpoints:
GET  /api/v1/queue/status       # Get queue status
GET  /api/v1/queue/active       # Get active executions
POST /api/v1/queue/clear        # Clear queue (admin)
GET  /api/v1/queue/statistics   # Queue statistics
```

#### 4. Configuration
**File:** `backend/app/core/config.py`

```python
# Add settings:
MAX_CONCURRENT_EXECUTIONS = 5
QUEUE_CHECK_INTERVAL = 2  # seconds
EXECUTION_TIMEOUT = 300  # seconds
```

## 📊 Database Schema

### New Fields in TestExecution
```python
# Add to existing TestExecution model:
queued_at = Column(DateTime, nullable=True)
priority = Column(Integer, default=5)  # 1=high, 5=medium, 10=low
queue_position = Column(Integer, nullable=True)
```

### Migration
```bash
# Create migration
cd backend
alembic revision -m "Add queue fields to test_execution"
```

## 🔄 Workflow

### Current Flow (Day 1):
```
User calls POST /tests/{id}/run
    ↓
Create execution record
    ↓
Start execution immediately in background thread
    ↓
Return execution ID
```

### New Flow (Day 2):
```
User calls POST /tests/{id}/run
    ↓
Create execution record with status=queued
    ↓
Add to queue based on priority
    ↓
Return execution ID (queued)
    ↓
Queue manager checks if under limit
    ↓
If yes: Start execution (status=running)
If no: Keep in queue (status=queued)
    ↓
When execution completes, start next from queue
```

## 🛠️ Implementation Steps

### Phase 1: Queue Infrastructure (2-3 hours)
1. Create `ExecutionQueue` class
2. Implement priority queue logic
3. Add thread-safe operations
4. Unit tests for queue

### Phase 2: Queue Manager (2-3 hours)
1. Create `QueueManager` class
2. Implement concurrent execution handling
3. Add resource limit enforcement
4. Background worker for queue processing

### Phase 3: API Integration (1-2 hours)
1. Modify `/tests/{id}/run` to use queue
2. Add queue status endpoints
3. Update execution endpoint responses
4. Add queue statistics

### Phase 4: Testing (1-2 hours)
1. Test single execution (should work as before)
2. Test concurrent executions (5 at once)
3. Test queue overflow (>5 queued)
4. Test priority ordering
5. Test resource cleanup

### Phase 5: Documentation (30 min)
1. API documentation
2. Configuration guide
3. Queue behavior explanation
4. Completion report

## 📝 API Design

### Modified Endpoint: POST /tests/{id}/run
**Response (when queued):**
```json
{
  "id": 123,
  "test_case_id": 45,
  "status": "queued",
  "priority": 5,
  "queue_position": 3,
  "message": "Test queued for execution"
}
```

### New Endpoint: GET /queue/status
**Response:**
```json
{
  "active_count": 5,
  "queued_count": 12,
  "max_concurrent": 5,
  "queue": [
    {
      "execution_id": 124,
      "test_case_id": 46,
      "priority": 1,
      "queue_position": 1,
      "queued_at": "2025-11-24T..."
    }
  ]
}
```

### New Endpoint: GET /queue/statistics
**Response:**
```json
{
  "total_queued_today": 150,
  "total_executed_today": 145,
  "average_queue_time": 3.5,
  "current_active": 5,
  "current_queued": 5
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# Add to .env
MAX_CONCURRENT_EXECUTIONS=5
QUEUE_CHECK_INTERVAL=2
EXECUTION_TIMEOUT=300
```

### Settings Class
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # Existing settings...
    
    # Queue settings
    MAX_CONCURRENT_EXECUTIONS: int = 5
    QUEUE_CHECK_INTERVAL: int = 2
    EXECUTION_TIMEOUT: int = 300
```

## 🧪 Testing Strategy

### Unit Tests
- Queue add/remove operations
- Priority ordering
- Thread safety
- Resource limit enforcement

### Integration Tests
- Single execution (backward compatibility)
- Multiple concurrent executions
- Queue overflow handling
- Priority-based execution order

### Load Tests
- 20 executions queued at once
- Verify only 5 run concurrently
- Verify all complete successfully
- Check for memory leaks

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Concurrent Limit | 5 max | Monitor active count |
| Queue Response Time | < 100ms | API response time |
| Execution Start Time | < 3s after queue | Time from queued to running |
| Resource Cleanup | 100% | No leaked threads/memory |
| Test Pass Rate | 100% | All tests pass |

## 🚧 Potential Challenges

### Challenge 1: Thread Safety
**Solution:** Use threading.Lock for queue operations

### Challenge 2: Database Contention
**Solution:** Use optimistic locking, retry logic

### Challenge 3: Stuck Executions
**Solution:** Implement execution timeout, cleanup job

### Challenge 4: Priority Starvation
**Solution:** Age-based priority boost for long-queued items

## 📅 Timeline

**Total Estimated Time:** 6-8 hours

| Phase | Time | Tasks |
|-------|------|-------|
| Planning | 30 min | ✅ This document |
| Infrastructure | 2-3 hours | Queue + Manager |
| API Integration | 1-2 hours | Endpoints + Modify existing |
| Testing | 1-2 hours | Unit + Integration + Load |
| Documentation | 30 min | API docs + Completion report |
| Buffer | 1 hour | Unexpected issues |

## 🎯 Next Steps

1. ✅ Create branch `backend-dev-sprint-3-queue`
2. ✅ Create this plan document
3. ⏳ Implement `ExecutionQueue` class
4. ⏳ Implement `QueueManager` class
5. ⏳ Add database migration
6. ⏳ Modify execution endpoint
7. ⏳ Add queue endpoints
8. ⏳ Write tests
9. ⏳ Create documentation
10. ⏳ Merge to main

## 📚 References

- Day 1 Code: `backend/app/services/stagehand_service.py`
- Execution Endpoint: `backend/app/api/v1/endpoints/executions.py`
- Python Queue: `queue.PriorityQueue` (for inspiration)
- Threading: `threading.Thread`, `threading.Lock`

---

**Status:** ✅ Planning Complete  
**Next:** Implement ExecutionQueue class  
**Branch:** backend-dev-sprint-3-queue  
**Ready to Code!** 🚀

