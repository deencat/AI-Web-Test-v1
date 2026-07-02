# Generator State — Iteration 002

## What Was Built
- **Sidebar split**: Replaced single "Tests" nav with "Generate Tests" (`/tests`, Sparkles icon) and "Saved Tests" (`/tests/saved`, FolderOpen icon)
- **GenerateTestsPage**: Extracted from TestsPage — NL generation form, KB context, generated test cards, save/edit/delete before persist; no saved-test list or edit redirect handling
- **SavedTestsPage enhancements**: `?edit=` drawer (slide-over), editable title field in drawer, inline title rename via `InlineTitleEditor`
- **InlineTitleEditor**: New reusable component — click/pencil to edit, Enter/blur save, Escape cancel, validation, loading state, error revert
- **App.tsx**: `TestsRoute` redirects `/tests?edit={id}` → `/tests/saved?edit={id}`; imports `GenerateTestsPage`
- **TestDetailPage**: Edit link updated to `/tests/saved?edit=`
- **E2E tests**: Updated `03-tests-page.spec.ts`, `06-navigation.spec.ts`; also fixed `02-dashboard.spec.ts`, `07-sprint2-features.spec.ts` for new nav labels

## What Changed This Iteration
- **Fixed**: TestDetailPage back navigation — `handleBack` now navigates to `/tests/saved` instead of `/tests` (Generate Tests)
- **Improved**: Renamed back button label from "Back to Tests" to "Back to Saved Tests" in error, not-found, and main views
- **Added**: E2E test `should navigate back to saved tests from test detail` in Saved Tests Page — Sprint 1 suite

## Files Changed
| File | Action |
|------|--------|
| `frontend/src/pages/TestDetailPage.tsx` | Modified — back nav to `/tests/saved`, button label |
| `tests/e2e/03-tests-page.spec.ts` | Modified — back navigation E2E test |

## Known Issues
- `npm run build` still fails due to pre-existing TS errors in unrelated files (mock/knowledgeBase, AgentWorkflow, SettingsPage-Old, etc.) — **no new errors in Sprint 1 changed files**
- Inline title E2E tests skip when no saved tests exist in the environment
- SavedTestsPage edit drawer uses `TestStepEditor` auto-save for steps; manual `steps` in PUT may be stale if user edits steps then immediately clicks Save Changes without waiting for auto-save debounce
- TestDetailPage delete action still navigates to `/tests` after deletion (not addressed in this iteration)

## Dev Server
- URL: http://localhost:5173
- Status: running
- Command: `npm run dev` (in `frontend/`)
