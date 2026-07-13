# Evaluation Rubric: ASG Deterministic Test Generation

**Feature:** App State Graph (ASG)-based deterministic test generation  
**Spec:** `gan-harness/spec.md` (Feature 3 section)  
**Weight total:** 1.0  
**Pass threshold:** >= 0.85 weighted score  
**Automatic fail:** breaks execution dispatch path (`ExecutionService -> ThreeTierExecutionService`), changes `TestCase.steps` away from `string[]`, removes confidence-gated fallback, or requires random unbounded crawling for primary flow

---

## Weighted Criteria

### 1) Architecture and Constraints (0.20)
- `A1` (0.05) ASG APIs implemented under `/api/v2/asg`.
- `A2` (0.05) Router -> service -> CRUD layering preserved.
- `A3` (0.05) SQLAlchemy-only model/migration implementation.
- `A4` (0.05) Existing execution runtime architecture unchanged.

### 2) Data Model and API Completeness (0.20)
- `D1` (0.05) `asg_graphs`, `asg_nodes`, `asg_edges` persisted with required indexes.
- `D2` (0.05) `asg_paths`, `asg_synthesized_tests` added with FK integrity.
- `D3` (0.05) Build/plan/synthesize endpoints return stable contracts.
- `D4` (0.05) Artifact bundle written with graph/plan/synthesis/replay traces.

### 3) Determinism and Confidence Gates (0.25)
- `C1` (0.08) Graph build deterministic ID stability >= 95% on fixed seeds.
- `C2` (0.07) Planner output deterministic for same graph+policy inputs.
- `C3` (0.05) Confidence scoring and threshold gate enforced before synthesis.
- `C4` (0.05) Low-confidence flow auto-falls back with reason codes.

### 4) Workflow Integration and Compatibility (0.20)
- `I1` (0.05) crawl-and-save can trigger ASG shadow build.
- `I2` (0.05) generate-tests integrates ASG branch behind flags.
- `I3` (0.05) Synthesized outputs save as `TestCase.steps: string[]`.
- `I4` (0.05) Feature flags support shadow mode and cohort allowlist.

### 5) Quality, Testing, and Operations (0.15)
- `Q1` (0.04) Unit + integration coverage for build/plan/synthesize flows.
- `Q2` (0.04) KPI dashboards/logs include confidence/fallback/replay metrics.
- `Q3` (0.04) Failure triage playbook available and actionable.
- `Q4` (0.03) ADR-010 authored and linked from relevant docs.

---

## KPI Gates (must meet in pilot)

- Deterministic replay pass rate >= 90%.
- Flake rerun delta <= 8%.
- Coverage stability (3 reruns Jaccard) >= 0.90.
- P95 generation latency <= 6 minutes for <= 150 nodes.
- Fallback trigger rate <= 20% after threshold tuning.

### Phase 4: Confidence Scoring v2 (pilot remediation)

- Rebuild graph 5 or 6 `flow_steps` artifact → mean confidence **>= 0.75**.
- `POST /api/v2/asg/{graph_id}/validate` → `fallback_recommended: false` on pilot rebuild.
- Readiness snapshots on **>= 50%** of click/input edges in new crawls.
- ASG module coverage **100%** (`cov-fail-under=100`).
- **`ASG_CONFIDENCE_MIN` not lowered** as primary fix.

---

## Phase 4 Evaluator Checks

1. Unit: `score_selector_stability` with xpath + `playwright_suggestions` role+name → **0.85** (not 0.55).
2. Unit: xpath-only, no suggestions → **0.55** (regression).
3. Unit: `score_readiness_signal(settled=True)` → **0.90**; missing snapshot → **0.60**.
4. Unit: `trigger_shadow_build` passes `readiness_snapshots` to `ASGBuildRequest`.
5. Integration: rebuild graph 5/6 fixture without re-crawl; assert mean confidence >= 0.75.
6. Integration: validate endpoint returns `fallback_recommended: false` on uplifted pilot graph.
7. Regression: all-weak-signals graph still fails `ASG_CONFIDENCE_MIN` gate.

---

## Evaluator Checks

1. Build ASG twice for same seed/policy; compare node/edge deterministic keys.
2. Request plan twice for same graph/goal; verify stable ranked output.
3. Synthesize tests and confirm `steps` remains `string[]`.
4. Force low confidence (threshold bump or weak selectors) and verify fallback activation.
5. Execute synthesized tests through existing execution path; verify no runtime contract regressions.
6. Confirm observability records include `graph_id`, `plan_id`, `synthesis_id`, `execution_id`.

---

## Scoring

`score = sum(weight_i * pass_i)`

- **Pass**: >= 0.85 and no automatic fail
- **Revise**: 0.70-0.84
- **Fail**: < 0.70 or any automatic fail
