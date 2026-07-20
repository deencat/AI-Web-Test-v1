# Architecture Decision Record — Test Readiness Status vs Execution Status

**Document ID:** ADR-010  
**Component:** Saved Tests Library — Workflow Readiness Tags  
**Status:** Accepted  
**Date:** July 20, 2026  
**Author:** GAN Generator  
**Related:** ADR-008 (categories), `gan-harness/spec.md` Feature 4

---

## Context

Saved Tests need a lightweight workflow signal: which cases are still being authored (**Draft**), approved to run (**Ready to Test**), or stuck on external deps (**Blocked**).

`TestCase.status` already stores **execution lifecycle** values (`pending`, `in_progress`, `passed`, `failed`, `skipped`). Reusing that column for Ready/Draft/Blocked would break list stats, clone reset behavior (`status=pending`), and execution semantics.

---

## Decision

1. Add a separate column `test_cases.readiness_status` with enum values:
   - `draft` (default)
   - `ready_to_test`
   - `blocked`
2. Keep `TestCase.status` / `TestStatus` exclusively for execution results.
3. Expose readiness on existing GET/PUT/list/clone APIs; filter via `GET /tests?readiness_status=`.
4. UI label on Saved Tests: **Readiness** (not “Status”) to avoid confusion with execution status.
5. Do **not** gate Run behind `ready_to_test` in v1.

---

## Consequences

| Positive | Trade-off |
|----------|-----------|
| Clear separation of authoring vs run outcomes | Two status-like fields on the same entity |
| Filter/badge UX mirrors category pattern | Clients must not map readiness onto `status` |
| Clone copies readiness; execution status still resets to `pending` | Documented intentionally |

---

## Related Files

- `backend/app/models/test_case.py` — `ReadinessStatus`
- `backend/migrations/add_readiness_status.py`
- `backend/app/schemas/test_case.py`, `crud/test_case.py`, `api/v1/endpoints/tests.py`
- `frontend/src/pages/SavedTestsPage.tsx`
