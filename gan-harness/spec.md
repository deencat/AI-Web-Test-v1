# Product Specification: AI Web Test v1 — GAN Harness Features

This document contains feature specs for the GAN harness. Each major section is self-contained.

| # | Feature | Brief |
|---|---------|-------|
| 1 | Stop Execution | Cooperative cancel for 3-tier test runs |
| 2 | Clone Test Case | Duplicate a saved test case with one click |
| 3 | CRM Login Toggle Persist | Fix `requires_runtime_credentials` omitted by API sanitizer |
| 4 | Timed Wait Step | First-class cancel-aware wait steps (UI + NL parse); not a loop block |
| 5 | Signature Pad Ink Verification | Fix Tier 3 false-PASS on empty canvas; programmatic stroke + ink verify |

---

# Feature 1: Stop Execution — Cooperative Cancel for 3-Tier Test Runs

> Generated from brief: *"Add a Stop button to stop 3-tier test execution (Playwright → XPath → Stagehand AI) for saved test runs."*

---

## Vision

When a saved test is running through the 3-tier execution stack, users need a **safe, predictable way to abort** without waiting for every step and tier fallback to finish. **Stop Execution** gives them a red **Stop** control on the execution progress page that mirrors the existing agent workflow cancel pattern: cooperative polling between steps and between tiers, no thread killing, and backend-confirmed `cancelled` status via the existing 2-second poll loop.

The experience should feel identical in spirit to **Stop Agent** — click Stop, see "Stopping execution…", wait for the badge to flip to **Cancelled**, partial step history preserved. Users who queued a long test by mistake can cancel while **pending** before a browser ever opens.

---

## User Story

**As a** QA engineer running a saved test case,  
**I want** to stop an in-progress or queued execution from the progress page,  
**So that** I can abort mistaken runs, long-hanging Stagehand fallbacks, or tests pointed at the wrong environment without force-refreshing or deleting the execution record.

**Acceptance (happy path):**
1. User clicks **Run** on a saved test → lands on `/executions/{id}`.
2. While `status` is `pending` or `running`, **Stop Execution** is visible and enabled.
3. User clicks Stop → inline **"Stopping execution…"** appears; button disables.
4. Within cooperative bounds (up to ~120s if mid–Tier 3 LLM call), status becomes `cancelled`.
5. Partial completed steps remain listed; Execution History shows `cancelled` filter match.
6. `DELETE /executions/{id}` still deletes the record; cancel does not.

---

## Scope

### In scope

| Area | Deliverable |
|------|-------------|
| Backend store | `execution_cancel_store.py` — thread-safe in-memory cancel flags keyed by `execution_id` |
| Backend API | `DELETE /api/v1/executions/{execution_id}/cancel` → 204 |
| CRUD | `cancel_execution()` — DB finalization helper |
| Queue | Dequeue pending; pre-start guard in `queue_manager` |
| Execution loop | Cooperative polls in `execute_test()` step loop (incl. loop bodies) |
| 3-tier | `cancel_check` param on `ThreeTierExecutionService.execute_step()` |
| Frontend | `StopExecutionButton.tsx`, `executionService.cancelExecution()`, wire on `ExecutionProgressPage` |
| Tests | Unit + component tests per rubric |
| Docs | ADR-009 (new) or ADR-002 addendum section |

### Out of scope

- Stop button on `SavedTestsPage` or list views (progress page only for v1)
- Suite-level bulk cancel (`suite_execution_service.py`)
- WebSocket push for instant status (keep 2s polling)
- Force-kill threads, `asyncio.Task.cancel()`, or process signals
- Reusing `DELETE /executions/{id}` for cancel (breaks delete semantics)
- Optimistic UI (`status=cancelled` before API/poll confirms)
- Redis-backed cancel store (in-memory mirrors `workflow_store.py` for v1)
- Admin "cancel any user's execution" (ownership rules match existing execution endpoints)

---

## Current State Analysis

### What exists

| Layer | Location | Status |
|-------|----------|--------|
| `ExecutionStatus.CANCELLED` | `backend/app/models/test_execution.py` | Enum value present |
| Frontend `cancelled` type | `frontend/src/types/execution.ts` | `ExecutionStatus` includes `'cancelled'` |
| Status badge styling | `ExecutionProgressPage.tsx` `ExecutionStatusBadge` | Gray badge for `cancelled` |
| History filter | `ExecutionHistoryPage.tsx` | `<option value="cancelled">` |
| Queue dequeue primitive | `execution_queue.remove_from_queue()` | Exists; not wired to cancel |
| Agent cancel pattern | `workflow_store.py`, `workflows.py` DELETE, `StopAgentButton.tsx` | **Reference implementation** |
| Progress polling | `ExecutionProgressPage.tsx` | 2s interval while `pending`/`running` |
| Execution worker | `queue_manager.py` → `ExecutionService.execute_test()` | No cancel awareness |
| 3-tier engine | `three_tier_execution_service.py` | No `cancel_check` |
| Delete execution | `DELETE /executions/{id}` | Deletes record — must stay distinct |

### What's missing

| Gap | Required artifact |
|-----|-------------------|
| In-memory cancel flags | `backend/app/services/execution_cancel_store.py` |
| Cancel API route | `DELETE /executions/{id}/cancel` in `executions.py` |
| DB cancel helper | `crud/test_execution.cancel_execution()` |
| Step-loop polling | `ExecutionService.execute_test()` |
| Tier-boundary polling | `ThreeTierExecutionService.execute_step(..., cancel_check=)` |
| Queue lifecycle hooks | Register on worker start, clear on finish, pre-start DB check |
| Frontend button | `frontend/src/components/execution/StopExecutionButton.tsx` |
| Frontend API method | `executionService.cancelExecution(id)` |
| Tests | `test_execution_cancel_store.py`, `test_execution_cancel.py`, `StopExecutionButton.test.tsx` |
| ADR | ADR-009 or ADR-002 addendum |

---

## Architecture Decision: Cooperative Cancel (Mirror Workflow Cancel)

### Decision

Adopt the **same cooperative cancel pattern** used for agent workflows (ADR-004):

1. **API** sets a cancel flag (in-memory store + optional immediate DB update for `pending`).
2. **Worker** polls the flag between logical boundaries (steps, tier fallbacks).
3. **Worker** finalizes with `status=cancelled`, `completed_at`, partial counts — never `failed`.
4. **`finally`** always runs `cleanup()` (Playwright + Stagehand).

### Rationale

| Approach | Verdict |
|----------|---------|
| Cooperative in-memory flag + poll | **Accept** — proven by `workflow_store` + `orchestration_service` |
| Force-kill worker thread | **Reject** — orphaned browsers, corrupt DB state |
| `DELETE /executions/{id}` for cancel | **Reject** — conflates cancel with record deletion |
| DB-only cancel flag | **Reject for v1** — running worker needs fast poll without per-step DB round-trips |
| Optimistic frontend cancel | **Reject** — user brief requires poll-confirmed status |

### State machine

```
                    ┌─────────────┐
         run        │   pending   │◄── cancel: DB cancelled + dequeue
        ──────────► │             │
                    └──────┬──────┘
                           │ worker picks up
                           ▼
                    ┌─────────────┐
                    │   running   │◄── cancel: request_cancel(execution_id)
                    └──────┬──────┘
                           │ cooperative poll detects cancel
                           ▼
                    ┌─────────────┐
                    │  cancelled  │  (terminal)
                    └─────────────┘
```

**Pending path:** API sets `status=cancelled`, `completed_at`, calls `queue.remove_from_queue(execution_id)`, returns 204. Worker never starts.

**Running path:** API calls `request_cancel(execution_id)` (registers flag if not already), returns 204. Worker detects flag, calls `cancel_execution()` with partial stats, breaks loop, `finally` cleanup.

**Terminal path (`completed`, `failed`, `cancelled`):** API returns 204 idempotently (no error).

### Reference files (copy patterns from)

- `backend/app/services/workflow_store.py` — `request_cancel`, `is_cancel_requested`
- `backend/app/api/v2/endpoints/workflows.py` — `DELETE` → 204
- `backend/app/services/orchestration_service.py` — `cancel_check=lambda: is_cancel_requested(id)`
- `frontend/src/features/agent-workflow/components/StopAgentButton.tsx` — UX parity

---

## API Contract

### `DELETE /api/v1/executions/{execution_id}/cancel`

**Auth:** Required (`deps.get_current_user`)

**Ownership:** Non-admin → `execution.user_id == current_user.id`; else 403

**Responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Execution not found | 404 | `{"detail": "Execution not found"}` |
| Wrong user | 403 | `{"detail": "You don't have permission to cancel this execution"}` |
| Success (any cancellable or terminal state) | 204 | No content |

**Handler logic (pseudocode):**

```python
@router.delete("/{execution_id}/cancel", status_code=204)
def cancel_execution_endpoint(execution_id: int, current_user, db):
    execution = crud_executions.get_execution(db, execution_id)
    # 404 / 403 checks ...

    if execution.status == ExecutionStatus.PENDING:
        queue.remove_from_queue(execution_id)
        crud_executions.cancel_execution(db, execution_id, ...)
        clear_cancel(execution_id)  # idempotent cleanup
        return None

    if execution.status == ExecutionStatus.RUNNING:
        register_cancel(execution_id)   # ensure key exists
        request_cancel(execution_id)    # set flag
        return None

    # completed | failed | cancelled → idempotent 204
    return None
```

**Route ordering:** Register **before** `DELETE /{execution_id}` is impossible since they share path depth — use distinct path segment:

```
DELETE /{execution_id}/cancel   ← cancel (new)
DELETE /{execution_id}          ← delete record (existing)
```

Place `@router.delete("/{execution_id}/cancel")` **above** `@router.delete("/{execution_id}")` in `executions.py` (FastAPI matches more specific paths first when declared first; verify in tests).

### CRUD: `cancel_execution`

**File:** `backend/app/crud/test_execution.py`

```python
def cancel_execution(
    db: Session,
    execution_id: int,
    *,
    total_steps: int = 0,
    passed_steps: int = 0,
    failed_steps: int = 0,
    skipped_steps: int = 0,
) -> TestExecution:
    """Mark execution as cancelled with partial progress."""
```

Sets:
- `status = ExecutionStatus.CANCELLED`
- `result = None` (or leave unchanged — prefer `None` for cancelled mid-run)
- `completed_at = datetime.utcnow()`
- `duration_seconds` from `started_at` if set
- step count fields from kwargs

Does **not** set `error_message` (not a failure).

---

## Backend Implementation Detail

### 1. `execution_cancel_store.py` (new)

**Path:** `backend/app/services/execution_cancel_store.py`

Mirror `workflow_store.py` API:

```python
def register_cancel(execution_id: int) -> None:
    """Ensure execution_id key exists in store (called when worker starts)."""

def request_cancel(execution_id: int) -> bool:
    """Set cancel_requested=True. Returns True if key existed."""

def is_cancel_requested(execution_id: int) -> bool:
    """Return True if cancellation was requested."""

def clear_cancel(execution_id: int) -> bool:
    """Remove entry. Returns True if existed. Call in worker finally."""
```

Implementation: `threading.Lock` + `Dict[int, Dict[str, Any]]` keyed by integer `execution_id`.

### 2. `ExecutionService.execute_test()` hooks

**File:** `backend/app/services/execution_service.py`

**New import:** `from app.services.execution_cancel_store import register_cancel, is_cancel_requested, clear_cancel`

**At start of try block** (after resolving `execution` record, before `start_execution`):

```python
register_cancel(execution.id)
```

**New helper** (module-level or method):

```python
def _is_cancelled(execution_id: int) -> bool:
    return is_cancel_requested(execution_id)
```

**New exception** (optional, for clarity):

```python
class ExecutionCancelledError(Exception):
    """Raised internally when cooperative cancel detected."""
```

**Poll sites** — call at top of each iteration:

1. Main `while idx <= total_steps:` loop (line ~816)
2. Inner `for iteration in range(...)` loop body (loop blocks)
3. Inner `for loop_step_idx in range(...)` inside loop blocks

On cancel detected:

```python
execution = crud_execution.cancel_execution(
    db=db,
    execution_id=execution.id,
    total_steps=total_steps,
    passed_steps=passed_steps,
    failed_steps=failed_steps,
    skipped_steps=skipped_steps,
)
if progress_callback:
    await progress_callback({"execution_id": execution.id, "status": "cancelled", ...})
raise ExecutionCancelledError()  # or break + goto finalize
```

**Exception handling** — extend existing `except` chain:

```python
except ExecutionCancelledError:
    pass  # already finalized
except Exception as e:
    ...  # existing fail_execution
finally:
    clear_cancel(execution.id)
    await self.cleanup()
```

**Pass `cancel_check` into `_execute_step`:**

```python
async def _execute_step(
    self,
    page: Page,
    step_description: str,
    step_number: int,
    base_url: str,
    detailed_step: Dict[str, Any] = None,
    execution_id: int = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
```

When calling `three_tier_service.execute_step`:

```python
result = await self.three_tier_service.execute_step(
    step=step_data,
    execution_id=execution_id,
    step_index=step_number - 1,
    cancel_check=cancel_check,
)
```

Wire from `execute_test`:

```python
cancel_check = lambda: is_cancel_requested(execution.id)
result = await self._execute_step(..., cancel_check=cancel_check)
```

### 3. `ThreeTierExecutionService.execute_step()` hooks

**File:** `backend/app/services/three_tier_execution_service.py`

**Updated signature:**

```python
async def execute_step(
    self,
    step: Dict[str, Any],
    execution_id: Optional[int] = None,
    step_index: Optional[int] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
```

**Helper:**

```python
def _check_cancelled(cancel_check) -> bool:
    if callable(cancel_check):
        try:
            return bool(cancel_check())
        except Exception:
            return False
    return False
```

**Poll points** (return early with cancelled result):

| # | Location | When |
|---|----------|------|
| 1 | Start of `execute_step`, after strategy log | Before Tier 1 |
| 2 | After Tier 1 fails, before fallback branch | Before Tier 2/3 |
| 3 | Inside `_execute_option_a` | Before `tier2_executor.execute_step` |
| 4 | Inside `_execute_option_b` | Before `tier3_executor.execute_step` |
| 5 | Inside `_execute_option_c` | Before Tier 2 **and** before Tier 3 escalation |

**Cancelled result shape:**

```python
return {
    "success": False,
    "cancelled": True,
    "tier": None,
    "error": "Execution cancelled by user",
    "error_type": "cancelled",
    "execution_history": execution_history,
    "strategy_used": strategy,
}
```

**`ExecutionService._execute_step`** must propagate `cancelled: True` so the step loop can break without recording a FAIL step (or record SKIP — **prefer: no new step record for in-flight step; break immediately**).

### 4. `queue_manager.py` lifecycle

**File:** `backend/app/services/queue_manager.py`

**Pre-start guard** in `_check_and_start_next()` after `get_next_execution()`:

```python
execution = crud_execution.get_execution(db, queued_execution.execution_id)
if execution and execution.status == ExecutionStatus.CANCELLED:
  logger.info(f"Skipping cancelled execution {execution.id}")
  return  # do not mark active / do not start thread
```

Use a short-lived DB session in `_check_and_start_next` or pass status on `QueuedExecution` — simplest: query DB before `mark_as_active`.

**Worker `run_execution` finally block** (after `service.cleanup()`):

```python
from app.services.execution_cancel_store import clear_cancel
clear_cancel(queued_execution.execution_id)
```

**Register** happens inside `execute_test` (not queue_manager) so direct `execute_test` calls also work.

**Note:** `queue_manager` already calls `service.cleanup()` in its own `finally`; `execute_test` also has `finally: cleanup()`. Ensure double-cleanup is safe (idempotent — verify existing `cleanup()` handles this).

---

## Frontend UX Spec

### `StopExecutionButton.tsx` (new)

**Path:** `frontend/src/components/execution/StopExecutionButton.tsx`

Mirror `StopAgentButton.tsx` with these mappings:

| StopAgentButton | StopExecutionButton |
|-----------------|---------------------|
| `workflowStatus` | `executionStatus: ExecutionStatus \| null` |
| `onStop` | `onStop: () => void` |
| `data-testid="stop-agent-button"` | `data-testid="stop-execution-button"` |
| `data-testid="stop-confirmation"` | `data-testid="stop-execution-confirmation"` |
| "Stop Agent" | "Stop Execution" |
| "Stopping workflow…" | "Stopping execution…" |
| `aria-label="Stop agent workflow"` | `aria-label="Stop test execution"` |

**Terminal statuses (disabled):** `completed`, `failed`, `cancelled`

**Enabled when:** `pending`, `running`

**Styling:** Red outline — `bg-red-50 text-red-600 border border-red-200 hover:bg-red-100` (copy from StopAgentButton).

### `executionService.cancelExecution`

**File:** `frontend/src/services/executionService.ts`

```typescript
async cancelExecution(executionId: number): Promise<void> {
  await api.delete(`/executions/${executionId}/cancel`);
}
```

Mock mode: `Promise.resolve()`.

### `ExecutionProgressPage.tsx` wiring

**Imports:**

```typescript
import { StopExecutionButton } from '../components/execution/StopExecutionButton';
```

**State:**

```typescript
const [isStopping, setIsStopping] = useState(false);
```

**Handler:**

```typescript
const handleStopExecution = async () => {
  if (!executionId || isStopping) return;
  setIsStopping(true);
  try {
    await executionService.cancelExecution(Number(executionId));
    // Do NOT set execution.status locally — poll will confirm
    await fetchExecutionDetail();
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to stop execution');
    setIsStopping(false);
  }
};
```

**Reset `isStopping`** when poll observes terminal status:

```typescript
useEffect(() => {
  if (execution?.status === 'cancelled' || execution?.status === 'completed' || execution?.status === 'failed') {
    setIsStopping(false);
  }
}, [execution?.status]);
```

**Header placement** (line ~193, before Debug Step button):

```tsx
<div className="flex items-center gap-3">
  {(execution.status === 'pending' || execution.status === 'running') && (
    <StopExecutionButton
      executionStatus={execution.status}
      onStop={handleStopExecution}
      isLoading={isStopping}
    />
  )}
  <Button variant="primary" ...>🐛 Debug Step</Button>
  <ExecutionStatusBadge ... />
</div>
```

**Polling:** Existing `useEffect` continues — when status becomes `cancelled`, polling stops (`shouldPoll` false).

**No optimistic cancel:** `setExecution` must not set `status: 'cancelled'` in `handleStopExecution`.

---

## Design Direction

- **Color palette:** Stop button `#dc2626` (red-600) on `#fef2f2` (red-50); confirmation text `#ea580c` (orange-600) — match StopAgentButton
- **Typography:** `text-sm font-medium` button; `text-xs font-medium` confirmation
- **Layout:** Inline in execution header toolbar, left of Debug Step
- **Visual identity:** ⏹ stop icon character (not Heroicons) for parity with agent workflow
- **Inspiration:** `StopAgentButton`, GitHub Actions "Cancel workflow" (cooperative, status-driven)

**Anti-patterns to avoid:**
- Gradient buttons, generic "destructive" purple
- Hiding Stop behind a kebab menu
- Browser `window.confirm()` dialog (use inline confirmation like agent)
- Spinner replacing the button text (keep button label stable)

---

## Features (Prioritized)

### Must-Have (Sprint 1–2)

1. **execution_cancel_store** — thread-safe register/request/is_cancel/clear
2. **cancel_execution CRUD** — DB finalization with partial counts
3. **DELETE /executions/{id}/cancel** — auth, pending dequeue, running flag, idempotent 204
4. **execute_test polls** — before each step; finalize as `cancelled`
5. **three_tier cancel_check** — poll between Tier 1/2/3
6. **queue pre-start guard** — skip cancelled pending items
7. **StopExecutionButton** — parity with StopAgentButton
8. **ExecutionProgressPage wire-up** — `isStopping`, no optimistic UI

### Should-Have (Sprint 3)

9. **ADR-009** — document cooperative cancel decision
10. **Loop-block cancel** — polls inside nested loop iterators (included in Sprint 2 implementation)
11. **ExecutionHistoryPage** — verify cancelled rows display correctly (likely already works)

### Nice-to-Have (Sprint 4+)

12. Stop from Execution History row actions
13. Redis-backed cancel store for multi-worker deployments
14. E2E Playwright test in `tests/e2e/` for full stop flow

---

## Technical Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind (utility classes), Vitest + Testing Library
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL 15
- **Automation:** Playwright 1.56, Stagehand 0.5.6
- **Key new files:** `execution_cancel_store.py`, `StopExecutionButton.tsx`
- **Key modified files:** `executions.py`, `execution_service.py`, `three_tier_execution_service.py`, `queue_manager.py`, `test_execution.py` (crud), `ExecutionProgressPage.tsx`, `executionService.ts`

---

## Sprint Plan

### Sprint 1: Cancel Store + API + CRUD

**Goals:** Backend can accept cancel requests and dequeue pending executions.

**Tasks:**

| # | File | Task |
|---|------|------|
| 1.1 | `backend/app/services/execution_cancel_store.py` | Create store (mirror workflow_store) |
| 1.2 | `backend/tests/unit/test_execution_cancel_store.py` | Unit tests for store |
| 1.3 | `backend/app/crud/test_execution.py` | Add `cancel_execution()` |
| 1.4 | `backend/app/api/v1/endpoints/executions.py` | Add `DELETE /{execution_id}/cancel` |
| 1.5 | `backend/tests/unit/test_execution_cancel.py` | API tests: 404, 403, pending→cancelled+dequeue, running→204, idempotent |

**Definition of done:** `pytest backend/tests/unit/test_execution_cancel*.py` passes; pending cancel removes item from queue.

---

### Sprint 2: Cooperative Execution Hooks

**Goals:** Running executions stop cleanly between steps and tiers.

**Tasks:**

| # | File | Task |
|---|------|------|
| 2.1 | `execution_service.py` | `register_cancel`, poll in step loops, `ExecutionCancelledError`, `cancel_execution` finalize |
| 2.2 | `execution_service.py` | Pass `cancel_check` to `_execute_step` |
| 2.3 | `three_tier_execution_service.py` | Add `cancel_check` param; poll at tier boundaries; return `cancelled` result |
| 2.4 | `queue_manager.py` | Pre-start DB status guard; `clear_cancel` in worker finally |
| 2.5 | `backend/tests/unit/test_execution_cancel.py` | Integration-style tests with mocked execute_test / tier service |

**Definition of done:** Cancel mid-run yields `status=cancelled`, not `failed`; `cleanup()` invoked.

---

### Sprint 3: Frontend Stop UX

**Goals:** User can stop from progress page; UI matches agent pattern.

**Tasks:**

| # | File | Task |
|---|------|------|
| 3.1 | `frontend/src/services/executionService.ts` | `cancelExecution()` |
| 3.2 | `frontend/src/components/execution/StopExecutionButton.tsx` | New component |
| 3.3 | `frontend/src/components/execution/__tests__/StopExecutionButton.test.tsx` | Component tests |
| 3.4 | `frontend/src/pages/ExecutionProgressPage.tsx` | Wire button, `isStopping`, poll reset |

**Definition of done:** `npm run build` succeeds; component tests pass; manual stop flow works.

---

### Sprint 4: Documentation + Non-Regression

**Goals:** ADR written; full test suite green.

**Tasks:**

| # | File | Task |
|---|------|------|
| 4.1 | `documentation/ADR-009-execution-cancel.md` | New ADR (or ADR-002 addendum) |
| 4.2 | Full backend test suite | No regressions on normal pass/fail |
| 4.3 | `gan-harness/eval-rubric.md` | Evaluator sign-off |

**Definition of done:** Weighted eval score ≥ 0.85 per rubric.

---

## Test Strategy

### Backend unit: `test_execution_cancel_store.py`

- `register_cancel` creates key
- `request_cancel` returns False for unknown, True when registered
- `is_cancel_requested` True after request
- `clear_cancel` removes key; subsequent `is_cancel_requested` False
- Thread-safety smoke (optional: concurrent request_cancel)

### Backend unit/integration: `test_execution_cancel.py`

| Test | Assertion |
|------|-----------|
| `test_cancel_pending_execution` | DB `cancelled`, not in queue |
| `test_cancel_running_sets_flag` | `is_cancel_requested(id)` True, DB still `running` until worker finishes |
| `test_cancel_completed_idempotent` | 204, status unchanged |
| `test_cancel_wrong_user` | 403 |
| `test_cancel_not_found` | 404 |
| `test_execute_test_cancel_mid_step` | Mock 3-tier slow; request cancel; final status `cancelled` |
| `test_delete_execution_still_works` | `DELETE /executions/{id}` deletes; distinct from cancel route |

### Frontend: `StopExecutionButton.test.tsx`

Copy structure from `StopAgentButton.test.tsx`:
- Renders with `data-testid="stop-execution-button"`
- Disabled for `completed`, `failed`, `cancelled`, `null`
- Enabled for `pending`, `running`
- Click calls `onStop`, shows `stop-execution-confirmation`
- Disabled when `isLoading=true`

### Manual / Evaluator script

See `gan-harness/eval-rubric.md` § Evaluator Test Script.

---

## Risks & Edge Cases

| Risk | Mitigation |
|------|------------|
| Mid–Tier 3 LLM call takes 60–120s before next poll | Document in UI copy; poll only between tiers/steps; acceptable v1 latency |
| Double `cleanup()` (queue_manager + execute_test) | Verify `ExecutionService.cleanup()` idempotent |
| Cancel requested before `register_cancel` | `request_cancel` should `register_cancel` if missing (auto-create key) |
| Race: worker starts same moment as pending cancel | Pre-start DB status check in queue_manager; transactional cancel in API |
| In-memory store lost on server restart | Running execution continues; v1 acceptable; document in ADR |
| Loop block mid-iteration | Poll at inner loop headers; break all nested loops |
| OTP expansion step in progress | Poll before `_execute_step`; cannot interrupt IMAP poll mid-flight — acceptable |
| `cancel_check` raises | Treat as not cancelled (mirror requirements_agent pattern) |
| Admin viewing another user's execution | Cancel endpoint respects same ownership as GET |
| Concurrent double-click Stop | `isStopping` disables button; API idempotent |

**Empty/error states:**
- API network error → show error banner, re-enable Stop (`setIsStopping(false)`)
- Execution already `cancelled` on page load → Stop hidden (not rendered for terminal)

---

## Evaluation Criteria

See `gan-harness/eval-rubric.md` for weighted scoring (pass ≥ 0.85).

**Summary weights:**
- Backend Cancel API & Store: 0.30
- Cooperative Execution Hooks: 0.25
- Frontend Stop UX: 0.25
- Tests & Documentation: 0.10
- Non-Regression: 0.10

**Automatic fail conditions:**
- No cancel endpoint
- No Stop on ExecutionProgressPage
- Running execution stuck after stop
- Cancel conflated with delete
- Normal pass/fail runs regress

---

# Feature 2: Clone Test Case — Duplicate Saved Tests

> Generated from brief: *"Add a Clone Test Case button for saved tests in the AI Web Test v1 platform."*

---

## Vision

QA engineers frequently need to fork an existing saved test — tweak a few steps for a variant flow, test against a different environment, or preserve a baseline before risky edits. **Clone Test Case** gives them a one-click duplicate from the Saved Tests list (and edit drawer) that creates an independent copy with a smart title suffix, fresh timestamps, and all step content preserved. The flow should feel as fast and obvious as duplicating a row in a spreadsheet: click Clone, see the new test appear at the top of the list, optionally land in edit mode.

Mirror the proven **test template clone** pattern (`POST /test-templates/{id}/clone`) already in the codebase — same API shape, same ownership rules, adapted for `TestCase` fields.

---

## User Story

**As a** QA engineer managing saved test cases,  
**I want** to clone an existing test case with one click,  
**So that** I can create variations without manually re-entering steps, assertions, categories, and metadata.

**Acceptance (happy path):**
1. User is on `/tests/saved` with at least one saved test visible.
2. User clicks **Clone** on a test row (or in the edit drawer).
3. Button shows brief loading state; API returns 201 with the new test.
4. List refreshes; cloned test appears at top with title `{original title} (Copy)` (or `(Copy 2)` if name collides).
5. Cloned test has identical `steps`, `expected_result`, `priority`, `test_type`, `test_category_id`, `tags`, `requires_runtime_credentials`, and `preconditions`.
6. Cloned test has `status=pending`, new `id`, new `created_at`/`updated_at`, `user_id` = current user.
7. User can immediately **Run** or **Edit** the clone without affecting the original.

---

## Scope

### In scope

| Area | Deliverable |
|------|-------------|
| Backend CRUD | `clone_test_case()` in `backend/app/crud/test_case.py` |
| Backend API | `POST /api/v1/tests/{test_case_id}/clone` → 201 `TestCaseResponse` |
| Schema | `TestCaseCloneRequest` with optional `new_title` override |
| Frontend service | `testsService.cloneTest(id, options?)` |
| Frontend UI | Clone button on `SavedTestsPage` row actions + edit drawer footer |
| Tests | Backend unit/API tests + frontend component test |
| Docs | Brief ADR addendum or section in existing test-management ADR |

### Out of scope

- Bulk clone (multi-select → clone all)
- Clone into another user's account or cross-tenant copy
- Copying execution history (`test_executions` rows)
- Copying schedules (`test_schedules` — clone does not inherit cron/interval jobs)
- Adding clone to test suite membership automatically (suites keep referencing original `test_case_id`)
- Copying full step version history (only current `steps`/`expected_result`/`test_data` snapshot; optional v1 version record — see Should-Have)
- Clone from Execution History or Execution Progress pages
- MCP server exposure (defer unless trivial — add `clone_test_case` tool in Nice-to-Have)

---

## Current State Analysis

### What exists

| Layer | Location | Status |
|-------|----------|--------|
| Saved tests list | `frontend/src/pages/SavedTestsPage.tsx` | Row actions: View, Edit, Run, Schedule, Delete — **no Clone** |
| Test CRUD API | `backend/app/api/v1/endpoints/tests.py` | `POST /tests`, `GET/PUT/DELETE /tests/{id}` |
| TestCase model | `backend/app/models/test_case.py` | Full field set including `steps`, `tags`, `test_category_id`, `requires_runtime_credentials` |
| Template clone (reference) | `test_templates.py` + `TestTemplateService.clone_template()` | **Pattern to mirror** |
| Edit drawer | `SavedTestsPage` slide-over | Save/Cancel only — no Clone |
| Step versioning | `versions.py` + `VersionService` | Versions tied to `test_case_id`; not cloned by default |

### What's missing

| Gap | Required artifact |
|-----|-------------------|
| Clone CRUD helper | `crud/test_case.clone_test_case()` |
| Clone API route | `POST /tests/{test_case_id}/clone` in `tests.py` |
| Request schema | `TestCaseCloneRequest` in `schemas/test_case.py` |
| Frontend API method | `testsService.cloneTest()` |
| Clone button (list) | `SavedTestsPage` row action with `Copy` icon |
| Clone button (drawer) | Edit drawer footer secondary action |
| Tests | `test_test_case_clone.py`, `SavedTestsPage.clone.test.tsx` (or equivalent) |

---

## Architecture Decision: Server-Side Deep Copy

### Decision

Implement clone as a **server-side deep copy** of the `TestCase` row (new primary key), not a client-side re-POST of fetched JSON. Rationale:

1. Single source of truth for which fields copy vs reset.
2. Ownership and auth enforced in one place.
3. Title de-duplication logic centralized on backend.
4. Consistent with `TestTemplateService.clone_template()`.

### Fields to copy

| Field | Behavior |
|-------|----------|
| `title` | `{original} (Copy)` or `{original} (Copy N)` if collision |
| `description` | Deep copy as-is |
| `test_type` | Copy |
| `priority` | Copy |
| `steps` | Deep copy JSON array |
| `expected_result` | Copy |
| `preconditions` | Copy (nullable) |
| `test_data` | Deep copy (nullable) |
| `category_id` (KB) | Copy |
| `test_category_id` (saved-test folder) | Copy — clone stays in same folder |
| `tags` | Deep copy array |
| `test_metadata` | Deep copy |
| `requires_runtime_credentials` | Copy boolean |
| `scenario_id` | Copy (preserve lineage) |
| `template_id` | Copy (preserve lineage) |

### Fields to reset / assign

| Field | Behavior |
|-------|----------|
| `id` | New auto-increment |
| `status` | `TestStatus.PENDING` |
| `user_id` | `current_user.id` (cloner owns the copy) |
| `created_at` / `updated_at` | DB defaults (`utc_now`) |
| `executions` | Empty (no relationship rows) |

### Title suffix algorithm

```python
def _generate_clone_title(db, user_id, base_title: str) -> str:
    candidate = f"{base_title} (Copy)"
    if not title_exists_for_user(db, user_id, candidate):
        return candidate
    n = 2
    while title_exists_for_user(db, user_id, f"{base_title} (Copy {n})"):
        n += 1
    return f"{base_title} (Copy {n})"
```

Scope title uniqueness to **same `user_id`** (titles are not globally unique today).

Optional request body `new_title` overrides auto-suffix when provided (validated: non-empty, max 255 chars).

---

## API Contract

### `POST /api/v1/tests/{test_case_id}/clone`

**Auth:** Required (`deps.get_current_user`)

**Ownership:** Source test must exist; non-admin must own source test (`test_case.user_id == current_user.id`), else 403.

**Request body (optional):**

```json
{
  "new_title": "My Custom Clone Name"
}
```

`TestCaseCloneRequest`:
- `new_title: Optional[str]` — min 1, max 255; when omitted, auto-suffix applied.

**Responses:**

| Condition | Status | Body |
|-----------|--------|------|
| Source not found | 404 | `{"detail": "Test case not found"}` |
| Wrong user | 403 | `{"detail": "You don't have permission to clone this test case"}` |
| `new_title` already exists for user | 409 | `{"detail": "A test case with this title already exists"}` |
| Success | 201 | `TestCaseResponse` for new test |

**Route ordering:** Register **before** any catch-all `/{test_case_id}` routes that might conflict. Path `/tests/{test_case_id}/clone` is distinct from `/tests/{test_case_id}` — no collision.

**Handler logic (pseudocode):**

```python
@router.post("/{test_case_id}/clone", response_model=TestCaseResponse, status_code=201)
def clone_test_case_endpoint(test_case_id, body: TestCaseCloneRequest | None, current_user, db):
    original = crud.get_test_case(db, test_case_id)
    # 404 / 403 checks ...
    new_title = body.new_title if body and body.new_title else _generate_clone_title(db, current_user.id, original.title)
    if title_exists_for_user(db, current_user.id, new_title):
        raise HTTPException(409, "A test case with this title already exists")
    cloned = crud.clone_test_case(db, original, user_id=current_user.id, new_title=new_title)
    return sanitize_test_case_for_response(cloned)
```

### CRUD: `clone_test_case`

**File:** `backend/app/crud/test_case.py`

```python
def clone_test_case(
    db: Session,
    original: TestCase,
    *,
    user_id: int,
    new_title: str,
) -> TestCase:
    """Create a new TestCase copied from original. Does not copy executions or schedules."""
```

Use `copy.deepcopy` or explicit field assignment for JSON columns (`steps`, `tags`, `test_data`, `test_metadata`).

---

## Frontend UX Spec

### Clone button — list row

**Path:** `frontend/src/pages/SavedTestsPage.tsx`

**Placement:** Row action toolbar, between **Edit** and **Run** (logical grouping: non-destructive mutations before execution).

| Attribute | Value |
|-----------|-------|
| Icon | `Copy` from `lucide-react` |
| `title` / `aria-label` | "Clone Test Case" |
| `data-testid` | `clone-test-button-{test.id}` |
| Styling | `p-2 text-blue-600 hover:bg-blue-50 rounded-lg` (matches secondary action palette; not green Run or red Delete) |

**Interaction:**
1. Click → `setCloningTestId(test.id)` disables that row's Clone button, shows spinner on icon.
2. `await testsService.cloneTest(test.id)`.
3. On success → `loadTests()` refresh; toast/notice: `"Cloned: {newTitle}"`.
4. On error → show inline error or page notice; re-enable button.

**Optional enhancement (Should-Have):** After clone, navigate to `?edit={newId}` so user lands in edit drawer immediately.

### Clone button — edit drawer

**Placement:** Footer button row, left of Cancel:

```tsx
<Button variant="secondary" onClick={handleCloneFromDrawer} data-testid="clone-test-drawer-button">
  <Copy className="w-4 h-4 mr-1" /> Clone
</Button>
```

Clones the test currently open in the drawer (even if user has unsaved edits — **clone source is server state**, not dirty form; show tooltip: "Clones saved version").

### `testsService.cloneTest`

**File:** `frontend/src/services/testsService.ts`

```typescript
async cloneTest(
  testId: number,
  options?: { newTitle?: string }
): Promise<Test> {
  const response = await api.post(`/tests/${testId}/clone`, options ?? {});
  return response.data;
}
```

Mock mode: append a copy to `mockTests` with new id and `(Copy)` suffix.

---

## Design Direction

- **Color palette:** Clone button `#2563eb` (blue-600) on `#eff6ff` (blue-50) hover — distinct from green Run (`#16a34a`) and red Delete (`#dc2626`)
- **Typography:** Icon-only on list row with `title` tooltip; drawer uses `text-sm font-medium` label "Clone"
- **Layout:** Inline in existing row action cluster; no new modals for default flow
- **Visual identity:** `Copy` icon (Lucide), not "duplicate document" emoji
- **Inspiration:** GitHub "Duplicate workflow", Notion "Duplicate page", existing `test-templates` clone

**Anti-patterns to avoid:**
- `window.confirm()` before every clone (clone is non-destructive — no confirmation needed)
- Navigating away from list without refresh (stale list)
- Client-only clone that omits `requires_runtime_credentials` or `test_category_id`
- Reusing Delete's red styling for Clone

---

## Features (Prioritized)

### Must-Have (Sprint 5)

1. **`clone_test_case` CRUD** — deep copy with field matrix above
2. **`POST /tests/{id}/clone`** — auth, ownership, 201/404/403/409
3. **`TestCaseCloneRequest` schema** — optional `new_title`
4. **Title suffix algorithm** — `(Copy)` / `(Copy N)` per user
5. **`testsService.cloneTest()`** — service layer + mock
6. **List row Clone button** — `SavedTestsPage` with loading state
7. **Backend tests** — happy path, 404, 403, title collision, field parity

### Should-Have (Sprint 6)

8. **Edit drawer Clone button** — clone from open drawer
9. **Post-clone navigation** — optional `?edit={newId}` redirect
10. **Frontend component test** — button renders, calls service, loading state
11. **Initial version snapshot** — `VersionService.save_version(..., change_reason="cloned_from_{id}")` on clone (v1 for new test)

### Nice-to-Have (Sprint 7+)

12. MCP `clone_test_case` tool in `mcp_server.py`
13. Keyboard shortcut `C` when row focused (accessibility power-user)
14. Bulk clone from multi-select
15. Clone with "Reset status only" option for advanced users

---

## Sprint Plan

### Sprint 5: Clone API + List Button

**Goals:** User can clone from Saved Tests list; new test appears with correct content.

| # | File | Task |
|---|------|------|
| 5.1 | `backend/app/schemas/test_case.py` | Add `TestCaseCloneRequest` |
| 5.2 | `backend/app/crud/test_case.py` | Add `clone_test_case()`, title helper |
| 5.3 | `backend/app/api/v1/endpoints/tests.py` | Add `POST /{test_case_id}/clone` |
| 5.4 | `backend/tests/unit/test_test_case_clone.py` | API + CRUD tests |
| 5.5 | `frontend/src/services/testsService.ts` | `cloneTest()` |
| 5.6 | `frontend/src/pages/SavedTestsPage.tsx` | Row Clone button + handler |

**Definition of done:** Clone from list creates independent test; original unchanged; `pytest test_test_case_clone.py` passes; `npm run build` succeeds.

---

### Sprint 6: Drawer Clone + Polish

**Goals:** Clone from edit drawer; post-clone UX polish.

| # | File | Task |
|---|------|------|
| 6.1 | `SavedTestsPage.tsx` | Drawer Clone button |
| 6.2 | `SavedTestsPage.tsx` | Optional redirect to `?edit={newId}` |
| 6.3 | `frontend/src/pages/__tests__/SavedTestsPage.clone.test.tsx` | Component tests |
| 6.4 | `version_service.py` (optional) | Initial version on clone |

**Definition of done:** Evaluator script steps 1–8 in `eval-rubric-clone-test-case.md` pass.

---

## Test Strategy

### Backend: `test_test_case_clone.py`

| Test | Assertion |
|------|-----------|
| `test_clone_happy_path` | 201; new `id` ≠ source; title ends with `(Copy)`; steps equal |
| `test_clone_preserves_category_and_tags` | `test_category_id`, `tags`, `requires_runtime_credentials` match |
| `test_clone_resets_status` | `status=pending`; no execution rows |
| `test_clone_title_collision` | Second clone of same source → `(Copy 2)` |
| `test_clone_custom_title` | Body `new_title` used |
| `test_clone_custom_title_conflict` | Duplicate `new_title` → 409 |
| `test_clone_not_found` | 404 |
| `test_clone_wrong_user` | 403 |
| `test_clone_does_not_delete_original` | Source still exists after clone |

### Frontend

- Clone button visible per row with `data-testid`
- Click triggers `cloneTest` mock; list refresh called
- Loading disables button during request
- Error shows notice, does not remove original from list

### Manual / Evaluator script

See `gan-harness/eval-rubric-clone-test-case.md` § Evaluator Test Script.

---

## Risks & Edge Cases

| Scenario | Expected behavior |
|----------|-------------------|
| Source has `requires_runtime_credentials=true` | Copied to clone; Run still prompts/injects per ADR-002-12 |
| Source in a `test_category` folder | Clone placed in same folder |
| Source is `uncategorized` (`test_category_id=null`) | Clone also uncategorized |
| Source linked to `scenario_id` / `template_id` | IDs copied (lineage preserved); both tests independent thereafter |
| Source has active schedule | **Not** copied; user must schedule clone separately |
| Source member of test suite | Suite unchanged; clone is standalone |
| Empty `steps` array | Allowed — clone copies empty steps (edge case for draft tests) |
| Very long title (near 255 chars) | Truncate base before suffix or reject with 422 if suffix would exceed 255 |
| Admin clones another user's test | **403** unless admin-impersonation pattern exists (match existing test GET ownership) |
| Double-click Clone | `cloningTestId` guard prevents duplicate API calls |
| Clone while edit drawer has unsaved changes | Clone uses **persisted** server state, not dirty form |
| JSON fields with nested objects | Use deep copy to avoid shared references |
| Concurrent clones of same test | Each gets unique title `(Copy)`, `(Copy 2)`, etc. |

**Empty/error states:**
- Network error → page notice "Failed to clone test"; button re-enabled
- 409 title conflict → show detail message; suggest edit title in drawer after clone

---

## Evaluation Criteria

See `gan-harness/eval-rubric-clone-test-case.md` for weighted scoring (pass ≥ 0.85).

**Summary weights:**
- Backend Clone API & CRUD: 0.35
- Data fidelity (fields copied correctly): 0.25
- Frontend Clone UX: 0.25
- Tests: 0.15

**Automatic fail conditions:**
- No `POST /tests/{id}/clone` endpoint
- Clone mutates or deletes source test
- Clone shares `id` with source
- Steps not copied (empty clone)
- No Clone button on SavedTestsPage list

---

# Feature 3: CRM Login Toggle Persist — `requires_runtime_credentials` Round-Trip

> Generated from brief: *"Fix Requires CRM Login toggle not persisting on saved tests: API sanitizer omits `requires_runtime_credentials` so GET/PUT responses always default to false and UI resets to OFF after navigate/reload."*

---

## Vision

QA engineers mark saved tests that need a one-time CRM/UAT login before Run via the **Requires CRM Login** toggle. That boolean must survive save, list refresh, navigate-away, and page reload — passwords stay ephemeral (prompted at Run only), but the *flag* is durable configuration on `TestCase`. Today the UI looks correct until the next GET: the sanitizer drops the field, Pydantic defaults to `false`, and the toggle flips back to OFF. This feature is a **surgical bugfix**: restore the boolean on every sanitized API response (and keep the Saved Tests local list honest after save) without redesigning CRM auth, credential injection, or Run-prompt UX.

---

## User Story

**As a** QA engineer editing a saved test that needs CRM login,  
**I want** the **Requires CRM Login** toggle to stay ON after I save and return to the test,  
**So that** Run continues to show the credential prompt for that test without me re-enabling the toggle every session.

**Acceptance (happy path):**
1. User opens a saved test in edit drawer (`/tests/saved` → Edit) or on `TestDetailPage`.
2. User turns **Requires CRM Login** ON and saves (drawer Save, or inline toggle autosave on detail).
3. PUT response includes `"requires_runtime_credentials": true`.
4. User closes drawer / navigates away / hard-reloads.
5. User re-opens the same test — toggle is still **ON**.
6. GET list and GET by id both return `requires_runtime_credentials: true`.
7. Turning OFF and saving persists `false` the same way.
8. No password, username, or credential object is written to DB, response payloads, or `localStorage`.

---

## Scope

### In scope

| Area | Deliverable |
|------|-------------|
| Backend sanitizer | Add `requires_runtime_credentials` to `sanitize_test_case_for_response` dict in `backend/app/api/v1/endpoints/tests.py` |
| Backend verification | Unit/API test: update `true` → GET returns `true` (covers sanitize path used by GET/PUT/list/clone responses) |
| Frontend local list | Optional but recommended: include `requires_runtime_credentials` in `SavedTestsPage` post-save `setTests` map (parity with other edited fields) |
| Docs / harness | This Feature 3 section + `gan-harness/eval-rubric-crm-login-toggle.md` |

### Out of scope

- Redesigning CRM / UAT credential prompt, injection, or `{{CRM_PASSWORD}}` placeholder policy
- Persisting passwords, usernames, or any credential blob (ADR-crm / Sprint 10.14 policy unchanged)
- New columns, migrations, or schema renames (column already exists)
- Changing `RunTestButton` / `CredentialPromptModal` behavior beyond consuming the correct flag
- Refactoring sanitizer to auto-reflect ORM columns (hand-maintained dict stays; one key added)
- Bulk edit of the flag across many tests
- New Settings UI or org-wide "always require CRM login" defaults

---

## Current State Analysis

### What exists (works)

| Layer | Location | Status |
|-------|----------|--------|
| DB column | `test_cases.requires_runtime_credentials` | Present; migration `add_requires_runtime_credentials.py` |
| ORM | `backend/app/models/test_case.py` | `Column(Boolean, nullable=False, default=False)` |
| Schemas | `TestCaseBase` / `TestCaseUpdate` / `TestCaseResponse` | Field defined; Update is `Optional[bool]` |
| CRUD write | `testsService.updateTest` → endpoint → CRUD | Persists flag correctly when sent |
| UI controls | `SavedTestsPage` edit drawer checkbox; `TestDetailPage` inline switch | Save sends `requires_runtime_credentials` |
| Types | `frontend/src/types/api.ts` | Field on `Test` / update request |
| Run path | `RunTestButton` when flag true | Credential prompt (unchanged by this fix) |
| Existing unit coverage | `test_crm_ephemeral_credentials.py` | Model/column defaults; not sanitize round-trip |

### What's broken (root cause)

| Gap | Effect |
|-----|--------|
| `sanitize_test_case_for_response` builds a hand-maintained dict **without** `requires_runtime_credentials` | GET/PUT/list/clone responses omit the key |
| `TestCaseResponse` / base schema default `False` | Pydantic fills missing key → always `false` in JSON |
| UI hydrates from API (`?? false`) | Toggle shows OFF after reload/navigate even though DB is `true` |
| `SavedTestsPage` post-save `setTests` map omits the field | Local list can lag until `loadTests()`; after refresh, sanitizer bug still wins |

**Confirmed in sanitizer today** (`tests.py` ~lines 43–63): dict includes `id`, `title`, `steps`, `tags`, `test_metadata`, … but **not** `requires_runtime_credentials`.

**Architect finding:** This is a **bug**, not intended behavior. Flag is designed to persist; only credentials are ephemeral.

---

## Architecture Decision: Fix Sanitizer Only (Minimal)

### Decision

**Minimal fix:** one line in `sanitize_test_case_for_response`:

```python
'requires_runtime_credentials': getattr(test_case, 'requires_runtime_credentials', False),
```

Use `getattr` for defensive compatibility with any partial ORM objects in tests.

### Rationale

| Approach | Verdict |
|----------|---------|
| Add missing key to sanitizer dict | **Accept** — matches how other columns are exposed; smallest correct fix |
| Stop using sanitizer / return ORM directly | **Reject** — sanitizer still needed for empty `description` / `expected_result` |
| Auto-generate response from `TestCase.__table__.columns` | **Reject for this feature** — scope creep; can be a later cleanup |
| Persist credentials to fix "login forgotten" | **Reject** — security policy; wrong problem |
| Frontend-only localStorage for the flag | **Reject** — DB already stores it; would mask the API bug |

### Secondary (Should-Have) frontend parity

In `SavedTestsPage` `handleSaveEdit` / equivalent, extend the optimistic `setTests` map:

```typescript
requires_runtime_credentials: editForm.requires_runtime_credentials,
```

So list-derived UI stays correct even before `closeEditDrawer` → `loadTests()`. Primary user-visible fix remains the API round-trip.

---

## API Contract Impact

No new routes. All existing test-case responses that go through `sanitize_test_case_for_response` must include the boolean:

| Endpoint | Method | Must include field |
|----------|--------|--------------------|
| `/api/v1/tests` | GET (list) | Yes |
| `/api/v1/tests/{id}` | GET | Yes |
| `/api/v1/tests` | POST create | Yes |
| `/api/v1/tests/{id}` | PUT update | Yes |
| `/api/v1/tests/{id}/clone` | POST | Yes (clone already copies ORM flag; response must not zero it) |

**Example PUT/GET body fragment:**

```json
{
  "id": 42,
  "title": "CRM checkout flow",
  "requires_runtime_credentials": true
}
```

**Security invariant (unchanged):** Response never contains password, username, `login_credentials`, or similar. Only the boolean flag.

---

## Design Direction

- **No visual redesign** — keep existing checkbox / switch copy ("Requires CRM Login" / 🔐 label).
- **Color / typography:** Unchanged; reuse current SavedTests / TestDetail patterns.
- **Layout:** No new panels, modals, or cards for this fix.
- **Anti-AI-slop / anti-scope:** Do not invent a "Credentials Hub", password vault UI, or settings page.
- **Inspiration:** Treat like fixing a missing field in a DTO mapper — invisible when correct, obviously wrong when missing.

**Anti-patterns to avoid:**
- Writing credentials into `test_data`, `test_metadata`, or `localStorage`
- Removing schema default so omission returns `null` without fixing sanitizer (still breaks UI)
- "Fixing" by always forcing toggle ON in the frontend
- Broad sanitizer rewrite while shipping this bugfix

---

## Features (Prioritized)

### Must-Have (Sprint 7)

1. **Sanitizer field** — `requires_runtime_credentials` in `sanitize_test_case_for_response`
2. **Round-trip unit/API test** — create/update with `true`, GET asserts `true`; update `false`, GET asserts `false`
3. **Manual / E2E check** — toggle ON → save → reload → still ON

### Should-Have (Sprint 7, same PR if cheap)

4. **SavedTestsPage local map** — include flag in post-save `setTests` patch
5. **Frontend regression test** — mock update + reopen / reload hydrate uses API value `true`
6. **Sanitizer coverage note** — assert list endpoint responses also include the field when DB is true

### Nice-to-Have (Sprint 8+)

7. Shared helper or schema `model_validate` from ORM to reduce future omitted-field bugs
8. Lint/checklist: when adding `TestCase` columns, update sanitizer dict

---

## Sprint Plan

### Sprint 7: Sanitize + Persist Round-Trip

**Goals:** Toggle survives save + GET; credentials remain ephemeral; tests prove sanitize path.

| # | File | Task |
|---|------|------|
| 7.1 | `backend/app/api/v1/endpoints/tests.py` | Add `requires_runtime_credentials` to sanitizer dict |
| 7.2 | `backend/tests/unit/` (extend `test_crm_ephemeral_credentials.py` or new `test_requires_runtime_credentials_sanitize.py`) | PUT true → GET true via sanitized response |
| 7.3 | `frontend/src/pages/SavedTestsPage.tsx` | Include flag in post-save list map (Should-Have) |
| 7.4 | Frontend test (optional) | SavedTests / detail hydrate from response with `true` |
| 7.5 | E2E (optional but preferred) | Playwright: toggle → save → reload → assert checked |

**Definition of done:**
- GET `/api/v1/tests/{id}` after update with `requires_runtime_credentials: true` returns `true`
- Hard reload of edit UI shows toggle ON
- No credential values in DB row / API JSON / `localStorage`
- Backend unit tests for sanitize round-trip pass
- Feature 1/2 behavior unchanged

---

## Acceptance Criteria

| ID | Criterion | Pass condition |
|----|-----------|----------------|
| AC1 | Sanitizer includes field | Dict key present; value from ORM (`getattr` safe) |
| AC2 | Persist true | Update `true` → subsequent GET/list item is `true` |
| AC3 | Persist false | Update `false` → subsequent GET is `false` |
| AC4 | UI survive reload | SavedTests drawer and/or TestDetail toggle stay ON after navigate/reload |
| AC5 | Credentials ephemeral | No password/username persisted; Run prompt still uses ephemeral credentials only |
| AC6 | Clone response honest | Clone of flag=`true` source returns `requires_runtime_credentials: true` (not forced false by sanitizer) |
| AC7 | Surgical scope | No CRM redesign, no new migration, no credential storage |

---

## Test Plan

### Backend unit / API

| Test | Assertion |
|------|-----------|
| `test_sanitize_includes_requires_runtime_credentials_true` | ORM `True` → sanitized response `.requires_runtime_credentials is True` |
| `test_sanitize_includes_requires_runtime_credentials_false` | ORM `False` → response `False` |
| `test_update_then_get_preserves_true` | PUT `{requires_runtime_credentials: true}` → GET body `true` |
| `test_update_then_get_preserves_false` | PUT `false` → GET `false` |
| `test_list_includes_flag` | List item for updated test has `true` |
| Existing ephemeral credential tests | Still pass; no credential persistence regressions |

Prefer testing through the sanitizer and/or HTTP layer so a future sanitizer omission fails CI.

### Frontend

| Test | Assertion |
|------|-----------|
| Hydrate from GET | Opening edit with API `true` checks the box / switch |
| Post-save local map (if AC implemented) | List state includes updated flag without waiting for full refetch quirks |
| No localStorage credential write | Grep/assert: credential keys never written on toggle save |

### E2E / Evaluator script

See `gan-harness/eval-rubric-crm-login-toggle.md` § Evaluator Test Script.

Suggested flow:
1. Log in → Saved Tests → Edit a test.
2. Enable **Requires CRM Login** → Save.
3. Close drawer → soft navigate away → return → Edit again → assert ON.
4. Hard reload page → Edit same test → assert ON.
5. Run test → credential modal appears (flag consumed).
6. Confirm Network: GET/PUT JSON has `"requires_runtime_credentials": true` and no password fields.
7. Disable toggle → Save → reload → assert OFF.
8. Optional: Clone a `true` test → clone response/edit shows ON.

---

## Risks & Edge Cases

| Scenario | Expected behavior |
|----------|-------------------|
| Legacy rows created before column existed | DB default `false`; response `false` |
| Toggle ON but user never Runs | Flag stays true; no credentials stored |
| Concurrent edit of same test | Last write wins for boolean (existing PUT semantics) |
| Clone after fix | Source `true` → clone ORM `true` → sanitized response `true` |
| Admin GET of another user's test | Ownership rules unchanged; response includes true value if permitted |
| `getattr` when attribute missing | Defaults to `False` (defensive); real `TestCase` always has column |
| Frontend sends `undefined` on partial update | Existing Update schema `Optional` — omit leaves prior DB value (do not treat omit as force-false in CRUD) |

**Empty/error states:** Unchanged — save errors still show edit drawer error string; do not clear the toggle on failed save.

---

## Evaluation Criteria

See `gan-harness/eval-rubric-crm-login-toggle.md` for weighted scoring (pass ≥ 0.85).

**Summary weights:**
- Backend sanitizer & API round-trip: 0.40
- Security (credentials remain ephemeral): 0.20
- Frontend persistence UX: 0.25
- Tests & E2E expectations: 0.15

**Automatic fail conditions:**
- Sanitizer still omits `requires_runtime_credentials`
- GET after update `true` returns `false`
- Any password/credential persisted to DB or `localStorage`
- Unrelated CRM auth redesign shipped as part of this fix

---

# Feature 4: Timed Wait Step — First-Class Cancel-Aware Pause

> Generated from brief / architect recommendation: *"NL step `wait 10 seconds` on saved tests is NOT honored. Approach C: UI-insertable wait step + NL/canonical parsing (NOT a loop-block); short-circuit before tier escalation with cancel-aware chunked sleep (ADR-009); fix Tier 1 duration fields and Tier 2 wait no-op; never Stagehand-act waits; do not conflate with ADR-002 readiness waits."*

---

## Vision

QA engineers need an intentional, predictable **pause between steps** — e.g. wait 10 seconds for a third-party redirect, SMS OTP window, or slow backend job — without relying on Stagehand, without cloning the loop-block UX, and without blocking Stop Execution (Feature 1 / ADR-009). **Timed Wait Step** makes wait a **first-class ordinal step** in the same newline-separated `steps` list as click/fill/navigate: insertable from the editor via **[+ Add Wait]**, parseable from natural language (`Wait 10 seconds`) and canonical forms (`wait: 10s`), executed as a **short-circuit sleep** in `ExecutionService` that never escalates through Tier 2/3, and interruptible mid-wait via cancel-aware chunked polling.

The product feel: inserting a wait is as ordinary as inserting a click — a single line in the step list, visible in progress as a normal step, cancelled mid-sleep within ~0.5s of Stop, and clearly distinct from automatic readiness sleeps (spinners, payment gateways, post-click settle).

---

## User Story

**As a** QA engineer authoring or editing a saved test,  
**I want** to insert a timed wait of N seconds as a normal step (or write `wait 10 seconds` in NL),  
**So that** the run actually pauses for that duration before the next step, I can Stop mid-wait, and the engine does not burn LLM/Stagehand tokens pretending to “wait.”

**Acceptance (happy path):**
1. User opens Saved Tests edit drawer or `TestDetailPage` / `TestStepEditor`.
2. User clicks **[+ Add Wait]**, picks **10 seconds** (or types `Wait 10 seconds` / `wait: 10s` as a line).
3. Save → `steps` array contains a wait line at the chosen ordinal (e.g. between step 3 and 4).
4. User Runs the test → progress shows the wait step; wall-clock pause ≈ 10s (± chunk resolution).
5. During the wait, user clicks **Stop Execution** → status becomes `cancelled` within ~1s (chunk poll); no unbroken 10s sleep after cancel.
6. Step result for the wait is `passed` (or `cancelled` if stopped mid-wait); `tier_used` is not Tier 2/3 Stagehand.
7. A non-timed instruction like `Wait for the success message to appear` does **not** sleep a fixed duration; it follows normal action detection / verify / readiness paths.

---

## Scope

### In scope

| Area | Deliverable |
|------|-------------|
| Action detection | Timed-wait detection in `ExecutionService._execute_step` (and/or a shared helper) for NL + canonical + structured forms |
| Short-circuit sleep | Cancel-aware chunked sleep **before** `ThreeTierExecutionService.execute_step` / tier escalation |
| Duration fields | Read `timeout_ms` / `timeout` / parsed seconds; not only pure-int `value` |
| Tier 1 | `tier1_playwright._execute_wait` honors ms from structured fields; still used only if short-circuit is bypassed (prefer short-circuit as primary path) |
| Tier 2 | Fix `tier2_hybrid` `action == "wait": pass` no-op — either never reached for timed waits, or implement real sleep if hit |
| Tier 3 | Do **not** send timed waits to Stagehand `act("wait…")` |
| Cap | Max duration clamp (default **120 seconds**) to limit runaway runs |
| NL boundaries | Timed sleep vs condition wait (`wait for …`) carefully distinguished |
| UI | **[+ Add Wait]** duration picker inserts a canonical step **line** into the steps textarea/list — **not** `test_data.loop_blocks` / not a `wait_blocks` overlay |
| Tests | Unit: duration honored, cancel mid-wait, non-timed “wait for X” does not sleep |
| Docs | ADR note (ADR-002 addendum or short ADR): intentional timed wait vs automatic readiness |

### Out of scope

- **Loop-block-style wait UX** — no `wait_blocks` metadata parallel to `loop_blocks`; no overlay editor that marks start/end ranges for waits
- Using Stagehand / Tier 3 `act()` to implement sleeps
- Conflating timed waits with ADR-002 readiness (`post_click_readiness.py`, spinner clears, payment gateway settles, step-boundary loading)
- Parsing **every** sentence containing the word “wait” as a fixed sleep
- Unbroken `asyncio.sleep(N)` without cancel chunks (violates ADR-009 mid-wait cancel)
- Relying on tier escalation (T1 fail → T2 → T3) to “discover” waits
- Condition waits as a new product (`wait until selector visible` with polling UI) — existing element-wait paths may remain; this feature is **timed** only
- Suite-level “global delay between all steps” setting
- Changing queue / cancel store APIs beyond consuming existing `cancel_check` / `is_cancel_requested`
- Calling tier executors from endpoints (hard constraint unchanged)

---

## Current State Analysis

### What exists

| Layer | Location | Status |
|-------|----------|--------|
| Step storage | `TestCase.steps` — typically `List[str]` newline-authored | Works; wait lines are plain strings today |
| Step editor | `frontend/src/components/TestStepEditor.tsx`, SavedTests edit drawer | Textarea of newline steps + separate `LoopBlockEditor` |
| Loop blocks | `test_data.loop_blocks` via `LoopBlockEditor.tsx` | **Different concern** — repeat ranges; must not be cloned for waits |
| Action inference | `ExecutionService._execute_step` (~lines 1350–1388) | Detects navigate/click/fill/verify/upload/… — **no wait/sleep/delay branch** |
| Tier dispatch | `ThreeTierExecutionService.execute_step` via `ExecutionService` | Correct layering; waits incorrectly fall through as unknown/verify/click-ish |
| Tier 1 wait | `tier1_playwright.py` `action == "wait"` → `_execute_wait` | Sleeps only if `selector_or_time` parses as **pure int** ms; ignores `timeout_ms` / `timeout`; uses unbroken `asyncio.sleep` |
| Tier 2 wait | `tier2_hybrid.py` `elif action == "wait": pass` | **No-op** — reports success without sleeping |
| Tier 3 | `tier3_stagehand.py` | May `act()` on NL including “wait…” without real timed sleep guarantee |
| Cancel | ADR-009 / `execution_cancel_store` / `cancel_check` in step loop | Exists between steps & tiers; **not** inside a long sleep |
| Readiness waits | `post_click_readiness.py`, step-boundary loading | Automatic engine behavior — **must stay separate** from user timed waits |
| Validation | `test_validation_service.py` | Structured `wait` expects `timeout` or `condition` — useful for structured form |

### What's broken (root cause)

| Gap | Effect |
|-----|--------|
| No timed-wait detection in `_execute_step` | NL `"wait 10 seconds"` never becomes `action=wait` with duration |
| No short-circuit before tiers | Engine tries Playwright/Hybrid/Stagehand; Tier 2 no-op “passes” instantly; Tier 3 may hallucinate |
| Tier 1 `_execute_wait` only `int(selector_or_time)` | Structured `{timeout_ms: 10000}` ignored if value is `"10s"` or empty |
| Tier 2 `pass` | False-positive success with zero pause |
| Unbroken sleep if Tier 1 path used | Stop mid-wait blocked until sleep ends (ADR-009 gap for waits) |
| No UI insert helper | Users type freeform NL that the engine ignores |

**Architect decision:** **Approach C** — UI-insertable wait **step** + NL/canonical parsing. Not a loop-block. Not “fix Stagehand wait.”

---

## Architecture Decision: Approach C — Step + Short-Circuit Sleep

### Decision

1. **Data:** Prefer a **canonical step line** in `steps[]` (string list). Optional structured dict steps remain supported when present.
2. **Detect** timed waits early in `ExecutionService._execute_step` (or immediately before calling `three_tier_service.execute_step`).
3. **Short-circuit:** perform cancel-aware chunked sleep in `ExecutionService` (or a tiny helper module owned by execution service), return success **without** calling Tier 1/2/3 for timed waits.
4. **Hardening:** Fix Tier 1 duration field reads; neutralize Tier 2 wait no-op (so accidental fall-through still sleeps or fails closed — prefer never fall through).
5. **Never** route timed waits to Stagehand `act()`.
6. **Cap** duration at **120s** (configurable constant); reject or clamp above max.
7. **NL:** only patterns that express a **numeric duration** are timed sleeps; “wait for \<UI condition\>” is **not**.

### Rationale

| Approach | Verdict |
|----------|---------|
| **C: UI step + NL/canonical + ExecutionService short-circuit** | **Accept** — fits string-step model; cancel-aware; surgical; no parallel metadata |
| A: Only fix Tier 1 `_execute_wait` | **Reject as sole fix** — NL never maps to wait; Tier 2 no-op still traps escalation; no cancel chunks |
| B: `wait_blocks` like `loop_blocks` | **Reject** — duplicates UX, splits storage, harder to ordinalize in progress UI |
| Stagehand `act("wait 10 seconds")` | **Reject** — nondeterministic, costly, not real sleep, breaks cancel story |
| Unbroken `asyncio.sleep(timeout_ms/1000)` | **Reject** — blocks ADR-009 Stop mid-wait |
| Treat all “wait …” as sleep | **Reject** — breaks condition/verify phrasing |

### Layering (hard constraints)

```
Endpoint → ExecutionService.execute_test / _execute_step
                │
                ├─ timed wait detected? ──► chunked cancel-aware sleep ──► return (no tiers)
                │
                └─ else ──► ThreeTierExecutionService.execute_step(..., cancel_check=)
                              Tier1 → Tier2 → Tier3
```

- Endpoints never call tier executors.
- Lazy Tier 2/3 init (ADR-002-1) remains: timed waits must not force Stagehand init.
- Cancel polls reuse Feature 1’s `cancel_check` / `is_cancel_requested(execution_id)`.

### Timed vs readiness vs condition (must not conflate)

| Kind | Example | Owner |
|------|---------|--------|
| **Timed wait (this feature)** | `Wait 10 seconds`, `wait: 10s`, `{action:"wait", timeout_ms:10000, kind:"timed"}` | User step; ExecutionService short-circuit |
| **ADR-002 readiness** | Spinner clear, payment iframe settle, post-click networkidle | `post_click_readiness.py` / tier internals — automatic |
| **Condition / element wait** | `Wait for the success message`, wait until selector visible | Existing verify / selector wait paths — **not** fixed-duration sleep |

---

## Data Model / Canonical Forms

### Preferred: string step lines (fit today’s model)

Canonical forms the parser **must** accept (case-insensitive where noted):

| Form | Example | Parsed duration |
|------|---------|-----------------|
| Human NL | `Wait 10 seconds` / `wait 10 second` / `wait 5 secs` | 10000 / 5000 ms |
| Human NL (minutes) | `Wait 1 minute` / `wait 2 minutes` | 60000 / 120000 ms (then clamp) |
| Compact | `wait: 10s` / `wait:10s` | 10000 ms |
| Milliseconds | `WAIT 10000ms` / `wait 10000 ms` | 10000 ms |
| Seconds keyword | `sleep 3` / `delay 3 seconds` | 3000 ms |

**Canonical insert from UI (recommended single form):**

```text
wait: 10s
```

Human-readable alternatives remain valid so existing handwritten tests work:

```text
Wait 10 seconds
```

### Optional structured step (when `steps` item is a dict)

```json
{
  "action": "wait",
  "timeout_ms": 10000,
  "instruction": "Wait 10 seconds",
  "kind": "timed"
}
```

Also accept `timeout` (ms) as alias for `timeout_ms`. Do **not** require `value` to be a pure int string.

### Explicitly not the data model

```json
// ❌ Do NOT add
"test_data": {
  "wait_blocks": [{ "after_step": 3, "duration_ms": 10000 }]
}
```

```json
// ❌ Do NOT reuse loop_blocks for waits
"loop_blocks": [{ "start": 2, "end": 2, "iterations": 1, "wait_ms": 10000 }]
```

Wait is an **ordinal step**, same as `"Click Login"`.

### Duration rules

| Rule | Value |
|------|-------|
| Minimum | 100 ms (or 1 second if UI only offers whole seconds — document choice; backend should accept ≥100 ms) |
| Maximum (hard cap) | **120_000 ms (120 s)** — clamp or fail with clear error; prefer **clamp + log warning** for NL; UI picker max 120s |
| Default UI presets | 1s, 2s, 5s, 10s, 30s, 60s, custom (1–120) |
| Units | Prefer seconds in UI; store/parse to ms internally |

### Non-timed patterns (must NOT sleep)

Examples that must **not** map to timed sleep:

- `Wait for the success message to appear`
- `Wait until the spinner disappears`
- `Wait for navigation to complete`
- `Wait for #checkout-button to be visible`
- `Please wait while we process` (no numeric duration)

Heuristic (decisive):

1. Match timed pattern only if a **numeric duration + time unit** (or bare `sleep N` / `WAIT Nms`) is present **and** the primary intent is pause — not “wait for \<target\>”.
2. Prefer regexes like:
   - `^\s*(wait|sleep|delay)\s*:?\s*(\d+)\s*(ms|milliseconds?|s|secs?|seconds?|m|mins?|minutes?)?\s*$`
   - `^\s*(wait|sleep|delay)\s+(\d+)\s*(ms|milliseconds?|s|secs?|seconds?|m|mins?|minutes?)\s*$`
3. Reject if `wait for` / `wait until` appears (unless a separate timed clause is unambiguously present — v1: **reject** `wait for` entirely as timed).

---

## Backend Behavior Spec

### 1. Detection + short-circuit (`execution_service.py`)

In `_execute_step`, **after** test-data substitution, **before** building heavy tier payloads / calling `three_tier_service.execute_step`:

1. Resolve duration from (priority):
   - structured `timeout_ms` / `timeout` if `action == "wait"` or `kind == "timed"`
   - else parse `instruction` / `step_description` with timed-wait regexes
2. If timed wait:
   - Clamp to `[min, MAX_TIMED_WAIT_MS]` (120_000)
   - Call `_sleep_cancel_aware(duration_ms, cancel_check)`
   - If cancel during sleep → raise/return path consistent with Feature 1 cancel (execution ends `cancelled`; wait step not marked as ordinary failure)
   - On success return `{ success: True, action: "wait", tier_used: "timed_wait" | "execution_service", duration_ms: actual, ... }` — **do not** invoke tiers
3. If not timed wait → existing three-tier path unchanged

**Suggested helper** (same file or `backend/app/services/timed_wait.py`):

```python
async def sleep_cancel_aware(
    duration_ms: int,
    cancel_check: Optional[Callable[[], bool]] = None,
    *,
    chunk_ms: int = 250,
) -> None:
    """Sleep in chunks; if cancel_check() becomes true, abort promptly (ADR-009)."""
```

- Default chunk **250 ms** (≤500 ms acceptable).
- Each chunk: `await asyncio.sleep(min(chunk_ms, remaining))` then `if cancel_check and cancel_check(): raise CancelledError` / return sentinel consumed by `_execute_step` / `execute_test`.
- Must work when `cancel_check` is `None` (still sleep in chunks for consistency, or single sleep — prefer chunks always).

### 2. Tier 1 field fix (`tier1_playwright.py`)

`_execute_wait` today:

```python
wait_ms = int(selector_or_time)  # fails for "10s", ignores timeout_ms
await asyncio.sleep(wait_ms / 1000)
```

Required:

- Prefer `step.get("timeout_ms")` or `step.get("timeout")` when present
- Else parse duration strings (`10s`, `10000ms`)
- Else pure int ms
- Else selector visibility wait (existing non-timed behavior)
- Use cancel-aware sleep if `cancel_check` is plumbed; if Tier 1 is only a backstop and short-circuit always wins for timed waits, still fix duration parsing + avoid unbroken sleep when cancel is available

### 3. Tier 2 no-op fix (`tier2_hybrid.py`)

```python
elif action == "wait":
    pass  # ❌ must not remain
```

Required: either unreachable for timed waits (preferred via short-circuit) **and** if reached, perform cancel-aware sleep using `timeout_ms`/`timeout`/parsed value — never `pass`.

### 4. Tier 3 / Stagehand

- Timed waits must not call `stagehand.act(...)`.
- Do not initialize Stagehand solely for a wait step (preserves ADR-002-1 lazy init).

### 5. Progress / screenshots

- Wait steps appear in progress like other steps (step index, instruction text).
- Screenshot: optional; prefer lightweight (skip or capture once after wait) — do not require Tier 2 observe.
- `execution_time_ms` should reflect approximate sleep duration.

---

## Frontend UX Spec

### Placement

Primary: **`TestStepEditor`** toolbar (alongside Insert Module / near steps textarea). Secondary: Saved Tests edit drawer if it uses a raw textarea without `TestStepEditor` — add the same control or reuse a shared `AddWaitControl` component.

**Path targets:**
- `frontend/src/components/TestStepEditor.tsx` (preferred)
- `frontend/src/pages/SavedTestsPage.tsx` edit drawer steps field (if not using TestStepEditor)
- Optional: `frontend/src/components/AddWaitButton.tsx` or inline control

### Control: [+ Add Wait]

| Attribute | Value |
|-----------|-------|
| Label | `+ Add Wait` |
| `data-testid` | `add-wait-step-button` |
| Interaction | Opens compact duration picker (popover or inline select) — **not** a loop-block panel |
| Presets | 1s, 2s, 5s, 10s, 30s, 60s |
| Custom | Number input 1–120 (seconds); disable/clamp >120 |
| Confirm | Inserts line `wait: {n}s` at **cursor position** or **end of steps** (document: prefer end if no cursor API; TestStepEditor textarea — insert at caret if feasible, else append with newline) |
| Result | Steps remain a newline-separated list; user can reorder by editing text |

**Critical:** Do **not** open `LoopBlockEditor`. Do **not** write `test_data.wait_blocks`.

### Progress page

No special Stop UX beyond Feature 1 — wait must respect existing Stop. Optional badge text: step instruction shows `wait: 10s`.

### Empty / error states

| State | Behavior |
|-------|----------|
| Custom duration empty | Disable Insert |
| Custom > 120 | Clamp to 120 or show inline error “Max 120 seconds” |
| Custom < 1 | Show error or clamp to 1 |
| Unsaved insert | User still Save / autosave as today |

---

## Design Direction

- **Color palette:** Neutral secondary control — e.g. slate border `#64748b` text, hover `#f1f5f9`; not purple gradient, not alarm red (red reserved for Stop)
- **Typography:** Same `text-sm` as Insert Module / loop toolbar; monospace optional for inserted `wait: 10s` line only
- **Layout:** Compact toolbar button + small popover; airy, not a card grid of durations
- **Visual identity:** Clock / timer icon (Lucide `Timer` or `Clock`) — distinct from Loop (`Repeat`) and Module insert
- **Inspiration:** Playwright codegen pause, Cypress `cy.wait(ms)` as an explicit step, Postman delay — utilitarian, not decorative
- **Anti-AI-slop:** No animated hourglass mascot; no “smart wait AI” marketing copy; no duplicate loop-block chrome

**Anti-patterns to avoid:**
- Cloning `LoopBlockEditor` UX for waits
- Modal wizard with 5 screens to add a wait
- Hiding wait only inside Advanced settings
- Inserting structured JSON into the textarea mixed with NL lines unless the editor already supports dict steps

---

## Features (Prioritized)

### Must-Have (Sprint 8–9)

1. **Timed-wait detector** — NL + canonical + structured `timeout_ms`/`timeout`
2. **ExecutionService short-circuit** — cancel-aware chunked sleep; no tier call
3. **Duration cap** — 120s max
4. **NL boundaries** — `wait for …` does not sleep
5. **Tier 1 duration fields** — read `timeout_ms`/`timeout`; parse `10s`
6. **Tier 2 wait no-op fix** — no silent `pass` for timed wait
7. **Unit tests** — duration, cancel mid-wait, non-timed exclusion
8. **UI [+ Add Wait]** — duration picker inserts `wait: Ns` step line

### Should-Have (Sprint 10)

9. Shared `timed_wait.py` helper used by ExecutionService (and Tier 1/2 backstops)
10. Progress metadata: `tier_used: "timed_wait"`, `duration_ms` on step result
11. ADR-002 addendum / short note: intentional timed wait vs readiness
12. Frontend component test for Add Wait insert
13. SavedTests drawer parity if steps edited outside TestStepEditor

### Nice-to-Have (Sprint 11+)

14. Drag-reorder visual steps (only if product already moving off pure textarea)
15. Per-project max wait override in settings
16. Telemetry: count timed-wait steps / cancel-during-wait rate
17. MCP / Hermes step library module “Wait N seconds”

---

## Sprint Plan

### Sprint 8: Backend Short-Circuit + Cancel-Aware Sleep

**Goals:** NL/canonical/structured timed waits actually pause; Stop works mid-wait; no Stagehand for waits.

| # | File | Task |
|---|------|------|
| 8.1 | `backend/app/services/timed_wait.py` (new) or helpers in `execution_service.py` | `parse_timed_wait_ms(instruction, step=None) -> Optional[int]`; `sleep_cancel_aware(...)` |
| 8.2 | `backend/app/services/execution_service.py` | Detect timed wait in `_execute_step`; short-circuit before `three_tier_service.execute_step` |
| 8.3 | `backend/app/services/tier1_playwright.py` | `_execute_wait` reads `timeout_ms`/`timeout`; parse duration strings; prefer cancel-aware sleep if check available |
| 8.4 | `backend/app/services/tier2_hybrid.py` | Replace `action == "wait": pass` with real sleep or explicit “unsupported without duration” error — never silent success |
| 8.5 | Guard | Assert timed-wait path does not call Tier 3 / does not init Stagehand |
| 8.6 | `backend/tests/unit/test_timed_wait.py` (new) | Parse matrix, sleep duration (±tolerance), cancel mid-wait, non-timed exclusion, clamp 120s |

**Definition of done:**
- Running a test whose steps include `Wait 10 seconds` pauses ~10s
- Cancel during wait → `cancelled` within ~1s
- `wait for the success message` does not take a fixed 10s sleep from this feature
- `pytest -k timed_wait` green
- Feature 1 Stop still works for non-wait steps

---

### Sprint 9: UI Add Wait + Editor Integration

**Goals:** Users can insert a wait without memorizing syntax.

| # | File | Task |
|---|------|------|
| 9.1 | `frontend/src/components/AddWaitControl.tsx` (or inline) | Duration picker + presets + clamp 1–120s |
| 9.2 | `frontend/src/components/TestStepEditor.tsx` | Wire **[+ Add Wait]**; insert `wait: {n}s` into steps text |
| 9.3 | `SavedTestsPage.tsx` (if needed) | Same control on drawer steps editor |
| 9.4 | Frontend test | Button inserts expected canonical line; rejects >120 |

**Definition of done:** Evaluator can Add Wait → Save → Run → observe pause; steps JSON contains the wait line (not `loop_blocks`).

---

### Sprint 10: Docs + Polish

**Goals:** Document intentional vs automatic waits; result metadata clarity.

| # | File | Task |
|---|------|------|
| 10.1 | `documentation/ADR-002-test-execution-engine.md` addendum **or** short ADR-010 | Timed wait vs readiness; Approach C; cancel chunks |
| 10.2 | `docs/CODEMAPS/execution-engine.md` | Note short-circuit timed wait in dispatch diagram |
| 10.3 | Step result fields | Expose `duration_ms` / `tier_used` for wait steps in execution progress payload if cheap |

**Definition of done:** Docs state wait is a **step**, not a loop block; Evaluator rubric script passes.

---

## Test Strategy

### Backend unit: `test_timed_wait.py`

| Test | Assertion |
|------|-----------|
| `test_parse_wait_10_seconds` | `"Wait 10 seconds"` → 10000 |
| `test_parse_wait_canonical` | `"wait: 10s"` → 10000 |
| `test_parse_wait_ms` | `"WAIT 5000ms"` → 5000 |
| `test_parse_structured_timeout_ms` | `{action:"wait", timeout_ms:3000}` → 3000 |
| `test_parse_structured_timeout_alias` | `{action:"wait", timeout:3000}` → 3000 |
| `test_reject_wait_for_message` | `"Wait for the success message"` → `None` (not timed) |
| `test_reject_wait_until` | `"Wait until spinner disappears"` → `None` |
| `test_clamp_above_120s` | `"Wait 999 seconds"` → 120000 (or rejected — pick one; document) |
| `test_sleep_duration_approx` | Short-circuit sleep 500ms completes in ~500ms ±250ms |
| `test_cancel_mid_wait` | Set cancel flag after start; sleep aborts <1s for a 10s wait |
| `test_tier2_wait_not_noop` | If Tier 2 wait path invoked with duration, does not return instant success via `pass` |
| `test_no_stagehand_for_timed_wait` | Mock three-tier; timed wait never calls Tier 3 execute |

### Frontend

| Test | Assertion |
|------|-----------|
| Add Wait inserts line | After confirm 10s, textarea/steps contain `wait: 10s` |
| Not loop_blocks | Save payload `test_data.loop_blocks` unchanged by Add Wait |
| Max clamp | Custom 200 → error or clamped 120 |

### Manual / Evaluator script

See `gan-harness/eval-rubric-timed-wait.md` § Evaluator Test Script.

---

## Risks & Edge Cases

| Scenario | Expected behavior |
|----------|-------------------|
| Wait as first step | Allowed; sleeps before other actions (after initial navigation if engine always navigates first — do not skip wait) |
| Wait as last step | Allowed; sleep then complete |
| Wait inside loop body | Treated as normal step in expanded loop iterations; still cancel-aware |
| Multiple waits | Each honored independently |
| `wait: 0s` / empty | Reject or treat as no-op min; prefer validation error in UI |
| Mixed dict + string steps | Parser handles both |
| Cancel before wait starts | Existing step-boundary cancel; wait never begins |
| Cancel during wait | Abort chunked sleep; finalize `cancelled` (ADR-009) |
| Tier 2 observe init | Timed wait must not force xpath/Stagehand init |
| Concurrent readiness after previous click | Readiness runs for **previous** action path only; timed wait does not replace or disable readiness for other steps |
| User writes `wait 10 seconds for the modal` | v1: treat as **non-timed** if `for` present (safe); or document as ambiguous — prefer non-timed |
| Very long suite with many 120s waits | Cap per step still 120s; no suite-level sum cap in v1 |
| Clone test with wait steps (Feature 2) | Clone copies step strings including `wait: 10s` |

**Empty/error states:**
- Parse failure on structured wait without duration → fail step with clear message: `Timed wait requires timeout_ms or duration in instruction`
- Do not mark as passed via Tier 2 `pass`

---

## Evaluation Criteria

See `gan-harness/eval-rubric-timed-wait.md` for weighted scoring (pass ≥ 0.85).

**Summary weights:**
- Backend short-circuit & duration fidelity: 0.35
- Cancel mid-wait (ADR-009): 0.20
- NL parse boundaries & anti-conflation: 0.15
- Tier safety (no Stagehand / Tier 2 no-op fixed): 0.15
- UI Add Wait (step, not loop block): 0.15

**Automatic fail conditions:**
- Timed wait implemented only via Stagehand `act()`
- Wait stored as `loop_blocks` / `wait_blocks` instead of a step line
- Unbroken sleep with no cancel polling (Stop blocked for full duration)
- Every phrase containing “wait” sleeps a fixed duration
- Tier 2 `action == "wait": pass` remains for timed waits
- Conflates feature with changing `post_click_readiness` as the primary “fix”

---

## Success Metrics

| Metric | Target |
|--------|--------|
| NL `Wait N seconds` honored | Pause within ±1s of N for N≤30 |
| Cancel latency mid-wait | ≤ 1s from Stop click to cooperative abort of sleep |
| False-positive timed parse | 0 on evaluation phrase set (`wait for…`, `wait until…`) |
| Stagehand invocations on pure wait step | 0 |
| UI insert | 1 click + duration confirm → canonical line in `steps` |
| Cap | Durations >120s never run unbounded |

---

## Implementation Order (Generator — do not reorder)

1. Backend short-circuit + cancel-aware chunked sleep  
2. Fix Tier 1 duration fields; neutralize Tier 2 no-op  
3. Unit tests (duration, cancel mid-wait, non-timed exclusion)  
4. UI Add Wait duration picker → inserts canonical line  
5. Docs/ADR note: intentional timed wait vs automatic readiness  

---

## Related Artifacts

| Artifact | Role |
|----------|------|
| `gan-harness/eval-rubric-timed-wait.md` | Weighted Evaluator rubric |
| `documentation/ADR-009-execution-cancel.md` | Cancel must work mid-wait |
| `docs/CODEMAPS/execution-engine.md` | Execution layering / readiness distinction |
| `documentation/ADR-002-test-execution-engine.md` | Readiness waits; addendum target for timed wait note |
| Feature 1 Stop Execution | Cancel UX + `cancel_check` plumbing to reuse |

---

# Feature 5: Signature Pad Ink Verification — No False-PASS on Empty Canvas

> **Implementation status:** Done (Sprints 11–14, Feature 5.1). Eval: [`gan-harness/eval-report-signature-pad.md`](eval-report-signature-pad.md) — PASS 1.00, 61 unit tests, 100% coverage on `backend/app/services/signature_pad.py`.

> Generated from brief / architect investigation: *"Fix: Step 'sign under please sign here' (and credit-card 'sign it') marked PASS with empty canvas — Stagehand act() only scrolls/locates; programmatic stroke fallback never runs; no ink verification. Executions #1120 / #1122."*

---

## Vision

QA runs that include consent or payment **signature pads** must leave real ink on the canvas before a step can PASS. Today Tier 3 Stagehand `act()` often returns soft success after `scrollIntoView` / locator-only work on the label text ("Please sign here:"), `_execute_draw_signature_fallback()` never runs because `act()` does not throw, and the step is marked `success=true` with a blank pad — then the form rejects with "Please complete the highlighted required fields." **Signature Pad Ink Verification** makes **programmatic pointer/mouse/touch stroke + ink verification** the source of truth for `draw_signature` / `sign` actions: never treat scroll/locate alone as signed; fail closed when the pad is empty so escalation/retry can occur; share Tier 2’s multi-strategy draw into a reusable module.

The product feel: a sign step either draws a verifiable stroke (PASS) or fails honestly (FAIL) — never a green check on an empty SignaturePad.

---

## User Story

**As a** QA engineer running a saved test that includes "Sign under Please sign here" or "Sign it" on a credit-card pad,  
**I want** the engine to actually draw on the canvas and verify ink before marking the step passed,  
**So that** consent/payment forms accept the signature and I do not get false PASS followed by required-field validation errors.

**Acceptance (happy path):**
1. User Runs a test with a step like `Sign under "Please sign here"` or `Sign it` (credit card modal).
2. Engine reaches the signature step (Tier 1 may lack selector; Tier 2 may observe `[]` for canvas-not-in-a11y-tree).
3. On Tier 3 (or shared helper used by Tier 2/3): programmatic stroke runs — **not** only `act()` scroll/locator.
4. Ink verification passes (`SignaturePad.isEmpty === false` and/or non-blank pixel sample) → step `success=true`, screenshot shows ink.
5. If stroke fails or pad remains empty → step `success=false` with a clear error (not silent PASS).
6. Downstream form submit no longer fails solely because the pad was never signed by a false-PASS step.
7. Step `Click the Signature button` (open modal) is treated as **click**, not `draw_signature` (P2).

---

## Scope

### In scope

| Area | Deliverable |
|------|-------------|
| Tier 3 sign path | For `draw_signature` / `sign`: programmatic pointer stroke is source of truth; never treat `act()` `scrollIntoView` / locator-only as signed |
| Ink verification | Before PASS: pixels and/or `SignaturePad.isEmpty === false`; else FAIL |
| Shared helper | Prefer `backend/app/services/signature_pad.py` extracting Tier 2 multi-strategy draw + verify |
| Tier 2 observe-empty | On observe `[]` for sign steps, locate canvas by heuristics (near label / largest visible canvas) before escalate (P1) |
| Action detection | "Click … Signature" (open modal) → `click`, not `draw_signature` (P2) |
| Tests | Comprehensive unit coverage of helper + Tier 3 false-success path |
| Docs | Short note in execution-engine / ADR-002 addendum if architecture changes |
| Rubric | `gan-harness/eval-rubric-signature-pad.md` |

### Out of scope

- Early Stagehand init for signatures (violates ADR-002-1 lazy tiers)
- Calling tier executors from endpoints (hard constraint unchanged)
- Rewiring ObservationAgent `draw_signature_pad` tooling into three-tier as the primary path (may remain generation-only)
- Painting via `getContext` **alone** without pointer/mouse/touch events (SignaturePad library state requires events; ctx paint may be secondary)
- Redesigning signature UX in the product under test
- Changing ExecutionService → ThreeTierExecutionService dispatch layering
- Frontend UI for a new "Add Signature" control (this is an execution correctness fix)
- Broad Stagehand `act()` reliability overhaul beyond sign/draw_signature gating

### Goals

1. **P0:** Eliminate false PASS when `act()` only scrolls/locates on sign steps.
2. **P0:** Ink verification gate before PASS.
3. **P1:** Tier 2 canvas heuristics when observe returns empty for sign steps.
4. **P2:** Correct action detection so "Click … Signature" opens the pad via click.

### Non-goals

- Making Stagehand `act()` draw real ink via LLM (unreliable; optional locator aid only).
- Replacing the three-tier stack for signatures with ObservationAgent tooling.
- Perfect OCR of handwritten names — only presence of ink / non-empty SignaturePad state.

---

## Current State Analysis

### Investigation evidence (must not regress)

| Execution | Step | Observed failure mode |
|-----------|------|----------------------|
| **#1120** | Consent sign (LLM step 48 / UI Step 49) | Tier 2 observe returns `{"elements":[]}` (canvas not in a11y tree); Tier 3 `act()` returns `method:"scrollIntoView"` on "Please sign here:" text; `_execute_draw_signature_fallback()` **never runs** because `act()` does not throw; `success=true` with blank pad (`exec_1120_step_49_pass.png`) |
| **#1122** | Same pattern | Confirms reproducible false success |
| Credit card | Steps 43–44 "sign it" | Same false success via locator / `scrollIntoView` |
| Downstream | Form validation | "Please complete the highlighted required fields" after false-PASS sign |

### What exists

| Layer | Location | Status |
|-------|----------|--------|
| Action inference | `execution_service.py` ~1398–1400 | `"sign" \| "signature" \| "draw"` → `draw_signature` (also catches "Click … Signature" — P2 bug) |
| Tier 1 | `tier1_playwright.py` `_execute_draw_signature` | Draws if selector present; often no selector on NL steps |
| Tier 2 observe | Hybrid observe / a11y | Canvas often **absent** from a11y tree → `elements: []` → escalate |
| Tier 2 draw | `tier2_hybrid.py` `_execute_draw_signature` ~3734–3905 | **Capable:** mouse drag + ctx stroke + pointer/touch dispatch |
| Tier 3 act path | `tier3_stagehand.py` ~270–282 | Trusts `act()` success; fallback **only on exception** |
| Tier 3 fallback | `_execute_draw_signature_fallback` ~433+ | Exists but **unreachable** on soft act() success |
| ObservationAgent | `draw_signature_pad` tooling | Generation/orchestration — **not** wired into three-tier execution |
| SignaturePad apps | Common in consent/payment UIs | Require pointer events for `isEmpty === false`; bare canvas paint may not update library state |

### What's broken (root cause)

| Gap | Effect |
|-----|--------|
| Tier 3 trusts `act()` without ink check | `scrollIntoView` / locator soft success → PASS on blank pad |
| Fallback only on exception | Soft success never triggers `_execute_draw_signature_fallback()` |
| No ink verification | Blank pad indistinguishable from signed pad at step result layer |
| Tier 2 empty observe | Escalates to Tier 3 without trying canvas heuristics near "Please sign here" |
| Action detection over-broad | "Click Signature" misclassified as `draw_signature` |

**Architect decision:** Programmatic stroke is **source of truth** for sign/draw_signature; `act()` may aid locating at most; ink verify before PASS; extract shared `signature_pad.py`.

---

## Architecture Decision: Programmatic Stroke + Ink Gate

### Decision

1. **Source of truth:** For `action in ("draw_signature", "sign")`, always perform (or confirm) a **programmatic multi-strategy stroke** via shared helper — prefer pointer/mouse/touch events (SignaturePad-compatible); ctx paint optional secondary.
2. **Never PASS on locate-only:** If `act()` result is only `scrollIntoView`, locator, or equivalent non-draw method, treat as **not signed** — run programmatic stroke (do not require `act()` to throw).
3. **Ink gate:** After stroke attempt, verify ink (`SignaturePad.isEmpty === false` when library present, and/or non-blank pixel sampling on canvas). If empty → **fail** the step (so escalation/retry can happen).
4. **Shared module:** Extract Tier 2 strategies into `backend/app/services/signature_pad.py` (locate canvas, stroke, verify). Tier 2 and Tier 3 call the same helper.
5. **`act()` role (optional):** Locator/scroll aid only; never sole success signal for sign steps.
6. **Lazy tiers:** Do not init Stagehand early solely for signatures (ADR-002-1). Tier 2 heuristics (P1) reduce unnecessary Tier 3.
7. **Action detection (P2):** Prefer `click` when instruction is clearly "click … signature" (open control), not draw-on-pad.

### Rationale

| Approach | Verdict |
|----------|---------|
| **Programmatic stroke + ink verify (shared helper)** | **Accept** — capability already in Tier 2; Tier 3 fallback exists but unreachable |
| Trust `act()` success for sign | **Reject** — proven false PASS (#1120/#1122) |
| Fallback only on `act()` exception | **Reject** — soft success skips fallback |
| Ctx `getContext` paint alone | **Reject as sole strategy** — SignaturePad may stay `isEmpty` |
| Wire ObservationAgent tool into three-tier | **Defer** — out of scope; generation tooling ≠ execution path |
| Early Stagehand for every sign step | **Reject** — ADR-002-1 |

### Layering (hard constraints)

```
Endpoint → ExecutionService._execute_step
              │
              └─► ThreeTierExecutionService.execute_step
                    Tier1 (selector draw if any)
                      → Tier2 (observe; P1: canvas heuristics on [] for sign)
                        → Tier3 (act optional locate aid ONLY)
                              → signature_pad.stroke + verify  ← source of truth
                              → PASS iff ink verified else FAIL
```

- Endpoints never call tier executors.
- Lazy Tier 2/3 init unchanged: do not init Stagehand before Tier 1 failure / normal escalation.
- Prefer shared helper over duplicating stroke logic in Tier 3 fallback only.

### Soft-success methods that must NOT imply signed

Treat as **not signed** (non-exhaustive; implement via allowlist of draw-like methods or denylist):

- `scrollIntoView` / `scroll`
- Locator / highlight / focus without pointer stroke
- `click` on **label text** only (without canvas interaction) — still require stroke + ink
- Any `act()` result where no pointer path was applied to a `<canvas>`

---

## Target Behavior Spec

### 1. Shared helper (`backend/app/services/signature_pad.py`)

Suggested surface (names flexible; behaviors required):

```python
async def locate_signature_canvas(page, *, instruction: str | None = None) -> Locator: ...
async def draw_signature_stroke(page, canvas, *, strategies: ...) -> None: ...
async def verify_signature_ink(page, canvas) -> bool: ...
async def sign_canvas(page, *, instruction: str | None = None, xpath: str | None = None) -> SignResult: ...
```

**Locate heuristics (P0 minimal + P1 expansion):**
- Explicit xpath/selector when provided
- `canvas.signature-pad`, `canvas[id*='signature' i]`, `canvas[class*='signature' i]`
- Near text: "Please sign here", "signature", "Sign here" (ancestor/sibling search)
- Largest visible `<canvas>` in viewport as last resort (with logging)

**Stroke strategies (order — prefer events for SignaturePad):**
1. Playwright mouse drag across canvas bbox
2. Dispatch `pointerdown` / `pointermove` / `pointerup` (+ mouse/touch analogs) on canvas
3. Optional: ctx 2d stroke as visual backup **after** events (not alone for PASS)

**Verify (required before PASS):**
1. If `canvas` has SignaturePad instance / `window` hook / common `isEmpty` API → require `isEmpty === false`
2. Else sample ImageData / dataURL — require non-near-white / non-transparent pixel change vs pre-stroke snapshot when feasible
3. If verify fails → raise / return failure (do not PASS)

### 2. Tier 3 (`tier3_stagehand.py`)

Replace trust-act-or-exception pattern (~270–282):

**Required logic:**
1. Optionally call `act()` as locator aid (may scroll label into view).
2. **Always** call shared `sign_canvas` / strengthen `_execute_draw_signature_fallback` to use shared helper.
3. **Always** verify ink before returning success.
4. If ink missing → fail (exception or `success=False`) — do **not** mark PASS because `act()` returned.

Do **not** gate fallback on `except` alone.

### 3. Tier 2 (`tier2_hybrid.py`) — P1

When action is sign/draw_signature and observe returns empty elements:
- Run canvas locate heuristics before escalating to Tier 3
- On found canvas → call shared `sign_canvas` + verify
- On not found → escalate as today

Refactor existing `_execute_draw_signature` to call shared helper (surgical; preserve behavior).

### 4. Action detection (`execution_service.py`) — P2

Adjust order/heuristics so:

| Instruction | Expected action |
|-------------|-----------------|
| `Sign under "Please sign here"` | `draw_signature` |
| `Sign it` / `Draw signature` | `draw_signature` |
| `Click the Signature button` / `Click Signature` | `click` |
| `Open the signature pad` | `click` (or navigate/click — not draw) |

Rule of thumb: leading **click/open/tap** on a Signature **control** → `click`; **sign/draw** on pad/label → `draw_signature`.

### 5. Tier 1

Keep selector-based draw; optionally route through shared helper for verify consistency when selector present. Not the primary #1120 fix path.

---

## Design Direction

This feature is **execution correctness**, not a new branded UI surface.

- **Color palette:** N/A for product chrome; failure messages stay existing error red / toast patterns
- **Typography:** Existing progress step text; error string should be explicit, e.g. `Signature pad appears empty after stroke (ink verification failed)`
- **Layout philosophy:** No new cards/modals
- **Visual identity:** Screenshots after PASS must show ink; evaluator compares blank vs signed
- **Inspiration:** Playwright canvas drawing recipes; SignaturePad event model
- **Anti-AI-slop:** Do not "fix" by teaching Stagehand a longer prompt alone; do not mark PASS on scroll; do not ship decorative signature animations in our UI

**Anti-patterns to avoid:**
- `except: fallback` only (soft success hole remains)
- PASS when `act()` method is `scrollIntoView`
- Ctx fill alone without events when SignaturePad is present
- Eager Stagehand init for every sign step
- Broad unrelated refactors of Tier 2/3

---

## Features (Prioritized)

### Must-Have (Sprint 11 — P0)

1. **Shared `signature_pad.py`** — locate + multi-strategy stroke + ink verify
2. **Tier 3 always strokes** — programmatic stroke source of truth; `act()` not sole success
3. **Deny soft-success PASS** — `scrollIntoView` / locator-only ≠ signed
4. **Ink verification gate** — empty pad → FAIL
5. **Unit tests** — helper strategies + Tier 3 false-success path (mock `act()` soft success → must still stroke/verify)

### Should-Have (Sprint 12 — P1)

6. **Tier 2 empty-observe heuristics** — find canvas near "Please sign here" / largest visible canvas before escalate
7. **Tier 2 refactor** — `_execute_draw_signature` delegates to shared helper
8. **Docs note** — execution-engine / ADR-002 addendum: sign steps require ink verify

### Nice-to-Have (Sprint 13 — P2)

9. **Action detection** — "Click … Signature" → `click` not `draw_signature`
10. **Pre/post canvas snapshot** in step metadata for debugging
11. **Telemetry** — count sign false-fail vs ink-verified pass

---

## Sprint Plan

### Sprint 11: P0 — Tier 3 Truth + Ink Gate + Shared Helper

**Goals:** Executions like #1120/#1122 cannot PASS on blank pad; programmatic stroke always runs for sign actions; unit tests lock the false-success path.

| # | File | Task |
|---|------|------|
| 11.1 | `backend/app/services/signature_pad.py` (new) | `locate_signature_canvas`, `draw_signature_stroke` (mouse + pointer/touch; optional ctx), `verify_signature_ink`, `sign_canvas` |
| 11.2 | `backend/app/services/tier3_stagehand.py` | For `draw_signature`/`sign`: do not trust `act()` alone; always call shared stroke; verify ink before success; soft `scrollIntoView` must not PASS |
| 11.3 | `backend/app/services/tier3_stagehand.py` | Refactor `_execute_draw_signature_fallback` to shared helper (or replace call sites) |
| 11.4 | `backend/tests/unit/test_signature_pad.py` (new) | Locate heuristics, stroke strategy presence, ink verify true/false, soft-act path never PASS without verify |
| 11.5 | Tier 3 unit/integration test | Mock `act()` returning `method: scrollIntoView` / success without throw → assert fallback/helper invoked and empty ink → failure |

**Definition of done:**
- Simulated #1120 path: `act()` soft success + empty canvas → step **fails** (or strokes then verifies)
- After successful stroke + ink → PASS
- `pytest -k signature_pad` green
- No early Stagehand init beyond normal escalation
- Dispatch still ExecutionService → ThreeTier only

---

### Sprint 12: P1 — Tier 2 Canvas Heuristics + Shared Refactor

**Goals:** Reduce unnecessary Tier 3 when canvas is findable near label despite empty a11y observe.

| # | File | Task |
|---|------|------|
| 12.1 | `signature_pad.py` | Heuristics: near "Please sign here" / signature text; largest visible canvas |
| 12.2 | `tier2_hybrid.py` | On observe `[]` for sign steps, locate via helper before escalate |
| 12.3 | `tier2_hybrid.py` | `_execute_draw_signature` uses shared helper |
| 12.4 | Unit tests | Empty observe + visible canvas near label → stroke without requiring Tier 3 |
| 12.5 | Docs | `docs/CODEMAPS/execution-engine.md` and/or ADR-002 short note |

**Definition of done:** Sign steps with canvas outside a11y tree but visible in DOM can succeed at Tier 2 when heuristics find canvas; ink still verified.

---

### Sprint 13: P2 — Action Detection Hygiene

**Goals:** Opening a signature modal is a click; drawing on the pad is draw_signature.

| # | File | Task |
|---|------|------|
| 13.1 | `execution_service.py` | Refine detection so `Click … Signature` → `click` before broad `sign`/`signature` match |
| 13.2 | Unit tests | Matrix of instructions → expected action |
| 13.3 | Non-regression | `Sign under Please sign here` still `draw_signature` |

**Definition of done:** Detection matrix green; no regression on true sign NL.

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC1 | For `draw_signature`/`sign`, programmatic stroke runs even when `act()` returns soft success (`scrollIntoView` / locator) without throwing |
| AC2 | Step PASS requires ink verification (`SignaturePad.isEmpty === false` and/or non-blank pixels); empty canvas → FAIL |
| AC3 | `_execute_draw_signature_fallback` / shared helper is reachable on soft `act()` success (not exception-only) |
| AC4 | Pointer/mouse/touch strategies preferred over ctx-only paint for SignaturePad compatibility |
| AC5 | Shared module preferred (`signature_pad.py`); Tier 2/3 reuse |
| AC6 | No eager Stagehand init for signatures (ADR-002-1); dispatch remains ExecutionService → ThreeTier |
| AC7 | Unit tests cover helper + Tier 3 false-success path comprehensively |
| AC8 (P1) | Tier 2 on observe `[]` attempts canvas heuristics before escalate |
| AC9 (P2) | `Click … Signature` → `click`; true sign NL → `draw_signature` |
| AC10 | Regression: consent + credit-card sign steps must not false-PASS blank pads as in #1120/#1122 |

---

## Test Strategy

### Backend unit: `test_signature_pad.py`

| Test | Assertion |
|------|-----------|
| `test_verify_ink_empty_fails` | Blank canvas → `verify_signature_ink` false |
| `test_verify_ink_after_stroke_passes` | After pointer stroke (or mocked ink) → true |
| `test_signaturepad_isempty_false` | When `isEmpty` API present, require false |
| `test_locate_near_please_sign_here` | Heuristic finds canvas near label text |
| `test_locate_largest_visible_canvas` | Fallback picks largest visible canvas |
| `test_stroke_uses_pointer_events` | Dispatch/mouse path invoked (not ctx-only) |
| `test_tier3_soft_act_scrollintoview_does_not_pass` | Mock `act()` → `scrollIntoView` success, empty ink → step failure / helper called |
| `test_tier3_soft_act_then_stroke_and_verify_passes` | Soft act + successful stroke + ink → success |
| `test_fallback_not_exception_only` | Helper runs when `act()` does not throw |
| `test_ctx_only_insufficient_when_signaturepad_empty` | If library still empty after ctx paint alone, verify fails (or stroke includes events) |

### Action detection (Sprint 13)

| Test | Assertion |
|------|-----------|
| `test_click_signature_is_click` | `"Click the Signature button"` → `click` |
| `test_sign_under_is_draw` | `"Sign under Please sign here"` → `draw_signature` |
| `test_sign_it_is_draw` | `"Sign it"` → `draw_signature` |

### Manual / Evaluator script

See `gan-harness/eval-rubric-signature-pad.md` § Evaluator Test Script.

Reproduce mentally against #1120: consent pad + credit-card pad must show ink on PASS screenshots; empty → FAIL.

---

## Risks & Edge Cases

| Scenario | Expected behavior |
|----------|-------------------|
| Canvas not in a11y tree | P1 heuristics / Tier 3 DOM locate; not false PASS |
| Multiple canvases | Prefer signature-named / near label; else largest visible; log choice |
| SignaturePad requires pen pressure | pointer events with `pointerType` / pressure as in Tier 2 today |
| `act()` throws | Still run programmatic stroke (or existing fallback path) + verify |
| `act()` draws real ink somehow | Verify still runs; PASS only if ink present |
| Iframe signature pad | Document limitation; best-effort locate in frame if existing patterns allow; else FAIL clearly |
| Read-only / disabled canvas | Stroke may fail → FAIL with clear error |
| Step is click-to-open modal | P2: `click`, then later step signs |
| Tier 1 has good selector | Draw + verify via helper; consistent gate |
| Cancel mid-stroke | Feature 1 cancel_check if plumbed; do not leave false PASS |
| Downstream validation message | Should not appear solely due to blank pad after a "passed" sign step |

**Empty/error states:**
- No canvas found → FAIL: `No signature canvas found`
- Canvas found, ink still empty after strategies → FAIL: `Signature pad appears empty after stroke (ink verification failed)`
- Never PASS with blank pad screenshot for sign actions

---

## Evaluation Criteria

See `gan-harness/eval-rubric-signature-pad.md` for weighted scoring (pass ≥ 0.85).

**Summary weights:**
- Tier 3 no false-PASS / stroke source of truth: 0.35
- Ink verification gate: 0.25
- Shared helper + event strategies: 0.15
- Tests (helper + soft-act path): 0.15
- P1 heuristics / P2 detection (partial credit if P0 solid): 0.10

**Automatic fail conditions:**
- Sign step can PASS when `act()` only returns `scrollIntoView` / locator and canvas remains empty
- Fallback still exception-only (soft success skips stroke)
- PASS without ink verification
- Ctx `getContext` paint alone is the only strategy and SignaturePad stays empty while step PASSes
- Stagehand eagerly initialized for signatures outside normal lazy escalation
- Tier executors called from endpoints
- Unrelated large refactors shipped as the "fix"

---

## Success Metrics

| Metric | Target |
|--------|--------|
| False PASS on blank consent pad (#1120 class) | 0 |
| False PASS on credit-card sign (#1122 class) | 0 |
| Ink verify on every sign PASS | 100% |
| Soft `act()` success without stroke | 0 (must stroke or fail) |
| Unit tests for helper + Tier 3 soft path | Comprehensive; CI green |
| Lazy Stagehand | No new early-init path |

---

## Implementation Order (Generator — do not reorder)

1. Create `signature_pad.py` (locate + event stroke + ink verify)  
2. Wire Tier 3 sign path: always stroke + verify; kill soft-success PASS  
3. Unit tests for helper + Tier 3 `scrollIntoView` false-success path  
4. (P1) Tier 2 empty-observe canvas heuristics + refactor to shared helper  
5. (P2) Action detection: Click Signature → click  

---

## Related Artifacts

| Artifact | Role |
|----------|------|
| `gan-harness/eval-rubric-signature-pad.md` | Weighted Evaluator rubric (this feature) |
| `backend/app/services/tier3_stagehand.py` | Soft-success hole ~270–282; fallback ~433+ |
| `backend/app/services/tier2_hybrid.py` | Capable `_execute_draw_signature` ~3734–3905 |
| `backend/app/services/tier1_playwright.py` | Selector draw path |
| `backend/app/services/execution_service.py` | Action detection ~1398–1400 |
| `documentation/ADR-002-test-execution-engine.md` | Lazy tiers ADR-002-1; execution architecture |
| `docs/CODEMAPS/execution-engine.md` | Dispatch / tier map |
| Executions #1120 / #1122 | Repro evidence (consent + credit-card blank PASS) |
