# Generator State — Iteration 002 (Three HK HPPRM observe fix)

## Root cause (exec #967, #971)
- Catalog DOM readiness waits were insufficient: `observe()` accessibility tree omitted plan cards even when Playwright DOM had `HPPRM…` visible.
- Tier 3 treated empty `act()` responses as success.
- Cached checkout XPath proceeded with cart `$ 0`.

## What Was Built (ADR-002-50)
- `_try_three_hk_promotion_card_click()` — direct Playwright HPPRM card click before cache/observe
- `_try_three_hk_moneyback_panel_click()` — direct Moneyback panel click
- Checkout guard when footer cart is still `$ 0` on Three HK UAT
- Tier 3 fails `click` when `act()` returns empty elements
- ADR-002-50 documented in `documentation/ADR-002-test-execution-engine.md`

## Files changed
- `backend/app/services/tier2_hybrid.py`
- `backend/app/services/tier3_stagehand.py`
- `backend/tests/test_tier2_plan_selection.py`
- `documentation/ADR-002-test-execution-engine.md`

## Verification
- `python -m pytest tests/test_tier2_plan_selection.py -q` — 48 passed

## Required for live re-test
- **Restart backend** (`python start_server.py`) so Tier 2 code loads
- Re-run the failing test case (same flow as exec #971)
- Expect logs: `Clicked Three HK promotion card HPPRM0000002896` (Tier 2, no observe for that step)
