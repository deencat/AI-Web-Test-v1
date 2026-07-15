# Evaluation Report — CRM Login Toggle Persist (Feature 3)

**Date:** 2026-07-15  
**Feature:** Fix `requires_runtime_credentials` omitted by API sanitizer  
**Evaluator:** gan-evaluator  
**App URL:** http://localhost:5173  
**Backend:** http://127.0.0.1:8000  
**Spec:** `gan-harness/spec.md` § Feature 3  
**Rubric:** `gan-harness/eval-rubric-crm-login-toggle.md` (pass threshold ≥ 0.85)

---

## Executive Summary

Feature 3 is **implemented and verified**. Sanitizer includes `requires_runtime_credentials`; unit/API tests pass (38/38); live PUT→GET/list/clone round-trips succeed after backend reload with the new code; SavedTestsPage local map includes the flag; browser E2E confirms toggle survives navigate-away and hard reload, OFF persists after disable+save, and TestDetail `RunTestButton` shows the credential prompt when ON.

**Weighted score: 1.00 / 1.00 — PASS**

All automatic-fail conditions are clear. Credentials remain ephemeral (boolean only).

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
| Sanitizer still omits `requires_runtime_credentials` | ✅ Clear — key present in `sanitize_test_case_for_response` |
| GET after update `true` returns `false` | ✅ Clear — live PUT→GET `true` (test id 1405) after server reload |
| Passwords/credentials persisted to DB or `localStorage` | ✅ Clear — no credential columns; GET has boolean only; LS keys `token`/`user` only |
| CRM auth redesign scope creep | ✅ Clear — surgical sanitizer + SavedTests map + tests only |

---

## Per-Criterion Results

### Backend Sanitizer & API Round-Trip (0.40)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| B1 | Sanitizer key present | 0.12 | ✅ PASS | `tests.py` includes `'requires_runtime_credentials': getattr(...)` |
| B2 | True round-trip | 0.12 | ✅ PASS | Live: PUT `true` → GET `true` on id 1405; unit `test_update_then_get_preserves_true` |
| B3 | False round-trip | 0.06 | ✅ PASS | Live + unit: PUT `false` → GET `false` |
| B4 | List includes field | 0.05 | ✅ PASS | Live list item `requires_runtime_credentials: true`; unit `test_list_includes_flag` |
| B5 | Clone response honest | 0.05 | ✅ PASS | Live clone of `true` source returned `true` (id 1406); unit `test_clone_of_true_source_returns_true` |

**Section score: 0.40 / 0.40**

### Security — Credentials Remain Ephemeral (0.20)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| S1 | No credential in DB | 0.08 | ✅ PASS | `TestCase` columns: boolean only; unit asserts no `password`/`username`/`login_credentials` columns |
| S2 | No credential in API body | 0.06 | ✅ PASS | Live GET keys include `requires_runtime_credentials`; forbidden keys `NONE` |
| S3 | No localStorage secrets | 0.06 | ✅ PASS | `SavedTestsPage` has no storage writes; browser LS keys only `token`, `user` (no password fields) |

**Section score: 0.20 / 0.20**

### Frontend Persistence UX (0.25)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| F1 | Toggle survives navigate | 0.08 | ✅ PASS | Flag ON → leave → login/dashboard → `/tests/saved?edit=1405` → checkbox **checked** |
| F2 | Toggle survives hard reload | 0.08 | ✅ PASS | Hard reload edit URL → `#saved-edit-requires-creds` **checked=true** |
| F3 | OFF still works | 0.04 | ✅ PASS | Uncheck → Save → reload edit → **checked=false**; API `false` |
| F4 | SavedTests local map | 0.03 | ✅ PASS | Post-save `setTests` includes `requires_runtime_credentials: editForm.requires_runtime_credentials` |
| F5 | Run consumes flag | 0.02 | ✅ PASS | TestDetail `RunTestButton` → credential modal (`input[type=password]` present). Note: SavedTests **list** Run still calls `executionService.startExecution` directly (pre-existing; out of Feature 3 scope) |

**Section score: 0.25 / 0.25**

### Tests & E2E Expectations (0.15)

| ID | Criterion | Weight | Status | Evidence |
|----|-----------|--------|--------|----------|
| T1 | Unit/API covers sanitize | 0.07 | ✅ PASS | `test_requires_runtime_credentials_sanitize.py` — true/false sanitize + PUT→GET |
| T2 | CRM ephemeral tests green | 0.03 | ✅ PASS | `test_crm_ephemeral_credentials.py` green with sanitize suite: **38 passed** |
| T3 | E2E or evaluator script | 0.05 | ✅ PASS | Evaluator browser + API script executed (no committed Playwright for this feature; rubric allows evaluator script) |

**Section score: 0.15 / 0.15**

---

## E2E Checklist (Rubric Script)

| # | Step | Result |
|---|------|--------|
| 1 | Log in; open Saved Tests | ✅ Pass (`admin` / `admin123`) |
| 2 | Edit existing / created test | ✅ Pass (id 1405 `CRM Toggle Eval …`) |
| 3 | Enable Requires CRM Login → Save | ✅ Pass (API + UI) |
| 4 | PUT response includes `"requires_runtime_credentials": true` | ✅ Pass |
| 5 | Navigate away → return → Edit → ON | ✅ Pass |
| 6 | Hard-reload → Edit → ON | ✅ Pass |
| 7 | GET `/api/v1/tests/{id}` → `true` | ✅ Pass |
| 8 | Run → credential prompt | ✅ Pass on **TestDetail** (`RunTestButton`); list Run bypasses prompt (pre-existing) |
| 9 | No password in Local Storage from toggle/save | ✅ Pass |
| 10 | Disable → Save → reload → OFF; GET `false` | ✅ Pass |
| 11 | Optional clone of `true` → sanitized `true` | ✅ Pass (API) |
| 12 | Backend unit tests sanitize/ephemeral | ✅ Pass (38) |

**Passed: 12 / 12** (step 8 qualified: prompt via TestDetail path)

---

## Non-Regression Spot Checks

| Check | Result |
|-------|--------|
| Empty description sanitization still present | ✅ Sanitizer still rewrites empty `description` / `expected_result` |
| Clone still works | ✅ Clone endpoint returned 201 with flag parity |
| No new migration / column rename | ✅ Confirmed surgical change |
| Feature 1 Stop Execution | ✅ Not touched (out of this eval’s code paths) |

---

## Ops Note (Evaluator)

First live API check against an already-running backend returned `requires_runtime_credentials: false` while SQLite had `True` — process was serving **stale code** without the sanitizer line. After restarting `python start_server.py`, live round-trips matched unit tests. Implementation is correct; deploy/reload required for verification.

---

## Generator Gaps / Follow-ups

1. **No committed Playwright** for toggle → save → reload (Generator known issue; T3 satisfied via evaluator script).
2. **SavedTests list Run** does not use `RunTestButton` / CredentialPromptModal — pre-existing; out of Feature 3 scope. Consider wiring list Run to the same flag path in a later sprint.
3. Ensure backend is restarted after sanitizer deploy so staging/local don’t mask the fix.

---

## Verdict

**PASS — 1.00 / 1.00** (threshold ≥ 0.85)

Ready to merge from Feature 3 rubric perspective.
