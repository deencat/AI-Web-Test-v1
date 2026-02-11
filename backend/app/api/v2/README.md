# API v2 - Agent Workflow Endpoints

**Sprint:** Sprint 10 - Frontend Integration & Real-time Agent Progress  
**Developer:** Developer A  
**Branch:** `feature/sprint10-backend-api`  
**Status:** 🔨 **STUB IMPLEMENTATION** (Ready for Day 1 API Contract Definition)

---

## 📋 Overview

API v2 provides endpoints for managing the 4-agent workflow:
- **POST** `/api/v2/generate-tests` - Trigger workflow
- **GET** `/api/v2/workflows/{id}/stream` - SSE progress stream
- **GET** `/api/v2/workflows/{id}` - Get workflow status
- **GET** `/api/v2/workflows/{id}/results` - Get workflow results
- **DELETE** `/api/v2/workflows/{id}` - Cancel workflow

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
    ├── generate_tests.py           ✅ Created (STUB - returns 501)
    ├── workflows.py                ✅ Created (STUB - returns 501)
    └── sse_stream.py              ✅ Created (STUB - returns 501)

backend/app/schemas/
└── workflow.py                    ✅ Created (Pydantic models)

backend/app/services/
├── orchestration_service.py       ✅ Created (STUB)
└── progress_tracker.py            ✅ Created (STUB)
```

### Updated Files

- `backend/app/core/config.py` - Added `API_V2_STR = "/api/v2"`
- `backend/app/main.py` - Registered v2 router

---

## 🔨 Stub Implementation Status

All endpoints currently return **501 Not Implemented**. This is intentional - they will be implemented during Sprint 10:

| Endpoint | Status | Implementation |
|----------|--------|----------------|
| POST `/api/v2/generate-tests` | 🔨 STUB | Sprint 10 Days 2-3 |
| GET `/api/v2/workflows/{id}/stream` | 🔨 STUB | Sprint 10 Days 4-5 |
| GET `/api/v2/workflows/{id}` | 🔨 STUB | Sprint 10 Day 8 |
| GET `/api/v2/workflows/{id}/results` | 🔨 STUB | Sprint 10 Day 8 |
| DELETE `/api/v2/workflows/{id}` | 🔨 STUB | Sprint 10 Day 8 |

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

