# Evaluation Rubric: Test Readiness Status

**Feature:** Saved Tests readiness tags (Ready to Test / Draft / Blocked) + filter  
**Spec:** `gan-harness/spec.md` — Feature 4  
**Weight total:** 1.0  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Reuses `TestCase.status` (execution lifecycle) for these labels; multi-tag/contradictory model; no Saved Tests filter; `readiness_status` omitted from sanitizer/list/GET; gates Run behind ready-only; shipping a new page/redesign instead of extending Saved Tests

---

## Implementation Checklist (Generator)

Sprint order — **do not skip**:

| Sprint | Deliverables | Key paths |
|--------|--------------|-----------|
| 1 | Enum + migration + schemas + sanitizer + CRUD/list filter | `models/test_case.py`, migrations, `schemas/test_case.py`, `crud/test_case.py`, `api/v1/endpoints/tests.py` |
| 2 | Saved Tests row select + filter + edit drawer | `SavedTestsPage.tsx`, `types/api.ts`, `testsService` (payload only) |
| 3 | Clone copy + bulk assign (Should-Have) + non-regression | `clone_test_case`, SavedTests bulk toolbar |
| 4 | ADR-010 + tests green | `documentation/ADR-010-*.md`, unit/component tests |

**Required model shape:**

```python
class ReadinessStatus(str, enum.Enum):
    DRAFT = "draft"
    READY_TO_TEST = "ready_to_test"
    BLOCKED = "blocked"

# TestCase.readiness_status — NOT NULL, default DRAFT, indexed
```

**Do not** map Ready/Draft/Blocked onto existing `TestStatus` (`pending` / `passed` / …).

---

## Data Model & API (0.35)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| A1 | Distinct column | `test_cases.readiness_status` exists; `TestCase.status` semantics unchanged | 0.08 |
| A2 | Enum values | Only `draft`, `ready_to_test`, `blocked`; invalid → 422 | 0.06 |
| A3 | Default + backfill | Create and migrated rows default/backfill to `draft` | 0.05 |
| A4 | Sanitizer | `sanitize_test_case_for_response` always includes `readiness_status` | 0.06 |
| A5 | Update round-trip | PUT then GET returns same readiness value | 0.05 |
| A6 | List filter param | `GET /tests?readiness_status=blocked` returns only matching (or documented client-only with CRUD support planned — prefer server filter in Sprint 1–2) | 0.05 |

---

## Saved Tests UX (0.35)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| U1 | Row assign | Inline select on each row; `data-testid="row-readiness-select-{id}"`; persists after reload | 0.08 |
| U2 | Filter control | Status/Readiness filter in existing filter bar; `data-testid="saved-tests-readiness-filter"` | 0.07 |
| U3 | Filter logic | AND with search/type/priority/schedule/category | 0.06 |
| U4 | Edit drawer | Readiness editable and saved with other fields | 0.06 |
| U5 | Empty filter | Clear empty-state when no tests match readiness filter | 0.04 |
| U6 | Labels | UI shows Ready to Test / Draft / Blocked (not raw snake_case only) | 0.04 |

---

## Craft & Non-Regression (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| C1 | Design fit | Matches existing badge/select patterns; no marketing hero, no purple gradient redesign | 0.04 |
| C2 | Failed inline save | Error surfaced; prior readiness restored | 0.03 |
| C3 | Clone | Clone copies source `readiness_status`; response includes field | 0.04 |
| C4 | No Run gate | Draft/Blocked tests remain runnable via existing Run | 0.04 |

---

## Tests & Documentation (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | Backend tests | Unit/API coverage for default, update, invalid enum, sanitizer, list filter | 0.06 |
| T2 | Frontend tests | Filter and/or row-assign coverage on SavedTestsPage | 0.05 |
| T3 | ADR | `documentation/ADR-010-*.md` (or equivalent) distinguishes readiness vs execution `status` | 0.04 |

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

1. Log in → open **Saved Tests** (`/tests/saved`).
2. Confirm each row shows a readiness control; default **Draft** for legacy tests.
3. Set one test to **Ready to Test** via row select → hard reload → still Ready to Test.
4. Set another to **Blocked**.
5. Set readiness filter to **Blocked** → only blocked row(s); other filters still apply when combined.
6. Set filter to **All** → full list returns.
7. Open Edit drawer → change readiness → Save → list reflects change.
8. Clone a **Blocked** test → clone is Blocked (and titled with Copy suffix).
9. Click **Run** on a **Draft** test → execution still starts (no gate).
10. Network: GET/PUT JSON includes `"readiness_status": "..."`; existing `"status"` remains execution enum values.
11. Backend: `pytest` readiness-related unit tests; frontend Saved Tests tests pass.

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Stores Ready/Draft/Blocked in `TestCase.status` | Automatic fail |
| Uses `tags[]` multi-select for exclusive readiness | Automatic fail |
| Omits field from sanitizer (CRM-toggle bug class) | Fail A4 |
| Filter only in drawer, not list filter bar | Fail U2 |
| New page instead of extending Saved Tests | Automatic fail |
| Blocks Run when not `ready_to_test` | Fail C4 / automatic fail |
| Purple gradient / marketing landing for this feature | Fail C1 |
