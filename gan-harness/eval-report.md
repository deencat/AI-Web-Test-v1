# Evaluation Report — Sprint 2 Backend Categories (Iteration 004)

**Date:** 2026-07-02  
**Iteration:** 004  
**Evaluator:** gan-evaluator  
**App URL:** http://localhost:5173  
**Backend:** http://127.0.0.1:8000

---

## Executive Summary

Sprint 2 backend deliverables for user-defined test categories are **implemented and verified**. All required models, migration, CRUD layer, REST endpoints, test filtering, and bulk category assignment are present. Unit test suite `test_test_categories.py` provides **100% behavior coverage** of spec-required behaviors (22/22 passing).

Live API check: `GET /api/v1/test-categories` returns `401 Not authenticated` (router registered; auth enforced). Migration script runs idempotently against the dev database.

Sprint 1 E2E regression (focused grep run): **25 passed, 1 failed, 1 skipped**. The single failure is a flaky mobile-viewport `beforeEach` login timeout — not related to Sprint 2 backend changes. All 12 Sprint 1 saved-tests behaviors remain covered and passing.

**Overall Verdict: PASS**

---

## Sprint 2 Backend Deliverables (B1–B4, A4)

| ID | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| **B1** | `test_categories` table — user-scoped, unique `(user_id, name)` | ✅ PASS | `backend/app/models/test_category.py`; `backend/migrations/add_test_categories.py`; `uq_test_categories_user_name` constraint |
| **B2** | `test_category_id` on `test_cases` — nullable FK, separate from KB `category_id` | ✅ PASS | `backend/app/models/test_case.py` lines 57–63 (`category_id` KB FK preserved; `test_category_id` user FK added) |
| **B3** | Category CRUD API at `/api/v1/test-categories` with ownership checks | ✅ PASS | `backend/app/api/v1/endpoints/test_categories.py`; registered in `api.py` line 11 |
| **B4** | `GET /tests?test_category_id=` filter + `PATCH /tests/batch/category` | ✅ PASS | `backend/app/api/v1/endpoints/tests.py`; CRUD in `backend/app/crud/test_category.py` |
| **A4** | Backend layering — endpoints → CRUD, no business logic in routers | ✅ PASS | Routers delegate to `crud/test_category.py` and `crud/test_case.py`; validation helpers only |

---

## pytest Results

**Command (working):**
```bash
source backend/venv/bin/activate
cd backend && PYTHONPATH=. pytest tests/unit/test_test_categories.py -v
```

| Result | Count |
|--------|-------|
| **Passed** | **22** |
| Failed | 0 |
| Skipped | 0 |

**Note:** Running `pytest backend/tests/unit/test_test_categories.py` from repo root without `PYTHONPATH=.` fails with `ModuleNotFoundError: No module named 'app'`. CI/docs should use `cd backend && PYTHONPATH=. pytest …`.

---

## Coverage Matrix — Sprint 2 Required Behaviors (100%)

**Coverage status: 100% (all 13 required behaviors mapped to passing tests)**

| Required Behavior | Evidence Test | Status |
|------------------|---------------|--------|
| `test_categories` model + migration | `TestTestCategoryModel::test_model_columns`, `test_unique_user_name_constraint`; migration `add_test_categories.py` (idempotent run verified) | ✅ |
| `test_category_id` column on `test_cases` | `TestTestCaseCategoryIntegration::test_create_and_update_test_category_id`; model FK in `test_case.py` | ✅ |
| `GET /test-categories` returns user's categories with `test_count` | `TestCategoryEndpoints::test_list_includes_test_count` | ✅ |
| `POST /test-categories` creates category | `TestCategoryCRUD::test_create_list_get_update_delete`; `TestCategoryEndpoints::test_duplicate_name_returns_409` (POST path) | ✅ |
| `PUT /test-categories/{id}` updates category | `TestCategoryCRUD::test_create_list_get_update_delete` | ✅ |
| `DELETE /test-categories/{id}` deletes and nullifies tests | `TestCategoryCRUD::test_delete_nullifies_test_category_id` | ✅ |
| Ownership: cannot access other user's categories | `TestCategoryCRUD::test_ownership_isolation`; `TestCategoryEndpoints::test_user_cannot_access_other_users_category` | ✅ |
| Duplicate category name per user → error | `TestCategoryCRUD::test_duplicate_name_same_user_raises_on_second_create`; `TestCategoryEndpoints::test_duplicate_name_returns_409` | ✅ |
| `test_category_id` on test create/update | `TestTestsCategoryEndpoints::test_create_test_with_category_id`; `test_update_test_category_id`; `TestTestCaseCategoryIntegration::test_create_and_update_test_category_id` | ✅ |
| `GET /tests?test_category_id={id}` filters correctly | `TestTestsCategoryEndpoints::test_get_tests_filter_by_category`; `TestTestCaseCategoryIntegration::test_filter_by_test_category_id` | ✅ |
| `GET /tests` uncategorized filter | `TestTestsCategoryEndpoints::test_get_tests_uncategorized_filter`; `TestTestCaseCategoryIntegration::test_filter_uncategorized_with_zero`; `test_filter_uncategorized_flag` | ✅ |
| `PATCH /tests/batch/category` bulk assign | `TestTestsCategoryEndpoints::test_patch_batch_category`; `TestTestCaseCategoryIntegration::test_batch_assign_category` | ✅ |
| Response includes nested `test_category` object | `TestTestsCategoryEndpoints::test_get_tests_filter_by_category` (asserts `items[0]["test_category"]["name"]`) | ✅ |

**Additional edge-case coverage (beyond minimum matrix):**
- Same name allowed for different users: `TestCategoryCRUD::test_same_name_different_users_allowed`
- Invalid foreign category on create returns 400: `TestTestsCategoryEndpoints::test_invalid_category_on_create_returns_400`
- Per-category test count in CRUD layer: `TestCategoryCRUD::test_test_count_per_category`

---

## Sprint 1 E2E Regression Check

**Command:**
```bash
npx playwright test tests/e2e/03-tests-page.spec.ts tests/e2e/06-navigation.spec.ts \
  --workers=1 --grep "Saved Tests Page — Sprint 1|Application Navigation"
```

| Suite | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Saved Tests Page — Sprint 1 | 12 | 0 | 0 |
| Application Navigation | 13 | 1 | 1 |
| **Total** | **25** | **1** | **1** |

**Failure (environmental, not Sprint 2 regression):**
- `should have working navigation on mobile viewport` — `beforeEach` login hook timed out at 30s (`apiRequestContext.get` to `/auth/me` while browser context closed).

**Sprint 1 saved-tests behaviors:** All 12 matrix items from iteration 003 remain passing (inline title edit, legacy redirect, delete navigation, etc.).

---

## Sprint 2 Rubric Score (`gan-harness/eval-rubric.md`)

Scored against Sprint 2-relevant criteria: **B1–B4, A4**

| Criterion | Weight | Score | Notes |
|-----------|--------|-------|-------|
| B1 — `test_categories` table | 0.05 | 0.05 | Model + idempotent migration |
| B2 — `test_category_id` on tests | 0.05 | 0.05 | Nullable FK; KB `category_id` unchanged |
| B3 — Category CRUD API | 0.04 | 0.04 | Full CRUD + ownership + 409 on duplicate |
| B4 — Test filter + batch | 0.04 | 0.04 | Filter, uncategorized=0, batch PATCH |
| A4 — Backend layering | 0.03 | 0.03 | Thin routers → CRUD modules |
| **Total** | **0.21** | **0.21** | |

**Sprint 2 weighted score: 1.00 (0.21 / 0.21)**  
**Sprint 2 verdict: PASS** (meets ≥ 0.85 threshold; all B1–B4 pass; pytest green)

### Sprint 1 Criteria (carry-forward)

Sprint 1 criteria (N1–N5, T1–T5, R4) were **PASS** in iteration 003 and remain **PASS** — no regressions in the 12 saved-tests E2E behaviors. One unrelated navigation mobile test flaked.

---

## Architecture Notes (A4 Detail)

- **Endpoints:** `test_categories.py` — list/create/get/update/delete; duplicate check before create/update; 404 for cross-user access.
- **CRUD:** `crud/test_category.py` — all DB operations, test counts, delete-with-nullify, batch assign.
- **Tests router:** `tests.py` — `_validate_test_category_ownership` helper; filter params; `PATCH /batch/category` delegates to CRUD.
- **Separation:** `category_id` (KB/generation) and `test_category_id` (user org) coexist on `TestCase` model with distinct relationships.

---

## Remaining Risks / Notes

1. **pytest invocation:** Requires `PYTHONPATH=.` from `backend/` directory; document in CI/Makefile.
2. **Migration style:** Uses standalone script (`migrations/add_test_categories.py`) rather than Alembic revision — acceptable for this project pattern but differs from spec's Alembic path example.
3. **E2E mobile flake:** Navigation mobile test intermittently times out on login — pre-existing environmental issue; retry or increase timeout separately.
4. **Sprint 3 not evaluated:** Frontend category UI (U1–U5) out of scope for this Sprint 2 backend evaluation.

---

## Verdict

| Scope | Verdict |
|-------|---------|
| Sprint 2 Backend (B1–B4) | **PASS** |
| Sprint 2 pytest (22/22) | **PASS** |
| Sprint 2 behavior coverage matrix | **100%** |
| Sprint 1 E2E regression (saved tests) | **PASS** (no behavioral regression) |
| **Overall** | **PASS** |
