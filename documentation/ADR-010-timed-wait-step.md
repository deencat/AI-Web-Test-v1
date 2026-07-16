# ADR-010: Timed Wait Step (Cancel-Aware Short-Circuit)

**Document ID:** ADR-010  
**Component:** Test Execution / Step Editor  
**Status:** Accepted  
**Date:** July 16, 2026  
**Related:** ADR-002 (execution engine / readiness), ADR-009 (cooperative cancel)  
**Related Files:**
- `backend/app/services/timed_wait.py`
- `backend/app/services/execution_service.py` (`_execute_step` short-circuit)
- `backend/app/services/tier1_playwright.py` (`_execute_wait`)
- `backend/app/services/tier2_hybrid.py` (wait backstop)
- `frontend/src/components/AddWaitControl.tsx`
- `frontend/src/components/TestStepEditor.tsx`

---

## Context

QA authors need an intentional pause between steps (OTP window, third-party redirect, slow job). Natural-language lines like `Wait 10 seconds` were ignored or mishandled: Tier 2 treated `action == "wait"` as a silent `pass`, and long sleeps blocked ADR-009 Stop.

Automatic readiness waits (spinners, payment settle, post-click network) already live in ADR-002 (`post_click_readiness.py`). Those must stay separate from user-authored timed pauses.

## Decision

**Approach C — ordinal step + ExecutionService short-circuit:**

1. Timed wait is a normal step line in `steps[]` (canonical insert: `wait: 10s`). Not `loop_blocks` / not `wait_blocks`.
2. `parse_timed_wait_ms` accepts NL (`Wait 10 seconds`), canonical (`wait: 10s`), and structured (`action=wait` + `timeout_ms` / `timeout`). Cap **120_000 ms**.
3. `Wait for …` / `Wait until …` are **not** timed sleeps (condition / verify paths).
4. In `_execute_step`, after test-data substitution and **before** `ThreeTierExecutionService.execute_step`, detect timed wait → `sleep_cancel_aware` (≈250 ms chunks, poll `cancel_check`) → return success with `tier_used: "timed_wait"`.
5. Cancel mid-wait returns `cancelled` and finalizes as `cancelled` (ADR-009), never `failed`.
6. Tier 1/2 remain backstops (correct duration parsing; Tier 2 never silent-pass). Timed waits must not call Stagehand `act()` or force Stagehand init.

## Timed vs readiness vs condition

| Kind | Example | Owner |
|------|---------|--------|
| Timed wait (this ADR) | `wait: 10s`, `Wait 10 seconds` | User step; ExecutionService short-circuit |
| ADR-002 readiness | Spinner clear, payment iframe settle | `post_click_readiness.py` / tier internals |
| Condition wait | `Wait for the success message` | Verify / selector wait paths — not fixed sleep |

## Consequences

- Pure wait steps skip Tier 1–3 (no LLM / Stagehand cost).
- Stop Execution works within ~one chunk (~250–500 ms) during a wait.
- UI **[+ Add Wait]** inserts a step line only; loop-block editor unchanged.
