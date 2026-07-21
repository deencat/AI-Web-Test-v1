# Evaluation — Iteration price-only-plan-continue (iteration 2)

**Date:** 2026-07-21  
**Evaluator:** gan-evaluator  
**Scenario:** TC 1417 step 6 — `Click $228 / 36 month plan`  
**Live e2e attempted:** **No** (credential blocker)

## Scores

| Criterion | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Design Quality | N/A (backend classification fix) | 0.3 | — |
| Originality | N/A | 0.2 | — |
| Craft | 7/10 | 0.3 | 2.1 |
| Functionality | 5/10 | 0.2 | 1.0 |
| **Adapted TOTAL (unit+live+coverage)** | | | **~4.9/10** |

## Verdict: FAIL (threshold: live Tier-2 proof; unit-only would PASS)

## Critical Issues (must fix)
1. **[No CRM SSO credentials]:** `AWT_LOGIN_CREDS_JSON` unset; `backend/.env` has no login-creds keys → Provide `login_credentials` / `AWT_LOGIN_CREDS_JSON` and re-run TC 1417 until browser is on select-plan with `$228` visible. Success = **Tier 2** `actual_result` on step 6 + catalog screenshot (not Tier 3 on SSO/404).
2. **[False Tier-3 PASS persists]:** Exec 1166 steps 2–5 “pass” on blank/404; exec 1164 plan step Tier 3 on SSO page → Fail closed on SSO/404 for plan flows; never treat as e2e proof.

## Major Issues
1. **[L1253 untested]:** `"monthly plan"` branch miss at L1253 → Add unit asserting `_extract_three_hk_promotion_text_variants("Click $228 monthly plan") == ("plan", "monthly plan")`.
2. **[No Tier-2 live proof]:** All plan-step executions (1154 step 9, 1156/1164 step 6) report **Tier 3** — fix path never exercised in browser.

## Minor Issues
1. Whole-module coverage 34.1% — wrong bar; measure helper (96% on L1231–1255).
2. Exec 1166 cancelled at 5/50 steps — expected under no-creds policy.

## What Improved Since Last Iteration
- Unit suite re-confirmed green (77 passed; price-only k-filter 1 passed).
- Coverage re-measured with fresh JSON artifact (96% on changed helper).
- API re-verified TC 1417 + execution history; plan-step tier table documented.

## What Regressed Since Last Iteration
- None in product code (evaluator report-only). Live proof still absent.

## Specific Suggestions for Next Iteration
1. Supply CRM SSO credentials; run `POST /api/v1/executions/tests/1417/run` with `base_url` + `login_credentials`; poll until step 6 completes with Tier 2 actual_result.
2. Add monthly-plan variant unit test (close L1253).
3. Optional hardening: reject Tier-3 success when page is login/404 for price+plan instructions.

## Artifacts (iteration 2)
- `gan-harness/_eval_artifacts/pytest_price_only_plan_iter2.txt`
- `gan-harness/_eval_artifacts/pytest_price_only_k_filter_iter2.txt`
- `gan-harness/_eval_artifacts/coverage_price_only_plan_iter2.json`
- `gan-harness/_eval_artifacts/creds_blocker_iter2.txt`
- `gan-harness/_eval_artifacts/plan_step_summary_iter2.json`
- `gan-harness/_eval_artifacts/tc1417_iter2.json`
- `gan-harness/_eval_artifacts/ex1166_iter2.json`

## Screenshots (prior runs; no new captures)
- `backend/screenshots/exec_1154_step_9_pass.png` — real catalog + `$228` card (Tier 3)
- `backend/screenshots/exec_1164_step_6_pass.png` — SSO login false positive (Tier 3)
- `backend/screenshots/exec_1166_step_5_pass.png` — nginx 404 (invalid “pass” before plan step)
