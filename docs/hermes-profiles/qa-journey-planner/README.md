# qa-journey-planner

Coverage gaps, ReqIQ readiness, and journey backlog enqueue (Loop A planner step).

| File | Purpose |
|------|---------|
| `SOUL.md` | System prompt — matrix, readiness, enqueue |
| `config.yaml` | MCP connection to AI Web Test (`:8001`) |

## Install on Ubuntu (Hermes Node)

```bash
hermes profile create "qa-journey-planner"
cp SOUL.md ~/.hermes/profiles/qa-journey-planner/
cp config.yaml ~/.hermes/profiles/qa-journey-planner/
# ~/.hermes/.env needs AWT_MCP_* and REQIQ_PROJECT_ID
qa-journey-planner model
```

## Smoke (via orchestrator delegate)

After orchestrator smoke passes:

```bash
qa-orchestrator chat -q 'delegate to qa-journey-planner: drain_backlog for Three-HK max_items 1'
```

**Acceptance (HF-3.1b):** delegated task returns a backlog item or `items_for_test_gen` row for a coverage gap.

## MCP tools used

`get_coverage_matrix`, `get_reqiq_readiness`, `suggest_scenarios_from_wiki`, `list_test_cases`,
`list_journey_backlog`, `enqueue_journey` — see [MCP_CONNECTIVITY.md](../_shared/MCP_CONNECTIVITY.md).
