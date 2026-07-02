# Generator State — Iteration 001

## What Was Built
- **Sidebar split**: Replaced single "Tests" nav with "Generate Tests" (`/tests`, Sparkles icon) and "Saved Tests" (`/tests/saved`, FolderOpen icon)
- **GenerateTestsPage**: Extracted from TestsPage — NL generation form, KB context, generated test cards, save/edit/delete before persist; no saved-test list or edit redirect handling
- **SavedTestsPage enhancements**: `?edit=` drawer (slide-over), editable title field in drawer, inline title rename via `InlineTitleEditor`
- **InlineTitleEditor**: New reusable component — click/pencil to edit, Enter/blur save, Escape cancel, validation, loading state, error revert
- **App.tsx**: `TestsRoute` redirects `/tests?edit={id}` → `/tests/saved?edit={id}`; imports `GenerateTestsPage`
- **TestDetailPage**: Edit link updated to `/tests/saved?edit=`
- **E2E tests**: Updated `03-tests-page.spec.ts`, `06-navigation.spec.ts`; also fixed `02-dashboard.spec.ts`, `07-sprint2-features.spec.ts` for new nav labels

## What Changed This Iteration
- Initial Sprint 1 implementation per gan-harness/spec.md
- Deleted `frontend/src/pages/TestsPage.tsx` (replaced by `GenerateTestsPage.tsx`)
- Post-save navigation from generate page → `/tests/saved` with toast

## Files Changed
| File | Action |
|------|--------|
| `frontend/src/pages/GenerateTestsPage.tsx` | Created |
| `frontend/src/pages/TestsPage.tsx` | Deleted |
| `frontend/src/pages/SavedTestsPage.tsx` | Modified — edit drawer, InlineTitleEditor, header |
| `frontend/src/components/tests/InlineTitleEditor.tsx` | Created |
| `frontend/src/components/layout/Sidebar.tsx` | Modified — two nav items |
| `frontend/src/App.tsx` | Modified — GenerateTestsPage, edit redirect |
| `frontend/src/pages/TestDetailPage.tsx` | Modified — edit link |
| `tests/e2e/03-tests-page.spec.ts` | Modified |
| `tests/e2e/06-navigation.spec.ts` | Modified |
| `tests/e2e/02-dashboard.spec.ts` | Modified (nav label) |
| `tests/e2e/07-sprint2-features.spec.ts` | Modified (nav label) |

## Known Issues
- `npm run build` still fails due to pre-existing TS errors in unrelated files (mock/knowledgeBase, AgentWorkflow, SettingsPage-Old, etc.) — **no new errors in Sprint 1 changed files**
- Inline title E2E tests skip when no saved tests exist in the environment
- SavedTestsPage edit drawer uses `TestStepEditor` auto-save for steps; manual `steps` in PUT may be stale if user edits steps then immediately clicks Save Changes without waiting for auto-save debounce

## Dev Server
- URL: http://localhost:3000
- Status: not started in this session (Evaluator should run `npm run dev` in `frontend/`)
- Command: `npm run dev`
