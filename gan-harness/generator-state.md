# Generator State — Iteration 004

## What Was Built
- Fixed payment helper regression: `test_execute_action_with_xpath_waits_for_popup_login_loading_to_clear` expects `timeout=20000` (matches `post_click_readiness`)
- New 3-tier integration suite: `backend/tests/test_three_tier_registration_widgets.py` (6 tests)
- E2E re-run script: `backend/scripts/run_exec990_rerun.py` for test case **1399** (Exec #990 equivalent)

## What Changed This Iteration
- **P0-1:** Payment helper timeout aligned — `test_tier2_payment_helpers.py` all pass
- **P0-2:** 3-tier integration tests route through `ThreeTierExecutionService` + `ExecutionService._execute_step`:
  - Tier 1 miss → Tier 2 custom dropdown (no Tier 3)
  - Tier 1 miss → Tier 2 date picker (no Tier 3)
  - Tier 1 miss → anchor cache invalidation + augmented observe retry
  - Tier 2 verification failure → Tier 3 escalation (option_c)
  - Tier 2+3 both fail → no false PASS
  - ExecutionService dispatch to three-tier for `select area 'Hong Kong'`
- **P0-3:** OGP-PPD E2E re-run triggered for test case 1399 (`base_url=https://web.three.com.hk`) — see E2E section below

## Test Results (iteration 004 verify)

```bash
python -m pytest tests/test_execution_service_value_extraction.py \
  tests/test_tier2_registration_widgets.py \
  tests/test_three_tier_registration_widgets.py \
  tests/test_tier2_plan_selection.py \
  tests/test_tier2_payment_helpers.py -q
→ 195 passed, 0 failed
```

## E2E Re-run (OGP-PPD Sales Portal — test case 1399)

| Field | Value |
|-------|-------|
| Source execution | #990 |
| Test case ID | 1399 |
| Test case title | Subscribe 5GBB Plan Successfully via 3 Website Sales Portal |
| Base URL | `https://web.three.com.hk` |
| Key rubric steps | 14 (eye), 24 (+3 after birth), 36 (+2 after area) |

**Pre-fix Exec #990 key steps (baseline):**
- Step 14: `Click eye button next to 'Collect Personal Info'` — PASS (false; sidebar opened)
- Step 23: `Input Birth date '2000/01/01'`
- Step 35: `select area 'Hong Kong'`

**Post-fix re-run:** See `E2E_EXEC_ID` and screenshot paths below after poll completes.

## Known Issues
- Live E2E may be blocked by network/proxy to Three HK OGP-PPD or long runtime (~30+ min for full case)
- F6 (generic post-fill verification for all registration fields) deferred
- ADR-002-53 documentation deferred (P2)

## Dev Server
- URL: http://127.0.0.1:8000
- Status: running
- Command: \cd backend && python start_server.py\n