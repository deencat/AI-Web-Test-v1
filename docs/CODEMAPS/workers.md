# Workers Codemap

**Last Updated:** 2026-07-03
**Entry Points:** `backend/app/main.py`, `backend/app/services/queue_manager.py`, `backend/app/services/scheduler_service.py`

## Background Processing Model

```text
App startup (main.py)
  -> start_queue_manager(max_concurrent=5, check_interval=2s)
  -> scheduler_service.start()  (APScheduler, in-process)
  -> API requests enqueue work; workers poll cooperatively
```

All processing is **in-process** (no separate Celery/RQ worker). Single-process deployments use in-memory cancel stores.

## Key Worker Components

| Component | Module | Role |
|---|---|---|
| Queue Manager | `queue_manager.py` | Throttles concurrent test runs; dequeues pending jobs |
| Execution Service | `execution_service.py` | Step loop; polls `execution_cancel_store` between steps |
| 3-Tier Executor | `three_tier_execution_service.py` | `cancel_check` callback at tier boundaries |
| Cancel Store | `execution_cancel_store.py` | Thread-safe in-memory flags (ADR-009) |
| Scheduler | `scheduler_service.py` | Cron/interval scheduled test triggers |
| Workflow Store | `workflow_store.py` | Agent workflow state + cooperative cancel (ADR-004) |
| Orchestration | `orchestration_service.py` | Multi-agent pipeline async execution |

## Cooperative Cancel (ADR-009)

```text
DELETE /executions/{id}/cancel
  -> pending: dequeue + DB status=cancelled
  -> running: set in-memory cancel flag
  -> worker polls is_cancel_requested() between steps/tiers
  -> finalize: status=cancelled, partial steps preserved
  -> finally: clear_cancel() + browser cleanup
```

Terminal states (`completed`, `failed`, `cancelled`) return **204** idempotently on repeat cancel.

**Limitation:** Cancel latency bounded by current step (up to ~120s mid–Tier 3 LLM). Multi-worker deployments need Redis-backed store (deferred).

## Agent Workflow Workers

- v2 endpoints spawn background tasks tracked in `workflow_store.py`
- `DELETE /api/v2/workflows/{id}` — cooperative agent cancel
- SSE stream: `GET /api/v2/workflows/{id}/stream`

## Observability / Artifacts

| Artifact | Location |
|---|---|
| Screenshots | `backend/artifacts/screenshots/` |
| Flow recordings | `artifacts/flow_recordings/{workflow_id}/` |
| Server logs | `backend/logs/` (when `ENABLE_SERVER_FILE_LOGGING=true`) |
| LLM response logs | via `llm_response_logger.py` |

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `MAX_CONCURRENT_EXECUTIONS` | 5 | Queue concurrency |
| `QUEUE_CHECK_INTERVAL` | 2 | Queue poll seconds |
| `EXECUTION_TIMEOUT` | 300 | Max run seconds |

## Related Areas

- [Backend](./backend.md)
- [Integrations](./integrations.md)
- [ADR-009](../../documentation/ADR-009-execution-cancel.md)
