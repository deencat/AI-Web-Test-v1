# Product Specification: Stop Execution — Cooperative Cancel for 3-Tier Test Runs

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
