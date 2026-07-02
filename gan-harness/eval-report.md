# Evaluation Report — Sprint 1 (Navigation Split + Title Editing)

**Date:** 2026-07-02  
**Iteration:** 001  
**Evaluator:** gan-evaluator  
**App URL:** http://localhost:5173  
**Backend:** http://127.0.0.1:8000 (running)

---

## Executive Summary

**Sprint 1 Verdict: PASS**

Navigation split and inline title editing are implemented correctly and verified end-to-end. All 23 Sprint 1–relevant E2E tests pass after adding API seeding and token-based login helpers. Four pre-existing generate-flow E2E tests fail due to real-API AI latency exceeding the 30s Playwright test timeout (R1 non-regression, not Sprint 1 scope).

---

## Sprint 1 Rubric Scores

Applicable criteria only (Categories, ADR, Craft marked N/A for Sprint 1).

| Criterion | ID | Weight | Pass | Weighted |
|-----------|-----|--------|------|----------|
| **Navigation Split** | | **0.18** | | |
| Sidebar: Generate Tests → `/tests` | N1 | 0.05 | ✅ | 0.05 |
| Sidebar: Saved Tests → `/tests/saved` | N2 | 0.05 | ✅ | 0.05 |
| `/tests` shows NL generation only | N3 | 0.04 | ✅ | 0.04 |
| Edit uses `/tests/saved?edit={id}` drawer | N4 | 0.03 | ✅ | 0.03 |
| Legacy `/tests?edit=` → `/tests/saved?edit=` | N5 | 0.01 | ✅ | 0.01 |
| **Title Editing** | | **0.10** | | |
| Inline rename on list (no drawer) | T1 | 0.03 | ✅ | 0.03 |
| Enter/blur save; Escape cancel; empty blocked | T2 | 0.03 | ✅ | 0.03 |
| `PUT /tests/{id}` with `{ title }` only | T3 | 0.02 | ✅ | 0.02 |
| Loading + error revert on failed save | T4 | 0.01 | ✅ | 0.01 |
| Drawer title field + inline `aria-label` | T5 | 0.01 | ✅ | 0.01 |
| **Non-Regression** | | **0.01** | | |
| E2E specs updated for new nav | R4 | 0.01 | ✅ | 0.01 |
| **Sprint 1 TOTAL** | | **0.29** | | **0.29/0.29** |

**Sprint 1 weighted score: 1.00** (29/29 applicable weight units)

| Criterion Group | Verdict |
|-----------------|---------|
| Navigation Split (0.18) | **PASS** |
| Title Editing (0.10) | **PASS** |
| Non-Regression R4 (0.01) | **PASS** |
| User Categories (0.40) | N/A — Sprint 2+ |
| Architecture & Docs (0.14) | N/A — Sprint 2+ |
| Craft / UX (0.10) | N/A — Sprint 2+ |
| Non-Regression R1–R3 (0.07) | Not scored this sprint |

**Overall Sprint 1 verdict: PASS** (navigation + title editing working; threshold met)

---

## E2E Test Results

### Sprint 1 + Navigation (final run, `--workers=1`)

| Spec | Suite | Passed | Failed | Skipped |
|------|-------|--------|--------|---------|
| `03-tests-page.spec.ts` | Saved Tests Page — Sprint 1 | **8** | 0 | 0 |
| `06-navigation.spec.ts` | Application Navigation | **15** | 0 | 0 |
| **Sprint 1 subtotal** | | **23** | **0** | **0** |

### Generate Tests (not Sprint 1; R1 context)

| Spec | Suite | Passed | Failed | Skipped |
|------|-------|--------|--------|---------|
| `03-tests-page.spec.ts` | Generate Tests Page | 4 | **4** | 0 |

**Generate failures:** AI generation via real backend exceeds default 30s test timeout. Tests 1–3 never see "Generated Test Cases" within timeout; test 4 reaches results but times out on "Generate More Tests" click. Root cause: environment latency + `test.setTimeout` not raised for LLM calls. Not a Sprint 1 regression.

### E2E infrastructure added this evaluation

- `tests/e2e/helpers/auth.ts` — `seedSavedTest()`, token-cached `loginAsAdmin(page, request)` bypassing login rate limits
- Serial mode for saved-tests suites to avoid 429 errors
- Blur-save title test, drawer/legacy redirect tests in `06-navigation.spec.ts`
- Header assertion fixed: `Agentic QA` (was stale `AI Web Test`)

---

## E2E Coverage Matrix — Saved Tests Sprint 1 Features

| Feature | Spec | Test Case | Status |
|---------|------|-----------|--------|
| Navigate to Saved Tests tab | `06-navigation` | should navigate through all main pages | ✅ |
| Saved Tests sidebar link visible | `06-navigation` | should maintain sidebar across all pages | ✅ |
| Active Saved Tests highlight | `06-navigation` | should highlight active saved tests link | ✅ |
| Direct URL `/tests/saved` | `06-navigation` | should support direct URL navigation | ✅ |
| Mobile nav to Saved Tests | `06-navigation` | should have working navigation on mobile viewport | ✅ |
| Saved tests list displays | `03-tests-page` | should display saved tests list with rows | ✅ |
| Generate vs Saved separation | `06-navigation` | should keep generate and saved tests as separate routes | ✅ |
| No "View Saved Tests" on Generate | `03-tests-page` | should not show view saved tests button in header | ✅ |
| Inline title edit — click title | `03-tests-page` | should allow inline title rename via Enter | ✅ |
| Inline title save — Enter | `03-tests-page` | should allow inline title rename via Enter | ✅ |
| Inline title save — blur | `03-tests-page` | should save inline title edit on blur | ✅ |
| Inline title cancel — Escape | `03-tests-page` | should cancel inline title edit with Escape | ✅ |
| Empty title validation | `03-tests-page` | should block empty title on inline edit | ✅ |
| Pencil icon entry | `03-tests-page` | should enter inline edit via pencil icon | ✅ |
| Edit drawer via `?edit=` on saved tab | `03-tests-page` | should open edit drawer via ?edit= query param | ✅ |
| Legacy redirect `/tests?edit=` | `06-navigation` | should redirect legacy /tests?edit= URLs to saved tests | ✅ |
| Edit drawer via legacy redirect | `06-navigation` | should open edit drawer on saved tab via legacy redirect | ✅ |
| Drawer does not open Generate tab | `06-navigation` | should open edit drawer on saved tab via legacy redirect | ✅ |
| Drawer editable title field | `03-tests-page` | should open edit drawer via ?edit= (`#saved-edit-title`) | ✅ |
| Inline `aria-label` | `03-tests-page` | should enter inline edit via pencil icon | ✅ |
| API error revert on save | — | No E2E (code-only) | ⚠️ gap |
| Loading spinner during save | — | No E2E (code-only) | ⚠️ gap |

**Coverage: 20/22 Sprint 1 behaviors covered in E2E (91%).** Remaining gaps are T4 error/loading paths — implemented in `InlineTitleEditor.tsx` but not exercised by E2E.

---

## Implementation Verification (Code Review)

| Area | Finding | Status |
|------|---------|--------|
| Sidebar | `Generate Tests` (`/tests`, Sparkles) + `Saved Tests` (`/tests/saved`, FolderOpen) in `Sidebar.tsx` | ✅ |
| Generate page | `GenerateTestsPage.tsx` — generation only; post-save navigates to `/tests/saved` | ✅ |
| Legacy redirect | `TestsRoute` in `App.tsx` redirects `?edit=` to saved tab | ✅ |
| Inline editor | `InlineTitleEditor.tsx` — Enter/blur save, Escape cancel, validation, spinner, error toast | ✅ |
| API call | `testsService.updateTest(id, { title })` → `PUT /tests/{id}` | ✅ |
| Edit drawer | `SavedTestsPage.tsx` — slide-over with `#saved-edit-title`, `?edit=` param | ✅ |
| Mock mode bug | `updateTest` mock path ignores `data.title` (only `data.name`); harmless when `VITE_USE_MOCK=false` | ⚠️ |
| Build | `npm run build` fails on pre-existing TS errors in unrelated files | ⚠️ pre-existing |

---

## Critical Issues (must fix — outside Sprint 1 pass gate)

None blocking Sprint 1. Navigation and title editing work in the live app.

## Major Issues (should fix)

1. **Generate-flow E2E timeouts (R1):** Four tests in `03-tests-page.spec.ts` fail against real LLM backend. → Add `test.setTimeout(180_000)` on AI generation tests or gate them behind `VITE_USE_MOCK=true` in CI.
2. **Mock `updateTest` title field:** `testsService.updateTest` mock branch does not apply `data.title`. → Add `if (data.title) updates.name = data.title` for mock-mode parity.

## Minor Issues (nice to fix)

1. **T4 E2E gap:** No test for failed PUT revert. → Add route interception test that returns 500 and asserts title reverts + error toast.
2. **Long test titles:** Repeated E2E renames append suffixes; consider resetting seed test title in `afterAll`.
3. **Playwright browsers:** Sandbox cache missing Chromium; document `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright` or run `npx playwright install chromium`.

---

## What Improved Since Last Iteration

- Full sidebar split with distinct routes and active-state highlighting
- `InlineTitleEditor` with keyboard semantics and validation
- Edit drawer on Saved Tests tab with `?edit=` deep link
- Legacy URL redirect preserved
- Comprehensive E2E coverage with API seeding (no more skip-when-empty)

## What Regressed

- None observed for Sprint 1 scope

---

## Specific Suggestions for Next Iteration (Sprint 2+)

1. Implement user categories per spec; add `testCategoriesService.ts` and ADR-008.
2. Fix generate-flow E2E: either mock AI in CI or extend timeouts to match 120s API timeout.
3. Add E2E for T4 error path via `page.route()` mock failure on `PUT /tests/*`.
4. Resolve pre-existing `npm run build` TS errors before claiming C4 pass.

---

## Screenshots / Observations

- Login page branding: **Agentic QA** (not "AI Web Test")
- Generate page: no saved-test list, no "View Saved Tests" button
- Saved Tests: inline title buttons with `data-testid="inline-title-button-{id}"` and pencil icons
- Edit drawer: "Edit Test Case" heading, closes via aria-label "Close edit drawer"
- Legacy `/tests?edit=1321` → `/tests/saved?edit=1321` with drawer open
