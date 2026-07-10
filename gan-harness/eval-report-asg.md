# Evaluation — Feature 3: ASG Deterministic Test Generation

**Date:** July 10, 2026 (re-evaluation)  
**Evaluator:** GAN Evaluator (code + test verification)  
**Spec:** `gan-harness/spec.md` § Feature 3  
**Rubric:** `gan-harness/eval-rubric.md`  
**ADR:** `documentation/ADR-010-asg-deterministic-test-generation.md`  
**Generator state:** `gan-harness/generator-state.md`

---

## Verdict: **PASS**

| Metric | Previous | Current |
|--------|----------|---------|
| **Weighted score** | 0.86 / 1.00 | **0.94 / 1.00** |
| **Pass threshold** | ≥ 0.85 | ≥ 0.85 |
| **Automatic fail** | None | None |
| **Tests** | 31 passed (19 ASG-specific) | **70 passed / 0 failed** |
| **ASG module coverage** | 86% aggregate | **100%** (all 5 modules) |
| **Evaluator checks** | 4 PASS, 1 FAIL, 1 PARTIAL | **6 / 6 PASS** |

---

## Weighted Score Breakdown

| Criterion | Weight | Pass rate | Weighted | Δ |
|-----------|--------|-----------|----------|---|
| **1. Architecture and Constraints** | 0.20 | 1.00 | 0.20 | — |
| **2. Data Model and API Completeness** | 0.20 | 1.00 | 0.20 | +0.02 |
| **3. Determinism and Confidence Gates** | 0.25 | 0.96 | 0.24 | — |
| **4. Workflow Integration and Compatibility** | 0.20 | 1.00 | 0.20 | — |
| **5. Quality, Testing, and Operations** | 0.15 | 0.65 | 0.10 | +0.06 |
| **TOTAL** | 1.00 | | **0.94** | **+0.08** |

---

## Per-Criterion Scores (A1–Q4)

Scale: **10** = full pass, **5** = partial, **0** = fail.

### 1) Architecture and Constraints (0.20)

| ID | Score | Notes |
|----|-------|-------|
| A1 | 10/10 | `/api/v2/asg/*` registered in `backend/app/api/v2/api.py` (`prefix="/asg"`). |
| A2 | 10/10 | Endpoints delegate to `ASGService`; service uses `app.crud.asg`. |
| A3 | 10/10 | SQLAlchemy models in `app/models/asg.py`; migration `migrations/add_asg_tables.py`. |
| A4 | 10/10 | No edits to `ExecutionService` / `ThreeTierExecutionService` dispatch path. |

### 2) Data Model and API Completeness (0.20)

| ID | Score | Notes |
|----|-------|-------|
| D1 | 10/10 | `asg_graphs`, `asg_nodes`, `asg_edges` with composite indexes on `(graph_id, state_fingerprint)` and `(graph_id, deterministic_key)`. |
| D2 | 10/10 | `asg_paths`, `asg_synthesized_tests` with FK integrity to graphs/paths/test_cases. |
| D3 | 10/10 | Build/plan/synthesize/validate contracts exercised by `test_asg_api.py` and coverage tests. |
| D4 | 10/10 | `build/`, `plan/`, `synthesis/` JSON artifacts plus `replay/{execution_id}.json` via `write_replay_artifact()` — tested in `test_asg_coverage.py` and `test_asg_execution_contract.py`. |

### 3) Determinism and Confidence Gates (0.25)

| ID | Score | Notes |
|----|-------|-------|
| C1 | 10/10 | Same seed + policy → identical node fingerprints and edge `deterministic_key` values. |
| C2 | 10/10 | Repeated `shortest_path` plans on same graph yield identical `node_fingerprints` and score ordering. |
| C3 | 8/10 | `validate_graph` + `evaluate_confidence_gate` enforce threshold; orchestration primary path gates before synthesize. **`POST /synthesize` still does not enforce confidence gate** (callable directly). |
| C4 | 10/10 | `ASG_CONFIDENCE_MIN=0.99` → `fallback_recommended=True` + `fallback_reason_code`; orchestration logs fallback and routes to legacy. |

### 4) Workflow Integration and Compatibility (0.20)

| ID | Score | Notes |
|----|-------|-------|
| I1 | 10/10 | `crawl_and_save.py` calls `trigger_shadow_build()` when shadow/enabled flags on. |
| I2 | 10/10 | `orchestration_service.run_workflow` ASG primary branch with legacy fallback. |
| I3 | 10/10 | Synthesizer uses `_flow_steps_to_test_steps`; persisted `TestCase.steps` is `list[str]`. |
| I4 | 10/10 | `ASG_ENABLED`, `ASG_SHADOW_MODE`, `ASG_CONFIDENCE_MIN`, `ASG_PROJECT_ALLOWLIST` in `config.py` + `is_asg_enabled_for_project()`. |

### 5) Quality, Testing, and Operations (0.15)

| ID | Score | Prev | Notes |
|----|-------|------|-------|
| Q1 | **10/10** | 4/10 | **70 tests**, **100% coverage** on all 5 ASG modules with `cov-fail-under=100`. Covers `requirement_coverage` / `risk_first` planners, policy bound hits, API error paths, CRUD gaps, feature flags, and execution contract. |
| Q2 | 4/10 | 3/10 | `write_replay_artifact()` emits structured `logger.info` with `graph_id`, `plan_id`, `synthesis_id`, `execution_id`. `build_duration_ms` in build response. **No** dashboard starter or metrics export pipeline. |
| Q3 | 5/10 | 5/10 | Triage steps exist in spec §9 only — not a standalone runbook linked from ops docs. |
| Q4 | 7/10 | 7/10 | ADR-010 authored and complete. Referenced from generator-state and spec; **not** cross-linked from Phase3 docs or API guides. |

---

## Test Execution Summary

### Command (required)

```bash
cd backend && source venv/bin/activate
pytest tests/unit/test_asg*.py -v \
  --cov=app.services.asg_service --cov=app.crud.asg --cov=app.api.v2.endpoints.asg \
  --cov=app.models.asg --cov=app.schemas.asg \
  --cov-report=term-missing --cov-fail-under=100
```

**Result:** 70 passed in ~13s. **Coverage gate passed: 100.00%.**

`backend/pytest.ini` with `pythonpath = .` resolves prior `ModuleNotFoundError: No module named 'app'` without manual `PYTHONPATH=.`.

### Test files

| File | Tests | Purpose |
|------|-------|---------|
| `test_asg_service.py` | 11 | Core fingerprinting, build, plan, synthesize, validate |
| `test_asg_api.py` | 6 | HTTP endpoint contracts |
| `test_asg_integration.py` | 2 | End-to-end pipeline + legacy path unchanged |
| `test_asg_coverage.py` | 50 | Policy engine, planner modes, API errors, CRUD, replay artifact |
| `test_asg_execution_contract.py` | 1 | Synthesize → ExecutionService `string[]` contract |

---

## Coverage by Module

| Module | Stmts | Miss | Cover | Status |
|--------|-------|------|-------|--------|
| `app/models/asg.py` | 77 | 0 | **100%** | ✅ |
| `app/schemas/asg.py` | 91 | 0 | **100%** | ✅ |
| `app/crud/asg.py` | 67 | 0 | **100%** | ✅ |
| `app/api/v2/endpoints/asg.py` | 50 | 0 | **100%** | ✅ |
| `app/services/asg_service.py` | 421 | 0 | **100%** | ✅ |
| **TOTAL** | 706 | 0 | **100%** | ✅ |

---

## Evaluator Checks (1–6)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Build ASG twice; compare deterministic keys | **PASS** | `test_build_deterministic_on_fixed_seed`; edge `deterministic_key` stability in `TestDeterministicKeys`. |
| 2 | Plan twice; stable ranked output | **PASS** | `test_planner_deterministic_for_fixture`; `requirement_coverage` and `risk_first` modes also covered. |
| 3 | Synthesize tests; `steps` is `string[]` | **PASS** | `test_plan_and_synthesize_output_string_steps`, `test_synthesize_endpoint`, `test_end_to_end_pipeline_saves_test_case`. |
| 4 | Force low confidence; verify fallback | **PASS** | `test_validate_recommends_fallback_when_low_confidence`; `test_validate_low_*_confidence_reason` branches. |
| 5 | Execute synthesized tests via execution path | **PASS** | `test_asg_synthesize_then_execution_service_accepts_string_steps` — ASG synthesize → save `TestCase` → `ExecutionService.execute_test` consumes `string[]` steps without schema errors. |
| 6 | Observability includes `graph_id`, `plan_id`, `synthesis_id`, `execution_id` | **PASS** | `write_replay_artifact()` writes `replay/{execution_id}.json` with all four IDs; structured log line on write. Verified in `test_write_replay_artifact` and execution contract test. |

---

## Automatic Fail Conditions

| Condition | Status |
|-----------|--------|
| Breaks `ExecutionService → ThreeTierExecutionService` | ✅ Not broken (unchanged) |
| Changes `TestCase.steps` away from `string[]` | ✅ Preserved |
| Removes confidence-gated fallback | ✅ Present |
| Requires random unbounded crawling for primary flow | ✅ Goal-bounded ASG from `flow_steps` |

---

## KPI Gate Status (pilot — not measurable in this eval)

| KPI | Target | Status |
|-----|--------|--------|
| Deterministic replay pass rate | ≥ 90% | **N/A** — no replay execution harness run |
| Flake rerun delta | ≤ 8% | **N/A** |
| Coverage stability (Jaccard, 3 reruns) | ≥ 0.90 | **N/A** |
| P95 generation latency (≤150 nodes) | ≤ 6 min | **N/A** — unit builds complete in ms |
| Fallback trigger rate (post-tuning) | ≤ 20% | **N/A** |

---

## Critical Issues — Resolved

| Issue (previous) | Status |
|------------------|--------|
| Coverage gap (86% vs 100%) | ✅ **Fixed** — 100% on all 5 modules, 70 tests |
| No execution-path regression test (Check 5) | ✅ **Fixed** — `test_asg_execution_contract.py` |
| Missing `execution_id` observability (Check 6) | ✅ **Fixed** — `write_replay_artifact()` + tests |

---

## Remaining Issues

### Major (should fix before production)

1. **`POST /synthesize` bypasses confidence gate** — Gate only enforced in orchestration primary path; direct API call can synthesize low-confidence graphs. Add gate check or document as intentional admin override.

2. **`write_replay_artifact()` not auto-wired to execution flow** — Function exists and is tested, but `ExecutionService` does not call it after test runs. Call site integration needed for production observability.

3. **No structured metrics export / dashboard** — `build_duration_ms` returned in API but not emitted as persistent metric; no dashboard starter for confidence/fallback/replay KPIs.

### Minor

1. ADR-010 not linked from `Phase3-Implementation-Guide-Complete.md` or API integration guides.

2. Triage playbook embedded in spec only; should be `docs/asg-triage-playbook.md` for on-call use.

3. `plan_id` regenerated as UUID on every plan call — acceptable for artifacts; consider correlation IDs in orchestration logs.

---

## What Improved Since Last Iteration

- **100% ASG module coverage** (up from 86%) with `cov-fail-under=100` gate passing.
- **`backend/pytest.ini`** eliminates `PYTHONPATH=.` requirement.
- **`test_asg_coverage.py`** (50 tests) covers previously untested planner modes, policy bounds, API error handlers, CRUD gaps, feature flags.
- **`test_asg_execution_contract.py`** proves execution-path compatibility (Check 5).
- **`write_replay_artifact()`** delivers `replay/{execution_id}.json` bundle with all four correlated IDs (Check 6, D4).
- **Q1 score: 4/10 → 10/10**; **Criterion 5 weighted contribution: 0.04 → 0.10**.

## What Regressed Since Last Iteration

- None observed.

---

## Recommendations for Next Generator Iteration

1. Wire `write_replay_artifact()` into post-execution hook when `TestCase.strategy == "asg"`.
2. Enforce confidence gate on `/synthesize` or return `fallback_reason_code` when below threshold.
3. Add `asg_build_duration_ms` / `asg_fallback_total` structured metrics and a minimal Grafana/dashboard starter.
4. Extract spec §9 triage playbook to `docs/asg-triage-playbook.md` and link from ADR-010.
5. Cross-link ADR-010 from Phase3 implementation guide.

---

## Screenshots / Live Browser

**Not performed.** Dev server was not running (`generator-state.md`: status *not started*). This evaluation is **code + pytest verification** mode. ASG is a backend API/service feature with no dedicated frontend surface.
