# Evaluation Rubric: Clone Test Case

**Feature:** One-click duplicate of saved test cases  
**Spec:** `gan-harness/spec.md` § Feature 2  
**Weight total:** 1.0  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** No clone API endpoint; clone mutates or deletes source; clone shares id with source; steps not copied; no Clone button on SavedTestsPage list

---

## Implementation Checklist (Generator)

Sprint order — **do not skip**:

| Sprint | Deliverables | Key paths |
|--------|--------------|-----------|
| 5 | CRUD + API + list button | `crud/test_case.clone_test_case`, `tests.py` POST `/{id}/clone`, `testsService.cloneTest`, `SavedTestsPage` row action |
| 6 | Drawer + polish | Edit drawer Clone button, optional `?edit={newId}` redirect, component tests |

**Required signatures:**

```python
# schemas/test_case.py
class TestCaseCloneRequest(BaseModel):
    new_title: Optional[str] = Field(None, min_length=1, max_length=255)

# crud/test_case.py
def clone_test_case(db: Session, original: TestCase, *, user_id: int, new_title: str) -> TestCase: ...

# tests.py
@router.post("/{test_case_id}/clone", response_model=TestCaseResponse, status_code=201)
def clone_test_case_endpoint(...): ...
```

```typescript
// testsService.ts
async cloneTest(testId: number, options?: { newTitle?: string }): Promise<Test>
```

---

## Backend Clone API & CRUD (0.35)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| B1 | Clone endpoint exists | `POST /api/v1/tests/{id}/clone` returns 201 with `TestCaseResponse` | 0.08 |
| B2 | Auth + ownership | Wrong user → 403; missing test → 404 | 0.05 |
| B3 | `clone_test_case` CRUD | New row with new `id`, `user_id=current_user`, `status=pending` | 0.07 |
| B4 | Title suffix | Auto `{title} (Copy)` or `(Copy N)` on collision within user | 0.06 |
| B5 | Optional `new_title` | Request body override; duplicate title for user → 409 | 0.05 |
| B6 | Source preserved | Original test unchanged after clone | 0.04 |

---

## Data Fidelity (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| D1 | Steps copied | `steps` JSON array deep-equal to source | 0.08 |
| D2 | Assertions copied | `expected_result`, `preconditions`, `test_data` match | 0.05 |
| D3 | Metadata copied | `priority`, `test_type`, `tags`, `test_metadata` match | 0.04 |
| D4 | Category copied | `test_category_id` and KB `category_id` match | 0.04 |
| D5 | Credentials flag | `requires_runtime_credentials` matches source | 0.04 |

---

## Frontend Clone UX (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| F1 | List row Clone button | Visible on each Saved Tests row; `data-testid="clone-test-button-{id}"` | 0.07 |
| F2 | Icon + styling | Lucide `Copy` icon; blue secondary styling (not green/red) | 0.04 |
| F3 | Loading state | Button disabled/spinner during API call; no double-submit | 0.05 |
| F4 | List refresh | Successful clone refreshes list; new test visible at top | 0.05 |
| F5 | `testsService.cloneTest` | POST via service layer; mock mode supported | 0.04 |

---

## Tests (0.15)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | Backend unit tests | `backend/tests/unit/test_test_case_clone.py` passes | 0.08 |
| T2 | Frontend test | Component test for Clone button behavior passes | 0.04 |
| T3 | Build clean | `npm run build` succeeds; no regressions on SavedTestsPage | 0.03 |

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

1. Log in; navigate to **Saved Tests** (`/tests/saved`).
2. Note an existing test's title, step count, and category badge.
3. Click **Clone** on that row (`data-testid="clone-test-button-{id}"`).
4. Confirm brief loading state on the button.
5. Confirm new test appears with title `{original} (Copy)` (or `(Copy 2)` if re-cloned).
6. Open clone in edit drawer — verify steps, expected result, priority, category match source.
7. Edit clone title only; save — confirm original title unchanged.
8. Run clone — confirm execution starts (independent of original).
9. Clone same test again — confirm `(Copy 2)` title auto-assigned.
10. `POST /api/v1/tests/{id}/clone` with `{ "new_title": "Duplicate Name" }` on existing title → 409.
11. `POST /api/v1/tests/99999/clone` → 404.
12. Run backend tests: `pytest backend/tests/unit/test_test_case_clone.py`.

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Client-side clone via `POST /tests` without dedicated endpoint | Fail B1 |
| Clone overwrites source test | Automatic fail |
| Clone reuses source `id` | Automatic fail |
| `steps` empty when source had steps | Fail D1 |
| Clone copies execution history | Deduct D1 |
| Clone copies schedules | Deduct (out of scope; should not copy) |
| Red destructive styling on Clone button | Deduct F2 |
| `window.confirm()` on every clone | Deduct F3 |
| Missing auth on clone endpoint | Fail B2 |
| No list refresh after clone | Fail F4 |
