# Evaluation Report: Exec #990 Registration Form Execution Fixes

**Evaluator:** GAN Evaluator  
**Date:** July 2, 2026  
**Iteration:** Generator 003  
**Spec:** `gan-harness/spec.md`  
**Rubric:** `gan-harness/eval-rubric.md`

---

## Verdict: **FAIL** (0.35 / 1.00)

Unit tests for F1–F4 handlers pass, but the **target OGP-PPD Sales Portal registration flow was not re-run post-fix**. The three reported Exec #990 failures remain unverified on the correct test case. Regression suite has 1 failing test. **Not ready to merge.**

---

## Overall Weighted Score

```
score = Σ (criterion_weight × pass?1:0)
```

| Category | Weight | Earned | Notes |
|----------|--------|--------|-------|
| Functionality (F1–F3) | 0.40 | 0.00 | No post-fix OGP-PPD E2E proof |
| Execution Engine (E1–E4) | 0.30 | 0.22 | Parsing/validation/cache unit-tested only |
| Craft / Tests (C1–C3) | 0.20 | 0.13 | New tests pass; regression suite fails |
| Evidence (V1–V2) | 0.10 | 0.00 | No post-fix OGP-PPD screenshots/logs |
| **Total** | **1.00** | **0.35** | Threshold ≥ 0.85 |

**Band:** Fail (< 0.70)

---

## Automatic Fail Checks

| Condition | Triggered? | Evidence |
|-----------|------------|----------|
| Any of three reported issues reproduces on re-run | **Unknown** | No post-fix re-run of OGP-PPD Exec #990 equivalent test case |
| Post-fix run marks failing steps PASS | **N/A** | No post-fix run on target test case; pre-fix Exec #990 still shows false PASS at steps 14, 23, 35 with broken UI |

Pre-fix Exec #990 demonstrates the false-PASS problem the rubric guards against:

| Step | DB Result | Tier | Screenshot Reality |
|------|-----------|------|-------------------|
| 14 (eye) | PASS | 3 | Sidebar nav opened (`exec_990_step_14_pass.png`); hamburger, not ID capture |
| 23 (birth date) | PASS | 2 | Field empty + "Required" at step 24 (`exec_990_step_24_pass.png`) |
| 35 (area) | PASS | 2 | "Select an Area" + Required at step 36 (`exec_990_step_36_pass.png`) |

LLM log `exec_990.jsonl` L5: observe for eye step returns element_id **67** — *"Eye icon button near the **top controls**"* (wrong target).

---

## Per-Criterion Results

### Functionality (0.40)

| ID | Criterion | Weight | Pass | Evidence |
|----|-----------|--------|------|----------|
| F1 | Eye button click | 0.12 | ❌ | No post-fix OGP-PPD run. Exec #992/#993 are a different test case (5G Handset public registration); steps 13–14 are "Confirm subscription", not eye icon. Pre-fix `exec_990_step_14_pass.png` shows sidebar opened. |
| F2 | Birth date persistence | 0.14 | ❌ | Rubric requires OGP-PPD flow: `2000/01/01` after step + 3 subsequent steps. Pre-fix step 24 shows empty field. Exec #992 step 27→30 shows `2000/1/1` persisted on **public** registration UI (Tier 2), but this is not the target Sales Portal widget. Exec #993 step 24 briefly showed `2008/1/1` before step 27 correction. |
| F3 | Area dropdown selection | 0.14 | ❌ | Pre-fix `exec_990_step_36_pass.png`: "Select an Area" + Required. Exec #992/#993 have **no** `select area 'Hong Kong'` step (grep DB: no area/eye steps). |

### Execution Engine Quality (0.30)

| ID | Criterion | Weight | Pass | Evidence |
|----|-----------|--------|------|----------|
| E1 | Step parsing | 0.06 | ✅ | `test_execution_service_value_extraction.py`: `"select area 'Hong Kong'"` → `True` + value `Hong Kong`. Plan click regression preserved. |
| E2 | Tier 2 handles widgets | 0.08 | ❌ | Unit tests mock Tier 2 handlers only. No live proof that OGP-PPD birth-date or Area steps complete at Tier 2 without Tier 3. Pre-fix: step 14 used Tier 3 and still failed visually. |
| E3 | Post-action verification | 0.08 | ✅ | `_fill_date_picker_field` rejects wrong calendar month; `_try_custom_dropdown_select` verifies display text; click anchor raises `ValueError`. Covered in `test_tier2_registration_widgets.py`. |
| E4 | Cache safety | 0.08 | ✅ | `test_validate_cached_xpath_rejects_bad_click_anchor`, `test_execute_step_augments_observe_after_anchor_cache_rejection` — cache invalidation + augmented observe with "NOT header/nav". |

### Craft / Tests (0.20)

| ID | Criterion | Weight | Pass | Evidence |
|----|-----------|--------|------|----------|
| C1 | Unit tests added | 0.08 | ✅ | `test_execution_service_value_extraction.py` (+3 terse phrasing cases); `test_tier2_registration_widgets.py` (15 tests, new file). **39/39 pass.** |
| C2 | No regressions | 0.07 | ❌ | `test_tier2_plan_selection.py` + `test_tier2_payment_helpers.py`: **149 passed, 1 failed**. Failure: `test_execute_action_with_xpath_waits_for_popup_login_loading_to_clear` — expects `timeout=8000`, implementation uses `20000`. Pre-existing per generator; rubric requires all pass. |
| C3 | Surgical diff | 0.05 | ✅ | Changes confined to `execution_service.py` (+27), `tier2_hybrid.py` (+453), tests, `generator-state.md`. No frontend/unrelated refactors. |

### Evidence (0.10)

| ID | Criterion | Weight | Pass | Evidence |
|----|-----------|--------|------|----------|
| V1 | Screenshots | 0.05 | ❌ | No post-fix `exec_*_step_14_pass.png` on OGP-PPD Sales Portal without sidebar. No post-fix step 24/36 area evidence on target flow. |
| V2 | LLM log | 0.05 | ❌ | No post-fix observe log for eye step on OGP-PPD. Only `exec_990.jsonl` exists for that flow; description still says "top controls". |

---

## Test Command Outputs

### Registration widget unit tests (required)

```bash
cd backend && .\venv\Scripts\activate
python -m pytest tests/test_execution_service_value_extraction.py tests/test_tier2_registration_widgets.py -q
```

```
39 passed, 16 warnings in 6.50s
```

### Regression suite (required)

```bash
python -m pytest tests/test_tier2_plan_selection.py tests/test_tier2_payment_helpers.py -q
```

```
149 passed, 1 failed in 24.85s

FAILED tests/test_tier2_payment_helpers.py::TestTier2PaymentHelpers::
  test_execute_action_with_xpath_waits_for_popup_login_loading_to_clear
  assert any(call.kwargs == {"state": "hidden", "timeout": 8000} ...)
```

---

## E2E Findings

### Blocker: Wrong test case for post-fix validation

Generator state explicitly notes: **"No live Exec #990 re-run in this iteration."**

Post-fix live runs (Exec #992, #993) target a **different test case**:

| | Exec #990 (target) | Exec #992 / #993 (post-fix runs) |
|--|-------------------|----------------------------------|
| UI | OGP-PPD Sales Portal agent flow | Public 5G Handset Voucher consumer registration |
| Step 14 | `Click eye button next to 'Collect Personal Info'` | `Click the 'Confirm' button...` |
| Step 35 | `select area 'Hong Kong'` | `sign the contract under Subscriber's signature` |
| Birth date step | Step 23 | Step 27 (`Input data of birth 2000/01/01`) |

### 3-tier execution coverage for registration widget handlers

**Not met.** Requested "100% test coverage for 3-tier execution" is **not satisfied**:

| Tier | Registration widget coverage | Evidence |
|------|------------------------------|----------|
| Tier 1 | ❌ None | No tests route birth/date/area/anchor through Tier 1 Playwright |
| Tier 2 | ✅ Unit mocks only | 15 tests call `Tier2HybridExecutor` methods directly with `MagicMock` pages |
| Tier 3 | ❌ None | No tests verify Tier 3 fallback behavior for these widgets |

`ThreeTierExecutionService` integration path is untested for F1–F4 handlers.

### Ancillary E2E observations (Exec #992 / #993, non-target flow)

| Step | Description | Tier | Observation |
|------|-------------|------|-------------|
| 27 | Input birth date 2000/01/01 | 2 | Calendar navigated to Jan 2000; field shows `2000/1/1` (`exec_992_step_27_pass.png`, `exec_993_step_27_pass.png`) |
| 30 | +3 steps after birth | 2 / 3 | Exec #992: birth date still `2000/1/1` on form (`exec_992_step_30_pass.png`). Exec #993: navigated to payment page (`exec_993_step_30_pass.png`) — field not visible |
| 13–14 | Confirm buttons | 2 | Mobile number modal (`exec_992_step_14_pass.png`) — unrelated to eye-button fix |
| Area | N/A | — | Test case has no billing-address Area step |

### Pre-fix baseline (Exec #990) — issues confirmed

| Issue | Step | Tier | Screenshot | LLM |
|-------|------|------|------------|-----|
| Eye → hamburger | 14 | 3 | Sidebar with "Direct Input Order" visible | L5: element_id 67, "top controls" |
| Birth date lost | 23→24 | 2 | Step 24: empty + Required | No LLM log for birth step |
| Area not selected | 35→36 | 2 | Step 36: "Select an Area" + Required | L7: observe returns dropdown **trigger** only |

---

## What Improved Since Baseline

- Terse dropdown parsing (`select area 'Hong Kong'`) with unit tests
- Tier 2 handlers: `_try_custom_dropdown_select`, `_fill_date_picker_field`, `_validate_click_target_for_instruction`
- Cache invalidation + augmented observe retry on anchor rejection
- Birth date handler works on **public** registration UI at Tier 2 (Exec #992/#993 step 27) — suggests handler logic is sound but unproven on OGP-PPD widgets

## What Did Not Improve / Gaps

- No OGP-PPD Sales Portal re-run — the actual failing environment
- Eye-button and Area dropdown fixes have **zero** live E2E validation
- False-PASS problem on Exec #990 steps 14/23/35 not re-tested post-fix
- 3-tier integration coverage missing
- Regression test still failing (payment helpers timeout expectation)

---

## Recommendations for Generator (Next Iteration)

### P0 — Required before merge

1. **Re-run the exact OGP-PPD test case** (same test_case_id as Exec #990) against live `ogp-ppd` Sales Portal with backend running post-fix code.
2. **Capture evidence at rubric steps:**
   - Step 14: ID document dashed box visible; sidebar **closed** (compare to `exec_990_step_14_pass.png`)
   - Step 24 (+3 after birth): field = `2000/01/01`, no "Required"
   - Step 36 (+2 after area): Area = "Hong Kong", menu closed, no "Required"
3. **Verify tier assignment** in `tier_execution_logs` for steps 14, 23, 35 — target: Tier 2 success without Tier 3 for widget steps.
4. **Fix or update** `test_execute_action_with_xpath_waits_for_popup_login_loading_to_clear` (align timeout 8000→20000 or revert `post_click_readiness` timeout).

### P1 — Hardening

5. Add `ThreeTierExecutionService` integration test: Tier 1 miss → Tier 2 custom dropdown/date/anchor path → assert no Tier 3.
6. Add Tier 3 negative test: anchor rejection should invalidate cache and retry observe before escalating.
7. Extend `_verify_filled_value` beyond payment fields (F6 deferred) to prevent false PASS on OGP-PPD birth date.

### P2 — Documentation

8. Add ADR-002-53 entry for Three HK registration widget handlers (spec F9).

---

## Summary for Parent Agent

| Metric | Value |
|--------|-------|
| **Verdict** | **FAIL** |
| **Score** | **0.35 / 1.00** (threshold 0.85) |
| **Unit tests (target)** | 39/39 pass |
| **Regression suite** | 149/150 pass (1 pre-existing failure) |
| **OGP-PPD E2E** | Not run post-fix |
| **3-tier widget coverage** | Tier 2 unit mocks only (~33% of requested coverage) |
| **Critical blockers** | F1, F2, F3 unverified on target flow; V1, V2 missing; C2 regression fail |
