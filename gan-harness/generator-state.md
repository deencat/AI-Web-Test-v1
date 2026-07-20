# Generator State — Iteration Feature 4 Readiness Status

## What Was Built
- Backend `ReadinessStatus` enum (`draft` | `ready_to_test` | `blocked`) + `TestCase.readiness_status` column (NOT NULL, default `draft`, indexed)
- Migration `backend/migrations/add_readiness_status.py` (backfill via DEFAULT `'draft'`)
- Schemas Create/Update/Response include `readiness_status`; invalid enum → 422
- `sanitize_test_case_for_response` always includes coerced `readiness_status`
- CRUD list filter `readiness_status`; clone copies readiness; execution `status` unchanged
- `PATCH /tests/batch/readiness` + frontend bulk Set Readiness control
- Saved Tests: Readiness filter, row inline select, edit drawer select, badge colors (gray / emerald / amber)

## What Changed This Iteration
- Added: Feature 4 Test Readiness Status end-to-end (API + Saved Tests UX)
- Added: ADR-010 distinguishing readiness vs execution `TestStatus`
- Added: backend `tests/unit/test_readiness_status.py`; frontend readiness cases in `SavedTestsPage.test.tsx`
- Updated: `docs/CODEMAPS/database.md` for readiness column

## Known Issues
- **Fixed during eval (2026-07-20):** `SQLEnum(ReadinessStatus)` needed `values_callable` for VARCHAR migration values (`draft` not `DRAFT`) — live list API was 500 before fix
- URL query sync for readiness filter (Should-Have) not implemented
- Filter counts per readiness (Should-Have) not implemented
- TestDetailPage readiness display (Should-Have) not implemented
- No Playwright E2E in this iteration — evaluator can use rubric manual script
- Dev servers not started here; Evaluator should start them

## Dev Server
- Frontend URL: http://localhost:5173
- Backend URL: http://127.0.0.1:8000
- Status: not started in this iteration
- Commands:
  - Backend: `cd backend && .\venv\Scripts\activate; python start_server.py` (auto-runs migrations including `add_readiness_status`)
  - Frontend: `cd frontend && npm run dev`
- Verify: open `/tests/saved` → change row readiness → reload → filter by Readiness
- Backend tests: `cd backend && .\venv\Scripts\activate; python -m pytest tests/unit/test_readiness_status.py -q`
- Frontend tests: `cd frontend && npm run test -- --run src/pages/__tests__/SavedTestsPage.test.tsx`
