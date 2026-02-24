# API v2 - Agent Workflow Endpoints

**Sprint:** Sprint 10 - Frontend Integration & Real-time Agent Progress  
**Developer:** Developer A  
**Branch:** `feature/sprint10-backend-api`  
**Status:** ✅ **PARTIAL** — generate-tests, status, results, SSE implemented; DELETE cancel still stub (Feb 2026)

---

## 📋 Overview

API v2 provides **multiple entry points** (per-agent and per-use-case). All runs return a `workflow_id`; status and results use the shared workflow resource.

- **POST** `/api/v2/generate-tests` - Full pipeline (generate from URL)
- **POST** `/api/v2/observation` - ObservationAgent only
- **POST** `/api/v2/requirements` - RequirementsAgent only (input: workflow_id or observation_result)
- **POST** `/api/v2/analysis` - AnalysisAgent only (input: workflow_id or prior results)
- **POST** `/api/v2/evolution` - EvolutionAgent only (input: workflow_id or prior results)
- **POST** `/api/v2/improve-tests` - Improve existing tests by ID (iterative)
- **GET** `/api/v2/workflows/{id}/stream` - SSE progress stream
- **GET** `/api/v2/workflows/{id}` - Workflow status
- **GET** `/api/v2/workflows/{id}/results` - Workflow results (partial or full)
- **DELETE** `/api/v2/workflows/{id}` - Cancel workflow

**📖 API reference:** Full request/response parameters, types, and examples: **[API_SPECIFICATION.md](./API_SPECIFICATION.md)**. Interactive docs: `/api/v2/docs`.

### What this API does

- **Full pipeline:** POST `/generate-tests` with a URL runs all 4 agents and returns `workflow_id`; results include `test_case_ids` and agent outputs.
- **Per-agent / improve:** POST `/observation`, `/requirements`, `/analysis`, `/evolution` run one stage (chain via `workflow_id`). POST `/improve-tests` with `test_case_ids` runs iterative improvement. 

- **Unified resource:** GET `/workflows/{id}` and GET `/workflows/{id}/results` for status and partial/full results.

### (Obsolete) What this API did *not* do before multi-entry

- **Re-run or improve by test case ID (now supported via POST /improve-tests):** The request body does **not** accept “existing test case IDs” to re-run or to ask the agents to “improve these tests.” Input is always a **URL** (and optional instruction/credentials). To **run** existing test cases (by ID), use the **execution API** (e.g. API v1: run test by ID). To **improve** existing tests in a loop (e.g. iterative evolution → analysis), the design exists in the codebase (e.g. `run_iterative_workflow` stub) but is **not** exposed as an API endpoint yet.

---

## 🏗️ Current Structure

### Created Files

```
backend/app/api/v2/
├── __init__.py                    ✅ Created
├── api.py                         ✅ Created (registers routers)
├── README.md                      ✅ Created (this file)
└── endpoints/
    ├── __init__.py                ✅ Created
    ├── generate_tests.py          ✅ Full pipeline (POST /generate-tests)
    ├── observation.py             ✅ Observation only (POST /observation)
    ├── requirements.py            ✅ Requirements only (POST /requirements)
    ├── analysis.py                ✅ Analysis only (POST /analysis)
    ├── evolution.py               ✅ Evolution only (POST /evolution)
    ├── improve_tests.py           ✅ Improve by ID (POST /improve-tests)
    ├── workflows.py               ✅ Status, results, cancel
    └── sse_stream.py              ✅ SSE progress stream

backend/app/schemas/
└── workflow.py                    ✅ Created (Pydantic models)

backend/app/services/
├── orchestration_service.py       ✅ Implemented (run_workflow, per-stage)
└── progress_tracker.py            ✅ Implemented (in-memory queues, emit, subscribe)
```

### Updated Files

- `backend/app/core/config.py` - Added `API_V2_STR = "/api/v2"`
- `backend/app/main.py` - Registered v2 router

---

## 🔨 Implementation Status (Feb 2026)

| Endpoint | Status | Notes |
|----------|--------|--------|
| POST `/api/v2/generate-tests` | ✅ Done | 202, background workflow; Observation (browser-use/Playwright) working on Windows |
| GET `/api/v2/workflows/{id}/stream` | ✅ Done | SSE; in-memory ProgressTracker, event types per API spec |
| GET `/api/v2/workflows/{id}` | ✅ Done | Workflow status |
| GET `/api/v2/workflows/{id}/results` | ✅ Done | Partial/full results |
| DELETE `/api/v2/workflows/{id}` | 🔨 Stub (501) | Next: implement cancel (store flag + orchestration check) |

---

## 📝 Next Steps

### Day 1: API Contract Definition (Mar 6, 2026)

**Morning Session (2 hours) with Developer B:**
- [ ] Review Pydantic schemas in `backend/app/schemas/workflow.py`
- [ ] Lock API contracts (no changes without discussion)
- [ ] Verify TypeScript types match Pydantic schemas
- [ ] Create example request/response payloads

**Afternoon: Implementation Setup**
- [ ] Test stub endpoints (should return 501)
- [ ] Verify API v2 router is registered
- [ ] Test OpenAPI docs at `/api/v2/docs`

### Days 2-3: Implement `/api/v2/generate-tests`

- [ ] Implement endpoint logic
- [ ] Integrate with OrchestrationService
- [ ] Add error handling
- [ ] Write unit tests

### Days 4-5: Implement SSE Streaming

- [ ] Implement ProgressTracker with Redis
- [ ] Create SSE endpoint
- [ ] Test event streaming
- [ ] Write unit tests

### Days 6-7: Implement OrchestrationService

- [ ] Integrate with existing 4 agents
- [ ] Implement workflow coordination
- [ ] Add progress tracking
- [ ] Write unit tests

### Day 8: Implement Workflow Status Endpoints

- [ ] Implement GET `/workflows/{id}`
- [ ] Implement GET `/workflows/{id}/results`
- [ ] Implement DELETE `/workflows/{id}`
- [ ] Write unit tests

### Day 9: Unit Tests

- [ ] Comprehensive test coverage
- [ ] Integration tests
- [ ] 90%+ code coverage

---

## 🧪 Testing

### Test Stub Endpoints

```bash
# Start backend server
cd backend
python -m uvicorn app.main:app --reload

# Test stub endpoint (should return 501)
curl -X POST http://localhost:8000/api/v2/generate-tests \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Expected Response (STUB)

```json
{
  "detail": {
    "error": "Endpoint not yet implemented",
    "code": "NOT_IMPLEMENTED",
    "message": "This endpoint is a stub. Implementation will be completed in Sprint 10 Days 2-3.",
    "workflow_id": null,
    "timestamp": "2026-02-11T..."
  }
}
```

---

## 📚 References

- [Developer A Next Steps](../Phase3-project-documents/DEVELOPER_A_NEXT_STEPS.md)
- [Task Split Strategy](../Phase3-project-documents/SPRINT_10_11_TASK_SPLIT_STRATEGY.md)
- [Sprint 10 Gap Analysis](../Phase3-project-documents/supporting-documents/SPRINT_10_GAP_ANALYSIS_AND_PLAN.md)
- [Architecture Design](../Phase3-project-documents/Phase3-Architecture-Design-Complete.md)

---

## ✅ Checklist

- [x] Create feature branch `feature/sprint10-backend-api`
- [x] Create API v2 directory structure
- [x] Create Pydantic schemas
- [x] Create stub endpoints (return 501)
- [x] Create service stubs (OrchestrationService, ProgressTracker)
- [x] Register v2 router in main app
- [x] Test stub endpoints
- [ ] Day 1: API Contract Definition with Developer B
- [ ] Days 2-9: Implement endpoints and services

---

**Status:** ✅ **BRANCH CREATED, STUB STRUCTURE READY**  
**Next Action:** Day 1 API Contract Definition session (Mar 6, 2026)

