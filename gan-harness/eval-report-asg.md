# Evaluation — Feature 3: ASG Deterministic Test Generation (Phase 3)

**Date:** July 10, 2026 (Phase 3 re-evaluation)  
**Evaluator:** GAN Evaluator (code + pytest verification)  
**Spec:** `gan-harness/spec.md` § Feature 3, Phase 3  
**Rubric:** `gan-harness/eval-rubric.md`  
**ADR:** `documentation/ADR-010-asg-deterministic-test-generation.md`  
**Generator state:** `gan-harness/generator-state.md`

---

## Verdict: **PASS**

| Metric | Previous (Phase 2) | Current (Phase 3) |
|--------|--------------------|-------------------|
| **Weighted score** | 0.94 / 1.00 | **0.99 / 1.00** |
| **Pass threshold** | ≥ 0.85 | ≥ 0.85 ✅ |
| **100% ASG module coverage** | Claimed (5 modules) | **100.00% — PASS** (`cov-fail-under=100`, 6 modules) |
| **Automatic fail** | None | None ✅ |
| **Tests** | 70 passed | **87 passed / 0 failed** |
| **Evaluator checks** | 6 / 6 PASS | **6 / 6 PASS** |

**Coverage fix:** Added `tests/unit/test_asg_metrics.py` covering rate getters and zero-denominator `_rate()` branch; all six ASG modules now at 100%.

---

## Weighted Score Breakdown

| Criterion | Weight | Pass rate | Weighted |
|-----------|--------|-----------|----------|
| **1. Architecture and Constraints** | 0.20 | 1.00 | 0.20 |
| **2. Data Model and API Completeness** | 0.20 | 1.00 | 0.20 |
| **3. Determinism and Confidence Gates** | 0.25 | 1.00 | 0.25 |
| **4. Workflow Integration and Compatibility** | 0.20 | 1.00 | 0.20 |
| **5. Quality, Testing, and Operations** | 0.15 | 0.90 | 0.14 |
| **TOTAL** | 1.00 | | **0.99** |

---

## Per-Criterion Scores (A1–Q4)

Scale: **10** = full pass, **5** = partial, **0** = fail.

### 1) Architecture and Constraints (0.20)

| ID | Score | Notes |
|----|-------|-------|
| A1 | 10/10 | `/api/v2/asg/*` registered (`build`, `GET /{graph_id}`, `plan`, `synthesize`, `validate`). |
| A2 | 10/10 | Endpoints → `ASGService` → `app.crud.asg`. |
| A3 | 10/10 | SQLAlchemy models + `migrations/add_asg_tables.py`. |
| A4 | 10/10 | `ThreeTierExecutionService` dispatch unchanged; ASG adds post-execution hook only. |

### 2) Data Model and API Completeness (0.20)

| ID | Score | Notes |
|----|-------|-------|
| D1 | 10/10 | `asg_graphs`, `asg_nodes`, `asg_edges` with composite indexes. |
| D2 | 10/10 | `asg_paths`, `asg_synthesized_tests` with FK integrity. |
| D3 | 10/10 | Build/plan/synthesize/validate contracts exercised by API + unit tests. |
| D4 | 10/10 | Artifact bundles under `artifacts/asg/{graph_id}/` including `replay/{execution_id}.json`. |

### 3) Determinism and Confidence Gates (0.25)

| ID | Score | Notes |
|----|-------|-------|
| C1 | 10/10 | `test_build_deterministic_on_fixed_seed` — identical fingerprints and `deterministic_key` on fixed seed. |
| C2 | 10/10 | `test_planner_deterministic_for_fixture`; `requirement_coverage` and `risk_first` modes covered. |
| C3 | 10/10 | **Fixed:** `synthesize_tests()` enforces `evaluate_confidence_gate` before synthesis; returns `fallback_reason_code` when below threshold. |
| C4 | 10/10 | Fallback with reason codes (`low_node_confidence`, `low_edge_confidence`, `low_replay_confidence`); metrics `record_fallback` on gate failure. |

### 4) Workflow Integration and Compatibility (0.20)

| ID | Score | Notes |
|----|-------|-------|
| I1 | 10/10 | `crawl_and_save.py` calls `trigger_shadow_build()` + `compare_shadow_vs_primary()`. |
| I2 | 10/10 | `orchestration_service.run_workflow` ASG primary branch with legacy fallback. |
| I3 | 10/10 | Synthesizer uses `_flow_steps_to_test_steps`; `TestCase.steps` remains `list[str]` (`Column(JSON)`). |
| I4 | 10/10 | `ASG_ENABLED`, `ASG_SHADOW_MODE`, `ASG_CONFIDENCE_MIN`, `ASG_PROJECT_ALLOWLIST` in config + `is_asg_enabled_for_project()`. |

### 5) Quality, Testing, and Operations (0.15)

| ID | Score | Notes |
|----|-------|-------|
| Q1 | **10/10** | **87 tests pass** including 4 E2E pipeline tests + 7 metrics unit tests. **Coverage gate PASS at 100.00%** on all 6 ASG modules. |
| Q2 | 8/10 | `ASGMetrics` records build/plan/synthesis/replay/fallback with structured `extra` log keys; `evaluate_canary_rollback()` implemented. No external dashboard/export pipeline. |
| Q3 | 9/10 | Standalone `docs/asg-triage-playbook.md` — actionable stages, artifact paths, canary rollback, feature-flag reference. |
| Q4 | 9/10 | ADR-010 authored; cross-linked from Phase3 guide and triage playbook. |

---

## Test Execution Summary

### Command (evaluator-mandated)

```bash
cd backend && source venv/bin/activate
pytest tests/unit/test_asg*.py tests/e2e/test_asg_pipeline_e2e.py -v \
  --cov=app.services.asg_service --cov=app.crud.asg --cov=app.api.v2.endpoints.asg \
  --cov=app.models.asg --cov=app.schemas.asg --cov=app.services.asg_metrics \
  --cov-report=term-missing --cov-fail-under=100
```

**Result:** 87 passed in ~13s. **Coverage gate PASSED: 100.00%.**

### Test files

| File | Tests | Purpose |
|------|-------|---------|
| `test_asg_service.py` | 11 | Core fingerprinting, build, plan, synthesize, validate |
| `test_asg_api.py` | 6 | HTTP endpoint contracts |
| `test_asg_integration.py` | 2 | End-to-end pipeline + legacy path unchanged |
| `test_asg_coverage.py` | 56 | Policy engine, planner modes, API errors, CRUD, Phase 3 integration |
| `test_asg_execution_contract.py` | 1 | Synthesize → ExecutionService `string[]` contract |
| `test_asg_metrics.py` | 7 | Rate getters, canary rollback, singleton |
| `test_asg_pipeline_e2e.py` | 4 | Full pipeline, shadow diff, canary rollback, confidence gate |

---

## Coverage by Module

| Module | Stmts | Miss | Cover | Status |
|--------|-------|------|-------|--------|
| `app/models/asg.py` | 77 | 0 | **100%** | ✅ |
| `app/schemas/asg.py` | 94 | 0 | **100%** | ✅ |
| `app/crud/asg.py` | 67 | 0 | **100%** | ✅ |
| `app/api/v2/endpoints/asg.py` | 50 | 0 | **100%** | ✅ |
| `app/services/asg_service.py` | 461 | 0 | **100%** | ✅ |
| `app/services/asg_metrics.py` | 90 | 0 | **100%** | ✅ |
| **TOTAL** | 839 | 0 | **100%** | ✅ |

---

## Phase 3 Acceptance Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| E2E pipeline: crawl → build → plan → synthesize → execute | **PASS** | `test_asg_full_pipeline_build_plan_synthesize_execute_replay` — build from `flow_steps`, plan, synthesize, `ExecutionService.execute_test`, replay artifact written |
| Shadow-vs-primary diff checks | **PASS** | `compare_shadow_vs_primary()` in orchestration + crawl-and-save; unit + E2E tests |
| Canary monitoring assertions with rollback triggers | **PASS** | `evaluate_canary_rollback()` — replay < 80% and fallback > 40% triggers; `test_canary_rollback_assertions` |
| Feature flags, progressive rollout | **PASS** | `ASG_ENABLED`, `ASG_SHADOW_MODE`, `ASG_CONFIDENCE_MIN`, `ASG_PROJECT_ALLOWLIST`; `TestFeatureFlags` suite |
| Observability metrics (graph/plan/synthesis/execution IDs) | **PASS** | `record_build/plan/synthesis/replay/fallback`; replay JSON + structured logs include all four IDs |
| Triage playbook and ADR cross-links | **PASS** | `docs/asg-triage-playbook.md`; Phase3 guide table links ADR-010 + playbook |

**Pilot KPI gates** (≥90% replay pass, ≤8% flake delta, etc.) remain **N/A** — no staging cohort data in this eval.

---

## Evaluator Checks (1–6)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Build ASG twice; compare deterministic keys | **PASS** | `test_build_deterministic_on_fixed_seed`; `TestDeterministicKeys::test_edge_key_stable` |
| 2 | Plan twice; stable ranked output | **PASS** | `test_planner_deterministic_for_fixture` |
| 3 | Synthesize tests; `steps` is `string[]` | **PASS** | `test_plan_and_synthesize_output_string_steps`, `test_end_to_end_pipeline_saves_test_case`, execution contract test |
| 4 | Force low confidence; verify fallback | **PASS** | `test_synthesize_confidence_gate_blocks_low_confidence` (E2E); `test_synthesize_confidence_gate_returns_fallback`; validate low-confidence branches |
| 5 | Execute synthesized tests via execution path | **PASS** | `test_asg_synthesize_then_execution_service_accepts_string_steps`; E2E pipeline mocks `ThreeTierExecutionService` but exercises real `ExecutionService.execute_test` + replay hook |
| 6 | Observability includes `graph_id`, `plan_id`, `synthesis_id`, `execution_id` | **PASS** | `ExecutionService._write_asg_replay_artifact_if_applicable` → `write_replay_artifact`; E2E asserts all four IDs in `replay/{execution_id}.json` |

---

## Automatic Fail Conditions

| Condition | Status |
|-----------|--------|
| Breaks `ExecutionService → ThreeTierExecutionService` | ✅ Not broken — hook runs in `finally` path after execution completes |
| Changes `TestCase.steps` away from `string[]` | ✅ Preserved (`app/models/test_case.py` line 47) |
| Removes confidence-gated fallback | ✅ Present on synthesize + validate + orchestration |
| Requires random unbounded crawling for primary flow | ✅ Goal-bounded ASG from `flow_steps` / seeded journeys |

---

## Critical Issues — Resolved

| Issue | Status |
|-------|--------|
| Coverage gate failure (99% vs 100%) | ✅ **Fixed** — `test_asg_metrics.py` added; 100% on all 6 modules |
| Generator coverage claim inaccurate | ✅ **Fixed** — `generator-state.md` updated with 6-module `--cov` scope |

---

## Major Issues (should fix)

1. **E2E tests are mocked, not live browser** — `test_asg_pipeline_e2e.py` uses SQLite + mocked Playwright/`ThreeTierExecutionService`. Acceptable for CI, but does not validate real replay pass rates against pilot KPIs.

2. **Happy-path tests relax confidence gate** — `conftest.py` autouse fixture sets `ASG_CONFIDENCE_MIN=0.1` for most ASG tests. Gate-failure tests opt out by name. Document clearly; consider explicit `@pytest.mark` instead of name heuristics.

3. **No external metrics dashboard** — Structured logs and in-memory counters only; no Grafana/Prometheus export for production canary monitoring.

---

## Minor Issues

1. Fixture graphs score ~0.71 replay confidence at default `ASG_CONFIDENCE_MIN=0.75` (generator known issue) — production cohorts need tuning or richer crawl locators.

2. Requirement-coverage planner uses title/fingerprint heuristics until Requirements agent mapping is wired.

3. `plan_id` is a new UUID per plan call — acceptable; consider correlation IDs in orchestration logs for cross-service tracing.

---

## What Improved Since Last Iteration

- **`write_replay_artifact()` wired** into `ExecutionService._write_asg_replay_artifact_if_applicable()` — resolves prior major issue.
- **Confidence gate on `POST /synthesize`** — `synthesize_tests()` blocks low-confidence graphs with `fallback_reason_code`.
- **`ASGMetrics` module** — structured logging, canary rollback helper, in-memory counters.
- **`compare_shadow_vs_primary()`** hooked in orchestration + crawl-and-save.
- **E2E pipeline test file** — 4 tests covering full pipeline, shadow diff, canary, gate failure.
- **`docs/asg-triage-playbook.md`** — standalone operational runbook.
- **ADR-010 cross-linked** from Phase3 implementation guide.
- **Test count 70 → 87**; coverage 100% on 6 ASG modules.

## What Regressed Since Last Iteration

- None observed.

---

## Recommendations for Next Generator Iteration

1. Optional: smoke test with live dev server (`http://localhost:8000`) for `/api/v2/asg/*` HTTP contracts.
2. Export `ASGMetricsSnapshot` to Prometheus counters or document log-based dashboard queries.
3. Tune `ASG_CONFIDENCE_MIN` per cohort using staging replay metrics.

---

## Screenshots / Live Browser

**Not performed.** ASG is a backend API/service feature. E2E tests use in-memory SQLite and mocked browser execution. Dev server status per generator-state: running on port 8000.
