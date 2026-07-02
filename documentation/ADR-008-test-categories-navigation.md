# Architecture Decision Records — Test Categories and Navigation Split for Saved Tests

**Document ID:** ADR-008  
**Component:** Tests Navigation + Saved Tests Library Organization  
**Status:** Proposed  
**Date:** July 2, 2026  
**Author:** GAN Generator  
**Related Files:**
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/App.tsx`
- `frontend/src/pages/TestsPage.tsx`
- `frontend/src/pages/SavedTestsPage.tsx`
- `frontend/src/components/tests/InlineTitleEditor.tsx` (planned)
- `frontend/src/services/testsService.ts`
- `frontend/src/services/testCategoriesService.ts` (planned)
- `backend/app/models/test_case.py`
- `backend/app/models/test_category.py` (planned)
- `backend/app/schemas/test_case.py`
- `backend/app/schemas/test_category.py` (planned)
- `backend/app/crud/test_case.py`
- `backend/app/crud/test_category.py` (planned)
- `backend/app/api/v1/endpoints/tests.py`
- `backend/app/api/v1/endpoints/test_categories.py` (planned)
- `backend/app/migrations/versions/*` (planned migration for `test_categories` + `test_category_id`)
- `gan-harness/spec.md`

---

## Context

The current UX combines generation and saved-test management under a single Tests navigation entry. Saved tests live at `/tests/saved` but are not a first-class sidebar destination. This mixes two different user jobs:

1. Generate new test cases from natural language and KB context.
2. Organize, rename, and curate an existing saved test library.

At the same time, test categorization is conflated with Knowledge Base categorization:
- `category_id` is currently tied to KB categories and generation context.
- Users requested custom categories for saved tests (product area/sprint/environment organization), which is semantically different from KB taxonomy.

Saved test titles are also not directly editable from the saved list. Users need inline title editing for quick curation without navigating back to generation flows.

### Assumptions (from repository context)

- This ADR is derived from `gan-harness/spec.md`, which explicitly requires ADR-008 for navigation split + data model separation + inline title editing.
- Feature implementation may still be in progress; this ADR records the architectural decision and intended structure.
- Existing test generation behavior that uses KB `category_id` for RAG context remains unchanged.

These assumptions are documented here because no separate, already-accepted ADR-008 existed in `documentation/` at the time of writing.

---

## Decision

1. **Split Tests navigation into two first-class destinations**
   - Keep `/tests` as **Generate Tests**.
   - Keep `/tests/saved` as **Saved Tests** and expose it directly in sidebar navigation.
   - Redirect edit-intent routes/query params toward Saved Tests ownership so curation happens in the saved library context.

2. **Separate saved-test organization from KB taxonomy**
   - Introduce a new `test_categories` domain (user-scoped) for saved test organization.
   - Add `test_category_id` on `test_cases` for saved test filing/filtering/bulk assignment.
   - Keep existing KB `category_id` semantics for generation context unchanged.

3. **Support title editing directly on Saved Tests**
   - Add inline title rename in saved test rows via a focused inline editor pattern.
   - Keep full edit drawer title editing available for parity with broader edits.
   - Reuse existing `PUT /tests/{id}` title update capability (already supported) instead of introducing a new title endpoint.

4. **Expose category management as an explicit Saved Tests capability**
   - Provide CRUD for test categories and category-based filtering/grouping on Saved Tests.
   - Support both single-test and bulk category reassignment flows.

---

## Changes Made

| Layer | File | Change |
|---|---|---|
| Documentation | `documentation/ADR-008-test-categories-navigation.md` | New ADR defining nav split, `test_categories`, `test_category_id`, and inline title editing |
| Spec tracking | `gan-harness/spec.md` | ADR status/checklist updated to reference this ADR as present |

---

## Consequences

**Positive**
- Clear separation of user intent: generation and library curation no longer compete in one screen/nav entry.
- Data model semantics are cleaner: KB category remains generation context; saved-test category becomes user organization.
- Inline rename reduces friction for high-volume test library maintenance.
- Decision supports future enhancements (category metadata, ownership, sharing) without overloading KB models.

**Negative**
- Requires migration and cross-layer updates (models, schemas, CRUD, API, frontend services/UI).
- Transitional complexity while both old and new category semantics coexist in code during rollout.
- Additional UX/state complexity in Saved Tests page (category filters, bulk assignment, inline rename states).

**Alternatives Considered**
- **Reuse `KBCategory` for saved-test organization:** Rejected due to semantic coupling and global taxonomy constraints.
- **Tags-only approach:** Rejected due to weaker management/filtering UX and lack of explicit category lifecycle.
- **Keep title edits only in full edit flow:** Rejected because it adds unnecessary navigation cost for simple rename actions.

---

## Test Coverage

Planned verification coverage aligned to spec:

| Area | Coverage |
|------|----------|
| Routing/navigation split | E2E update for separate Generate/Saved sidebar entries and route behavior |
| Data model/API separation | Backend tests for `test_category_id` filtering/assignment and category CRUD |
| Saved Tests title editing | Frontend tests for inline rename save/cancel/validation and edit-drawer parity |
| Non-regression | Existing generate/run/suite workflows remain functional; KB `category_id` generation context unchanged |

