# Evaluation Rubric: Test Navigator — Split Tabs + User Categories + Title Editing

**App:** AI Web Test v1 — Generate Tests + Saved Tests + User Categories + Inline Title Edit  
**Weight total: 1.0**  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Single combined Tests tab only (no sidebar split), no test category CRUD, edit saved test forces navigate to Generate tab, **saved test titles remain read-only with no inline rename**, or generate/run/suite flows regress

---

## Navigation Split (0.18)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| N1 | Sidebar: Generate Tests | Distinct sidebar link to `/tests` labeled "Generate Tests" | 0.05 |
| N2 | Sidebar: Saved Tests | Distinct sidebar link to `/tests/saved` labeled "Saved Tests" | 0.05 |
| N3 | Generate page scope | `/tests` shows NL generation only — no saved test library embedded | 0.04 |
| N4 | Edit on Saved tab | Editing saved test uses `/tests/saved?edit={id}` drawer/panel; does not require Generate tab | 0.03 |
| N5 | Legacy redirect | `/tests?edit={id}` redirects to `/tests/saved?edit={id}` | 0.01 |

---

## Title Editing (0.10)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| T1 | Inline rename on list | User can click title or pencil on Saved Tests row to edit title **without** opening edit drawer | 0.03 |
| T2 | Save / cancel semantics | Enter or blur saves valid changed title; Escape cancels and reverts; empty title blocked client-side | 0.03 |
| T3 | API partial update | Save calls `PUT /tests/{id}` with `{ title }` only via `testsService.updateTest` | 0.02 |
| T4 | Error + loading handling | Loading state during save; failed save reverts title and shows error feedback | 0.01 |
| T5 | Drawer title + a11y | Full edit drawer still has editable title field; inline editor has `aria-label` and keyboard support | 0.01 |

---

## User Categories — Backend (0.18)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| B1 | `test_categories` table | Migration exists; user-scoped; unique (user_id, name) | 0.05 |
| B2 | `test_category_id` on tests | Column on `test_cases`; nullable FK; separate from KB `category_id` | 0.05 |
| B3 | Category CRUD API | `GET/POST/PUT/DELETE /api/v1/test-categories` with ownership checks | 0.04 |
| B4 | Test filter + batch | `GET /tests?test_category_id=` works; bulk assign endpoint works | 0.04 |

---

## User Categories — Frontend (0.22)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| U1 | Manage Categories modal | Create, edit, delete categories from Saved Tests page | 0.06 |
| U2 | Category filter UI | Sidebar or chips filter saved list; "Uncategorized" supported | 0.06 |
| U3 | Single assign | User can change one test's category (row or edit drawer) | 0.04 |
| U4 | Bulk assign | Multi-select → Set Category updates all selected tests | 0.04 |
| U5 | Delete category behavior | Deleting category uncategorizes tests (not delete tests) | 0.02 |

---

## Architecture & Documentation (0.14)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| A1 | ADR-008 exists | `documentation/ADR-008-test-categories-navigation.md` present | 0.04 |
| A2 | KB vs org separation | ADR documents Option B; KB `category_id` retained for generation only | 0.04 |
| A3 | Service layer | `testCategoriesService.ts` in `frontend/src/services/`; no raw fetch in pages | 0.03 |
| A4 | Backend layering | Endpoints → CRUD; no business logic in routers | 0.03 |

---

## Craft / UX (0.10)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| C1 | Label clarity | Generate page KB selector ≠ Saved page "Test Category" (no conflation) | 0.03 |
| C2 | Visual consistency | Matches existing Tailwind sidebar, cards, blue-600 primary; inline title matches row typography | 0.03 |
| C3 | Empty states | Zero categories and zero tests have sensible CTAs | 0.02 |
| C4 | Build clean | `npm run build` in `frontend/` succeeds | 0.02 |

---

## Non-Regression (0.08)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| R1 | Generate flow | NL generate → review → save still works | 0.03 |
| R2 | Run / schedule | Run and schedule from Saved Tests unchanged | 0.02 |
| R3 | Test suites picker | `SuiteFormModal` still lists all saved tests | 0.02 |
| R4 | E2E updated | `03-tests-page` and `06-navigation` specs pass or updated for new nav | 0.01 |

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

1. Log in; confirm sidebar has **Generate Tests** and **Saved Tests** (not single "Tests").
2. Click **Generate Tests** → `/tests` → enter prompt → generate → save one test.
3. Click **Saved Tests** → saved test appears.
4. **Inline title edit:** click test title (or pencil) → type new title → press Enter → title updates in list without drawer opening.
5. **Inline cancel:** click title again → change text → press Escape → title reverts.
6. **Inline validation:** click title → clear text → blur → inline error shown; title not saved.
7. Open **Manage Categories** → create "Billing" (blue) → save.
8. Select test → **Set Category** → Billing → row shows Billing badge.
9. Filter sidebar to Billing → only that test shows.
10. Edit test via **Edit** → drawer opens on Saved tab → change title in drawer → save → remain on `/tests/saved`.
11. Bulk select 2 tests → Set Category → verify both updated.
12. Delete "Billing" category → tests show Uncategorized.
13. Visit `/tests?edit={id}` → lands on `/tests/saved?edit={id}`.
14. Open Test Suites → create/edit suite → test picker shows saved tests.
15. Confirm `documentation/ADR-008-test-categories-navigation.md` exists.
16. Run `npm run build` in `frontend/`; `pytest` for new backend tests if present.

---

## Anti-patterns (deduct or fail)

| Anti-pattern | Action |
|--------------|--------|
| Reuse `KBCategory` for user test folders without ADR justification | Fail A2 |
| Saved tests still only reachable via button on Generate page | Fail N2 |
| `category_id` repurposed to mean org category (breaks KB generation) | Automatic fail |
| Edit navigates to `/tests?edit=` on Generate page as primary flow | Fail N4 |
| Title rename requires opening full edit drawer or Generate tab | Fail T1 |
| Title remains static `<h3>` with no inline edit affordance | Automatic fail |
| No migration; only frontend labels | Fail B1 |
| Category CRUD via KB endpoints | Fail B3 |
| Broken generate or suite picker | Automatic fail |
| Modal-only title rename (no inline path) | Fail T1 |
