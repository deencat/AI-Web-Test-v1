# Developer A: Next Steps & Action Plan
**Date:** February 23, 2026  
**Status:** 📋 **SPRINT 10 IN PROGRESS**  
**Sprint 9 Status:** ✅ **100% COMPLETE** (30/30 points)  
**Sprint 10 Start:** March 6, 2026  
**Last doc update:** Feb 23, 2026 — Observation, SSE, workflow cancel, and unit tests (10A.6) done; next: API spec handoff to Developer B.

---

## 🎯 Current Status Summary

### ✅ Sprint 9 Complete (Feb 20 - Mar 5, 2026)

**Completed Tasks:**
- ✅ EvolutionAgent fully operational
- ✅ 4-agent workflow tested and verified
- ✅ Feedback loop activated and tested (70% pass rate, 2 insights generated)
- ✅ Caching layer complete (100% hit rate verified)
- ✅ Unit tests comprehensive (30+ tests)
- ✅ Integration tests passing

**Skipped/Optional:**
- ⏸️ Cerebras integration (Azure OpenAI sufficient)
- 📋 Infrastructure integration (depends on Developer B, optional)

**Result:** ✅ **Sprint 9 100% Complete** - Ready for Sprint 10

---

## ✅ What’s Already Done (API v2 – as of Feb 2026)

The following are **already implemented** in the codebase (no need to redo):

| Item | Status | Location |
|------|--------|----------|
| **10A.1** API schema & stubs | ✅ Done | `backend/app/schemas/workflow.py`, all v2 endpoints |
| **10A.2** POST `/api/v2/generate-tests` | ✅ Done | `backend/app/api/v2/endpoints/generate_tests.py` — 202, background workflow |
| **Multi-entry API** | ✅ Done | POST `/observation`, `/requirements`, `/analysis`, `/evolution`, `/improve-tests` |
| **10A.4** OrchestrationService | ✅ Done | `backend/app/services/orchestration_service.py` — `run_workflow` + per-stage methods |
| **10A.5** GET workflow status & results | ✅ Done | `backend/app/api/v2/endpoints/workflows.py` — GET `/{id}`, GET `/{id}/results` |
| **10A.3** SSE stream | ✅ Done | `backend/app/api/v2/endpoints/sse_stream.py` — StreamingResponse; `ProgressTracker` in-memory queues + `subscribe()` |
| **ProgressTracker** | ✅ Done | `backend/app/services/progress_tracker.py` — in-memory queues, `emit()`, `subscribe()`; orchestration emits; optional Redis hook |
| **API specification** | ✅ Done | [API_SPECIFICATION.md](../backend/app/api/v2/API_SPECIFICATION.md) — parameters, examples, chaining |
| **Workflow store** | ✅ Done | In-memory store in `workflow_store.py` (status/results); `request_cancel` / `is_cancel_requested` for cancel |
| **10A.5** DELETE cancel workflow | ✅ Done | `workflows.py` — 204/404; store flag; orchestration checks between stages |
| **10A.6** Unit tests | ✅ Done | `tests/unit/test_workflow_store.py`, `test_api_v2_endpoints.py`, `test_orchestration_cancel.py` (20 tests) |

**Recent (Feb 2026):** Observation working (Windows ProactorEventLoop); SSE (10A.3) implemented; workflow cancel (10A.5) and unit tests (10A.6) implemented.

**Still stub / not implemented:**

| Item | Status | What to do |
|------|--------|------------|
| **10A.8** Iterative improvement | 🔨 Stub | `run_iterative_workflow` logs only; implement evolution → analysis loop |
| **10A.7, 10A.9, 10A.10, 10A.11** | ⏳ Pending | Multi-page crawl, dynamic URL, goal-oriented nav, integration tests |

---

## 🎯 Developer A: Next Steps (in order)

### 1. ~~**SSE real-time progress (10A.3)**~~ — ✅ **DONE** (Feb 2026)

- **Goal:** Frontend can open `GET /api/v2/workflows/{workflow_id}/stream` and receive real-time events.
- **Implemented:** In-memory `ProgressTracker` (queues + `subscribe()`), SSE endpoint in `sse_stream.py` (StreamingResponse, event types per API spec). Optional Redis can be added later.

### 2. ~~**Implement workflow cancel (10A.5)**~~ — ✅ **DONE** (Feb 2026)

- **Implemented:** DELETE returns 204/404; `request_cancel` / `is_cancel_requested` in workflow store; orchestration checks between stages and sets status `cancelled`.

### 3. ~~**Unit tests (10A.6)**~~ — ✅ **DONE** (Feb 2026)

- **Implemented:** 20 unit tests in `tests/unit/`: workflow_store (get/set/update/delete, request_cancel, is_cancel_requested), API v2 endpoints (POST generate-tests 202, GET status/results 200/404, DELETE cancel 204/404), orchestration cancel (run_workflow exits when cancel requested).

### 4. **API spec handoff to Developer B**

- **Goal:** Developer B can build the frontend from a stable contract.
- **Tasks:**
  - [ ] Confirm OpenAPI at `/api/v2/docs` and `/api/v2/openapi.json` (FastAPI default).
  - [ ] Point Developer B to [API_SPECIFICATION.md](../backend/app/api/v2/API_SPECIFICATION.md) and `/api/v2/docs` for endpoints, request/response, and SSE.

### 5. **Later (Sprint 10 backlog)**

- **10A.8** Iterative improvement: implement `run_iterative_workflow` (evolution → analysis loop, convergence).
- **10A.7** Multi-page flow crawling (ObservationAgent).
- **10A.9** Dynamic URL crawling (EvolutionAgent).
- **10A.10** Goal-oriented navigation (ObservationAgent).
- **10A.11** Integration tests for iterative workflow.

---

## 🚀 Immediate Next Steps (Before Sprint 10)

### Week 1: Preparation & Planning (Feb 10-16, 2026)

#### Day 1-2: Review & Preparation (Feb 10-11)

**Action Items:**
- [ ] **Review Sprint 10 Requirements**
  - [ ] Read [Sprint 10 Gap Analysis](supporting-documents/SPRINT_10_GAP_ANALYSIS_AND_PLAN.md)
  - [ ] Review [Task Split Strategy](SPRINT_10_11_TASK_SPLIT_STRATEGY.md)
  - [ ] Understand API-first handoff (complete API → pass spec to Developer B)
  - [ ] Review Server-Sent Events (SSE) implementation patterns

- [ ] **Technical Research**
  - [ ] Research FastAPI SSE implementation (Starlette EventSourceResponse)
  - [ ] Review Redis pub/sub patterns for progress tracking
  - [ ] Study GitHub Actions API for UI inspiration
  - [ ] Review existing API v1 structure for consistency

- [ ] **Environment Setup**
  - [ ] Verify Redis is accessible (for pub/sub)
  - [ ] Test existing 4-agent workflow (ensure it works)
  - [ ] Review current agent integration points
  - [ ] Set up feature branch: `feature/sprint10-backend-api`

**Deliverables:**
- ✅ Understanding of Sprint 10 requirements
- ✅ Technical research notes
- ✅ Development environment ready

---

#### Day 3-5: Design & Architecture (Feb 12-14)

**Action Items:**
- [ ] **Design API v2 Structure**
  - [ ] Design `/api/v2/generate-tests` endpoint schema
  - [ ] Design workflow status endpoints
  - [ ] Design SSE event schema
  - [ ] Design error handling strategy

- [ ] **Design OrchestrationService**
  - [ ] Define service interface
  - [ ] Design workflow state machine
  - [ ] Design progress tracking mechanism
  - [ ] Design Redis pub/sub event structure

- [ ] **Create Technical Design Document**
  - [ ] API endpoint specifications
  - [ ] Service architecture diagram
  - [ ] Data flow diagrams
  - [ ] Integration points with existing agents

**Deliverables:**
- ✅ API v2 design document
- ✅ OrchestrationService design
- ✅ Technical architecture ready for implementation

---

#### Day 6-7: Code Review & Cleanup (Feb 15-16)

**Action Items:**
- [ ] **Code Review Sprint 9 Work**
  - [ ] Review EvolutionAgent code quality
  - [ ] Check for any technical debt
  - [ ] Ensure all tests are passing
  - [ ] Update documentation if needed

- [ ] **Prepare for Sprint 10**
  - [ ] Create feature branch structure
  - [ ] Set up development environment
  - [ ] Review existing codebase structure
  - [ ] Identify integration points

**Deliverables:**
- ✅ Clean codebase
- ✅ All tests passing
- ✅ Ready for Sprint 10 Day 1

---

### Week 2: Sprint 10 Preparation (Feb 17-23, 2026)

#### Day 8-10: Mockups & Prototypes (Feb 17-19)

**Action Items:**
- [ ] **Create API Mockups**
  - [ ] Create stub endpoints (return 501 Not Implemented)
  - [ ] Create example request/response payloads
  - [ ] Document API contract in OpenAPI format
  - [ ] Create Postman/Insomnia collection

- [ ] **Prototype OrchestrationService**
  - [ ] Create basic service structure
  - [ ] Implement stub methods
  - [ ] Test service initialization
  - [ ] Verify integration points

**Deliverables:**
- ✅ API stub endpoints
- ✅ OrchestrationService prototype
- ✅ API documentation draft

---

#### Day 11-14: Final Preparation (Feb 20-23)

**Action Items:**
- [ ] **Final Preparation**
  - [ ] Review all Sprint 10 tasks
  - [ ] Prepare implementation checklist
  - [ ] Set up development tools
  - [ ] Create task tracking (if using Jira/Linear)

- [ ] **Plan API Handoff (for Developer B)**
  - [ ] Ensure OpenAPI/Swagger will be available at `/api/v2/docs` when API is complete
  - [ ] Note: No joint session required; Developer A completes API and passes spec to Developer B for frontend development

**Deliverables:**
- ✅ Ready for Sprint 10 kickoff
- ✅ Clear handoff approach (API spec → Developer B)

---

## 📅 Sprint 10: Detailed Action Plan

**Workflow:** Developer A completes the API and documents the spec; then passes the spec to Developer B for frontend development. No joint API Contract Definition session required.

### Day 1: Verify Stubs & Start Implementation (Mar 6, 2026)

**Goal:** Confirm API v2 stubs and structure; begin full implementation.

**Tasks:**
- [ ] **Verify existing structure** (stubs already created in `feature/sprint10-backend-api`):
  - [ ] Confirm `backend/app/api/v2/` and `backend/app/schemas/workflow.py` exist
  - [ ] Confirm Pydantic schemas: `GenerateTestsRequest`, `WorkflowStatusResponse`, `AgentProgressEvent`, `WorkflowResultsResponse`, `WorkflowErrorResponse`
  - [ ] Confirm stub endpoints return 501; v2 router registered in main app
- [ ] **SSE event types** (already in design; implement during Days 2–5):
  - `agent_started`, `agent_progress`, `agent_completed`, `workflow_completed`, `workflow_failed`
- [ ] **Begin Task 10A.2** if time permits (generate-tests endpoint)

**Deliverables:**
- ✅ Stubs verified
- ✅ Ready to implement full API

---

### Days 2-3: Create `/api/v2/generate-tests` Endpoint (Mar 7-8, 2026)

**Task 10A.2: 2 days, 5 points**

**Implementation Steps:**

1. **Create Endpoint File:**
   ```python
   # backend/app/api/v2/endpoints/generate_tests.py
   from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
   from app.schemas.workflow import GenerateTestsRequest, WorkflowStatusResponse
   from app.services.orchestration_service import OrchestrationService
   
   router = APIRouter()
   
   @router.post("/generate-tests", response_model=WorkflowStatusResponse)
   async def generate_tests(
       request: GenerateTestsRequest,
       background_tasks: BackgroundTasks,
       orchestration_service: OrchestrationService = Depends(get_orchestration_service)
   ):
       # 1. Validate request
       # 2. Create workflow_id
       # 3. Start workflow in background
       # 4. Return workflow_id immediately
       pass
   ```

2. **Integrate with Existing Agents:**
   - Use existing `ObservationAgent`, `RequirementsAgent`, `AnalysisAgent`, `EvolutionAgent`
   - Call agents in sequence via `OrchestrationService`
   - Track progress via `ProgressTracker`

3. **Error Handling:**
   - Validate input (URL, user instructions)
   - Handle agent failures gracefully
   - Return appropriate error responses

**Deliverables:**
- ✅ `/api/v2/generate-tests` endpoint operational
- ✅ Returns workflow_id immediately
- ✅ Starts 4-agent workflow in background
- ✅ Basic error handling

**Success Criteria:**
- ✅ Endpoint accepts POST request
- ✅ Returns workflow_id
- ✅ Workflow starts in background
- ✅ Unit tests passing

---

### Days 4-5: Implement Server-Sent Events (SSE) (Mar 9-10, 2026)

**Task 10A.3: 2 days, 8 points**

**Implementation Steps:**

1. **Create SSE Endpoint:**
   ```python
   # backend/app/api/v2/endpoints/sse_stream.py
   from fastapi import APIRouter
   from sse_starlette.sse import EventSourceResponse
   from app.services.progress_tracker import ProgressTracker
   
   router = APIRouter()
   
   @router.get("/workflows/{workflow_id}/stream")
   async def stream_workflow_progress(workflow_id: str):
       async def event_generator():
           # Subscribe to Redis pub/sub
           # Yield SSE events as they arrive
           pass
       
       return EventSourceResponse(event_generator())
   ```

2. **Implement ProgressTracker:**
   ```python
   # backend/app/services/progress_tracker.py
   import redis.asyncio as redis
   import json
   
   class ProgressTracker:
       def __init__(self, redis_client: redis.Redis):
           self.redis = redis_client
       
       async def emit(self, workflow_id: str, event_type: str, data: dict):
           # Publish to Redis channel: workflow:{workflow_id}
           await self.redis.publish(
               f"workflow:{workflow_id}",
               json.dumps({
                   "event": event_type,
                   "data": data,
                   "timestamp": datetime.now().isoformat()
               })
           )
   ```

3. **Integrate with OrchestrationService:**
   - Emit `agent_started` when agent begins
   - Emit `agent_progress` during execution
   - Emit `agent_completed` when agent finishes
   - Emit `workflow_completed` when all agents done

**Deliverables:**
- ✅ SSE endpoint operational
- ✅ ProgressTracker emits events to Redis
- ✅ Events stream to frontend in real-time
- ✅ Event types: started, progress, completed, failed

**Success Criteria:**
- ✅ Frontend can connect to SSE stream
- ✅ Events received in real-time
- ✅ All event types working
- ✅ Unit tests passing

---

### Days 6-7: Implement OrchestrationService (Mar 11-12, 2026)

**Task 10A.4: 2 days, 8 points**

**Implementation Steps:**

1. **Create OrchestrationService:**
   ```python
   # backend/app/services/orchestration_service.py
   from app.agents.observation_agent import ObservationAgent
   from app.agents.requirements_agent import RequirementsAgent
   from app.agents.analysis_agent import AnalysisAgent
   from app.agents.evolution_agent import EvolutionAgent
   from app.services.progress_tracker import ProgressTracker
   
   class OrchestrationService:
       def __init__(self, progress_tracker: ProgressTracker):
           self.progress_tracker = progress_tracker
           self.observation_agent = ObservationAgent()
           self.requirements_agent = RequirementsAgent()
           self.analysis_agent = AnalysisAgent()
           self.evolution_agent = EvolutionAgent()
       
       async def run_workflow(self, workflow_id: str, request: GenerateTestsRequest):
           try:
               # Stage 1: Observation
               await self.progress_tracker.emit(workflow_id, "agent_started", {
                   "agent": "observation",
                   "timestamp": datetime.now().isoformat()
               })
               observation_result = await self.observation_agent.observe(request.url)
               await self.progress_tracker.emit(workflow_id, "agent_completed", {
                   "agent": "observation",
                   "result": observation_result,
                   "duration": ...
               })
               
               # Stage 2: Requirements
               await self.progress_tracker.emit(workflow_id, "agent_started", {
                   "agent": "requirements"
               })
               requirements_result = await self.requirements_agent.extract_requirements(
                   observation_result,
                   user_instruction=request.user_instruction
               )
               await self.progress_tracker.emit(workflow_id, "agent_completed", {
                   "agent": "requirements",
                   "result": requirements_result
               })
               
               # Stage 3: Analysis
               # ... similar pattern
               
               # Stage 4: Evolution
               # ... similar pattern
               
               # Final
               await self.progress_tracker.emit(workflow_id, "workflow_completed", {
                   "workflow_id": workflow_id,
                   "results": {...}
               })
               
           except Exception as e:
               await self.progress_tracker.emit(workflow_id, "workflow_failed", {
                   "error": str(e)
               })
               raise
   ```

2. **Integrate with Existing Agents:**
   - Use existing agent instances
   - Pass data between agents in sequence
   - Handle errors gracefully

3. **Workflow State Management:**
   - Store workflow state in database
   - Track current stage
   - Support cancellation

**Deliverables:**
- ✅ OrchestrationService coordinates 4-agent workflow
- ✅ Progress events emitted at each stage
- ✅ Error handling and recovery
- ✅ Workflow state persisted

**Success Criteria:**
- ✅ 4-agent workflow executes successfully
- ✅ Progress events emitted correctly
- ✅ Errors handled gracefully
- ✅ Unit tests passing

---

### Day 8: Create Workflow Status Endpoints (Mar 13, 2026)

**Task 10A.5: 1 day, 3 points**

**Implementation Steps:**

1. **Create Workflow Endpoints:**
   ```python
   # backend/app/api/v2/endpoints/workflows.py
   @router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
   async def get_workflow_status(workflow_id: str):
       # Query database for workflow status
       pass
   
   @router.get("/workflows/{workflow_id}/results", response_model=WorkflowResultsResponse)
   async def get_workflow_results(workflow_id: str):
       # Return generated tests
       pass
   
   @router.delete("/workflows/{workflow_id}")
   async def cancel_workflow(workflow_id: str):
       # Cancel running workflow
       pass
   ```

2. **Database Integration:**
   - Create workflow table (if not exists)
   - Store workflow state
   - Query workflow status

**Deliverables:**
- ✅ GET `/workflows/{id}` - Get status
- ✅ GET `/workflows/{id}/results` - Get results
- ✅ DELETE `/workflows/{id}` - Cancel workflow

**Success Criteria:**
- ✅ All endpoints operational
- ✅ Database integration working
- ✅ Unit tests passing

---

### Day 9: Unit Tests (Mar 14, 2026)

**Task 10A.6: 1 day, 5 points**

**Test Coverage:**
- [ ] Test `/api/v2/generate-tests` endpoint
- [ ] Test SSE streaming
- [ ] Test OrchestrationService workflow
- [ ] Test progress tracking
- [ ] Test error handling
- [ ] Test workflow cancellation

**Deliverables:**
- ✅ Comprehensive unit tests
- ✅ 90%+ code coverage
- ✅ All tests passing

---

### After API Complete: API Spec Handoff to Developer B

**Goal:** Hand off API spec so Developer B can build the frontend against a stable contract. No joint session required.

**Tasks:**
- [ ] **Publish API spec**
  - [ ] Ensure OpenAPI available at `GET /api/v2/openapi.json` and Swagger UI at `/api/v2/docs`
  - [ ] Document SSE: stream URL, event types, and example JSON payloads (e.g. in `backend/app/api/v2/README.md` or a short handoff note)
- [ ] **Hand off to Developer B**
  - [ ] Share spec location and any handoff note (endpoints, auth, SSE URL, event shapes)
  - [ ] Developer B uses spec to generate TypeScript types / API client and implement frontend

**Deliverables:**
- ✅ OpenAPI + SSE docs available
- ✅ Developer B has everything needed to start frontend development

---

## 📋 Sprint 10 Checklist

### Pre-Sprint Preparation (Feb 10 - Mar 5, 2026)
- [ ] Review Sprint 10 requirements
- [ ] Research SSE implementation
- [ ] Design API v2 structure
- [ ] Create technical design document
- [ ] Set up development environment

### Sprint 10 Day 1 (Mar 6, 2026)
- [ ] Verify API v2 stubs and structure
- [ ] Begin implementation (Task 10A.2 if time permits)

### Sprint 10 Days 2-9 (Mar 7-14, 2026)
- [ ] Task 10A.2: Create `/api/v2/generate-tests` endpoint
- [ ] Task 10A.3: Implement SSE for real-time progress
- [ ] Task 10A.4: Implement OrchestrationService
- [ ] Task 10A.5: Create workflow status endpoints
- [ ] Task 10A.6: Unit tests

### After API Complete: API Spec Handoff
- [ ] Publish OpenAPI + SSE docs
- [ ] Pass spec to Developer B for frontend development (no joint session)

### Sprint 10 Days 10-15 (Mar 15-19, 2026)
- [ ] Integration testing (once Developer B frontend is ready)
- [ ] Fix any integration issues
- [ ] Code review
- [ ] Merge to `develop` branch
- [ ] Sprint 10 retrospective

---

## 🎯 Success Metrics

### Sprint 10 Goals
- ✅ `/api/v2/generate-tests` operational
- ✅ SSE streaming working
- ✅ 4-agent workflow coordinated
- ✅ Real-time progress visible
- ✅ Zero merge conflicts (layer-based separation)
- ✅ 90%+ test coverage

### Quality Metrics
- ✅ All unit tests passing
- ✅ API documentation complete
- ✅ Code review approved
- ✅ Integration tests passing (after frontend integration)

---

## 📚 Key Resources

### Documentation
- **[API v2 Specification](../backend/app/api/v2/API_SPECIFICATION.md)** — Endpoints, request/response parameters, examples, SSE (§6), chaining
- [Sprint 10 Gap Analysis](supporting-documents/SPRINT_10_GAP_ANALYSIS_AND_PLAN.md)
- [Task Split Strategy](SPRINT_10_11_TASK_SPLIT_STRATEGY.md)
- [Architecture Design](Phase3-Architecture-Design-Complete.md)
- [Implementation Guide](Phase3-Implementation-Guide-Complete.md)

### Technical References
- FastAPI SSE: https://fastapi.tiangolo.com/advanced/server-sent-events/
- Redis Pub/Sub: https://redis.io/docs/manual/pubsub/
- Starlette EventSourceResponse: https://www.starlette.io/responses/#eventsourceresponse

### Code Examples
- Existing API v1 structure: `backend/app/api/v1/`
- Existing agents: `backend/agents/`
- Existing services: `backend/app/services/`

---

## 🚨 Risk Mitigation

### Potential Risks

1. **Redis Connection Issues**
   - **Mitigation:** Test Redis connection early, have fallback plan
   - **Action:** Verify Redis setup before Sprint 10 Day 1

2. **Agent Integration Complexity**
   - **Mitigation:** Use existing agent instances, test integration early
   - **Action:** Create integration test early in sprint

3. **SSE Implementation Challenges**
   - **Mitigation:** Research SSE patterns, use proven libraries
   - **Action:** Prototype SSE early (Week 2 preparation)

4. **Merge Conflicts (Low Risk)**
   - **Mitigation:** Layer-based separation (backend only)
   - **Action:** Follow task split strategy strictly

---

## ✅ Sign-Off

**Prepared By:** AI Development Assistant  
**Date:** February 10, 2026  
**Status:** ✅ **READY FOR SPRINT 10**  
**Next Action:** Begin Week 1 preparation tasks. After API is complete, pass spec to Developer B for frontend (no joint session).

---

**Developer A is ready to start Sprint 10 with a clear action plan!** 🚀

