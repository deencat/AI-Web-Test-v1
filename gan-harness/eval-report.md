# Evaluation Report — Sprint 1 (Navigation Split + Title Editing)

**Date:** 2026-07-02  
**Iteration:** 002  
**Evaluator:** gan-evaluator  
**App URL:** http://localhost:5173  
**Backend:** http://127.0.0.1:8000 (running)

---

## Executive Summary

**Sprint 1 Verdict: PASS**

Iteration 002 fixes TestDetailPage back navigation (`/tests/saved`, button label "Back to Saved Tests") and closes all prior E2E coverage gaps. **26/26 Sprint 1–relevant E2E tests pass** (11 Saved Tests + 15 Navigation). Two new E2E tests cover T4 API error revert and loading spinner during save. Four Generate-flow tests still fail due to real-LLM latency vs 30s Playwright test timeout (R1, outside Sprint 1 gate).

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
| Loading + error revert on failed save | T4 | 0.01 | ⚠️ | 0.00 |
| Drawer title field + inline `aria-label` | T5 | 0.01 | ✅ | 0.01 |
| **Non-Regression** | | **0.01** | | |
| E2E specs updated for new nav | R4 | 0.01 | ✅ | 0.01 |
| **Sprint 1 TOTAL** | | **0.29** | | **0.28/0.29** |

**Sprint 1 weighted score: 0.97** (28/29 applicable weight units)

| Criterion Group | Verdict |
|-----------------|---------|
| Navigation Split (0.18) | **PASS** |
| Title Editing (0.10) | **PARTIAL** — T4 error toast UX bug |
| Non-Regression R4 (0.01) | **PASS** |
| User Categories (0.40) | N/A — Sprint 2+ |
| Architecture & Docs (0.14) | N/A — Sprint 2+ |
| Craft / UX (0.10) | N/A — Sprint 2+ |
| Non-Regression R1–R3 (0.07) | Not scored this sprint |

**Overall Sprint 1 verdict: PASS** (≥ 0.85 threshold on applicable criteria; iteration 002 back-nav fix verified)

### T4 partial pass rationale

| T4 sub-requirement | E2E | Live UX |
|--------------------|-----|---------|
| Loading state during save | ✅ `should show loading spinner during inline title save` | ✅ `Loader2` spinner visible |
| Failed save reverts title | ✅ `should revert title when inline save fails with API error` | ✅ Title unchanged in list |
| Error feedback on failed save | ❌ Not asserted (toast not visible) | ❌ `errorToast` only rendered inside `isEditing` branch; cleared when edit mode exits on catch |

---

## E2E Test Results

### Sprint 1 + Navigation (final run, `--workers=1`)

| Spec | Suite | Passed | Failed | Skipped |
|------|-------|--------|--------|---------|
| `03-tests-page.spec.ts` | Saved Tests Page — Sprint 1 | **11** | 0 | 0 |
| `06-navigation.spec.ts` | Application Navigation | **15** | 0 | 0 |
| **Sprint 1 subtotal** | | **26** | **0** | **0** |

### Generate Tests (not Sprint 1; R1 context)

| Spec | Suite | Passed | Failed | Skipped |
|------|-------|--------|--------|---------|
| `03-tests-page.spec.ts` | Generate Tests Page | 4 | **4** | 0 |
| **Full run total** | | **30** | **4** | **0** |

**Generate failures:** Real LLM backend exceeds default 30s Playwright test timeout before "Generated Test Cases" appears. Root cause: `test.setTimeout` not raised for AI generation tests. Not a Sprint 1 regression.

### New in iteration 002

| Test | File | Status |
|------|------|--------|
| `should navigate back to saved tests from test detail` | `03-tests-page.spec.ts` | ✅ |
| `should revert title when inline save fails with API error` | `03-tests-page.spec.ts` | ✅ |
| `should show loading spinner during inline title save` | `03-tests-page.spec.ts` | ✅ |

---

## E2E Coverage Matrix — Saved Tests Sprint 1 Features

**Coverage: 23/23 behaviors — 100% E2E coverage**

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
| **View Details → Back to Saved Tests** | `03-tests-page` | should navigate back to saved tests from test detail | ✅ |
| API error revert on save | `03-tests-page` | should revert title when inline save fails with API error | ✅ |
| Loading spinner during save | `03-tests-page` | should show loading spinner during inline title save | ✅ |

---

## Iteration 002 Fix Verification

| Change | Expected | Result |
|--------|----------|--------|
| `handleBack` navigates to `/tests/saved` | URL `/tests/saved`, Saved Tests heading visible | ✅ |
| Button label "Back to Saved Tests" | Not "Back to Tests" / Generate heading | ✅ |
| Does not land on Generate Tests | No NL generation form after back | ✅ |

---

## Implementation Verification (Code Review)

| Area | Finding | Status |
|------|---------|--------|
| Sidebar | `Generate Tests` + `Saved Tests` distinct links | ✅ |
| Generate page | NL generation only; no saved list | ✅ |
| Legacy redirect | `TestsRoute` redirects `?edit=` to saved tab | ✅ |
| Inline editor | Enter/blur save, Escape cancel, validation, spinner | ✅ |
| API call | `testsService.updateTest(id, { title })` → `PUT /tests/{id}` | ✅ |
| Edit drawer | `SavedTestsPage` slide-over with `#saved-edit-title` | ✅ |
| TestDetailPage back nav | `navigate('/tests/saved')`, label "Back to Saved Tests" | ✅ |
| Error toast on failed save | `errorToast` not shown after edit mode exits | ❌ bug |
| TestDetailPage delete | Still navigates to `/tests` after delete | ⚠️ known, out of scope |
| Build | Pre-existing TS errors in unrelated files | ⚠️ pre-existing |

---

## Critical Issues (must fix)

None blocking Sprint 1 pass gate.

## Major Issues (should fix)

1. **T4 error toast UX bug:** `InlineTitleEditor` sets `isEditing(false)` before `showErrorToast()` in catch block; toast only renders in editing branch. → Move error toast to non-editing view or use global toast.
2. **Generate-flow E2E timeouts (R1):** Four tests fail against real LLM. → Add `test.setTimeout(180_000)` on AI generation tests or mock AI in CI.

## Minor Issues (nice to fix)

1. **TestDetailPage delete nav:** Delete still returns to `/tests` (Generate) — inconsistent with back button fix.
2. **Mock `updateTest` title field:** Mock branch ignores `data.title` (harmless when `VITE_USE_MOCK=false`).
3. **Title suffix accumulation:** Repeated E2E renames append suffixes; consider `afterAll` title reset.

---

## What Improved Since Iteration 001

- TestDetailPage back navigation fixed — returns to Saved Tests, not Generate
- E2E coverage gaps closed: T4 API error revert, loading spinner, back-from-detail flow
- Coverage matrix: 91% → **100%** for Sprint 1 saved-tests behaviors

## What Regressed

- None observed for Sprint 1 scope
- Generate E2E flakiness increased (4 failures vs 3 in iter 001) due to LLM latency variance

---

## Specific Suggestions for Next Iteration

1. Fix `InlineTitleEditor` error toast visibility on failed PUT.
2. Align TestDetailPage delete navigation with back button (`/tests/saved`).
3. Raise Playwright timeout or mock AI for generate-flow E2E in CI.
4. Proceed to Sprint 2: user categories, ADR-008, `testCategoriesService.ts`.

---

## Screenshots / Observations

- Saved Tests list: inline title buttons with `data-testid="inline-title-button-{id}"`
- Test detail: "Back to Saved Tests" button returns to `/tests/saved` with correct heading
- Failed PUT (intercepted 500): title reverts, edit mode closes; no visible error message (bug)
- Delayed PUT (1.5s): `.animate-spin` visible during save
- Legacy `/tests?edit={id}` → `/tests/saved?edit={id}` with drawer open
