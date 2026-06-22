# Architecture Decision Records — Test Suites

**Document ID:** ADR-007  
**Component:** Test Suites — Grouping, Execution, and Edit  
**Status:** Accepted  
**Date:** June 22, 2026  
**Author:** GAN Generator  
**Related Files:**
- `frontend/src/pages/TestSuitesPage.tsx`
- `frontend/src/components/SuiteFormModal.tsx`
- `frontend/src/services/testSuitesService.ts`
- `backend/app/api/v1/endpoints/test_suites.py`
- `backend/app/crud/crud_test_suite.py`
- `backend/app/schemas/test_suite.py`
- `backend/app/models/test_suite.py`
- `documentation/archive/TEST-SUITES-FEATURE-DESIGN.md` (historical)

---

## Context

- Test suites group ordered test cases for batch/sequential execution.
- Backend CRUD and `PUT /api/v1/suites/{id}` shipped in Sprint 3; frontend create/delete/run shipped; **edit UI was never wired** despite service method existing.
- Original design doc wireframes included Edit on suite cards.
- Users need to fix typos, retag suites, and reorder/add/remove tests without delete-and-recreate.

---

## Decision

1. **Document test suites** as a first-class feature in ADR-007 (no prior ADR).
2. **Expose edit in UI** via shared `SuiteFormModal` with create/edit modes.
3. **Use existing PUT endpoint** — full replacement of `test_case_ids` on membership change (matches CRUD behavior).
4. **Button order:** Run → Edit → Delete; Edit uses neutral outline styling.

---

## Changes Made

| Layer | File | Change |
|---|---|---|
| Frontend component | `CreateSuiteModal.tsx` → `SuiteFormModal.tsx` | Dual mode; pre-populate; `updateSuite` on edit |
| Frontend page | `TestSuitesPage.tsx` | Edit button; modal mode state |
| Documentation | `documentation/ADR-007-test-suites.md` | This ADR |

---

## Consequences

**Positive**
- Parity with create flow; no backend deploy needed.
- Single modal reduces maintenance vs duplicate component.
- Aligns UI with archived design spec.

**Negative**
- Full test list replacement on every membership edit (acceptable at current scale).
- No audit trail of suite edits (only `updated_at` timestamp).
- Orphan test references if a test case is deleted server-side while modal is open — handled by validation on submit.

**Alternatives Considered**
- **Separate EditSuiteModal:** Rejected — duplicates form logic.
- **Inline card editing:** Rejected — complex for test ordering UI.
- **PATCH partial updates only:** Rejected — PUT with full `test_case_ids` already implemented and simpler for membership changes.

---

## Test Coverage

| Area | Coverage |
|------|----------|
| Backend PUT | Manual / existing integration (no dedicated unit tests in repo today) |
| Frontend | Manual verification checklist below; optional future `SuiteFormModal.test.tsx` |
| ADR | Peer review that Related Files and Decision match implementation |
