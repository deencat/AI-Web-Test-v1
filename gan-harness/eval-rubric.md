# Evaluation Rubric: Exec #990 Registration Form Execution Fixes

**Target:** Three Hong Kong OGP-PPD registration test (Execution #990 or equivalent)  
**Weight total: 1.0**  
**Pass threshold:** ≥ 0.85 weighted score  
**Automatic fail:** Any of the three reported issues reproduces on re-run; or post-fix run marks failing steps PASS

---

## Functionality (0.40)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| F1 | Eye button click | Step "Click eye button next to 'Collect Personal Info'" activates ID capture / does **not** open hamburger sidebar | 0.12 |
| F2 | Birth date persistence | After birth-date step **and** after 3 subsequent steps, field displays `2000/01/01` (or normalized equivalent); no red "Required" on Birth Date | 0.14 |
| F3 | Area dropdown selection | Billing Address Area field shows **Hong Kong** (not "Select an Area"); dropdown closed; no "Required" under Area | 0.14 |

---

## Execution Engine Quality (0.30)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| E1 | Step parsing | `"select area 'Hong Kong'"` parsed as `action=select`, `value=Hong Kong` | 0.06 |
| E2 | Tier 2 handles widgets | Birth date and Area steps complete at Tier 2 (no Tier 3 fallback required for these steps) | 0.08 |
| E3 | Post-action verification | Engine fails step if fill/select value does not stick (not silent PASS) | 0.08 |
| E4 | Cache safety | Wrong hamburger xpath invalidated; re-observe finds eye icon on retry | 0.08 |

---

## Craft / Tests (0.20)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| C1 | Unit tests added | New tests in `test_execution_service_value_extraction.py` and `test_tier2_registration_widgets.py` (or equivalent) | 0.08 |
| C2 | No regressions | `pytest tests/test_tier2_plan_selection.py tests/test_tier2_payment_helpers.py tests/test_execution_service_value_extraction.py -q` all pass | 0.07 |
| C3 | Surgical diff | Changes confined to `execution_service.py`, `tier2_hybrid.py`, tests, optional ADR — no unrelated refactors | 0.05 |

---

## Evidence (0.10)

| ID | Criterion | Pass condition | Weight |
|----|-----------|----------------|--------|
| V1 | Screenshots | `exec_*_step_14_pass.png`: no sidebar overlay; step_24+: birth date filled; step_36: Area=Hong Kong | 0.05 |
| V2 | LLM log | Observe for eye step describes element near "Collect Personal Info", not "top controls" | 0.05 |

---

## Scoring

```
score = Σ (criterion_weight × pass?1:0)
```

| Band | Score | Meaning |
|------|-------|---------|
| Pass | ≥ 0.85 | Ready to merge |
| Revise | 0.70 – 0.84 | Fix failing criteria |
| Fail | < 0.70 or automatic fail | Reject |

---

## Evaluator Test Script

### Automated (unit)
```bash
cd backend && .\venv\Scripts\activate
python -m pytest tests/test_execution_service_value_extraction.py tests/test_tier2_registration_widgets.py -q
python -m pytest tests/test_tier2_plan_selection.py tests/test_tier2_payment_helpers.py -q
```

### Live E2E (Three HK registration)
1. Start backend: `cd backend && python start_server.py`
2. Re-run the same test case as Execution #990 (Three HK OGP-PPD registration flow)
3. At step 13–14: confirm eye/ID capture UI; sidebar menu **closed**
4. At birth-date step + 3 steps later: field = `2000/01/01`
5. At area step + 2 steps later: Area = `Hong Kong`, no Required error
6. Compare screenshots to baseline `exec_990_step_{14,24,36}_pass.png`
7. Check `backend/logs/llm/exec_<id>.jsonl` for improved observe descriptions

### Per-issue verification matrix

| Issue | Step index | PASS signal | FAIL signal |
|-------|------------|-------------|-------------|
| Eye click | ~13–14 | ID document dashed box / camera visible; main form in view | Left sidebar with "Direct Input Order" visible |
| Birth date | ~22–24 | Input shows 2000/01/01 after step 24 | Empty field + "Required" |
| Area | ~34–36 | Field text "Hong Kong", menu closed | "Select an Area" or open menu with highlight only |
