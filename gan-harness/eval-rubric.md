# Evaluation Rubric: Stop 3-Tier Execution

**Feature:** Cooperative cancel for saved test 3-tier execution  
**Spec:** `gan-harness/spec.md`  
**Weight total:** 1.0  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** No cancel API endpoint; no Stop button on ExecutionProgressPage; running execution stuck in `running` after stop click; cancel conflated with DELETE execution record; normal pass/fail runs regress

---

## Implementation Checklist (Generator)

Sprint order — **do not skip**:

| Sprint | Deliverables | Key paths |
|--------|--------------|-----------|
| 1 | Store + CRUD + API | `execution_cancel_store.py`, `crud/test_execution.cancel_execution`, `executions.py` DELETE `/{id}/cancel` |
| 2 | Execution hooks | `execution_service.execute_test`, `three_tier_execution_service.execute_step(..., cancel_check=)`, `queue_manager.py` |
| 3 | Frontend | `StopExecutionButton.tsx`, `executionService.cancelExecution`, `ExecutionProgressPage.tsx` |
| 4 | Docs + regression | `ADR-009-execution-cancel.md`, full test suite |

**Required signatures:**

```python
# execution_cancel_store.py
def register_cancel(execution_id: int) -> None: ...
def request_cancel(execution_id: int) -> bool: ...
def is_cancel_requested(execution_id: int) -> bool: ...
def clear_cancel(execution_id: int) -> bool: ...

# three_tier_execution_service.py
async def execute_step(
    self, step, execution_id=None, step_index=None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]: ...

# execution_service.py — _execute_step gains same cancel_check param
```

---

## Backend Cancel API & Store (0.30)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| B1 | Cancel endpoint exists | `DELETE /api/v1/executions/{id}/cancel` returns 204 | 0.06 |
| B2 | Auth + ownership | Wrong user → 403; missing execution → 404 | 0.04 |
| B3 | Pending cancel | `status=pending` → DB `cancelled`, `queue.remove_from_queue()`, never runs | 0.06 |
| B4 | Running cancel request | `status=running` → `register_cancel` + `request_cancel`; 204 immediately; DB stays `running` until worker finalizes | 0.05 |
| B5 | `execution_cancel_store.py` | Thread-safe register/request/is_cancel/clear mirroring `workflow_store.py` | 0.05 |
| B6 | Idempotent cancel | Double cancel or cancel on terminal state → 204, no error | 0.04 |

---

## Cooperative Execution Hooks (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| E1 | Step loop poll | `ExecutionService.execute_test()` checks `is_cancel_requested(execution.id)` before each step (incl. loop blocks) | 0.06 |
| E2 | Finalize cancelled | `crud.cancel_execution()` sets `status=cancelled`, `completed_at`, partial step counts; **not** `failed` | 0.06 |
| E3 | 3-tier cancel_check | `ThreeTierExecutionService.execute_step(..., cancel_check=)` polls before Tier 1, before fallback, between Tier 2→3 in option_c | 0.05 |
| E4 | Cleanup on cancel | `finally` runs `cleanup()` — browser/Stagehand closed; `clear_cancel(execution_id)` in worker | 0.04 |
| E5 | Queue pre-start guard | `queue_manager._check_and_start_next` skips execution when DB `status=cancelled` | 0.04 |

---

## Frontend Stop UX (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| F1 | StopExecutionButton component | Exists at `frontend/src/components/execution/StopExecutionButton.tsx` | 0.05 |
| F2 | Parity with StopAgentButton | Red styling, terminal disable, `data-testid="stop-execution-button"`, "Stopping execution…" via `stop-execution-confirmation` | 0.06 |
| F3 | ExecutionProgressPage wired | Stop visible when `pending`/`running`; hidden when terminal; placed in header before Debug Step | 0.06 |
| F4 | No optimistic cancel | `isStopping` local state only; `execution.status` updated via 2s poll, not set to `cancelled` in handler | 0.04 |
| F5 | executionService.cancelExecution | `DELETE /executions/{id}/cancel` via service layer | 0.04 |

---

## Tests & Documentation (0.10)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | Backend unit tests | `backend/tests/unit/test_execution_cancel_store.py` + `test_execution_cancel.py` pass | 0.04 |
| T2 | Frontend component test | `frontend/src/components/execution/__tests__/StopExecutionButton.test.tsx` passes | 0.03 |
| T3 | ADR or ADR addendum | `documentation/ADR-009-execution-cancel.md` or ADR-002 addendum section | 0.03 |

---

## Non-Regression (0.10)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| R1 | Normal execution complete | Run saved test → completes with pass/fail unchanged | 0.04 |
| R2 | Delete execution distinct | `DELETE /executions/{id}` still deletes record; cancel route is `/{id}/cancel` | 0.03 |
| R3 | Build clean | `npm run build` in frontend succeeds; backend tests pass | 0.03 |

---

## Scoring

```
score = Σ (criterion_weight × pass?1:0)
```

| Band | Score | Meaning |
|------|-------|---------|
| Pass | ≥ 0.85 | Ready to merge |
| Revise | 0.70 – 0.84 | Fix failing criteria |
| Fail | < 0.70 or any automatic fail | Reject |

---

## Evaluator Test Script (Playwright / manual)

1. Log in; open a saved test with ≥ 5 steps; click **Run**.
2. Land on `/executions/{id}` — confirm **Stop Execution** button visible (red outline).
3. While status is **pending** or **running**, click Stop.
4. Confirm inline **"Stopping execution…"** appears (`data-testid="stop-execution-confirmation"`).
5. Wait (up to 120s for cooperative tier completion) until status badge shows **Cancelled**.
6. Confirm Stop button hidden/disabled; partial completed steps still listed.
7. Navigate to Execution History — cancelled run appears with `cancelled` status filter.
8. Start another run; let it complete normally — pass/fail flow unchanged.
9. `DELETE /executions/{id}/cancel` on completed run → 204 (idempotent).
10. `DELETE /executions/{id}` on cancelled run → record deleted (distinct from cancel).
11. Run backend unit tests: `pytest backend/tests/unit/test_execution_cancel*.py`.

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| POST-only cancel with no DELETE route | Fail B1 |
| Stop button on SavedTestsPage only, not progress page | Fail F3 |
| Optimistic UI sets `execution.status = 'cancelled'` before poll confirms | Fail F4 |
| Cancel sets status `failed` or calls `fail_execution()` | Fail E2 |
| Uses `DELETE /executions/{id}` for cancel (breaks delete) | Automatic fail |
| No cleanup — orphaned Playwright after cancel | Fail E4 |
| Force-kill thread / `Task.cancel()` without cooperative poll | Deduct E1/E3 |
| Missing auth on cancel endpoint | Fail B2 |
| `request_cancel` without ensuring key exists for running execution | Deduct B4 |
