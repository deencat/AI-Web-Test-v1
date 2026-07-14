# Product Specification: Exec #990 Registration Form Execution Fixes

> Generated from brief: "Three misbehaviors in Execution #990 on Three Hong Kong telecom registration page — wrong eye-button click, birth date disappears, area dropdown not selected."

## Vision

Harden the three-tier execution engine so Three HK OGP-PPD registration steps reliably target the correct UI controls, persist reactive form values (date pickers, custom dropdowns), and verify post-action state before marking steps PASS. These are **execution engine bugs**, not bad test intent — the step text is reasonable; the engine lacks semantic validation and specialized handlers for this SPA's widget patterns.

---

## Evidence Summary (Execution #990)

| Issue | Step(s) | Tier | Log / Screenshot Evidence |
|-------|---------|------|---------------------------|
| Eye → hamburger | 13–14 | Tier 2 observe | `exec_990.jsonl` L4: observe returns element_id **67** — *"Eye icon button near the **top controls**"*; `exec_990_step_14_pass.png` shows **sidebar nav opened** (hamburger), not ID capture |
| Birth date lost | ~22–24 | Tier 1/2 (no LLM log) | `exec_990_step_23_pass.png`: field shows `2000/01/01` but calendar shows **June 2026**; `exec_990_step_24_pass.png`: field **empty** + red "Required" |
| Area not selected | 34–36 | Tier 2 observe | `exec_990.jsonl` L5: observe returns **dropdown trigger click**, not option; `exec_990_step_35_pass.png`: Hong Kong highlighted, field still "Select an Area"; `exec_990_step_36_pass.png`: "Required" under Area |

---

## Root Cause Analysis

### Issue 1: Wrong click target (eye → hamburger)

**Hypothesis:** Observe() mis-resolved the eye icon to a header control (element_id 67 in the global header a11y subtree). Tier 2 accepted the first observe result with **no click-target semantic validation** beyond Three HK promotion-card guards.

**Code evidence:**
- `xpath_extractor.py` L88–90: always takes **first** observe result.
- `tier2_hybrid.py` `_validate_cached_xpath_for_step()` L2791–2792: returns `True` for all non-fill clicks except Three HK promotion cards — **no proximity/anchor checks**.
- `exec_990_step_13_pass.png`: correct eye icon is centered next to "Collect Personal Info:"; hamburger is far top-right.

**Classification:** **Element resolution bug** (observe ranking + missing post-observe validation). Minor **test step integrity** opportunity: anchor phrase helps but should not be required.

**Fix layer:** Element resolution → action execution validation

---

### Issue 2: Birth date disappears

**Hypothesis:** Tier 2 used generic `element.fill("2000/01/01")` on a **custom date-picker widget**. Value briefly appeared in the text input but was cleared on blur/navigation because the calendar widget state (defaulting to **June 2026**, matching system date 2026-06-30) was never synchronized. No post-fill verification exists for non-payment fields.

**Code evidence:**
- `tier2_hybrid.py` `_execute_action_with_xpath()` L2641–2644: `await element.fill(value)` + `sleep(0.3)` only — no stickiness check.
- `_verify_filled_value()` L714–725: used for **payment fields only**.
- Screenshots: step 23 shows value + wrong calendar month; step 24 shows empty field after next step.

**Classification:** **Action execution bug** (missing date-picker handler) + **wait/validation bug** (no post-fill assert).

**Fix layer:** Action execution → wait/validation

---

### Issue 3: Area dropdown not selected

**Hypothesis (dual):**

1. **Step parsing:** `"select area 'Hong Kong'"` is **not** recognized as a dropdown step by `_is_dropdown_instruction()` because it lacks "dropdown", "from", or "menu" keywords (`execution_service.py` L1943–1961). Action is classified as **`click`**, not `select`.
2. **Action execution:** Even when Tier 2 runs, observe returns a **trigger click** to open the Area list (`exec_990.jsonl` L5). Native `select_option()` (`tier2_hybrid.py` L2653–2656) does not apply to this **custom div-based dropdown** (Billing Address Area). Engine opens menu, may hover-highlight "Hong Kong", but never commits selection or verifies field text.

**Code evidence:**
- `test_execution_service_value_extraction.py`: dropdown tests use `"from the Region dropdown"` phrasing — `"select area 'Hong Kong'"` pattern untested.
- `exec_990_step_35_pass.png`: open menu, highlighted option, placeholder unchanged.
- `exec_990_step_36_pass.png`: closed menu, still "Select an Area", Required error.

**Classification:** **Step parsing bug** + **action execution bug** (missing custom dropdown handler). Test step could add "dropdown" for clarity but engine should handle terse phrasing.

**Fix layer:** Step parsing → element resolution (two-phase) → action execution → validation

---

## Design Direction (Engineering)

- **Surgical handlers** in `tier2_hybrid.py` following existing patterns: payment gw-proxy, Three HK promotion cards, option XPath normalization (ADR-002-6).
- **No Tier 3 dependency** for these widget types — fix at Tier 2 where observe already succeeds.
- **Post-action verification** before PASS: field value, dropdown label, sidebar-not-open guard.
- **Invalidate poisoned XPath cache** entries when semantic validation fails.

---

## Features (Prioritized)

### Must-Have (Sprint 1)

#### F1: Dropdown instruction detection for terse phrasing
- **Description:** Extend `_is_dropdown_instruction()` to match `select <field> '<value>'` / `select <field> <value>` without requiring "dropdown" or "from".
- **Acceptance criteria:**
  - `"select area 'Hong Kong'"` → `action=select`, `value=Hong Kong`
  - `"Select the $288/month plan"` still → `action=click` (no regression)
  - Unit tests in `test_execution_service_value_extraction.py`

#### F2: Custom dropdown two-phase handler
- **Description:** `_try_custom_dropdown_select(page, instruction, value, xpath)` in `tier2_hybrid.py`:
  1. Click trigger (from observe xpath or label-scoped locator)
  2. Wait for listbox/menu visible
  3. Click option matching `value` (exact/normalized text)
  4. Wait for menu closed
  5. Verify trigger/display shows selected value
- **Acceptance criteria:**
  - Area field shows "Hong Kong" (not "Select an Area") after step
  - Works for Billing Address Area options: Hong Kong, Kowloon, New Territories
  - Falls back to native `select_option` when element is `<select>`

#### F3: Date picker fill handler with verification
- **Description:** `_fill_date_picker_field(locator, value, page)` for `yyyy/mm/dd` and `yyyy-mm-dd`:
  1. Parse target year/month/day from value
  2. Open picker if needed
  3. Navigate calendar to target month/year (not default June 2026)
  4. Click day cell OR type + Enter with format normalization
  5. Blur field; `_verify_filled_value` asserts persisted value
- **Acceptance criteria:**
  - After birth-date step: input contains `2000/01/01`
  - After next 3 steps: value still present (step 24+ screenshots)
  - Reject PASS if calendar month ≠ target month after fill

#### F4: Click anchor proximity validation
- **Description:** `_validate_click_target_for_instruction(page, locator, instruction)`:
  - Extract anchor phrases from instruction: `next to '...'`, `near '...'`, `under '...'`
  - Require anchor text visible on page and click target within same section (DOM distance / common ancestor heuristic)
  - Reject header/nav controls when anchor is in main content
  - On failure: invalidate cache, retry observe with augmented prompt including anchor
- **Acceptance criteria:**
  - Eye-button step clicks element adjacent to "Collect Personal Info", not hamburger (element_id 67 pattern rejected)
  - Sidebar does not open (`exec_990_step_14` regression fixed)

### Should-Have (Sprint 2)

#### F5: Observe result ranking (multi-candidate)
- When observe returns multiple elements, rank by: anchor proximity > description keyword match > vertical position in form (not header) > area size for cards.
- Prefer option element over trigger for select steps when value is known.

#### F6: Generic post-fill/post-select verification
- Extend `_verify_filled_value` to all fill/select steps (configurable, default on for registration forms).
- Step fails Tier 2 → escalate to Tier 3 only after verification failure logged.

#### F7: XPath cache semantic invalidation
- Store `element_description` from observe; re-validate on cache hit.
- Auto-invalidate entries where description contains "top controls" but instruction references main-content anchor.

### Nice-to-Have (Sprint 3+)

#### F8: Test step wording improvements (test definition layer)
- Optional clearer steps for brittle targets:
  - `"Click the eye icon to the right of 'Collect Personal Info:' in Registration Personal Information"`
  - `"Select 'Hong Kong' from the Billing Address Area dropdown"`
- Not required if F1–F4 land.

#### F9: ADR-002-53 sub-decision doc
- Document Three HK registration widget handlers (date picker, custom dropdown, anchored clicks).

---

## Technical Stack

| Layer | Module | Changes |
|-------|--------|---------|
| Step parsing | `execution_service.py` | `_is_dropdown_instruction`, value extraction patterns |
| Element resolution | `xpath_extractor.py`, `tier2_hybrid.py` | Multi-candidate ranking, anchor validation |
| Action execution | `tier2_hybrid.py` | `_fill_date_picker_field`, `_try_custom_dropdown_select` |
| Validation | `tier2_hybrid.py` | `_verify_filled_value` generalization, click context guard |
| Tests | `tests/test_execution_service_value_extraction.py`, `tests/test_tier2_registration_widgets.py` (new) | TDD for all handlers |
| Docs | `documentation/ADR-002-test-execution-engine.md` | ADR-002-53 entry |

**No frontend changes. No Tier 3 / Stagehand prompt changes required for MVP.**

---

## Sprint Plan

### Sprint 1: Registration widget handlers (P0)
- **Goals:** Fix all three Exec #990 failures
- **Features:** F1, F2, F3, F4
- **Definition of done:**
  - New unit tests pass (`pytest tests/test_execution_service_value_extraction.py tests/test_tier2_registration_widgets.py -q`)
  - Manual or harness re-run of registration test: steps 13–14, birth date, area pass with correct screenshots
  - No regression in `tests/test_tier2_plan_selection.py`, `tests/test_tier2_payment_helpers.py`

### Sprint 2: Hardening (P1)
- **Goals:** Prevent recurrence on similar widgets
- **Features:** F5, F6, F7
- **Definition of done:** Cache invalidation tests; post-fill verification on generic fill steps

### Sprint 3: Documentation & step hygiene (P2)
- **Features:** F8, F9
- **Definition of done:** ADR updated; optional test case text improvements

---

## Generator Task List (Ordered)

1. **TDD:** Add failing tests for `_is_dropdown_instruction("select area 'Hong Kong'")` → True
2. **TDD:** Add failing tests for custom dropdown handler (mock page / Playwright fixture)
3. **TDD:** Add failing tests for date picker fill + persistence verification
4. **TDD:** Add failing test for click anchor rejection (header button when anchor is main-content)
5. Implement F1 in `execution_service.py`
6. Implement F2 `_try_custom_dropdown_select` — wire into `execute_step` before generic select
7. Implement F3 `_fill_date_picker_field` — wire into `_execute_action_with_xpath` for date-like instructions
8. Implement F4 anchor validation — wire before click in `_execute_action_with_xpath` and on cache hit
9. Run full backend unit test suite for tier2/execution_service
10. Update `gan-harness/generator-state.md` with iteration notes

---

## Out of Scope

- Fixing OTP modal / email verification flow (orthogonal; test continues past with mobile OTP)
- Three HK promotion card / Wi-Fi plan selection (addressed in prior iteration)
- Tier 1 pre-defined selector support (no selectors in current test steps)
