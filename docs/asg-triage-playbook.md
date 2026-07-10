# ASG Failure Triage Playbook

Operational runbook for App State Graph (ASG) build, plan, synthesis, and replay failures.

**Related:** [ADR-010: ASG-Based Deterministic Test Generation](../documentation/ADR-010-asg-deterministic-test-generation.md)

---

## 1. Identify the failing stage

Use `fallback_reason_code` and structured logs (`metric=asg_build|asg_plan|asg_synthesis|asg_fallback|asg_replay`) to locate the stage:

| Stage | Symptom | Log keys |
|-------|---------|----------|
| **build** | No graph persisted, build API 400 | `asg_build_duration_ms`, `asg_node_count`, `policy_hits` |
| **plan** | Empty path set, low `asg_plan_success_rate` | `graph_id`, `path_count` |
| **synthesize** | Empty tests, `confidence_gate_passed=false` | `fallback_reason_code`, `asg_synthesis_success_rate` |
| **replay** | Execution fails on ASG-generated steps | `artifacts/asg/{graph_id}/replay/{execution_id}.json` |

Common `fallback_reason_code` values:

- `low_node_confidence` — node fingerprints unstable or sparse landmarks
- `low_edge_confidence` — selector/readiness scores below threshold
- `low_replay_confidence` — aggregate replay confidence below `ASG_CONFIDENCE_MIN`
- `asg_error` — unexpected exception in ASG pipeline (check stack trace)

---

## 2. Pull artifact bundle and confidence report

For graph `{graph_id}`:

```
artifacts/asg/{graph_id}/build/graph.json
artifacts/asg/{graph_id}/build/confidence-report.json
artifacts/asg/{graph_id}/plan/{plan_id}.json
artifacts/asg/{graph_id}/synthesis/{synthesis_id}.json
artifacts/asg/{graph_id}/replay/{execution_id}.json
```

Correlate logs with IDs: `graph_id`, `plan_id`, `synthesis_id`, `execution_id`.

---

## 3. Check policy bound hits

Inspect `policy_hits` in build stats or `graph.json`:

- `max_nodes_reached` — graph truncated; raise `max_nodes` cautiously or narrow seed intents
- `max_depth_reached` — deep navigation; tighten `max_depth` or seed shorter journeys
- `max_branching_reached` — too many outgoing edges from one state; review crawl branching
- `domain_blocked:{host}` — URL outside `domain_allowlist`; update policy or fix crawl scope
- `forbidden_action:{type}` — action filtered by policy

---

## 4. Low confidence (systemic)

If `asg_confidence_below_threshold_count` is high across a cohort:

1. Raise `ASG_CONFIDENCE_MIN` temporarily or keep legacy fallback (`ASG_ENABLED=false`)
2. Review selector stability in edge `action_payload_json` (prefer role+text over bare xpath)
3. Confirm `post_click_readiness` snapshots are present for transitions
4. Open tuning ticket with sample `graph_id` and confidence report

---

## 5. Deterministic mismatch bug

If replay fails but confidence scores look healthy:

1. Quarantine project: remove from `ASG_PROJECT_ALLOWLIST`
2. Compare shadow vs primary diff logs (`metric=asg_shadow_diff`, `step_jaccard_similarity`)
3. Patch planner or synthesizer; add regression fixture to `tests/unit/test_asg*.py`
4. Re-enable cohort only after replay pass rate ≥ 90% in staging

---

## 6. Confirm no execution stack regression

ASG must **not** change the execution dispatch path:

```
ExecutionService → ThreeTierExecutionService
```

Replay artifacts are written in a post-execution hook only. If failures correlate with tier changes unrelated to ASG steps, triage via standard execution RCA — not ASG planner.

---

## 7. Canary rollback triggers

Automatic rollback is recommended when (24h window on enabled cohort):

- **Replay pass rate < 80%** (`asg_replay_pass_rate`)
- **Fallback rate > 40%** (`asg_fallback_total` / attempts)

Use `evaluate_canary_rollback()` in `app.services.asg_metrics` for programmatic checks.

**Rollback actions:**

1. Set `ASG_ENABLED=false` (keep `ASG_SHADOW_MODE=true` for continued metrics)
2. Narrow `ASG_PROJECT_ALLOWLIST`
3. Notify on-call; attach failing `graph_id` artifacts

---

## 8. Feature flags reference

| Flag | Purpose |
|------|---------|
| `ASG_ENABLED` | Master switch for ASG-primary generation |
| `ASG_SHADOW_MODE` | Build/plan metrics without output takeover |
| `ASG_CONFIDENCE_MIN` | Threshold gate (default 0.75) |
| `ASG_PROJECT_ALLOWLIST` | Comma-separated project IDs for progressive rollout |

See `backend/env.example` for defaults.
