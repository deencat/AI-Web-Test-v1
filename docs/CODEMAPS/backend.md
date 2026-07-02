# Backend Codemap

**Last Updated:** 2026-07-02
**Entry Points:** `backend/app/main.py`, `backend/app/api/v1/api.py`, `backend/app/api/v2/api.py`

## Architecture

```text
FastAPI app (app/main.py)
  -> API v1 router (/api/v1)
  -> API v2 router (/api/v2)
  -> Services (queue manager, scheduler, AI/test execution)
  -> CRUD layer
  -> SQLAlchemy models
  -> SQLite/PostgreSQL via DATABASE_URL
```

## Key Modules

| Module | Purpose | Exports/Role | Dependencies |
|---|---|---|---|
| `app/main.py` | Bootstraps API, middleware, startup tasks | `app` | config, routers, services, db |
| `app/api/v1/api.py` | Main product API routing | `api_router` | endpoint modules |
| `app/api/v2/api.py` | Agent workflow API routing | `api_router` | agent workflow endpoint modules |
| `app/services/queue_manager.py` | Manages concurrent test execution queue | queue lifecycle | execution services |
| `app/services/scheduler_service.py` | In-process scheduling | scheduler service | execution APIs |
| `app/crud/*` | Data access and business persistence | CRUD functions | models, db session |
| `app/models/*` | SQLAlchemy tables and relationships | ORM entities | SQLAlchemy base |

## API Surface Highlights

- V1 includes auth, users, tests, test categories, executions, feedback, KB, suites, templates, settings, and schedules.
- V2 includes workflow endpoints for generation, observation, requirements, analysis, evolution, improve-tests, and SSE updates.

## Related Areas

- [Database](./database.md)
- [Integrations](./integrations.md)
- [Workers](./workers.md)
