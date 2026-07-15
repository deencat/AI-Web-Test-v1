# Evaluation Report — CRM Login Toggle Persist (Feature 3)

**Date:** 2026-07-15  
**Feature:** Fix `requires_runtime_credentials` omitted by API sanitizer  
**Evaluator:** gan-evaluator  
**App URL:** http://localhost:5173  
**Backend:** http://127.0.0.1:8000  
**Spec:** `gan-harness/spec.md` § Feature 3  
**Rubric:** `gan-harness/eval-rubric-crm-login-toggle.md` (pass threshold ≥ 0.85)  
**Eval artifact test:** `#1406` (`GAN Eval CRM Toggle Persist 134133`); clone `#1407`

---

## Executive Summary

Feature 3 is **fully implemented and verified**. The sanitizer now includes `requires_runtime_credentials`; live PUT→GET/list/clone round-trips preserve `true`/`false`; Saved Tests edit drawer toggle survives soft navigate and hard reload; credentials stay ephemeral. Backend unit suites for sanitize + CRM ephemeral credentials passed **38/38**.

**Weighted score: 1.00 / 1.00 — PASS**

All automatic-fail conditions are clear. No Generator gaps block merge.

---

## Weighted Score

```
score = Σ (criterion_weight × pass?1:0)
```

| Band | Score | Verdict |
|------|-------|---------|
| Pass | ≥ 0.85 | **PASS** |
| Revise | 0.70 – 0.84 | — |
| Fail | < 0.70 or automatic fail | — |

**Total: 1.00 / 1.00 — PASS**

---

## Automatic Fail Checklist

| Condition | Result |
|-----------|--------|
| Sanitizer still omits `requires_runtime_credentials` | ✅ Clear — present in `tests.py` L63 |
| GET after update `true` returns `false` | ✅ Clear — live `PUT true` → `GET true` on `#1406` |
| Passwords/credentials persisted to DB or `localStorage` | ✅ Clear — no password/username columns; LS keys only `token`,`user` |
| CRM auth redesign / scope creep | ✅ Clear — surgical sanitizer + SavedTests map + tests only |

---

## Per-Criterion Results

### Backend Sanitizer & API Round-Trip (0.40)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| B1 | Sanitizer key present | 0.12 | ✅ PASS | `sanitize_test_case_for_response` includes `'requires_runtime_credentials': getattr(...)` at `tests.py:63` |
| B2 | True round-trip | 0.12 | ✅ PASS | Live: create `#1406` → PUT `true` → GET `requires_runtime_credentials=True`; unit `test_update_then_get_preserves_true` |
| B3 | False round-trip | 0.06 | ✅ PASS | Live PUT `false` → GET `False`; UI OFF save → reload → checkbox unchecked |
| B4 | List includes field | 0.05 | ✅ PASS | GET list item for `#1406` returned `True` (not missing→default false) |
| B5 | Clone response honest | 0.05 | ✅ PASS | `POST /tests/1406/clone` → `#1407` with `requires_runtime_credentials=True` |

**Section score: 0.40 / 0.40**

### Security — Credentials Remain Ephemeral (0.20)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| S1 | No credential in DB | 0.08 | ✅ PASS | `PRAGMA table_info(test_cases)` — no password/username columns; row `#1406` JSON blobs have no `password` / `login_credentials` / `secret` |
| S2 | No credential in API body | 0.06 | ✅ PASS | GET `#1406` has boolean only; no `login_credentials` / `password` keys; unit `test_sanitize_response_has_no_credential_fields` |
| S3 | No localStorage secrets | 0.06 | ✅ PASS | After toggle save cycles, `localStorage` keys = `token`, `user` only; no password/credential blobs |

**Section score: 0.20 / 0.20**

### Frontend Persistence UX (0.25)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| F1 | Toggle survives navigate | 0.08 | ✅ PASS | Enable → Save Changes → Dashboard → Saved Tests → Edit `#1406` → checkbox **checked** |
| F2 | Toggle survives hard reload | 0.08 | ✅ PASS | Hard navigate `/tests/saved` → Edit `#1406` → checkbox **checked** (hydrate from API) |
| F3 | OFF still works | 0.04 | ✅ PASS | Uncheck → Save → hard reload → Edit → checkbox **unchecked** |
| F4 | SavedTests local map | 0.03 | ✅ PASS | `SavedTestsPage.tsx` post-save `setTests` includes `requires_runtime_credentials: editForm.requires_runtime_credentials` (L219) |
| F5 | Run consumes flag | 0.02 | ✅ PASS | Test Detail `#1406` with switch ON → **▶ Run Test** opens **CRM Login Required** modal (Username/Password). Cancelled without submitting |

**Section score: 0.25 / 0.25**

### Tests & E2E Expectations (0.15)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| T1 | Unit/API covers sanitize | 0.07 | ✅ PASS | `test_requires_runtime_credentials_sanitize.py` — sanitize true/false, no cred fields, PUT→GET, list, clone |
| T2 | CRM ephemeral still green | 0.03 | ✅ PASS | `test_crm_ephemeral_credentials.py` included in **38 passed** run |
| T3 | E2E / documented script | 0.05 | ✅ PASS | Rubric evaluator script executed live (API + browser); no new Playwright file (acceptable per rubric) |

**Section score: 0.15 / 0.15**

---

## E2E Checklist (rubric script)

| # | Step | Result |
|---|------|--------|
| 1 | Log in; open Saved Tests | ✅ `admin` / `admin123` → `/tests/saved` |
| 2 | Edit existing test | ✅ `#1406` edit drawer |
| 3 | Enable Requires CRM Login → Save | ✅ Save Changes |
| 4 | PUT response includes `true` | ✅ API + UI path |
| 5 | Soft navigate away → return → Edit → ON | ✅ F1 |
| 6 | Hard reload → Edit → ON | ✅ F2 |
| 7 | GET `/api/v1/tests/{id}` → `true` | ✅ |
| 8 | Run → credential prompt | ✅ via Test Detail `RunTestButton` |
| 9 | No password in localStorage | ✅ |
| 10 | Disable → Save → reload → OFF; GET false | ✅ F3 + API |
| 11 | Clone of `true` → clone `true` | ✅ `#1407` |
| 12 | Backend unit tests | ✅ 38 passed |

---

## Backend Tests Run

```text
cd backend && .\venv\Scripts\activate
python -m pytest tests/unit/test_requires_runtime_credentials_sanitize.py tests/unit/test_crm_ephemeral_credentials.py -q
→ 38 passed
```

---

## Non-Regression Notes

| Check | Status |
|-------|--------|
| Empty description sanitization still present | ✅ Still in `sanitize_test_case_for_response` (empty → placeholder strings) |
| Clone of `true` still returns `true` | ✅ Verified live + covered by sanitize tests |
| Feature 1 Stop / Feature 2 Clone API surfaces | ✅ Not broken by this change; clone used successfully |
| Scope remains surgical | ✅ No CredentialPrompt redesign, no migration, no credential persistence |

### Pre-existing observation (not a Feature 3 fail)

Saved Tests **list-row** green Play (`handleRunTest`) still calls `executionService.startExecution` directly and **does not** open `CredentialPromptModal`. Credential prompting is wired through `RunTestButton` (e.g. Test Detail). Out of scope for this feature; F5 verified on the existing RunTestButton path.

---

## Critical Issues (must fix)

*None.*

## Major Issues (should fix)

*None for Feature 3 merge.*

## Minor Issues (nice to fix)

1. **No Playwright journey** for toggle → save → reload — optional per rubric; T3 satisfied via evaluator script. Generator may add a focused E2E later.
2. **Saved Tests list Run bypasses credential modal** — pre-existing; if product wants parity with Test Detail, wire list Run through `RunTestButton` / check `requires_runtime_credentials` (separate ticket).

---

## What Improved Since Last Iteration

- Prior evaluator run was interrupted with **no** report; this run completed full rubric scoring.
- Sanitizer omission (root cause) is fixed and proven live.
- SavedTests post-save map includes the flag (Should-Have done).

## What Regressed Since Last Iteration

- None observed.

## Specific Suggestions for Next Iteration

1. Optional: add Playwright spec matching rubric F1/F2 (toggle → save → reload → assert `#saved-edit-requires-creds` checked).
2. Optional backlog: align Saved Tests list Run with `RunTestButton` credential gating (not part of Feature 3 DoD).

## Screenshots / Artifacts

- Edit drawer toggle ON: `crm-toggle-edit-drawer-on.png` (local screenshots folder)
- Credential modal: verified via accessibility snapshot — heading **CRM Login Required**, Username/Password fields present; cancelled without submit
- Live test IDs: `#1406` (source), `#1407` (clone)

---

## Verdict

**PASS — 1.00 / 1.00** (threshold 0.85)

Ready to merge for Feature 3.
