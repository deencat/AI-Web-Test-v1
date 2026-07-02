# Workers Codemap

**Last Updated:** 2026-07-02
**Entry Points:** `backend/app/main.py`, `backend/app/services/queue_manager.py`, `backend/app/services/scheduler_service.py`

## Background Processing Model

```text
App startup
  -> start_queue_manager(max_concurrent, check_interval)
  -> scheduler_service.start()
  -> execution and scheduled jobs processed in-process
```

## Key Worker Components

| Component | Role | Trigger |
|---|---|---|
| Queue Manager | Runs and throttles test executions | Startup + queued jobs |
| Scheduler Service | Handles scheduled test runs | Startup + schedule config |
| Workflow endpoints (v2) | Initiate async-style generation/analysis flows | API requests |

## Observability/Artifacts

- Execution artifacts and screenshots are persisted under backend artifact paths.
- Optional server file logging is enabled via `ENABLE_SERVER_FILE_LOGGING`.
- Flow recordings are configurable with `FLOW_RECORDINGS_ENABLED` and `FLOW_RECORDINGS_DIR`.

## Related Areas

- [Backend](./backend.md)
- [Integrations](./integrations.md)
