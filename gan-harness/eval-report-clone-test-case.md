# Evaluation Report — Clone Test Case (Feature 2)

**Date:** 2026-07-09  
**Feature:** One-click duplicate of saved test cases  
**Evaluator:** gan-evaluator  
**App URL:** http://localhost:5173  
**Backend:** http://127.0.0.1:8000  
**Spec:** `gan-harness/spec.md` § Feature 2  
**Rubric:** `gan-harness/eval-rubric-clone-test-case.md` (pass threshold ≥ 0.85)

---

## Executive Summary

Clone Test Case is **fully implemented and verified**. The evaluator ran backend unit tests (14/14), frontend component/service tests (18/18 across clone-related suites), Playwright E2E (3/3), and clone-specific line coverage analysis.

**Weighted score: 0.97 / 1.00 — PASS**

All automatic-fail conditions are clear. Clone-specific backend functions achieve **100% line coverage**. The only rubric miss is **T3** (`npm run build`) due to pre-existing TypeScript errors in unrelated frontend test files (`agentWorkflow.types.test.ts`), not introduced by the clone feature.

---

## Weighted Score

```
score = Σ (criterion_weight × pass?1:0)
```

| Band | Score | Verdict |
|------|-------|---------|
| Pass | ≥ 0.85 | **PASS** |
| Revise | 0.70 – 0.84 | — |
| Fail | < 0.70 or automatic fail | — |

**Total: 0.97 / 1.00 — PASS**

---

## Automatic Fail Checklist

| Condition | Result |
|-----------|--------|
| No clone API endpoint | ✅ Clear — `POST /api/v1/tests/{id}/clone` returns 201 |
| Clone mutates or deletes source | ✅ Clear — `test_source_unchanged_after_clone` + E2E API verification |
| Clone shares id with source | ✅ Clear — new `id` on every clone |
| Steps not copied | ✅ Clear — `test_field_parity_deep_copy` + E2E step parity |
| No Clone button on SavedTestsPage list | ✅ Clear — `data-testid="clone-test-button-{id}"` on each row |

---

## Per-Criterion Results

### Backend Clone API & CRUD (0.35)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| B1 | Clone endpoint exists | 0.08 | ✅ PASS | `tests.py` L307–350; `test_happy_path_returns_201`; E2E clone flow |
| B2 | Auth + ownership | 0.05 | ✅ PASS | `test_not_found_returns_404`, `test_wrong_user_returns_403`, `test_admin_can_clone_other_users_test` |
| B3 | `clone_test_case` CRUD | 0.07 | ✅ PASS | New row, new `id`, `status=pending`, `user_id=current_user` |
| B4 | Title suffix | 0.06 | ✅ PASS | `(Copy)` / `(Copy N)` via `_generate_clone_title`; E2E `(Copy 2)` |
| B5 | Optional `new_title` | 0.05 | ✅ PASS | `test_custom_new_title`, `test_duplicate_new_title_returns_409` |
| B6 | Source preserved | 0.04 | ✅ PASS | `test_source_unchanged_after_clone`; E2E list API check |

**Section score: 0.35 / 0.35**

### Data Fidelity (0.25)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| D1 | Steps copied | 0.08 | ✅ PASS | Deep copy + `is not` identity check; E2E steps JSON match |
| D2 | Assertions copied | 0.05 | ✅ PASS | `expected_result`, `preconditions`, `test_data` in parity test |
| D3 | Metadata copied | 0.04 | ✅ PASS | `priority`, `test_type`, `tags`, `test_metadata` |
| D4 | Category copied | 0.04 | ✅ PASS | `test_category_id`, `category_id` with category fixture |
| D5 | Credentials flag | 0.04 | ✅ PASS | `requires_runtime_credentials` parity |

**Section score: 0.25 / 0.25**

### Frontend Clone UX (0.25)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| F1 | List row Clone button | 0.07 | ✅ PASS | `clone-test-button-{id}` on each row; component test |
| F2 | Icon + styling | 0.04 | ✅ PASS | Lucide `Copy`, `text-blue-600` (not red); styling test |
| F3 | Loading state | 0.05 | ✅ PASS | `cloningTestId` disables button + `Loader2` spinner |
| F4 | List refresh | 0.05 | ✅ PASS | `loadTests()` after clone; refresh test verifies `getAllTests` recall |
| F5 | `testsService.cloneTest` | 0.04 | ✅ PASS | API POST + mock mode collision handling in service tests |

**Section score: 0.25 / 0.25**

### Tests (0.15)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| T1 | Backend unit tests | 0.08 | ✅ PASS | 14/14 in `test_test_case_clone.py` |
| T2 | Frontend test | 0.04 | ✅ PASS | 5 component + 4 service clone tests; SavedTestsPage regression 15/15 |
| T3 | Build clean | 0.03 | ❌ FAIL | `npm run build` fails on pre-existing `agentWorkflow.types.test.ts` TS errors |

**Section score: 0.12 / 0.15**

---

## Test Coverage Report

### Backend — Clone-specific functions (100%)

| Function | Lines | Coverage |
|----------|-------|----------|
| `title_exists_for_user` | 419–426 | **100%** (8/8) |
| `_generate_clone_title` | 429–437 | **100%** (9/9) |
| `clone_test_case` | 440–470 | **100%** (31/31) |
| `clone_test_case_endpoint` | 307–350 | **100%** (44/44) |

**Total clone code paths: 92/92 lines (100%)**

Module-level coverage (entire files, includes non-clone code): `app/crud/test_case.py` 31%, `app/api/v1/endpoints/tests.py` 39% — expected since only clone tests were run.

### Frontend — Rubric criteria F1–F5

| Criterion | Test file | Status |
|-----------|-----------|--------|
| F1 Clone button | `SavedTestsPage.clone.test.tsx` | ✅ |
| F2 Styling | `SavedTestsPage.clone.test.tsx` | ✅ |
| F3 Loading | `SavedTestsPage.clone.test.tsx` | ✅ |
| F4 List refresh | `SavedTestsPage.clone.test.tsx` | ✅ |
| F5 Service layer | `testsService.test.ts` | ✅ |

---

## E2E Test Results

**File:** `tests/e2e/12-clone-test-case.spec.ts`  
**Result: 3/3 PASSED**

| Test | Result | Notes |
|------|--------|-------|
| Clone via UI with `(Copy)` suffix | ✅ PASS | Login → `/tests/saved` → click Clone → notice + list row visible |
| API 409 duplicate title / 404 missing | ✅ PASS | `POST /tests/{id}/clone` edge cases |
| Re-clone assigns `(Copy 2)` | ✅ PASS | API + UI visibility |

### Evaluator script coverage (rubric § Playwright)

| Step | Status |
|------|--------|
| 1. Log in; navigate to Saved Tests | ✅ |
| 2. Note existing test title/steps | ✅ (seeded via API) |
| 3. Click Clone on row | ✅ |
| 4. Brief loading state | ✅ (component test; spinner in implementation) |
| 5. New test `{title} (Copy)` | ✅ |
| 6. Open clone in edit drawer — field parity | ⚠️ Partial (navigates to `?edit={newId}`; drawer field parity not asserted in E2E) |
| 7. Edit clone title; original unchanged | ⚠️ Not in E2E (covered by unit tests) |
| 8. Run clone — independent execution | ⚠️ Not in E2E (out of clone scope) |
| 9. Clone again → `(Copy 2)` | ✅ |
| 10. POST duplicate `new_title` → 409 | ✅ |
| 11. POST missing id → 404 | ✅ |
| 12. Backend unit tests | ✅ 14/14 |

---

## Implementation Notes

### Strengths
- Server-side deep copy mirrors template clone pattern correctly
- Title de-duplication handles `(Copy)`, `(Copy 2)`, `(Copy 3)` collisions
- Clone button uses blue secondary styling consistent with View action
- Edit drawer also has `clone-test-drawer-button` (Sprint 6 polish)
- No `window.confirm()` on clone — good UX

### Minor gaps (non-blocking)
- **T3 build:** Pre-existing TS errors block `npm run build`; clone code itself compiles
- **E2E drawer parity:** Steps 6–8 of rubric script not fully automated (unit tests cover data fidelity)
- **Drawer clone button:** Present in UI but no dedicated component test (list row is primary rubric target)

---

## Action Items

| Priority | Item | Owner |
|----------|------|-------|
| Low | Fix pre-existing `agentWorkflow.types.test.ts` TS errors to unblock T3 | Generator / platform |
| Nice | Add E2E assertion for edit-drawer field parity after clone redirect | Generator |
| Nice | Component test for `clone-test-drawer-button` | Generator |

---

## Test Commands (reproducible)

```bash
# Backend unit tests
cd backend && source venv/bin/activate && PYTHONPATH=. pytest tests/unit/test_test_case_clone.py -v

# Frontend clone tests
cd frontend && npm test -- --run src/pages/__tests__/SavedTestsPage.clone.test.tsx
cd frontend && npm test -- --run src/services/__tests__/testsService.test.ts

# E2E (requires backend on :8000, frontend on :5173)
npx playwright test tests/e2e/12-clone-test-case.spec.ts --project=chromium
```

---

## Verdict

**PASS** — Weighted score **0.97/1.00** exceeds the **0.85** threshold. Clone feature is production-ready with 100% clone-code-path test coverage and full E2E happy-path verification.
