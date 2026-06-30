# Generator State — Iteration 002

## What Was Built
- Wi-Fi 6/7 family targeting for Three HK promotion card clicks in `tier2_hybrid.py`
- Smallest-card locator selection with contradictory-family rejection
- Tightened post-click verification for empty-cart vs plan-switch cases
- Wi-Fi-aware plan-click retry and cached XPath semantic validation
- Six new unit tests in `test_tier2_plan_selection.py`

## What Changed This Iteration
- Fixed: wifi6 step clicking wifi7 due to broad parent XPath and page-wide verification
- Added: `_extract_three_hk_wifi_family`, snippet validation helpers, smallest-card picker
- Tightened: empty-cart progress signals require matching snippet or footer text
- Tightened: plan switches require local selected state matching instruction
- Retry: wifi6/wifi7 XPath predicates; blind first Select only when no wifi family

## Known Issues
- HPPRM-only locator paths unchanged (not part of wifi6/wifi7 bug)
- No live UAT E2E run in this iteration

## Dev Server
- URL: http://127.0.0.1:8000 (backend) / http://localhost:5173 (frontend)
- Status: not started this iteration
- Command: `cd backend && python start_server.py`
