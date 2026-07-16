# Generator State — Iteration Timed Wait (Feature 4)

## What Was Built
- **Sprint 8:** `timed_wait.py` parser + cancel-aware chunked sleep; `ExecutionService._execute_step` short-circuit before three-tier; Tier 1 `_execute_wait` duration fields; Tier 2 wait no-op replaced with real sleep / fail-closed; unit tests
- **Sprint 9:** `AddWaitControl` + **[+ Add Wait]** on `TestStepEditor` (also SavedTests / TestDetail via same editor) inserting `wait: Ns`; Vitest coverage; `data-testid="add-wait-button"`
- **Sprint 10:** `documentation/ADR-010-timed-wait-step.md`; `docs/CODEMAPS/execution-engine.md` short-circuit note

## What Changed This Iteration
- Verified Sprints 8–10 end-to-end against spec/rubric
- Aligned UI testid to rubric example: `add-wait-button` (was `add-wait-step-button`)
- Confirmed cancel mid-wait → `cancelled: True` → `_finalize_cancel()` → `ExecutionCancelledError` (status `cancelled`, not `failed`)

## Files Touched
| Path | Role |
|------|------|
| `backend/app/services/timed_wait.py` | Parse + `sleep_cancel_aware` (250ms chunks, 120s cap) |
| `backend/app/services/execution_service.py` | Short-circuit before `three_tier_service.execute_step` |
| `backend/app/services/tier1_playwright.py` | `_execute_wait` reads timeout_ms/timeout/parsed duration |
| `backend/app/services/tier2_hybrid.py` | Wait sleeps or fails closed (no silent `pass`) |
| `backend/tests/unit/test_timed_wait.py` | 22 unit tests |
| `frontend/src/components/AddWaitControl.tsx` | Duration picker → `wait: Ns` |
| `frontend/src/components/TestStepEditor.tsx` | Wire **[+ Add Wait]** |
| `frontend/src/components/__tests__/AddWaitControl.test.tsx` | 5 Vitest cases |
| `documentation/ADR-010-timed-wait-step.md` | Timed wait vs readiness |
| `docs/CODEMAPS/execution-engine.md` | Short-circuit in dispatch diagram |

## Known Issues
- Unrelated failure: `test_orchestration_stage_progress.py::test_run_workflow_can_cancel_during_observation_stage_work` (agent workflow cancel — not Feature 4)
- Backend must be **restarted** after code change so live runs pick up short-circuit

## How to Verify
```bash
cd backend && .\venv\Scripts\activate
python -m pytest tests/unit/test_timed_wait.py -q
# expect: 22 passed

python -m pytest tests/unit/ -q -k "timed_wait or cancel"
# expect: timed_wait + execution_cancel green; 1 unrelated orchestration fail OK

cd frontend && npm run test -- --run src/components/__tests__/AddWaitControl.test.tsx
# expect: 5 passed
```
Manual: open Saved Test → **[+ Add Wait]** → 5s → steps contain `wait: 5s` → Run → pause ≈5s; Stop mid-wait → `cancelled`.

## Dev Server
- Frontend URL: http://localhost:5173
- Backend URL: http://127.0.0.1:8000
- Status: restart backend (`python start_server.py`) so timed-wait short-circuit is loaded
- Commands:
  - Backend: `cd backend && .\venv\Scripts\activate; python start_server.py`
  - Frontend: `cd frontend && npm run dev`

## Rubric Auto-Fail Checklist
- [x] Not Stagehand-only wait
- [x] Not loop_blocks / wait_blocks
- [x] Chunked cancel-aware sleep (not unbroken asyncio.sleep)
- [x] `Wait for …` is not timed
- [x] Tier 2 wait no longer silent `pass`
- [x] Not readiness/`post_click_readiness` as primary path
