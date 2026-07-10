# ADR-010: ASG-Based Deterministic Test Generation

**Document ID:** ADR-010  
**Component:** Test Generation / Crawl Pipeline / API v2  
**Status:** Accepted  
**Date:** July 10, 2026  
**Related Files:**
- `backend/app/models/asg.py`
- `backend/app/services/asg_service.py`
- `backend/app/crud/asg.py`
- `backend/app/schemas/asg.py`
- `backend/app/api/v2/endpoints/asg.py`
- `backend/migrations/add_asg_tables.py`
- `backend/app/api/v2/endpoints/crawl_and_save.py`
- `backend/app/services/orchestration_service.py`

---

## Context

Random browser-use crawling produces unstable `flow_steps`, weak coverage consistency, and high flake on replay. AI Web Test v1 needs bounded, goal-directed exploration with confidence-gated fallback so generated tests are explainable and repeatable.

Baseline expectations (internal): crawl success-to-save ~55–65%, replay pass ~45–60%, flake rerun delta >25%.

## Decision

Introduce an **App State Graph (ASG)** domain with:

1. **Deterministic state fingerprinting** — DOM landmarks + URL + UI traits.
2. **Transition normalization** — crawl actions → stable edge payloads with `deterministic_key`.
3. **Confidence scoring v1** — `selector_stability`, `readiness_signal`, `action_reproducibility`.
4. **Policy engine** — `max_nodes`, `max_depth`, `max_branching`, domain allowlist, forbidden actions.
5. **Path planner** — shortest-path, requirement-coverage, risk-first modes.
6. **Test synthesizer** — outputs `TestCase.steps` as `string[]` via existing `_flow_steps_to_test_steps`.
7. **Confidence gate** — below `ASG_CONFIDENCE_MIN` → legacy fallback with `fallback_reason_code`.

### API (`/api/v2/asg`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/build` | Build graph from crawl artifacts |
| GET | `/{graph_id}` | Graph metadata + confidence distribution |
| POST | `/{graph_id}/plan` | Ranked path set |
| POST | `/{graph_id}/synthesize` | Draft tests + provenance |
| POST | `/{graph_id}/validate` | Replay confidence + fallback recommendation |

### Persistence

Tables (in FK order): `asg_graphs`, `asg_nodes`, `asg_edges`, `asg_paths`, `asg_synthesized_tests`.

Indexes: `(graph_id, state_fingerprint)`, `(graph_id, deterministic_key)`, `(graph_id, score)`.

Artifacts: `artifacts/asg/{graph_id}/build|plan|synthesis/*.json`.

## Constraints Honored

| Constraint | Status |
|------------|--------|
| `ExecutionService → ThreeTierExecutionService` unchanged | ✅ No execution path changes |
| Lazy Tier 2/3 after Tier 1 failure | ✅ Unchanged |
| Router → service → CRUD layering | ✅ |
| SQLAlchemy-only persistence | ✅ |
| `TestCase.steps` remains `array[string]` | ✅ |

## Alternatives Considered

| Alternative | Verdict |
|-------------|---------|
| Tune random crawl only | Rejected — does not fix determinism |
| Full autonomous open-world explorer | Rejected — state explosion, flake |
| Pure rule-based scripts | Rejected — poor adaptability |
| Replace execution runtime | Rejected — out of scope |

## Integration

### crawl-and-save

After observation completes, `trigger_shadow_build()` runs when `ASG_SHADOW_MODE` or `ASG_ENABLED` is on.

### generate-tests (`orchestration_service.run_workflow`)

1. Shadow-build ASG after observation.
2. If `ASG_ENABLED` and confidence ≥ `ASG_CONFIDENCE_MIN` → plan + synthesize + save; skip Requirements/Analysis/Evolution.
3. Else → legacy 4-agent pipeline; log `fallback_reason_code`.

## Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `ASG_ENABLED` | `false` | Master switch for primary ASG output |
| `ASG_SHADOW_MODE` | `true` | Build graphs without replacing legacy |
| `ASG_CONFIDENCE_MIN` | `0.75` | Confidence gate threshold |
| `ASG_PROJECT_ALLOWLIST` | `null` | Progressive rollout by project ID |

## Rollout / Rollback

- **Stage 0:** internal projects, shadow only.
- **Stage 1–3:** progressive cohort enablement via allowlist.
- **Rollback trigger:** replay pass <80% for 24h or fallback rate >40% in enabled cohort → disable `ASG_ENABLED`, keep shadow for diagnosis.

## Observability KPIs

- `asg_build_duration_ms`, `asg_node_count`, `asg_edge_count`
- `asg_confidence_score_mean`, `asg_fallback_rate`, `fallback_reason_code` distribution
- Correlated IDs: `graph_id`, `plan_id`, `synthesis_id`

## Consequences

- Additional DB tables and artifact storage.
- Shadow mode adds build latency on crawl/generate-tests (bounded by policy caps).
- Primary ASG mode bypasses Requirements/Analysis/Evolution when confidence passes — faster but narrower scenario diversity until requirement-coverage planner matures.
