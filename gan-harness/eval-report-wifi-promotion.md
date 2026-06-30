# Evaluation — Wi-Fi 6/7 Promotion Card Fix (Iteration 002)

**Date:** 2026-06-30  
**Evaluator:** GAN Evaluator (code-only mode)  
**Generator change:** `backend/app/services/tier2_hybrid.py` + `backend/tests/test_tier2_plan_selection.py`  
**Trigger:** Execution #983 — step instructed "click wifi6" but Tier 2 clicked Wi-Fi 7 plan card

---

## Verdict: **PASS**

All in-scope Wi-Fi 6/7 and three-tier unit tests pass. The fix is validated at the unit/integration layer. Live UAT E2E for Execution #983 was not re-run in this iteration (noted in generator-state).

---

## Test Run Summary

**Command:**
```bash
cd backend
.\venv\Scripts\activate
python -m pytest tests/test_tier2_plan_selection.py tests/test_three_tier_execution_service.py tests/test_three_tier_tab_verification.py -q --tb=short
```

**Result:** `87 passed`, `0 failed`, `3 warnings` (Pydantic deprecation), **46.09s**

| Test file | Collected | Passed | Failed |
|-----------|-----------|--------|--------|
| `tests/test_tier2_plan_selection.py` | 76 | 76 | 0 |
| `tests/test_three_tier_execution_service.py` | 4 | 4 | 0 |
| `tests/test_three_tier_tab_verification.py` | 7 | 7 | 0 |
| **Total (in-scope)** | **87** | **87** | **0** |

### Wi-Fi 6/7–specific tests (14 in `test_tier2_plan_selection.py`)

All **14 passed**:

| # | Test | Status |
|---|------|--------|
| 1 | `test_is_three_hk_promotion_card_click_true_for_wifi7_price_step` | PASS |
| 2 | `test_is_three_hk_promotion_card_click_true_for_wifi6_price_step` | PASS |
| 3 | `test_verify_promotion_card_accepts_wifi7_local_selected_state_without_hpprm` | PASS |
| 4 | `test_verify_promotion_card_accepts_wifi6_local_selected_state_without_hpprm` | PASS |
| 5 | `test_find_promotion_card_locator_matches_wifi7_price_without_hpprm` | PASS |
| 6 | `test_find_promotion_card_locator_matches_wifi6_price_without_hpprm` | PASS |
| 7 | `test_find_promotion_card_locator_rejects_shared_parent_with_wifi7_for_wifi6` | PASS |
| 8 | `test_verify_promotion_card_rejects_wifi7_snippet_for_wifi6_with_empty_cart_signals` | PASS |
| 9 | `test_instruction_matches_rejects_snippet_with_both_wifi_families_for_wifi6` | PASS |
| 10 | `test_snippet_has_contradictory_wifi_family_detects_wifi7_for_wifi6_step` | PASS |
| 11 | `test_validate_cached_xpath_rejects_wifi7_element_for_wifi6_instruction` | PASS |
| 12 | `test_validate_cached_xpath_accepts_wifi6_element_for_wifi6_instruction` | PASS |
| 13 | `test_execute_step_uses_direct_promotion_helper_for_wifi7_price_step` | PASS |
| 14 | `test_execute_step_uses_direct_promotion_helper_for_wifi6_price_step` | PASS |

---

## Out-of-Scope: Pre-Existing Logging Test Failures

**File:** `tests/test_execution_service_three_tier_logging.py`  
**Result:** `1 passed`, `4 failed` (not part of Wi-Fi fix pass criteria)

| Test | Failure |
|------|---------|
| `test_execute_step_passes_execution_id_to_three_tier_service` | Mock `assert_awaited_with` expects step dict **without** `expected_items` / `screenshot_region`; actual call includes both fields |
| `test_execute_step_extracts_windows_upload_path_from_step_description` | Same mock shape mismatch |
| `test_execute_step_extracts_quoted_windows_upload_path_with_spaces` | Same mock shape mismatch |
| `test_execute_step_preserves_posix_upload_path_from_step_description` | Same mock shape mismatch |

**Assessment:** Pre-existing test drift — `ExecutionService._execute_step` now forwards `expected_items: None` and `screenshot_region: 'viewport'` to `ThreeTierExecutionService.execute_step`. Not introduced by Wi-Fi 6/7 fix. Trivial fix would be updating mock expectations in the four tests; left out of scope per evaluator brief.

---

## Execution #983 — Scenario Evidence Map

Execution #983 reported: test step says **click Wi-Fi 6** (`$198/30 month`) but execution selected **Wi-Fi 7** (`$238/30 month`) on the Three HK promotion catalog page.

Architect root causes and corresponding unit-test evidence:

| #983 failure mode | Root cause (architect) | Unit test evidence | Result |
|-------------------|------------------------|-------------------|--------|
| Wi-Fi 6 step clicks Wi-Fi 7 card | Broad parent XPath matches container holding **both** Wi-Fi 6 and Wi-Fi 7 text | `test_find_promotion_card_locator_rejects_shared_parent_with_wifi7_for_wifi6` — shared parent rejected; smallest valid Wi-Fi 6 card selected | PASS |
| Step marked success despite wrong plan | Page-wide signals (Moneyback visible, footer ≠ $0) accepted without matching requested family | `test_verify_promotion_card_rejects_wifi7_snippet_for_wifi6_with_empty_cart_signals` — Wi-Fi 7 snippet rejected for Wi-Fi 6 instruction when cart was empty | PASS |
| Stale/wrong cached XPath reused | Cache path does not validate Wi-Fi family semantics | `test_validate_cached_xpath_rejects_wifi7_element_for_wifi6_instruction` | PASS |
| Correct Wi-Fi 6 targeting | Locator must resolve Wi-Fi 6 + `$198` without HPPRM code | `test_find_promotion_card_locator_matches_wifi6_price_without_hpprm` | PASS |
| Correct Wi-Fi 7 targeting (regression guard) | Locator must resolve Wi-Fi 7 + `$238` | `test_find_promotion_card_locator_matches_wifi7_price_without_hpprm` | PASS |
| Snippet contains opposite family | Instruction/snippet matcher must reject contradictory tokens | `test_instruction_matches_rejects_snippet_with_both_wifi_families_for_wifi6`, `test_snippet_has_contradictory_wifi_family_detects_wifi7_for_wifi6_step` | PASS |
| Post-click verification for plan switch | Local `selected` state + matching snippet required | `test_verify_promotion_card_accepts_wifi6_local_selected_state_without_hpprm`, `test_verify_promotion_card_accepts_wifi7_local_selected_state_without_hpprm` | PASS |
| Tier 2 routing for Wi-Fi price steps | `execute_step` must use direct promotion helper (not stale cache) | `test_execute_step_uses_direct_promotion_helper_for_wifi6_price_step`, `test_execute_step_uses_direct_promotion_helper_for_wifi7_price_step` | PASS |
| Promotion-card click detection | Wi-Fi 6/7 price instructions recognized as promotion-card clicks | `test_is_three_hk_promotion_card_click_true_for_wifi6_price_step`, `test_is_three_hk_promotion_card_click_true_for_wifi7_price_step` | PASS |
| Valid cache for correct family | Cached XPath for Wi-Fi 6 element accepted when instruction is Wi-Fi 6 | `test_validate_cached_xpath_accepts_wifi6_element_for_wifi6_instruction` | PASS |

**Gap:** No automated replay of Execution #983 against live `wwwuat.three.com.hk`. Unit tests mock DOM/locators. Recommend one manual or recorded UAT re-run of the failing step sequence before closing the incident.

---

## Implementation Evidence (generator-state)

Changes validated indirectly by passing tests:

- `_extract_three_hk_wifi_family` — family extraction from instruction
- `_pick_smallest_valid_promotion_card_locator` — rejects shared-parent containers
- `_snippet_has_contradictory_wifi_family` / tightened `_instruction_matches_three_hk_promotion_snippet`
- Tightened `_verify_three_hk_promotion_card_selected` for empty-cart vs plan-switch
- Wi-Fi-aware `_validate_cached_xpath_for_step` and plan-click retry predicates

---

## Scores (code-only rubric adaptation)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Functionality | 9/10 | All 87 in-scope tests pass; 14 Wi-Fi-specific scenarios covered |
| Regression safety | 8/10 | 62 non-Wi-Fi plan_selection tests still pass; logging tests drift unrelated |
| Test coverage vs #983 | 8/10 | Strong unit coverage of root causes; no live E2E replay |
| Scope discipline | 9/10 | Surgical change to `tier2_hybrid.py` + targeted tests |

**Weighted (functionality-heavy):** **8.5/10** — PASS for generator iteration gate.

---

## Recommendations for Next Iteration

1. **Replay Execution #983** on UAT with the fixed backend and confirm Wi-Fi 6 card selection in screenshots/logs.
2. **Fix logging test drift** — update four mocks in `test_execution_service_three_tier_logging.py` to expect `expected_items` and `screenshot_region` in the step dict (trivial, ~4-line change per test).
3. **Optional:** Add one integration test with fixture HTML containing side-by-side Wi-Fi 6/7 cards if Playwright fixture harness exists.

---

## Files

| File | Role |
|------|------|
| `gan-harness/eval-report-wifi-promotion.md` | This report (NEW) |
| `gan-harness/eval-report.md` | Prior ADR-007 report — **not modified** |
| `gan-harness/generator-state.md` | Generator iteration 002 notes |
