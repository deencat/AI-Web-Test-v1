# Implementation Spec: Test Navigator — Split Tabs + User Categories + Title Editing

> Generated from brief: *"Currently the saved tests are in tests tab. I want to have saved tests in an individual tab while generate tests have it own tab. For saved tests, I want user can customize their own category then they are add or change the test cases category. For saved tests, I also want user can edit test cases title."*

## Vision

AI Web Test users today land on a single **Tests** sidebar item that mixes natural-language generation, generated-test review, and a buried link to saved tests (`/tests/saved` is not in the sidebar). This creates cognitive overload: "generate" and "manage" are different jobs performed in the same place.

**Test Navigator** splits those jobs into two first-class sidebar destinations — **Generate Tests** and **Saved Tests** — and adds **user-defined test categories** so teams can organize saved cases by product area, sprint, or environment without conflating that with Knowledge Base document taxonomy. On the Saved Tests library, users can **rename test cases inline** (quick title edit on the list row) or via the full edit drawer — without opening the Generate tab. The target UX feels like a lightweight test library manager: generate on one tab, curate and run on another, filter by your own folders, rename titles in place.

---

## Scope and Current State

| Layer | Component | Status | Notes |
|-------|-----------|--------|-------|
| **Sidebar** | `frontend/src/components/layout/Sidebar.tsx` | Partial | Single "Tests" → `/tests` |
| **Generate flow** | `frontend/src/pages/TestsPage.tsx` | Combined | NL form, KB category for generation context, generated review/save, `?edit=` loads saved test into same page |
| **Saved list** | `frontend/src/pages/SavedTestsPage.tsx` | Hidden route | `/tests/saved` — search, type/priority/scheduled filters, batch delete, run, schedule; **title is read-only `<h3>`**; Edit → `/tests?edit={id}` |
| **Detail** | `frontend/src/pages/TestDetailPage.tsx` | Complete | `/tests/:testId` |
| **Routes** | `frontend/src/App.tsx` | Partial | `/tests`, `/tests/saved`, `/tests/:testId` — no generate/saved split in nav |
| **Test CRUD API** | `backend/app/api/v1/endpoints/tests.py` | Partial | Full CRUD; `PUT /tests/{id}` supports `title` (min 1, max 255) via `TestCaseUpdate`; `category_id` in response; **no category filter query param** |
| **Test model** | `backend/app/models/test_case.py` | Conflated | `category_id` FK → `kb_categories.id` (KB context, not user org) |
| **KB categories** | `backend/app/models/kb_document.py` (`KBCategory`) | KB-only | Global, unique `name`, no `user_id`; used for KB docs + optional generation context |
| **Generation API** | `backend/app/api/v1/endpoints/test_generation.py` | Complete | `category_id` = KB category for RAG context |
| **Frontend types** | `frontend/src/types/api.ts` | Conflated | `category_id` documented as KB |
| **Test suites picker** | `frontend/src/components/SuiteFormModal.tsx` | Unaffected | Uses `testsService.getAllTests()` — must still see all saved tests |
| **E2E** | `tests/e2e/03-tests-page.spec.ts`, `06-navigation.spec.ts` | Stale assumptions | Expect single "Tests" link and "Test Cases" heading on `/tests` |
| **ADR** | — | **Missing** | New **ADR-008** required for data model + navigation split |

**In scope:** Sidebar/routing split, user category CRUD, assign/change category (single + bulk), filter/group UI on Saved Tests, **inline title rename on saved test rows**, full edit drawer title field, backend model + API, migration, ADR-008, E2E updates.

**Out of scope:** Changing three-tier execution, test generation LLM logic, KB category management UX, drag-and-drop category ordering (nice-to-have), cross-user shared categories (future), backend changes for title update (already supported).

---

## Architectural Decision: Test Categories Data Model

### Options evaluated

| Option | Description | Verdict |
|--------|-------------|---------|
| **A) Reuse `KBCategory`** | Extend `kb_categories` for test organization | **Reject** — global unique names, no `user_id`, semantically tied to KB documents; editing/deleting KB categories would break test org; conflates RAG context with user filing |
| **B) New `test_categories` table** | User-scoped categories; separate FK on `test_cases` | **Accept** — clean separation; matches user brief ("customize their own category") |
| **C) Tags only** | Use existing `tags` JSON array | **Reject** — weaker filtering/grouping UX; no color/icon; no "manage categories" screen; bulk reassignment awkward |

### Recommendation: **Option B — `test_categories` table**

**Rationale:**
1. **Separation of concerns:** `category_id` on generation requests remains KB context (RAG). Saved-test organization uses `test_category_id`.
2. **User ownership:** Categories are per-user (same pattern as test cases, suites).
3. **Evolution:** Supports name, color, description, sort order without touching KB schema.
4. **Migration safety:** Existing `test_cases.category_id` (KB FK) can remain for historical/generation linkage; new column avoids breaking KB relationships.

**Field naming after migration:**

| Column | Purpose |
|--------|---------|
| `test_cases.category_id` | **Keep** — KB category used at generation time (optional); rename in API docs to `kb_category_id` in response alias if clarity needed |
| `test_cases.test_category_id` | **New** — user-defined organization category (nullable) |

Generation flow on `GenerateTestsPage` continues to pass `category_id` to `/tests/generate` as KB context only. Saving a test does **not** auto-assign `test_category_id` unless user explicitly picks an org category at save time (optional dropdown on save card — Sprint 2 polish).

---

## Navigation & Tab Design

### Sidebar changes

Replace single nav item with two (icons from `lucide-react`):

| Label | Path | Icon | Active when |
|-------|------|------|-------------|
| **Generate Tests** | `/tests` | `Sparkles` | `pathname === '/tests'` or `pathname.startsWith('/tests/generate')` |
| **Saved Tests** | `/tests/saved` | `FolderOpen` | `pathname === '/tests/saved'` or `pathname.startsWith('/tests/saved')` |

Place **Generate Tests** then **Saved Tests** adjacent (where "Tests" was), before Step Library.

### Route strategy

| Route | Page | Behavior |
|-------|------|----------|
| `/tests` | `GenerateTestsPage` | **Generate only** — extract generation + generated-review from current `TestsPage`; remove saved-test list and "View Saved Tests" header button |
| `/tests/saved` | `SavedTestsPage` | **Saved library** — list, filters, categories, inline title edit, edit-in-place drawer |
| `/tests/saved?edit={id}` | `SavedTestsPage` | Opens edit drawer/modal for test `{id}` (replaces `/tests?edit=`) |
| `/tests/:testId` | `TestDetailPage` | Unchanged |
| `/tests?edit={id}` | Redirect | `<Navigate to="/tests/saved?edit={id}" replace />` in `App.tsx` or page-level redirect — backward compat |
| `/tests/generate` | Optional alias | Redirect to `/tests` — only if Generator prefers explicit path; **default: `/tests` is generate** |

**Do not** redirect `/tests` → `/tests/saved`. Generate remains the default tests entry (matches current behavior and "Generate New Tests" CTAs).

### Page split: `TestsPage` → `GenerateTestsPage`

1. Rename `TestsPage.tsx` → `GenerateTestsPage.tsx` (or keep filename, change export — **prefer rename** for clarity).
2. **Remove** from generate page:
   - `loadAndEditTest` / `?edit=` handling (moves to SavedTestsPage)
   - `editingSavedTest` flow
   - Header "View Saved Tests" button (sidebar replaces it)
   - Any mock "existing tests" list view (`showGenerator` toggle for non-generation content)
3. **Keep** on generate page:
   - NL prompt form
   - KB category selector (`selectedCategory` → generation `category_id`)
   - Generated test cards, save/edit/delete before persist
   - Post-save navigation → `/tests/saved` (optionally with toast "View in Saved Tests")

### Edit flow decision

**Editing a saved test stays on the Saved Tests tab** — not the Generate tab.

| Action | Destination |
|--------|-------------|
| **Quick rename title only** | Inline on list row — no drawer, no navigation |
| Edit steps/title/description/category from saved list | `/tests/saved?edit={id}` — inline drawer or full-width edit panel on SavedTestsPage (reuse `TestStepEditor` + form state from current `TestsPage` edit block) |
| After save (drawer) | Remain on `/tests/saved`; clear `?edit=` param |
| Cancel edit (drawer) | Close drawer; `navigate('/tests/saved', { replace: true })` |

**Rationale:** Generate tab = create net-new from NL; Saved tab = curate persisted tests. Mixing edit on generate tab was the original pain point. Inline title edit covers the most common rename action without opening the full editor.

### Dashboard / deep links

| Source | Current | New |
|--------|---------|-----|
| `SavedTestsPage` "Generate New Tests" | `navigate('/tests')` | Keep → `/tests` |
| `SavedTestsPage` Edit button | `navigate('/tests?edit=…')` | `navigate('/tests/saved?edit=…')` |
| `RenameModuleModal` | `/tests/{id}` | Unchanged |
| `SuiteFormModal` test picker | `getAllTests()` | Unchanged — no category filter in picker (show all user tests) |

---

## Title Editing Feature

Users must be able to change a saved test's **title** from the Saved Tests list without opening the full edit drawer or navigating to the Generate tab. The full edit drawer also retains a title field for editing title alongside steps, description, priority, and category.

### Two edit surfaces (complementary, not redundant)

| Surface | When to use | Opens drawer? |
|---------|-------------|---------------|
| **Inline title editor** | User wants to rename only | **No** |
| **Full edit drawer** (`?edit=id`) | User edits steps, description, priority, category, or title in context of other fields | Yes |

### Inline title editor UX

**Component:** `frontend/src/components/tests/InlineTitleEditor.tsx` (new, reusable)

**Trigger:**
- Click the test title text (`<h3>` replacement), **or**
- Click a small pencil icon button adjacent to the title (`aria-label="Rename test title"`)

**Edit mode:**
- Title text becomes a single-line `<input>` styled to match `text-lg font-semibold text-gray-900`
- Input receives focus and selects all text on enter edit mode
- `maxLength={255}` (matches backend `TestCaseUpdate.title`)

**Save:**
- **Enter** — save if valid and changed
- **Blur** — save if valid and changed (debounce not required; single PUT per blur)
- Show inline loading indicator on the row (spinner or input `disabled` + opacity) while `PUT` in flight

**Cancel:**
- **Escape** — revert to previous title; exit edit mode without API call

**Validation (client):**
- Trim whitespace before save
- Empty or whitespace-only title → **block save**, show inline red helper text *"Title is required"* (or border `border-red-500`), keep edit mode open
- Unchanged title on blur/Enter → exit edit mode silently (no API call)

**API:**
```http
PUT /api/v1/tests/{id}
Content-Type: application/json

{ "title": "New title here" }
```
- Partial update — send `{ title }` only; no backend changes required (`TestCaseUpdate` already supports optional `title`, min 1, max 255 chars)
- Use existing `testsService.updateTest(id, { title })`

**Success:**
- Update local list state optimistically or from response
- Optional brief success toast: *"Title updated"* (green, bottom-right — match Step Library rename toast pattern)

**Error:**
- On network/4xx/5xx failure: **revert** displayed title to last known good value
- Show error toast: *"Failed to update title"* (or server message if available)
- Exit edit mode after revert

**Accessibility:**
- Title in view mode: `role="button"` or wrap in button with `aria-label="Edit title: {currentTitle}"` if not using native click on heading
- Edit input: `aria-label="Test title"`, `aria-invalid={hasError}`, `aria-describedby` for validation message
- Pencil button: `aria-label="Rename test title"`
- Keyboard: Tab to pencil → Enter activates edit; Escape cancels; Enter saves

**Visual pattern (match existing Tailwind):**
- View mode: `text-lg font-semibold text-gray-900 hover:text-blue-600 cursor-pointer` on title (subtle affordance)
- Edit input: `border border-blue-400 rounded px-2 py-0.5 focus:ring-2 focus:ring-blue-500 focus:outline-none`
- Pencil: `p-1 text-gray-400 hover:text-gray-600 rounded` with `Pencil` icon from `lucide-react` (`w-4 h-4`)
- Do **not** use `contentEditable` — use controlled `<input>` for predictable validation

**Reference patterns in codebase:**
- Step Library uses modal rename (`RenameModuleModal`) for slug changes — heavier than needed for title
- Knowledge Base uses inline edit in review panels — similar save/cancel semantics
- Prefer lightweight inline input over modal for title-only rename

### Full edit drawer title field

The edit drawer (`?edit=id`) **must** include an editable **Title** text input at the top of the form:
- Same validation: required, 1–255 chars
- Saves with full `testsService.updateTest` payload on "Save Changes"
- If user also edited title inline on the same row before opening drawer, drawer loads current title from list state / fresh fetch

### Edge cases — title editing

| Case | Behavior |
|------|----------|
| Empty title on save | Blocked client-side; inline error; no API call |
| Duplicate titles | **Allowed** — no uniqueness constraint on test titles per user |
| Title unchanged on blur | Exit edit mode; no API call |
| Concurrent edit (drawer + inline) | Last successful save wins; refresh list on drawer close if inline changed during session |
| Failed save | Revert to previous title; error toast |
| User editing title while batch delete selected | Inline edit allowed; row remains selectable |
| Inline edit during `batchDeleting` | Disable inline edit triggers while batch delete in progress |
| Very long title (255 chars) | `maxLength={255}` on input; server validates same |
| Mobile viewport | Inline input full width within card; touch-friendly tap target on title |
| Screen reader | Announce validation errors via `aria-live="polite"` region |

### API — no backend changes

| Item | Status |
|------|--------|
| `PUT /tests/{id}` with `{ title }` | Already supported via `TestCaseUpdate` |
| Title validation | Backend: min 1, max 255 chars |
| New endpoints | None required |

---

## User-Defined Categories Feature

### Category management (CRUD)

**Entry points on Saved Tests page:**
1. **"Manage Categories"** button in page header (secondary outline) → opens `CategoryManagerModal`
2. **"+ Category"** quick action in category filter sidebar/chip row

**CategoryManagerModal** (new component):

| Field | Validation |
|-------|------------|
| Name | Required, 1–100 chars, unique per user |
| Description | Optional |
| Color | Hex, default `#3B82F6` (reuse KB color picker pattern) |

**Actions:** Create, Edit, Delete.

**Delete behavior:** If category has tests → confirm dialog: *"N tests use this category. They will become Uncategorized."* Set `test_category_id = NULL` on affected tests (soft org removal, not test deletion).

### Assign / change category on test cases

| Mode | UI | API |
|------|-----|-----|
| **Single — row action** | Category dropdown in each test row (or in edit drawer) | `PUT /tests/{id}` with `test_category_id` |
| **Single — edit drawer** | Category `<select>` alongside priority | Same |
| **Bulk — multi-select** | Toolbar: "Set Category" → dropdown when `selectedIds.size > 0` | `PATCH /tests/batch/category` (new) with `{ test_ids: number[], test_category_id: number \| null }` |
| **On save from Generate** | Optional "Save to category" on each generated card before save | `POST /tests` includes `test_category_id` |

### Filtering & grouping UI

**Layout addition on SavedTestsPage** — left sidebar (desktop) or horizontal chip scroll (mobile):

```
┌─────────────────────────────────────────────────────────┐
│ Saved Test Cases                    [Manage Categories] │
├──────────────┬──────────────────────────────────────────┤
│ All (42)     │  [Search] [Type] [Priority] [Schedule]   │
│ ─────────    │  ┌─────────────────────────────────────┐ │
│ ● Billing(8) │  │ [✓] Login Flow ✎  [Billing] [high]   │ │
│ ● Login (5)  │  │     (inline title + row actions)    │ │
│ ● Uncategorized (12)                                      │
└──────────────┴──────────────────────────────────────────┘
```

- Click category → filter list client-side (or server `?test_category_id=` if list is large)
- **"Uncategorized"** = `test_category_id IS NULL`
- Category chip on each row shows color dot + name
- Filter bar adds **Category** dropdown (redundant with sidebar — keep sidebar as primary, dropdown for mobile)

### Empty states

| State | Message + CTA |
|-------|-----------------|
| No categories yet | Sidebar shows only "All" + "Uncategorized"; "Create your first category" in Manage Categories |
| No tests in category | "No tests in Billing yet" + link to Generate Tests |
| No saved tests at all | Existing empty state + "Generate New Tests" |

---

## Data Model & API

### New table: `test_categories`

```sql
CREATE TABLE test_categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  color VARCHAR(20) NOT NULL DEFAULT '#3B82F6',
  sort_order INTEGER NOT NULL DEFAULT 0,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  UNIQUE (user_id, name)
);
CREATE INDEX ix_test_categories_user_id ON test_categories(user_id);
```

### Alter `test_cases`

```sql
ALTER TABLE test_cases
  ADD COLUMN test_category_id INTEGER REFERENCES test_categories(id) ON DELETE SET NULL;
CREATE INDEX ix_test_cases_test_category_id ON test_cases(test_category_id);
```

**Keep** existing `category_id` → `kb_categories` for KB/generation linkage.

### New backend modules

| File | Purpose |
|------|---------|
| `backend/app/models/test_category.py` | SQLAlchemy model |
| `backend/app/schemas/test_category.py` | Create/Update/Response |
| `backend/app/crud/test_category.py` | CRUD + count tests per category |
| `backend/app/api/v1/endpoints/test_categories.py` | REST router |
| `backend/app/migrations/versions/xxxx_add_test_categories.py` | Alembic migration |

### API endpoints

**`/api/v1/test-categories`** (new router, register in `api.py`):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/test-categories` | List current user's categories with `test_count` |
| POST | `/test-categories` | Create |
| GET | `/test-categories/{id}` | Get one (ownership check) |
| PUT | `/test-categories/{id}` | Update |
| DELETE | `/test-categories/{id}` | Delete; nullify `test_cases.test_category_id` |

**Extend `/api/v1/tests`:**

| Change | Detail |
|--------|--------|
| `GET /tests` | Add query param `test_category_id: Optional[int]`; special value `uncategorized` via `test_category_id=0` convention or `uncategorized=true` |
| `TestCaseCreate/Update/Response` | Add `test_category_id: Optional[int]` |
| `PATCH /tests/batch/category` | Bulk assign `{ test_ids, test_category_id }` |
| Response enrichment | Include nested `test_category: { id, name, color }` when loaded |
| `PUT /tests/{id}` | **Unchanged** — `title` partial update already supported |

**Schemas** — update descriptions:
- `category_id` → document as "KB category ID (generation context)"
- `test_category_id` → "User-defined organization category"

### Frontend service

New `frontend/src/services/testCategoriesService.ts`:

```ts
getAll(), create(data), update(id, data), delete(id)
batchAssignCategory(testIds, categoryId | null)  // via tests batch endpoint
```

Update `testsService.ts`: add `test_category_id` to create/update types; `getAllTests({ test_category_id })` filter param. Existing `updateTest(id, { title })` used by inline editor.

---

## Files to Change

### Must change

| File | Change |
|------|--------|
| `frontend/src/components/layout/Sidebar.tsx` | Two nav items: Generate Tests, Saved Tests |
| `frontend/src/pages/TestsPage.tsx` | Rename → `GenerateTestsPage.tsx`; strip saved-test edit/list; update headings |
| `frontend/src/pages/SavedTestsPage.tsx` | Category sidebar, filters, bulk assign, edit drawer with `?edit=`, **replace read-only `<h3>` with `InlineTitleEditor`** |
| `frontend/src/components/tests/InlineTitleEditor.tsx` | **New** — click-to-edit title, validation, PUT on save |
| `frontend/src/App.tsx` | Import rename; redirect `/tests?edit=` → saved; route order preserved |
| `frontend/src/types/api.ts` | Add `TestCategory`, `test_category_id` on Test types |
| `frontend/src/services/testsService.ts` | `test_category_id` support, batch category; `updateTest` for title (existing) |
| `frontend/src/services/testCategoriesService.ts` | **New** |
| `frontend/src/components/testCategories/CategoryManagerModal.tsx` | **New** |
| `frontend/src/components/testCategories/CategorySidebar.tsx` | **New** (optional extract) |
| `backend/app/models/test_category.py` | **New** |
| `backend/app/models/test_case.py` | Add `test_category_id` FK + relationship |
| `backend/app/schemas/test_case.py` | Add `test_category_id` fields |
| `backend/app/schemas/test_category.py` | **New** |
| `backend/app/crud/test_category.py` | **New** |
| `backend/app/crud/test_case.py` | Filter by `test_category_id`; batch category update |
| `backend/app/api/v1/endpoints/test_categories.py` | **New** |
| `backend/app/api/v1/endpoints/tests.py` | Filter param, batch category endpoint |
| `backend/app/api/v1/api.py` | Register test_categories router |
| `backend/app/migrations/versions/…` | **New** migration |
| `documentation/ADR-008-test-categories-navigation.md` | **New** ADR (include title editing on Saved tab) |
| `tests/e2e/03-tests-page.spec.ts` | Update for "Generate Tests" nav label/heading |
| `tests/e2e/06-navigation.spec.ts` | Two test nav links; saved tests route |

### Optional (Sprint 2+)

| File | Change |
|------|--------|
| `frontend/src/pages/__tests__/SavedTestsPage.test.tsx` | Category filter + bulk assign + **inline title edit** tests |
| `frontend/src/components/tests/__tests__/InlineTitleEditor.test.tsx` | **New** — unit tests for save/cancel/validation |
| `backend/tests/unit/test_test_categories.py` | **New** unit tests |
| `frontend/src/pages/GenerateTestsPage.tsx` | Optional category on save card |
| `docs/CODEMAPS/frontend.md` | Route map update |

### No change required

| File | Reason |
|------|--------|
| `backend/app/api/v1/endpoints/test_generation.py` | KB `category_id` unchanged |
| `backend/app/schemas/test_case.py` (title field) | `TestCaseUpdate.title` already exists |
| `frontend/src/components/SuiteFormModal.tsx` | Picker uses all tests |
| `backend/app/models/kb_document.py` | KB categories independent |
| Execution engine / ADR-002 | Out of scope |

---

## UI/UX Specification

### Generate Tests page (`/tests`)

**Header:**
- Title: **Generate Tests**
- Subtitle: *Generate test cases using natural language*
- No "View Saved Tests" button (sidebar handles navigation)

**Body:** Unchanged generation form + KB context panel + results area.

**Post-save:** `navigate('/tests/saved')` with optional query `?highlight={newId}`.

### Saved Tests page (`/tests/saved`)

**Header:**
- Title: **Saved Tests**
- Buttons: `[Manage Categories]` (secondary), `[Generate New Tests]` (primary → `/tests`)

**Category sidebar (md+):** Fixed width `w-56`, white card, category rows with count badge, color dot, active state `bg-blue-50 border-l-4 border-blue-600`.

**Test table/card row:**
- **Title row:** `InlineTitleEditor` (click title or pencil → inline input) — replaces static `<h3>`
- Category badge (colored pill) or "Uncategorized" gray pill
- Quick category change: click pill → small popover select
- Description, metadata, action buttons unchanged

**Edit drawer (`?edit=id`):**
- Slide-over from right, `max-w-2xl`
- Fields: **title** (required text input), description, steps (`TestStepEditor`), priority, **Test Category** dropdown, runtime credentials flag
- Footer: Cancel | Save Changes
- Uses `testsService.updateTest`

**Bulk toolbar** (when rows selected):
`[N selected] [Set Category ▾] [Delete]` — extends existing batch delete bar.

### Edge cases

| Case | Behavior |
|------|----------|
| Delete category with tests | Tests → Uncategorized (`test_category_id = null`) |
| Duplicate category name | API 409; inline validation in modal |
| Edit test category to null | "Uncategorized" in UI |
| `?edit=` invalid id | Toast error; strip query param |
| User has 0 categories | Sidebar: All + Uncategorized only; assign via "Set Category" prompts create |
| KB `category_id` on test from generation | Shown only in test detail metadata (optional "KB context" label) — not in org sidebar |
| Admin viewing other user's tests | Categories scoped to test owner; admin list shows tests but category CRUD only for own categories |
| Mobile viewport | Category sidebar → horizontal scroll chips above filters |
| Empty title inline edit | Blocked; inline validation message |
| Failed title save | Revert title; error toast |
| Duplicate test titles | Allowed |

### Responsive

- `< md`: hide left sidebar; category chips row below header
- Table horizontal scroll preserved
- Edit drawer full-screen on mobile
- Inline title input spans available row width on mobile

---

## Migration Path

### Existing data

1. **Deploy migration** adding `test_categories` + `test_cases.test_category_id` (nullable, default NULL).
2. **Do not auto-migrate** `test_cases.category_id` (KB FK) into `test_category_id` — they are different concepts. Existing tests appear as **Uncategorized** in org sidebar.
3. **Optional admin script** (out of band): if team previously misused KB categories as folders, one-time script can create `test_categories` rows and map by KB name — document in ADR, not required for MVP.

### Backward compatibility

| Item | Strategy |
|------|----------|
| `/tests?edit={id}` | 302/Navigate to `/tests/saved?edit={id}` |
| API clients using `category_id` | Unchanged semantics (KB); additive `test_category_id` |
| `GET /tests` without new param | Returns all tests (unchanged) |
| `PUT /tests/{id}` with `{ title }` | Unchanged — already supported |
| OpenAPI | Bump field docs; no breaking removals |

### Rollback

Migration `downgrade()` drops `test_category_id` column and `test_categories` table. No impact on KB or execution. Inline title editor is frontend-only rollback.

---

## Sprint Breakdown

### Sprint 1: Navigation split + title editing (~1.25 days)

| # | Deliverable | Effort |
|---|-------------|--------|
| 1.1 | Sidebar: Generate Tests + Saved Tests | 1h |
| 1.2 | Extract `GenerateTestsPage`; remove edit/saved cross-links | 2–3h |
| 1.3 | `App.tsx` redirects; update headings | 1h |
| 1.4 | Move `?edit=` handling to `SavedTestsPage` (reuse existing edit UI) | 3h |
| 1.5 | **`InlineTitleEditor` component + integrate in SavedTestsPage rows** | 2–3h |
| 1.6 | Edit drawer includes title field; Edit button → `/tests/saved?edit=` | 1h (part of 1.4) |
| 1.7 | Update E2E `03-tests-page`, `06-navigation`; add inline title rename case | 2h |

**DoD:** Two sidebar tabs work; generate at `/tests`; saved at `/tests/saved`; edit stays on saved; old `?edit=` URLs work; **user can rename title inline on list row without opening drawer**; drawer title field works for full edits.

### Sprint 2: Backend categories (~1.5 days)

| # | Deliverable | Effort |
|---|-------------|--------|
| 2.1 | Model, migration, CRUD, endpoints | 4h |
| 2.2 | Extend test schemas + `test_category_id` on create/update | 2h |
| 2.3 | `GET /tests?test_category_id=` filter | 1h |
| 2.4 | `PATCH /tests/batch/category` | 2h |
| 2.5 | Unit tests for CRUD + ownership | 2h |

**DoD:** API documented in OpenAPI; migration runs clean; pytest for test_categories passes.

### Sprint 3: Saved Tests category UI (~1.5 days)

| # | Deliverable | Effort |
|---|-------------|--------|
| 3.1 | `testCategoriesService.ts` | 1h |
| 3.2 | `CategoryManagerModal` CRUD | 3h |
| 3.3 | Category sidebar + filter integration | 3h |
| 3.4 | Row badge + single assign dropdown | 2h |
| 3.5 | Bulk "Set Category" in selection toolbar | 2h |

**DoD:** User can create categories, assign single/bulk, filter list; delete category uncategorizes tests.

### Sprint 4: Docs + polish (~0.5 day)

| # | Deliverable | Effort |
|---|-------------|--------|
| 4.1 | ADR-008 | 1h |
| 4.2 | Edit drawer polish on Saved Tests; inline title edge cases (concurrent edit, a11y audit) | 2h |
| 4.3 | Frontend `SavedTestsPage.test.tsx` + `InlineTitleEditor.test.tsx` | 2h |

**Total estimate:** ~4.5–5 days across 4 sprints.

---

## Verification Checklist

### Navigation & pages

- [ ] Sidebar shows **Generate Tests** and **Saved Tests** as separate items
- [ ] `/tests` shows only generation UI (no saved test list)
- [ ] `/tests/saved` in sidebar navigates to saved list
- [ ] `/tests?edit=5` redirects to `/tests/saved?edit=5`
- [ ] Edit saved test opens drawer on Saved Tests; save does not leave saved tab
- [ ] "Generate New Tests" on saved page → `/tests`
- [ ] `/tests/:testId` detail page still works

### Title editing

- [ ] Saved test row title is **not** read-only — click title or pencil enters edit mode
- [ ] Inline rename does **not** open edit drawer or navigate to Generate tab
- [ ] Enter or blur saves changed title via `PUT /tests/{id}` with `{ title }` only
- [ ] Escape cancels edit and restores previous title
- [ ] Empty/whitespace title blocked with inline validation (no API call)
- [ ] Loading state shown while save in progress
- [ ] Failed save reverts title and shows error toast
- [ ] Duplicate titles allowed (two tests can share a title)
- [ ] Edit drawer title field still editable alongside steps/description
- [ ] `aria-label` on pencil button and title input; keyboard Enter/Escape work

### Categories

- [ ] Create category via Manage Categories modal
- [ ] Rename/recolor category; list updates
- [ ] Delete category → tests become Uncategorized
- [ ] Assign category on single test (row dropdown + edit drawer)
- [ ] Bulk select → Set Category → all selected updated
- [ ] Sidebar filter by category; counts match
- [ ] Uncategorized filter shows only `test_category_id = null`
- [ ] Duplicate category name per user → validation error

### API & data

- [ ] `GET /test-categories` returns only current user's categories with counts
- [ ] `PUT /tests/{id}` with `test_category_id` persists
- [ ] `PUT /tests/{id}` with `{ title }` persists (inline + drawer)
- [ ] `GET /tests?test_category_id={id}` filters correctly
- [ ] `PATCH /tests/batch/category` works for 2+ tests
- [ ] KB generation with `category_id` still works; distinct from `test_category_id`

### Non-regression

- [ ] Test suite picker shows all saved tests
- [ ] Run, schedule, batch delete on Saved Tests unchanged
- [ ] `npm run build` (frontend) passes
- [ ] `pytest` backend unit tests pass
- [ ] E2E navigation + generate tests specs pass

### Documentation

- [ ] `documentation/ADR-008-test-categories-navigation.md` complete (mentions inline title edit)
- [ ] OpenAPI shows new endpoints and fields

---

## Evaluation Criteria

See `gan-harness/eval-rubric.md` for weighted scorer sheet.

**Pass requires:** Sidebar split functional, edit on saved tab, **inline title rename on saved list**, category CRUD + assign + filter working, ADR-008 present, no regression on generate/run/suites.

---

## Design Direction

Match existing AI Web Test Tailwind/Layout patterns — no redesign.

| Token | Value |
|-------|-------|
| Primary | `#2563eb` (blue-600) — primary buttons, active nav |
| Active nav | `bg-blue-700 text-white` (existing sidebar) |
| Page background | `bg-gray-50` via Layout |
| Cards | White, `border-gray-200`, `rounded-lg` |
| Category colors | User-picked hex; pill `bg-{color}20` with dot |
| Typography | Page title `text-3xl font-bold text-gray-900`; labels `text-sm font-medium text-gray-700`; row title `text-lg font-semibold text-gray-900` |
| Secondary actions | `border border-gray-300 text-gray-700 hover:bg-gray-50` |
| Destructive | Red-600 (delete only) |
| Inline edit focus | `border-blue-400 ring-blue-500` |

**Layout philosophy:** Dense operational dashboard (Saved Tests) + focused single-column flow (Generate). Category sidebar mirrors KB document filter mental model without copying KB data. Inline title edit keeps rename friction near zero.

**Visual identity:**
- Color dots next to category names (not generic folder icons everywhere)
- Count badges `text-xs bg-gray-100 rounded-full px-2`
- Edit drawer slide-over (not modal-on-modal)
- Subtle pencil affordance on title hover (not always-visible chrome overload)

**Anti-AI-slop / anti-patterns:**
- No gradient headers or hero sections on list pages
- No card grid redesign for saved tests — keep table/list efficiency
- Do not conflate KB category selector (Generate page) with org category sidebar (Saved page) — different labels: **"KB Context (optional)"** vs **"Test Category"**
- No icon-only category management without text labels
- Avoid third floating action button; use header toolbar
- Do not open a modal just to rename a title — use inline input
- No `contentEditable` divs for title

**Inspiration:** GitHub Issues inline title edit on list view; Jira quick rename on issue row; Step Library rename toast pattern — adapted to existing blue-gray enterprise UI.

---

## ADR-008 Content Outline

**File:** `documentation/ADR-008-test-categories-navigation.md`

Sections (per ADR-005 structure):
1. **Context** — Combined Tests page; KB `category_id` misuse risk; user request for custom categories; read-only titles on saved list
2. **Decision** — Split nav; new `test_categories` table; `test_category_id` on `test_cases`; edit on saved tab; **inline title editor on Saved Tests**; keep KB `category_id` for generation
3. **Changes Made** — table of files (include `InlineTitleEditor.tsx`)
4. **Consequences** — positive/negative; alternatives A/C rejected
5. **Test Coverage** — checklist mapping

---

## Technical Stack

- **Frontend:** React, Vite, TypeScript, Tailwind, React Router, lucide-react
- **Backend:** FastAPI, SQLAlchemy, Alembic, Pydantic v2
- **Key patterns:** `FormMode` create/edit (`StepLibraryPage`, `SuiteFormModal`); services in `frontend/src/services/`; endpoints → services → CRUD; inline edit via controlled input (`InlineTitleEditor`)
