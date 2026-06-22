# Evaluation Rubric: Test Suite Edit + ADR-007

**App:** AI Web Test — Test Suites page  
**Weight total: 1.0**  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Edit button missing, edit save does not call PUT/updateSuite, or create flow regresses

---

## Functionality (0.35)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| F1 | Edit button visible | Every suite card on `/test-suites` has Edit between Run and Delete | 0.08 |
| F2 | Modal pre-population | Edit opens modal with correct name, description, tags, and test IDs in `execution_order` | 0.10 |
| F3 | Save updates suite | Submit in edit mode calls `testSuitesService.updateSuite(id, …)`; list refreshes with changes | 0.10 |
| F4 | Create flow intact | "New Suite" still opens create mode; calls `createSuite`; validation unchanged | 0.04 |
| F5 | Membership edit | User can add, remove, and reorder tests; saved order matches expanded card view | 0.03 |

---

## Scope Discipline (0.20)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| S1 | No unnecessary backend | No backend file changes unless a real PUT gap is found and documented | 0.08 |
| S2 | Minimal file footprint | Changes limited to modal component, TestSuitesPage, ADR-007 (≤4 meaningful files) | 0.06 |
| S3 | Service reuse | Uses existing `updateSuite` in `testSuitesService.ts` — no duplicate API client | 0.06 |

---

## Documentation (0.25)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| D1 | ADR-007 exists | `documentation/ADR-007-test-suites.md` present | 0.05 |
| D2 | ADR structure | Header (ID, Component, Status, Date, Author, Related Files) + Context, Decision, Changes Made, Consequences, Test Coverage | 0.10 |
| D3 | Decision accuracy | ADR documents SuiteFormModal dual-mode, PUT endpoint, Run-Edit-Delete order | 0.05 |
| D4 | Related files | ADR Related Files match implemented paths (including `SuiteFormModal.tsx` if renamed) | 0.05 |

---

## Craft / UX (0.20)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| C1 | Edit button styling | Gray outline (`border-gray-300`), not competing with green Run / red Delete | 0.05 |
| C2 | Modal copy | Title and submit button differ between create ("Create Test Suite" / "Create Suite") and edit ("Edit Test Suite" / "Save Changes") | 0.05 |
| C3 | Form reset | Closing modal clears state; reopening edit shows fresh data from suite | 0.05 |
| C4 | Error handling | API errors surface in modal error banner; loading disables submit | 0.03 |
| C5 | Build clean | `npm run build` in `frontend/` succeeds; no stale `CreateSuiteModal` imports | 0.02 |

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

1. Log in; go to `/test-suites`.
2. If no suites, create one via "New Suite" (proves F4).
3. Click **Edit** on first suite — assert modal fields match card.
4. Append ` (edited)` to name; save — assert card shows new name.
5. Remove one test, add another, move order — save — expand card; assert order.
6. Open create modal — assert empty form and "Create" labels.
7. Confirm `documentation/ADR-007-test-suites.md` exists and mentions edit capability.
8. Run `npm run build` in `frontend/`.

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Duplicate `EditSuiteModal.tsx` copying entire create form | Fail S2 unless strongly justified in PR |
| Edit button only in expanded section | Fail F1 |
| Edit uses `POST` or new endpoint instead of PUT | Fail F3 |
| ADR missing or only stub | Fail D1 |
| Broken create after refactor | Automatic fail |
