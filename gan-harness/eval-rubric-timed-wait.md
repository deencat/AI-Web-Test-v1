# Evaluation Rubric: Timed Wait Step

**Feature:** First-class cancel-aware timed wait steps (UI + NL/canonical parse)  
**Spec:** `gan-harness/spec.md` § Feature 4  
**Weight total:** 1.0  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Timed wait via Stagehand `act()` only; wait stored as `loop_blocks` / `wait_blocks`; unbroken sleep with no cancel chunks; every “wait …” phrase sleeps; Tier 2 `action == "wait": pass` remains for timed waits; feature “fixed” only by changing readiness/`post_click_readiness` as the primary path

---

## Implementation Checklist (Generator)

Sprint order — **do not skip**:

| Sprint | Deliverables | Key paths |
|--------|--------------|-----------|
| 8 | Parse + short-circuit + cancel-aware sleep; Tier 1/2 hardening; unit tests | `execution_service.py`, `timed_wait.py` (or helpers), `tier1_playwright.py`, `tier2_hybrid.py`, `tests/unit/test_timed_wait.py` |
| 9 | UI Add Wait inserts canonical step line | `TestStepEditor.tsx`, optional `AddWaitControl.tsx`, SavedTests drawer if needed |
| 10 | Docs / ADR note | ADR-002 addendum or ADR-010; `docs/CODEMAPS/execution-engine.md` |

**Required behaviors:**

```text
# Canonical UI insert
wait: 10s

# NL must also work
Wait 10 seconds
```

```python
# Conceptual — ExecutionService short-circuit BEFORE three_tier_service.execute_step
duration_ms = parse_timed_wait_ms(instruction, step)
if duration_ms is not None:
    await sleep_cancel_aware(min(duration_ms, 120_000), cancel_check)
    return success_result  # no Tier 1/2/3
```

**Do NOT:**
- Add `test_data.wait_blocks` or reuse `LoopBlockEditor` for waits
- Call Stagehand / Tier 3 for timed waits
- Use unbroken `asyncio.sleep(full_duration)` without cancel polls
- Treat `Wait for the success message` as a fixed sleep
- Call tier executors from API endpoints

---

## Backend Short-Circuit & Duration Fidelity (0.35)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| B1 | NL duration honored | Step `Wait 10 seconds` (or equivalent) pauses ≈10s (±1s) before next step | 0.10 |
| B2 | Canonical form honored | Step `wait: 10s` pauses ≈10s | 0.05 |
| B3 | Structured fields | `{action:"wait", timeout_ms:3000}` (or `timeout`) sleeps ≈3s — not only pure-int `value` | 0.05 |
| B4 | Short-circuit location | Timed wait handled in `ExecutionService` (or helper it owns) **before** tier escalation | 0.05 |
| B5 | Cap 120s | Duration >120s clamped or rejected; never runs unbounded | 0.05 |
| B6 | Tier 1 duration fix | `_execute_wait` / backstop reads `timeout_ms`/`timeout` or parses `10s` (not only `int(pure)`) | 0.05 |

---

## Cancel Mid-Wait — ADR-009 (0.20)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| C1 | Chunked sleep | Sleep implemented in chunks (≤500 ms; prefer ~250 ms) with `cancel_check` / `is_cancel_requested` | 0.08 |
| C2 | Stop mid-wait | During a ≥5s wait, Stop → execution `cancelled` within ≤1s of cooperative detect (not after full remaining sleep) | 0.08 |
| C3 | No false failed | Cancel mid-wait finalizes as `cancelled`, not `failed`, per Feature 1 / ADR-009 | 0.04 |

---

## NL Parse Boundaries & Anti-Conflation (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| P1 | Non-timed exclusion | `Wait for the success message` / `Wait until …` does **not** map to fixed-duration sleep | 0.07 |
| P2 | Not readiness rewrite | Primary fix is not “add sleep inside `post_click_readiness`”; readiness module behavior unchanged as the wait product | 0.04 |
| P3 | Wait is a step | Duration lives in `steps[]` ordinal line (or structured step item), not parallel wait metadata | 0.04 |

---

## Tier Safety (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | No Stagehand for timed wait | Timed wait path does not call Tier 3 / `act("wait…")`; does not force Stagehand init | 0.07 |
| T2 | Tier 2 no-op gone | `tier2_hybrid` no longer `pass`-succeeds timed waits without sleeping | 0.05 |
| T3 | Layering preserved | Endpoints do not call tier executors; dispatch remains ExecutionService → ThreeTier for non-wait steps | 0.03 |

---

## UI Add Wait — Step Not Loop Block (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| U1 | Control present | **[+ Add Wait]** (or equivalent) on TestStepEditor and/or SavedTests steps editor; `data-testid` preferred | 0.05 |
| U2 | Inserts canonical line | Confirming 10s inserts `wait: 10s` (or documented equivalent) into steps text/list | 0.05 |
| U3 | Not loop UX | Add Wait does not open `LoopBlockEditor` and does not write `loop_blocks` / `wait_blocks` | 0.03 |
| U4 | Duration clamp in UI | Custom duration limited to ≤120s (error or clamp) | 0.02 |

---

## Tests (cross-cutting — scored inside bands above; CI expectation)

Mandatory unit coverage (fail B/C/P if missing):

| Test theme | Must assert |
|------------|-------------|
| Duration | Sleep ≈ requested for NL + canonical |
| Cancel mid-wait | Abort before full duration |
| Non-timed | `wait for …` → not timed |
| Cap | >120s clamped/rejected |

---

## Non-Regression

| Check | Pass condition |
|-------|----------------|
| Feature 1 Stop Execution | Still works for non-wait steps; also works mid-wait (C2) |
| Feature 2 Clone | Clones wait step lines with other steps |
| Feature 3 CRM toggle | Unchanged |
| ADR-002 readiness | Spinners/payment/post-click waits still run for normal click/nav steps |
| Lazy tiers | Pure wait-only step does not eagerly init Stagehand |

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

**Weight check:** B 0.35 + C 0.20 + P 0.15 + T 0.15 + U 0.15 = **1.00**

---

## Evaluator Test Script (manual / Playwright-assisted)

1. **Backend unit:**  
   `cd backend && .\venv\Scripts\activate && python -m pytest tests/unit/test_timed_wait.py -q`  
   (or `-k timed_wait` if file name differs). All must pass.
2. Log in; open a saved test in **Test Detail** or Saved Tests edit with `TestStepEditor`.
3. Click **[+ Add Wait]** → choose **5 seconds** → confirm.  
   Assert steps contain `wait: 5s` (or equivalent). Assert Network/save body: wait is in `steps`, **not** under `test_data.loop_blocks`.
4. Optionally add a second line manually: `Wait for the success message to appear` (for negative parse check later).
5. **Run** the test. On the wait step, confirm wall-clock pause ≈5s (watch progress timestamps or wall clock).
6. **Cancel mid-wait:** Run again with a **30s** wait; while on the wait step, click **Stop Execution**.  
   Assert status becomes `cancelled` within ~1s (poll), not after ~30s. Partial steps preserved.
7. Confirm wait step result did not require Stagehand (no Tier 3 / no Stagehand init logs solely for that step).
8. Confirm a step `Wait for the success message` (if present) did **not** cause a multi-second fixed sleep from the timed-wait feature (may still do verify/readiness — that is OK).
9. Attempt custom duration **200** in UI → rejected or clamped to 120.
10. Optional: structured/API path — ensure Tier 2 wait path cannot silently `pass` (code review or unit).

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Stagehand `act` implements the wait | Automatic fail (T1) |
| `wait_blocks` or loop-block UX for waits | Automatic fail (U3 / P3) |
| Unbroken `asyncio.sleep(N)` with no cancel poll | Automatic fail (C1/C2) |
| `wait for X` sleeps N seconds | Automatic fail (P1) |
| Tier 2 `pass` still present for timed wait | Automatic fail (T2) |
| “Fix” only by lengthening readiness sleeps | Automatic fail (P2) |
| Calling `Tier1`/`Tier2`/`Tier3` from endpoints | Automatic fail (T3 / hard constraint) |
