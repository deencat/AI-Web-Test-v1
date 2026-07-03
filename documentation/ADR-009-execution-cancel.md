# ADR-009: Cooperative Cancel for Test Executions

**Document ID:** ADR-009  
**Component:** Test Execution / Queue Manager / Execution Progress UI  
**Status:** Accepted  
**Date:** July 3, 2026  
**Related Files:**
- `backend/app/services/execution_cancel_store.py`
- `backend/app/crud/test_execution.py` (`cancel_execution`)
- `backend/app/api/v1/endpoints/executions.py` (`DELETE /{execution_id}/cancel`)
- `backend/app/services/execution_service.py`
- `backend/app/services/three_tier_execution_service.py`
- `backend/app/services/queue_manager.py`
- `frontend/src/components/execution/StopExecutionButton.tsx`
- `frontend/src/services/executionService.ts`
- `frontend/src/pages/ExecutionProgressPage.tsx`

---

## Context

Saved test runs execute through a 3-tier stack (Playwright → XPath → Stagehand). Users need to abort long or mistaken runs without force-refreshing or deleting execution records. Agent workflows already use cooperative cancel via `workflow_store.py` (ADR-004).

## Decision

Adopt the **same cooperative cancel pattern** as agent workflows:

1. **`DELETE /api/v1/executions/{id}/cancel`** sets cancel state (dequeue + DB cancel for `pending`; in-memory flag for `running`).
2. **Worker** polls between steps and tier boundaries — no thread killing.
3. **Finalize** with `status=cancelled`, partial step counts preserved; never `failed`.
4. **`finally`** always runs Playwright/Stagehand cleanup.
5. **Frontend** shows Stop on progress page; poll-confirmed status (no optimistic UI).

## Alternatives Rejected

| Approach | Verdict |
|----------|---------|
| Force-kill worker thread | Rejected — orphaned browsers, corrupt DB |
| `DELETE /executions/{id}` for cancel | Rejected — conflates cancel with record deletion |
| DB-only cancel flag | Rejected for v1 — per-step DB polls too slow |
| Optimistic frontend cancel | Rejected — requires poll-confirmed badge flip |
| Redis-backed store | Deferred — in-memory mirrors `workflow_store` for v1 |

## State Machine

```
pending ──cancel──► cancelled (dequeued, DB updated)
   │
   ▼ worker start
running ──cancel flag──► cancelled (cooperative finalize)
```

Terminal states (`completed`, `failed`, `cancelled`) return **204** idempotently on cancel.

## API Contract

- **Route:** `DELETE /api/v1/executions/{execution_id}/cancel`
- **Auth:** Required; ownership matches existing execution endpoints
- **Responses:** 204 success, 404 not found, 403 wrong user

## Implementation Notes

- `execution_cancel_store.py`: thread-safe `register_cancel`, `request_cancel`, `is_cancel_requested`, `clear_cancel` keyed by `execution_id` (int).
- `queue_manager`: pre-start DB guard skips cancelled items; `clear_cancel` in worker `finally`.
- `ThreeTierExecutionService.execute_step(..., cancel_check=)` polls before Tier 1/2/3 boundaries.
- `StopExecutionButton` mirrors `StopAgentButton` UX on `ExecutionProgressPage`.

## Consequences

- Cancel latency bounded by current step/tier (up to ~120s mid–Tier 3 LLM call).
- In-memory store is single-process; multi-worker deployments need Redis (future).
- Suite-level bulk cancel remains out of scope.
