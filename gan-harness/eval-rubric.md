# Evaluation Rubric: Defer Agent Workflow Nav

**Weight total: 1.0**

## Functionality (0.4)

| Criterion | Pass |
|-----------|------|
| Agent Workflow absent from sidebar | Nav labels do not include "Agent Workflow" or "Agent Console" |
| Direct URL handling | `/agent-workflow` does not render incomplete page to end users (redirect or 404) |
| Core app unaffected | Dashboard, Tests, KB, Settings, Executions still reachable |
| No regressions | `npm test` / build in frontend passes |

## Documentation (0.3)

| Criterion | Pass |
|-----------|------|
| ADR-004 amended | Header notes frontend deferral; Status distinguishes API-ready vs nav-deferred |
| No contradiction | Technical ADR decisions (004-1–004-8) unchanged |
| Re-enable path | ADR or spec mentions files to restore |

## Scope discipline (0.2)

| Criterion | Pass |
|-----------|------|
| Minimal diff | No deletion of `features/agent-workflow`, backend v2, or agent tests |
| Agent Console | No spurious new files; acknowledged as not yet in codebase |

## Craft (0.1)

| Criterion | Pass |
|-----------|------|
| Clean imports | No unused `Bot` import in Sidebar |
| Consistent redirect | Uses existing `Navigate` pattern from `App.tsx` |

**Pass threshold:** ≥ 0.85 weighted score; any failure in "Agent Workflow absent from sidebar" is automatic fail.
