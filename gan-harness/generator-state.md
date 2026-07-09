# Generator State — Iteration Clone Test Case

## What Was Built
- `TestCaseCloneRequest` schema with optional `new_title`
- `clone_test_case()`, `title_exists_for_user()`, `_generate_clone_title()` in CRUD
- `POST /api/v1/tests/{test_case_id}/clone` endpoint (201, 403, 404, 409)
- `testsService.cloneTest()` with mock mode support
- Clone button on SavedTestsPage list row (between Edit and Run) and edit drawer footer
- Loading state via `cloningTestId` with Copy/Loader2 icons
- Post-clone navigation to `?edit={newId}`
- Backend unit tests (`test_test_case_clone.py`) and frontend component tests

## What Changed This Iteration
- Implemented Feature 2: Clone Test Case per gan-harness/spec.md § Feature 2
- Mirrored test template clone pattern for API shape and ownership rules
- Deep copy of steps, tags, test_data, test_metadata JSON fields

## Known Issues
- Version snapshot on clone not wired (optional Should-Have deferred)
- `sanitize_test_case_for_response` does not include `requires_runtime_credentials` in dict (pre-existing)

## Dev Server
- URL: http://localhost:5173 (frontend) / http://localhost:8000 (backend)
- Status: not started in this iteration
- Command: `docker compose up` or separate frontend/backend dev servers
