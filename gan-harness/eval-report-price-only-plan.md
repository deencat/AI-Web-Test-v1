# Evaluation — Price-Only Plan Click (`Click $228 / 36 month plan`)

**Date:** 2026-07-21 (iteration 2 re-verify)  
**Evaluator:** gan-evaluator  
**Scenario:** Test Case #1417 (Sales Portal plan select); baseline Execution #1154  
**Generator change:** `backend/app/services/tier2_hybrid.py` → `_extract_three_hk_promotion_text_variants` fallback `("plan",)` (+ optional `"monthly plan"`)  
**Unit regression:** `tests/test_tier2_plan_selection.py::TestThreeHkPromotionCardDirectClick::test_is_three_hk_promotion_card_click_true_for_price_only_plan_step`

---

## Verdict: **FAIL** (live Tier-2 direct-click still not proven)

| Gate | Result |
|------|--------|
| Unit classification for price-only plan step | **PASS** (re-verified) |
| Live e2e plan click on authenticated select-plan page via **Tier 2 direct promotion handler** | **FAIL** (not observed; blocked by missing CRM SSO credentials) |
| Plan step not misclassified as dropdown/wait | **PASS** (unit) |
| Harness “100% coverage” on changed surface | **NOT MET** (see Coverage) |

Automatic concern unchanged: unauthenticated / wrong-page runs still produce Tier 3 “PASS” while screenshots show blank or nginx 404 pages. Do not treat those as plan-click proof.

---

## Iteration 2 (this run)

### 1) Unit re-verification

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/test_tier2_plan_selection.py -q
# → 77 passed, 0 failed (~24s)
python -m pytest tests/test_tier2_plan_selection.py -k "price_only" -vv
# → 1 passed (price-only regression)
```

Artifacts:
- `gan-harness/_eval_artifacts/pytest_price_only_plan_iter2.txt`
- `gan-harness/_eval_artifacts/pytest_price_only_k_filter_iter2.txt`

Classification gate remains green. No product code changes by evaluator.

### 2) Coverage (re-run)

```bash
python -m pytest tests/test_tier2_plan_selection.py \
  --cov=app.services.tier2_hybrid \
  --cov-report=json:gan-harness/_eval_artifacts/coverage_price_only_plan_iter2.json -q
# → 77 passed
```

| Scope | Cover | Notes |
|-------|-------|-------|
| `tier2_hybrid.py` (whole module) | **34.1%** | Unchanged ballpark (~34%) |
| `_extract_three_hk_promotion_text_variants` L1231–1255 | **24/25 stmts (96.0%)** | Missing **L1253** (`"monthly plan"` append) |

Artifact: `gan-harness/_eval_artifacts/coverage_price_only_plan_iter2.json`, `pytest_cov_iter2.txt`

### 3) Credential gate

| Check | Result |
|-------|--------|
| `AWT_LOGIN_CREDS_JSON` (process env) | **unset** |
| `backend/.env` keys `AWT_LOGIN` / `LOGIN_CREDS` | **none** |
| Evaluator invented creds? | **No** |

Artifact: `gan-harness/_eval_artifacts/creds_blocker_iter2.txt`

### 4) API verification (backend up)

- `http://127.0.0.1:8000` — **up** (OpenAPI 200)
- Login: OAuth2 form `username=admin` / `password=admin123`
- TC 1417 re-fetched: `requires_runtime_credentials=true`, plan step = **step 6** (`Click $228 / 36 month plan`)
- Recent executions for TC 1417: 1166 (cancelled, 5 steps), 1164, 1156 (completed), 1154 (cancelled)

Plan-step tier summary (API `GET /executions/{id}` → `steps`):

| Exec | Status | Plan step | Tier at plan step | Live Tier-2 proof? |
|------|--------|-----------|-------------------|-------------------|
| 1154 | cancelled | 9 | **Tier 3** | No (pre-fix baseline; real catalog screenshot) |
| 1156 | completed | 6 | **Tier 3** | No |
| 1164 | cancelled | 6 | **Tier 3** | No (SSO false positive) |
| 1166 | cancelled | — (never reached) | — | No |

Artifact: `gan-harness/_eval_artifacts/tc1417_iter2.json`, `ex1417_recent_iter2.json`, `ex1166_iter2.json`, `plan_step_summary_iter2.json`

### 5) Live e2e attempt (TC 1417)

**NOT attempted** this iteration — blocked by missing CRM SSO credentials (see §3). Prior exec 1166 evidence still stands; no new run started.

---

## Prior iteration (continue eval)

### Live e2e attempt (TC 1417) — exec 1166

| Fact | Value |
|------|--------|
| Backend | `http://127.0.0.1:8000` up (`/api/v1/openapi.json` title AI Web Test) |
| TC 1417 | `requires_runtime_credentials: true` |
| `AWT_LOGIN_CREDS_JSON` | **unset** (process env + `.env` grep: none) |
| Evaluator action | Did **not** invent CRM SSO credentials |
| Run | `POST /api/v1/executions/tests/1417/run` with `base_url=https://web.three.com.hk`, `triggered_by=gan-evaluator-price-only-plan-continue` → **exec 1166** |

**Exec 1166 outcome:**

- Reached steps 1–5 only; cancelled after ~5 min poll before step 6 (`Click $228 / 36 month plan`).
- Steps 2–5 reported Tier 3 “success” while screenshots are invalid for CRM UI:
  - `exec_1166_step_2_pass.png` … step 4: blank gray frames (~4KB)
  - `exec_1166_step_5_pass.png`: nginx **404 Not Found**
- Log for step 4 observe URL stayed on portal root `https://sales-portal-ogp-crm.apps.ocpppd.three.com.hk/` (no select-plan catalog).
- Therefore: **Tier-2 direct promotion click was not exercised live** this iteration.

Artifacts: `ex_continue_start.json`, `ex1166_continue.json`, `ex1166_steps.json`, screenshots under `backend/screenshots/exec_1166_*`.

### 3) Prior live evidence (still stands)

| Exec | Plan step | Notes |
|------|-----------|-------|
| **1154** (pre-fix baseline) | Tier **3** PASS on real select-plan + `$228` card | Not the new Tier-2 path |
| **1156 / 1164** (post-fix) | Tier **3** PASS on **RHS SSO login** | Guard `host_match=False page_match=False`; false confidence |
| **1166** (continue) | Plan step **never reached** | False Tier-3 PASS on blank/404 earlier steps; no creds |

---

## What the fix is supposed to do

Pre-fix: wifi6/wifi7-only variant extraction returned `()` for `Click $228 / 36 month plan`, so `_is_three_hk_promotion_card_click` stayed false and Tier 2 fell through to observe → Tier 3.

Post-fix (unit-proven):

- variants include `"plan"` for price-only plan wording
- with UAT/CRM page match, `_is_three_hk_promotion_card_click(...)` is **True**
- `"monthly plan"` phrase also appends that variant (branch L1253; still untested in suite)

---

## Coverage vs “100%”

From `gan-harness/_eval_artifacts/coverage_price_only_plan_iter2.json` (iteration 2 re-run):

| Scope | Cover | Notes |
|-------|-------|-------|
| `app/services/tier2_hybrid.py` (whole module) | **34.1%** | Not a meaningful “100%” target for this fix |
| `_extract_three_hk_promotion_text_variants` (L1231–1255) | **96.0%** (24/25 stmts); missing **L1253** | Honest nearest metric to “changed surface” |
| Strict 100% on helper | **NOT MET** | Add unit for `"Click $228 monthly plan"` → `("plan", "monthly plan")` |

**Honest answer to “100% coverage” request:** whole-module 100% is unrealistic here; function-level is **96%** with one miss on the `"monthly plan"` append branch (L1253).

---

## Scores (adapted)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Unit functionality (classification gate) | 8/10 | Re-verified green (iter2); L1253 monthly-plan untested |
| Live Tier-2 direct plan click | 2/10 | Still not demonstrated; creds blocked; all plan steps Tier 3 |
| Coverage honesty vs 100% ask | 5/10 | 96% fn / 34.1% module; L1253 gap documented |
| Scope discipline | 9/10 | Surgical generator change; evaluator report-only |

**Weighted (functionality-heavy):** **~4.9/10** — **FAIL** for merge-on-e2e-proof gate. Unit-only gate would be PASS.

**Live e2e attempted this iteration:** **No** (credential blocker).

---

## Critical issues (must fix before claiming e2e success)

1. **Authenticated re-run required:** Supply CRM SSO via UI ephemeral `login_credentials` or `AWT_LOGIN_CREDS_JSON` (do not invent). Re-run TC 1417 until browser is on `.../select-plan` with Featured Monthly Plans / `$228` visible.  
   → Success evidence: guard `page_match=True` (or UAT host), **Tier 2** `actual_result` for the plan step (not Tier 3), preferably cart ≠ `$ 0` after click + catalog screenshot.

2. **Do not trust Tier-3 PASS without screenshot/URL proof:** Exec 1166 steps 2–5 and prior 1164 plan step are false positives (blank/404/SSO).

## Major issues

1. **Coverage gap L1253:** No unit hits `"monthly plan"` append.
2. **Whole-module 100%** is the wrong bar for this change; measure the helper (or add a focused cov target).

## Minor

1. Blind Tier-3 success on empty/404 pages continues to waste eval time before the plan step.
2. Exec 1166 cancel after partial progress is expected under no-creds policy.

---

## Specific suggestions for Generator / next iteration

1. Provide credentials (or a seeded browser profile with valid OIDC session) and re-run TC 1417; attach plan-step screenshot + guard log proving Tier 2 direct handler.
2. Add unit: `_extract_three_hk_promotion_text_variants("Click $228 monthly plan") == ("plan", "monthly plan")`.
3. Optional hardening: fail closed when instruction is price+plan but page is SSO/login/404 instead of Tier-3 “success.”
4. On CRM select-plan, confirm `_looks_like_three_hk_promotion_page` sees “Featured Monthly Plans” so `page_match=True` after auth.

---

## Artifacts

| Path | Role |
|------|------|
| `gan-harness/eval-report-price-only-plan.md` | This report |
| `gan-harness/_eval_artifacts/pytest_price_only_plan_iter2.txt` | Iter2 unit suite (77 passed) |
| `gan-harness/_eval_artifacts/pytest_price_only_k_filter_iter2.txt` | Iter2 price_only k-filter (1 passed) |
| `gan-harness/_eval_artifacts/coverage_price_only_plan_iter2.json` | Iter2 pytest-cov (34.1% module; L1253 miss) |
| `gan-harness/_eval_artifacts/creds_blocker_iter2.txt` | Credential gate — unset, no live run |
| `gan-harness/_eval_artifacts/plan_step_summary_iter2.json` | Plan-step tier summary 1154/1156/1164/1166 |
| `gan-harness/_eval_artifacts/tc1417_iter2.json` | TC 1417 API re-fetch |
| `gan-harness/_eval_artifacts/ex1166_iter2.json` | Exec 1166 full steps (cancelled at 5) |
| `gan-harness/_eval_artifacts/pytest_price_only_plan_continue.txt` | Prior continued unit re-run |
| `gan-harness/_eval_artifacts/coverage_price_only_plan.json` | Prior pytest-cov JSON |
| `gan-harness/_eval_artifacts/ex1166_steps.json` | Continue-run steps 1–5 (false Tier-3 PASS) |
| `gan-harness/_eval_artifacts/ex1164_plan_step.json` | Post-fix false Tier-3 PASS on SSO |
| `gan-harness/_eval_artifacts/ex1154_plan_step.json` | Baseline Tier-3 on real catalog |
| `backend/screenshots/exec_1166_step_5_pass.png` | nginx 404 (invalid “pass”) |
| `backend/screenshots/exec_1154_step_9_pass.png` | Real catalog + `$228` card |
| `backend/logs/server_20260721.log` | Guard / URL / exec 1166 evidence |
