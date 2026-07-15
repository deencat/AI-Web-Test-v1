# Generator State — Iteration CRM Login Toggle Persist

## What Was Built
- Added `requires_runtime_credentials` to `sanitize_test_case_for_response` so GET/PUT/list/clone responses no longer default the flag to `false`
- Unit/API tests for sanitizer true/false, PUT→GET round-trip, list inclusion, clone honesty, and no credential columns/fields
- SavedTestsPage post-save `setTests` map now includes `requires_runtime_credentials` (Should-Have)

## What Changed This Iteration
- Fixed: API sanitizer omitted `requires_runtime_credentials` (root cause of toggle resetting after reload)
- Fixed: SavedTests local list lag after edit save omitted the flag
- Added: `backend/tests/unit/test_requires_runtime_credentials_sanitize.py`
- Credentials remain ephemeral — only the boolean flag is persisted/returned

## Known Issues
- No new Playwright E2E for toggle → save → reload (evaluator can use rubric manual script; T1 unit coverage is present)
- Dev servers not started in this iteration (Evaluator should start them if needed)

## Dev Server
- Frontend URL: http://localhost:5173
- Backend URL: http://127.0.0.1:8000
- Status: not started in this iteration
- Commands:
  - Backend: `cd backend && .\venv\Scripts\activate; python start_server.py`
  - Frontend: `cd frontend && npm run dev`
- Verify flag: `GET http://127.0.0.1:8000/api/v1/tests/{id}` after PUT with `"requires_runtime_credentials": true` must return `true`
- Backend tests: `cd backend && .\venv\Scripts\activate; python -m pytest tests/unit/ -q -k "requires_runtime or crm_ephemeral"`
