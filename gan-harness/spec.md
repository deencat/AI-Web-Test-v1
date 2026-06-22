# Implementation Spec: Test Suite Edit + ADR-007

> Generated from brief: *"The Test Suites page shows suite cards with Run and Delete buttons but NO Edit button. Users cannot modify existing suites (name, description, tags, test membership/order). Create an ADR for test suites documenting this feature and the edit capability."*

## Vision

Close the last major gap in the Test Suites UX: users can create and delete suites but cannot edit them. The backend `PUT /suites/{id}` endpoint and `testSuitesService.updateSuite()` already exist — this work is **frontend + documentation only**, wiring an Edit affordance that reuses the existing create modal pattern and records the decision in **ADR-007**.

---

## Scope and Current State

| Layer | Component | Status | Notes |
|-------|-----------|--------|-------|
| **Frontend page** | `frontend/src/pages/TestSuitesPage.tsx` | Partial | Lists suites; Run + Delete only; expand shows ordered tests |
| **Frontend modal** | `frontend/src/components/CreateSuiteModal.tsx` | Create-only | Full form: name, description, tags, test pick + reorder |
| **Frontend service** | `frontend/src/services/testSuitesService.ts` | Complete | `updateSuite(id, UpdateTestSuiteRequest)` → `PUT /suites/{id}` |
| **Backend API** | `backend/app/api/v1/endpoints/test_suites.py` | Complete | `PUT /{suite_id}` with ownership check |
| **Backend CRUD** | `backend/app/crud/crud_test_suite.py` | Complete | Replaces items when `test_case_ids` provided |
| **Backend schema** | `backend/app/schemas/test_suite.py` | Complete | `TestSuiteUpdate` — all fields optional |
| **Design doc** | `documentation/archive/TEST-SUITES-FEATURE-DESIGN.md` | Reference | Wireframes show `[Run] [Edit]` on cards |
| **ADR** | `documentation/ADR-007-test-suites.md` | **Missing** | New document required |

**Out of scope:** Backend changes, suite execution changes, drag-and-drop reorder (up/down arrows already exist), parallel run, new API endpoints, E2E test suite unless evaluator adds smoke coverage.

---

## Architectural Decision: `SuiteFormModal` (create + edit) vs `EditSuiteModal`

**Recommendation: Refactor `CreateSuiteModal` → `SuiteFormModal` with `mode: 'create' | 'edit'`.**

| Approach | Pros | Cons |
|----------|------|------|
| **SuiteFormModal (chosen)** | Single source of truth for form layout, validation, test picker, reorder; matches `StepLibraryPage` `FormMode` pattern; ~1 file change + import rename | Slightly larger component; must handle pre-populate + reset |
| **Separate EditSuiteModal** | Smaller initial diff | Duplicates 300+ lines; divergent validation/UX over time |

**Rationale:** `CreateSuiteModal.tsx` is already the complete suite editor UI. Edit differs only in: (1) initial state from `TestSuite`, (2) submit calls `updateSuite` vs `createSuite`, (3) title/button copy. `StepLibraryPage.tsx` (lines 7, 83–97, 113–119) is the established codebase pattern for create/edit in one form.

---

## Files to Change

### Must change

| File | Change |
|------|--------|
| `frontend/src/components/CreateSuiteModal.tsx` | **Rename** to `SuiteFormModal.tsx`. Add props: `mode: 'create' \| 'edit'`, optional `suite?: TestSuite`. Pre-populate form when `mode === 'edit' && suite`. Submit: `createSuite` vs `updateSuite(suite.id, ...)`. Dynamic title ("Create Test Suite" / "Edit Test Suite") and submit label ("Create Suite" / "Save Changes"). Reset form on close in both modes. |
| `frontend/src/pages/TestSuitesPage.tsx` | Add Edit button per card. State: `editingSuite: TestSuite \| null`, `showFormModal: boolean`, `formMode: 'create' \| 'edit'`. Wire `SuiteFormModal` for create (existing) and edit (new). Import rename from `CreateSuiteModal` → `SuiteFormModal`. |
| `documentation/ADR-007-test-suites.md` | **New file** — full ADR per outline in §ADR below |

### Optional (nice polish, same PR if time permits)

| File | Change |
|------|--------|
| `frontend/src/components/CreateSuiteModal.tsx` | Keep as thin re-export `export { default } from './SuiteFormModal'` for one release to avoid grep churn — **prefer direct rename** and update the single import in `TestSuitesPage.tsx` only. |

### No change required

| File | Reason |
|------|--------|
| `frontend/src/services/testSuitesService.ts` | `updateSuite` already implemented |
| `backend/**` | PUT endpoint complete |
| `documentation/archive/TEST-SUITES-FEATURE-DESIGN.md` | Historical reference; ADR-007 supersedes for architecture |

---

## UI/UX Specification

### Edit button placement and styling

Per original wireframe (`TEST-SUITES-FEATURE-DESIGN.md` line 103): **`[Run] [Edit] [Delete]`** — Edit sits **between Run and Delete**.

```tsx
// TestSuitesPage.tsx — suite card action row (~line 197)
<div className="flex gap-2 ml-4">
  <button /* Run — keep existing green */ />
  <button
    onClick={() => handleEdit(suite)}
    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
    title="Edit Suite"
    aria-label="Edit suite"
  >
    Edit
  </button>
  <button /* Delete — keep existing red */ />
</div>
```

**Styling rationale:** Match `StepLibraryPage` edit buttons (gray outline, not filled blue). Run = green (primary action), Delete = red (destructive), Edit = neutral secondary — avoids three competing filled colors.

### Modal behavior (edit mode)

1. User clicks **Edit** on a suite card.
2. `handleEdit(suite)` sets `formMode = 'edit'`, `editingSuite = suite`, `showFormModal = true`.
3. Modal opens with fields pre-populated:

| Field | Source |
|-------|--------|
| Name | `suite.name` |
| Description | `suite.description ?? ''` |
| Tags | `suite.tags?.join(', ') ?? ''` |
| Selected test IDs (ordered) | `suite.items` sorted by `execution_order` → map to `test_case_id` |

4. Available tests list loads as today (`testsService.getAllTests()` on open).
5. User modifies fields; validation unchanged (name required, ≥1 test).
6. Submit calls:

```ts
await testSuitesService.updateSuite(suite.id, {
  name: name.trim(),
  description: description.trim() || undefined,
  tags: tags.length > 0 ? tags : undefined,
  test_case_ids: selectedTestIds,
});
```

7. On success: `onSuccess()` → `loadSuites()` refreshes list; modal closes; form resets.
8. On error: show API `detail` in existing red banner (same as create).

### Create mode (unchanged behavior)

- Header "New Suite" button and empty-state CTA still set `formMode = 'create'`, `editingSuite = null`.
- Submit calls `createSuite` as today.

### Edge cases

| Case | Behavior |
|------|----------|
| Suite with missing `items` | Treat as `[]`; block submit with "Please select at least one test case" |
| Test in suite deleted from system | Still show in selected list as `#${id}` fallback if not in `availableTests` (fetch by id from `item.test_case` if present) |
| User clears all tests | Validation error before submit |
| Modal closed mid-edit | `handleClose` resets all state; unsaved changes discarded (same as create) |
| Concurrent edit | Last write wins (acceptable; no optimistic locking in backend) |

### Success feedback

- **Primary:** `loadSuites()` re-fetches and re-renders card with updated name/tags/count.
- **Optional polish:** No toast required (create flow doesn't use one); expanded state can remain as-is for edited suite id.

---

## `SuiteFormModal` Implementation Sketch

```tsx
// SuiteFormModal.tsx — new/extended props
type SuiteFormMode = 'create' | 'edit';

interface SuiteFormModalProps {
  isOpen: boolean;
  mode: SuiteFormMode;
  suite?: TestSuite;           // required when mode === 'edit'
  onClose: () => void;
  onSuccess: () => void;
}

// Pre-populate on open (useEffect when isOpen + mode + suite)
useEffect(() => {
  if (!isOpen) return;
  loadAvailableTests();
  if (mode === 'edit' && suite) {
    setName(suite.name);
    setDescription(suite.description ?? '');
    setTagsInput(suite.tags?.join(', ') ?? '');
    const orderedIds = [...(suite.items ?? [])]
      .sort((a, b) => a.execution_order - b.execution_order)
      .map(item => item.test_case_id);
    setSelectedTestIds(orderedIds);
  } else {
    // reset to empty (create)
  }
  setSearchQuery('');
  setError('');
}, [isOpen, mode, suite]);
```

```tsx
// TestSuitesPage.tsx — handler + modal wiring
const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
const [editingSuite, setEditingSuite] = useState<TestSuite | null>(null);
const [showFormModal, setShowFormModal] = useState(false);

const handleEdit = (suite: TestSuite) => {
  setFormMode('edit');
  setEditingSuite(suite);
  setShowFormModal(true);
};

const openCreate = () => {
  setFormMode('create');
  setEditingSuite(null);
  setShowFormModal(true);
};

<SuiteFormModal
  isOpen={showFormModal}
  mode={formMode}
  suite={editingSuite ?? undefined}
  onClose={() => setShowFormModal(false)}
  onSuccess={loadSuites}
/>
```

Update header and empty-state buttons: `onClick={openCreate}` instead of `setShowCreateModal(true)`.

---

## ADR-007 Content Outline

**File:** `documentation/ADR-007-test-suites.md`

Follow [ADR-005](documentation/ADR-005-kb.md) structure:

```markdown
# Architecture Decision Records — Test Suites

**Document ID:** ADR-007
**Component:** Test Suites — Grouping, Execution, and Edit
**Status:** Accepted
**Date:** [implementation date]
**Author:** [implementer]
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

## Decision

1. **Document test suites** as a first-class feature in ADR-007 (no prior ADR).
2. **Expose edit in UI** via shared `SuiteFormModal` with create/edit modes.
3. **Use existing PUT endpoint** — full replacement of `test_case_ids` on membership change (matches CRUD behavior).
4. **Button order:** Run → Edit → Delete; Edit uses neutral outline styling.

## Changes Made

| Layer | File | Change |
|-------|------|--------|
| Frontend component | `CreateSuiteModal.tsx` → `SuiteFormModal.tsx` | Dual mode; pre-populate; `updateSuite` on edit |
| Frontend page | `TestSuitesPage.tsx` | Edit button; modal mode state |
| Documentation | `documentation/ADR-007-test-suites.md` | This ADR |

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

## Test Coverage

| Area | Coverage |
|------|----------|
| Backend PUT | Manual / existing integration (no dedicated unit tests in repo today) |
| Frontend | Manual verification checklist below; optional future `SuiteFormModal.test.tsx` |
| ADR | Peer review that Related Files and Decision match implementation |
```

---

## Verification Checklist

### Functional

- [ ] Navigate to `http://localhost:5173/test-suites` with ≥1 suite
- [ ] Each suite card shows **Run**, **Edit**, **Delete** in that order
- [ ] Click **Edit** → modal title "Edit Test Suite"; fields match suite (name, description, tags, ordered tests)
- [ ] Change name only → Save → card reflects new name after refresh
- [ ] Reorder tests (up/down) → Save → expanded list shows new order
- [ ] Add/remove tests → Save → test count updates
- [ ] **Create** flow still works via "New Suite" (modal title "Create Test Suite")
- [ ] Cancel closes modal without API call; reopening edit shows original data
- [ ] Empty validation: blank name or zero tests shows error banner
- [ ] API error (e.g. network) shows error message in modal

### Non-regression

- [ ] **Run** and **Delete** unchanged
- [ ] Expand/collapse test list still works
- [ ] `npm run build` in `frontend/` passes (no broken imports after rename)

### Documentation

- [ ] `documentation/ADR-007-test-suites.md` exists with all ADR-005 sections
- [ ] ADR Related Files list matches actual paths post-rename
- [ ] ADR Status = Accepted after merge

---

## Effort Estimate

| Task | Estimate |
|------|----------|
| Refactor modal to `SuiteFormModal` | 45–60 min |
| Wire Edit in `TestSuitesPage` | 15–20 min |
| Write ADR-007 | 20–30 min |
| Manual verification | 15 min |
| **Total** | **~1.5–2 hours** (single PR) |

## Sprint Assignment

**Sprint 1 (single PR, frontend + docs):**

| # | Deliverable |
|---|-------------|
| 1 | `SuiteFormModal` with create + edit modes |
| 2 | Edit button on `TestSuitesPage` |
| 3 | `documentation/ADR-007-test-suites.md` |

**Definition of done:** All verification checklist items pass; ADR merged; no backend changes unless PUT gap discovered during QA.

---

## Design Direction (modal consistency)

Keep existing modal visual language — no redesign:

- **Colors:** White modal on `bg-black/50` overlay; primary submit `#2563eb` (blue-600); error `#fef2f2` banner
- **Typography:** `text-2xl font-bold` modal title; form labels `text-sm font-medium text-gray-700`
- **Layout:** `max-w-5xl` two-column test picker (unchanged)
- **Anti-patterns:** Do not add new gradient headers, icon-only Edit without label, or move Edit to overflow menu

---

## Evaluation Criteria (summary)

See `gan-harness/eval-rubric.md` for weighted scorer sheet. Pass requires: Edit button functional, modal pre-populates correctly, PUT called on save, ADR-007 complete, create flow unbroken.
