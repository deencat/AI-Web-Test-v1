# Generator State — Iteration 004

## What Was Built (continued from 003)
- **Iteration 003:** F1–F4 handlers in `execution_service.py` + `tier2_hybrid.py`; 15 unit tests in `test_tier2_registration_widgets.py`
- **Iteration 004:** 6 integration tests in `test_three_tier_registration_widgets.py` (ThreeTierExecutionService + ExecutionService dispatch)
- **Regression fix:** `test_execute_action_with_xpath_waits_for_popup_login_loading_to_clear` timeout aligned to 20000ms

## What Changed This Iteration
- Added 3-tier integration coverage: Tier 1 miss → Tier 2 dropdown/date/anchor paths; Tier 2 fail → Tier 3 escalation; all-tiers-exhausted no false PASS
- Fixed interrupted iteration test failures (mock page locators, `_execute_step` dispatch, tier3 result shape)
- Full spec regression suite: **195/195 pass**

## Test Results
```bash
pytest tests/test_execution_service_value_extraction.py \
       tests/test_tier2_registration_widgets.py \
       tests/test_three_tier_registration_widgets.py \
       tests/test_tier2_plan_selection.py \
       tests/test_tier2_payment_helpers.py -q
→ 195 passed
```

## 3-Tier Coverage (registration widgets)
| Tier | Coverage | Tests |
|------|----------|-------|
| Tier 1 | Miss path via mocked tier1 failure | 4 tests |
| Tier 2 | Real Tier2HybridExecutor + handler mocks | 4 tests |
| Tier 3 | Escalation on Tier 2 verification failure | 2 tests |
| Dispatch | ExecutionService → ThreeTierExecutionService | 1 test |

## E2E Status
- **Target:** test_case_id **1399** (same as Exec #990)
- **Note:** Test case steps updated since Exec #990 (step 14 is now HKID upload; birth date step 20; area dropdown step 32 with explicit "dropdown" phrasing)
- **Live re-run:** Attempted via API — requires OAuth2 login + OGP-PPD portal access (long-running ~49 steps)
- **Prior live runs:** Exec #992/#993 on different public registration flow showed birth-date handler working at Tier 2

## Known Issues
- OGP-PPD Sales Portal E2E not completed in this iteration (49-step run needs manual trigger + ~30+ min)
- Eye-button step no longer in current test case 1399 steps (replaced by HKID upload flow)
- Generic post-fill verification warn-only for non-date fields (F6 deferred)

## Dev Server
- URL: http://127.0.0.1:8000 (backend)
- Status: running
- Command: `cd backend && python start_server.py`
