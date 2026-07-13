# Evaluation — ASG Phase 4: Confidence Scoring v2 & Pilot Remediation

**Date:** July 13, 2026  
**Evaluator:** GAN Evaluator (pytest + code verification)  
**Spec:** `gan-harness/spec.md` § Feature 3, Phase 4  
**Rubric:** `gan-harness/eval-rubric.md` (Phase 4 Evaluator Checks §53–72)  
**Generator state:** `gan-harness/generator-state.md`

---

## Verdict: **PASS**

| Metric | Phase 3 | Phase 4 |
|--------|---------|---------|
| **Weighted score** | 0.99 / 1.00 | **0.99 / 1.00** |
| **Pass threshold** | ≥ 0.85 | ≥ 0.85 ✅ |
| **Phase 4 checks (1–7)** | N/A | **7 / 7 PASS** |
| **ASG module coverage** | 100% (87 tests) | **100.00% (94 tests)** |
| **Automatic fail** | None | None ✅ |

---

## Weighted Score Breakdown

| Criterion | Weight | Pass rate | Weighted |
|-----------|--------|-----------|----------|
| **1. Architecture and Constraints** | 0.20 | 1.00 | 0.20 |
| **2. Data Model and API Completeness** | 0.20 | 1.00 | 0.20 |
| **3. Determinism and Confidence Gates** | 0.25 | 1.00 | 0.25 |
| **4. Workflow Integration and Compatibility** | 0.20 | 1.00 | 0.20 |
| **5. Quality, Testing, and Operations** | 0.15 | 0.93 | 0.14 |
| **TOTAL** | 1.00 | | **0.99** |

### Per-criterion highlights (Phase 4 delta)

| ID | Score | Phase 4 notes |
|----|-------|---------------|
| C3 | 10/10 | `score_selector_stability` v2 prioritizes `playwright_suggestions` over bare xpath; `confidence-report.json` records `scoring_version: "v2"` and `uplift.{v1_mean,v2_mean}`. |
| C4 | 10/10 | `ASG_CONFIDENCE_MIN` remains **0.75** (not lowered); weak-signal graph still triggers `fallback_recommended: true`. |
| I1 | 10/10 | `trigger_shadow_build()` extracts and forwards `readiness_snapshots` into `ASGBuildRequest`. |
| Q1 | 10/10 | 94 tests pass; `TestPhase4ConfidenceV2` suite added; 100% coverage on all six ASG modules. |

---

## Phase 4 Evaluator Checks (1–7)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| **1** | `score_selector_stability`: xpath + `playwright_suggestions` role+name → **0.85** | **PASS** | `test_selector_stability_all_branches` asserts 0.85 for xpath + role suggestion; v2 checks suggestions before xpath (`asg_service.py` L204–214). |
| **2** | xpath-only, no suggestions → **0.55** (regression guard) | **PASS** | Same test asserts `{"locator": {"xpath": "//x"}}` → 0.55. |
| **3** | `score_readiness_signal(settled=True)` → **0.90**; missing → **0.60** | **PASS** | `test_readiness_all_branches`: `None` → 0.6, `{"settled": True}` → 0.9. |
| **4** | `trigger_shadow_build` passes `readiness_snapshots` to `ASGBuildRequest` | **PASS** | `test_trigger_shadow_build_forwards_readiness_snapshots`; implementation at `asg_service.py` L1097–1104. |
| **5** | Rebuild graph 5/6 fixture without re-crawl; mean confidence ≥ 0.75 | **PASS** | `test_pilot_rebuild_confidence_uplift` (graph5): mean **0.7703**. Manual rebuild of graph6: mean **0.77** (fixture exists; not yet in automated test). |
| **6** | Validate endpoint `fallback_recommended: false` on uplifted pilot graph | **PASS** | `test_pilot_rebuild_confidence_uplift` calls `validate_graph()` → `fallback_recommended is False`. |
| **7** | All-weak-signals graph still fails `ASG_CONFIDENCE_MIN` gate | **PASS** | `test_weak_signals_graph_fails_confidence_gate`: mean < 0.75, `fallback_recommended is True`. |

**Phase 4 KPI gates (rubric §53–59):**

| Gate | Result | Evidence |
|------|--------|----------|
| Pilot mean confidence ≥ 0.75 | **PASS** | Graph5: 0.7703; Graph6: 0.77 |
| `fallback_recommended: false` on pilot rebuild | **PASS** | Both pilot fixtures |
| Readiness on ≥ 50% click/input edges | **PASS** | Graph5: 17/17 (100%); Graph6: 16/16 (100%) in fixtures |
| ASG module coverage 100% | **PASS** | `cov-fail-under=100` satisfied |
| `ASG_CONFIDENCE_MIN` not lowered | **PASS** | `app/core/config.py` default **0.75**; pilot passes via scoring uplift, not threshold change |

---

## Test Execution Summary

### Coverage command (evaluator-mandated)

```bash
cd backend && source venv/bin/activate
pytest tests/unit/test_asg*.py tests/e2e/test_asg_pipeline_e2e.py -v \
  --cov=app.services.asg_service --cov=app.crud.asg --cov=app.api.v2.endpoints.asg \
  --cov=app.models.asg --cov=app.schemas.asg --cov=app.services.asg_metrics \
  --cov-report=term-missing --cov-fail-under=100
```

**Result:** **94 passed**, 0 failed, ~14s. **Coverage: 100.00%** (911 statements, 0 miss).

### E2E pipeline (standalone)

```bash
pytest tests/e2e/test_asg_pipeline_e2e.py -v
```

**Result:** **4 passed** (included in 94 above).

### Coverage by module

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| `app/services/asg_service.py` | 533 | 0 | **100%** |
| `app/schemas/asg.py` | 94 | 0 | **100%** |
| `app/models/asg.py` | 77 | 0 | **100%** |
| `app/crud/asg.py` | 67 | 0 | **100%** |
| `app/services/asg_metrics.py` | 90 | 0 | **100%** |
| `app/api/v2/endpoints/asg.py` | 50 | 0 | **100%** |
| **TOTAL** | **911** | **0** | **100%** |

### Phase 4 test additions (`TestPhase4ConfidenceV2`)

| Test | Purpose |
|------|---------|
| `test_normalize_transition_copies_playwright_suggestions` | Locator bundle suggestions copied to transition |
| `test_extract_readiness_snapshots_from_flow_steps` | Readiness / post_click_readiness extraction |
| `test_trigger_shadow_build_forwards_readiness_snapshots` | Check 4 |
| `test_build_confidence_report_includes_uplift` | `scoring_version: "v2"`, uplift fields |
| `test_pilot_rebuild_confidence_uplift` | Checks 5–6 (graph5) |
| `test_weak_signals_graph_fails_confidence_gate` | Check 7 |
| `test_v1_uplift_covers_legacy_selector_branches` | v1 comparison helper coverage |

---

## Pilot Confidence Scores (v2 rebuild from fixtures)

| Fixture | Steps | Readiness snaps | Mean | Min | Max | v1 Mean | v2 Mean | Uplift Δ | `below_threshold` | `fallback_recommended` |
|---------|-------|-----------------|------|-----|-----|---------|---------|-----------|-------------------|------------------------|
| **pilot_graph5** | 18 | 18 | **0.7703** | 0.65 | 0.85 | 0.7204 | 0.7703 | +0.0499 | 15 | **false** |
| **pilot_graph6** | 17 | 17 | **0.7700** | 0.65 | 0.85 | 0.7206 | 0.7700 | +0.0494 | 14 | **false** |

**confidence-report.json** (graph5 example): `scoring_version: "v2"`, `uplift.v1_mean` < `uplift.v2_mean` confirming v2 uplift over legacy xpath-first scoring.

**Implementation verified:**

- `score_selector_stability` v2: suggestions → role+name (0.85) / css_id (0.75) before xpath (0.55)
- `_score_selector_stability_v1()` retained for uplift comparison only
- `extract_readiness_snapshots_from_flow_steps()` + `normalize_transition()` playwright_suggestions copy
- `trigger_shadow_build()` → `ASGBuildRequest(readiness_snapshots=...)`

---

## Automatic Fail Conditions

| Condition | Status |
|-----------|--------|
| Breaks execution dispatch path | ✅ Not broken |
| Changes `TestCase.steps` away from `string[]` | ✅ Preserved |
| Removes confidence-gated fallback | ✅ Present on synthesize + validate |
| Requires random unbounded crawling | ✅ Goal-bounded from `flow_steps` |
| Lowered `ASG_CONFIDENCE_MIN` as primary fix | ✅ Threshold unchanged at 0.75 |

---

## Gaps and Recommendations

### Minor gaps

1. **Graph6 not in automated pilot test** — `test_pilot_rebuild_confidence_uplift` only exercises `pilot_graph5_flow_steps.json`. Graph6 passes manually (mean 0.77) but should be parametrized for regression safety.

2. **Pilot margin is thin** — Mean 0.7703 is only ~0.02 above the 0.75 gate; 15 node/edge confidences still sit below threshold individually. Production cohorts may need richer `playwright_suggestions` on remaining xpath-only steps.

3. **E2E remains mocked** — Pipeline E2E uses SQLite + mocked browser; does not validate live crawl → shadow build → readiness attachment in observation agent.

4. **Test autouse gate relaxation** — `conftest.py` sets `ASG_CONFIDENCE_MIN=0.1` for most ASG tests; Phase 4 gate tests opt out explicitly. Consider `@pytest.mark.confidence_gate` instead of name heuristics.

### Recommendations for next iteration

1. Parametrize pilot rebuild test over both `pilot_graph5` and `pilot_graph6` fixtures.
2. Add integration test that runs `trigger_shadow_build` end-to-end from a synthetic crawl payload with mixed readiness coverage.
3. Target remaining xpath-only edges in pilot fixtures to push mean confidence toward 0.80+ headroom.
4. Wire requirement-coverage planner to Requirements agent mapping (deferred from generator-state).

---

## What Improved Since Phase 3

- XPath-first regression fixed: xpath + role suggestion now scores **0.85** (was 0.55 under v1 ordering)
- Readiness snapshots wired through shadow build path (`settled` → 0.90 readiness component)
- Pilot graphs pass `ASG_CONFIDENCE_MIN=0.75` without lowering threshold
- `confidence-report.json` uplift telemetry (`v1_mean` vs `v2_mean`)
- Test count **87 → 94**; `asg_service.py` stmts **461 → 533** with full coverage maintained

## What Regressed Since Phase 3

- None observed.

---

## Screenshots / Live Browser

**Not performed.** Phase 4 is backend scoring and pilot fixture remediation. Verification via pytest and direct fixture rebuild scripts. Dev server reported running on port 8000 per generator-state.
