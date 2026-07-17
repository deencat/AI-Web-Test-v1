# Backend Codemap

**Last Updated:** 2026-07-17
**Entry Points:** `backend/app/main.py`, `backend/app/api/v1/api.py`, `backend/app/api/v2/api.py`

## Architecture

```text
FastAPI app (app/main.py)
  -> Middleware (CORS, rate limit, security, timing)
  -> API v1 router (/api/v1) — product APIs (~190 routes)
  -> API v2 router (/api/v2) — agent workflow APIs (~15 routes)
  -> Services (queue, scheduler, execution, generation, ReqIQ proxy)
  -> CRUD layer (app/crud/*)
  -> SQLAlchemy models (app/models/*)
  -> PostgreSQL via DATABASE_URL (SQLite supported for local dev)
```

## Startup Sequence

1. `Base.metadata.create_all` + `run_all_migrations_auto()`
2. `init_db()` + `seed_system_templates()`
3. `start_queue_manager(max_concurrent, check_interval)`
4. `scheduler_service.start()`

## API v1 Routers (`app/api/v1/api.py`)

| Prefix / Tag | Module | Purpose |
|---|---|---|
| `/health` | `health.py` | Health, DB health, detailed health |
| `/auth` | `auth.py` | Login, register, refresh, sessions, password reset |
| `/users` | `users.py` | User management |
| `/tests` | `test_generation.py` | AI test generation |
| `/tests` | `tests.py` | Test case CRUD, batch ops, stats |
| `/tests` | `versions.py` | Version history and rollback |
| `/test-categories` | `test_categories.py` | Saved-test category taxonomy |
| `/executions` | `executions.py` | Run, poll, cancel, queue management |
| `/kb` | `kb.py` | Knowledge base upload and categories |
| `/test-templates` | `test_templates.py` | Template library |
| `/scenarios` | `test_scenarios.py` | Scenario generation and Faker data |
| `/suites` | `test_suites.py` | Test suite CRUD and run |
| `/settings` | `settings.py` | Provider, execution, XPath cache, analytics |
| `/debug` | `debug.py` | Step-by-step debug sessions |
| `/browser-profiles` | `browser_profiles.py` | Persistent browser profiles |
| `/uploads` | `uploads.py` | File upload helper |
| `/email-credentials` | `email_credentials.py` | IMAP OTP credential store |
| `/step-library` | `step_library.py` | Reusable step modules |
| `/requirements` | `requirements.py` | ReqIQ proxy (projects, wiki, RAG) |
| `/hermes` | `hermes.py` | Hermes webhook trigger |
| `/schedules` | `schedules.py` | Cron/interval test scheduling |
| — | `execution_feedback.py` | Execution feedback and corrections |

### Execution Highlights

- `POST /executions/tests/{id}/run` — queue test for 3-tier execution
- `GET /executions/{id}` — poll status (`pending`, `running`, `passed`, `failed`, `cancelled`)
- `DELETE /executions/{id}/cancel` — cooperative cancel (ADR-009)
- `DELETE /executions/{id}` — delete execution record (not cancel)

## API v2 Routers (`app/api/v2/api.py`)

| Endpoint area | Module | Purpose |
|---|---|---|
| `POST /generate-tests` | `generate_tests.py` | Full multi-agent pipeline |
| `POST /observation` | `observation.py` | ObservationAgent only |
| `POST /requirements` | `requirements.py` | RequirementsAgent only |
| `POST /analysis` | `analysis.py` | AnalysisAgent only |
| `POST /evolution` | `evolution.py` | EvolutionAgent only |
| `POST /improve-tests` | `improve_tests.py` | Test improvement workflow |
| `POST /crawl-and-save-test` | `crawl_and_save.py` | Browser-use crawl + save |
| `/workflows/{id}` | `workflows.py` | Status, results, cancel |
| `/workflows/{id}/stream` | `sse_stream.py` | SSE progress stream |

## Key Services

| Module | Purpose |
|---|---|
| `queue_manager.py` | Concurrent execution queue (default max 5) |
| `execution_service.py` | Step loop with cooperative cancel polls |
| `three_tier_execution_service.py` | Playwright → XPath → Stagehand tiers |
| `signature_pad.py` | Shared locate / stroke / ink verify for `draw_signature`/`sign` (ADR-002-54; used by Tier 2/3) |
| `execution_cancel_store.py` | In-memory cancel flags (ADR-009) |
| `scheduler_service.py` | APScheduler-based test schedules |
| `workflow_store.py` | Agent workflow state and cancel |
| `orchestration_service.py` | Multi-agent pipeline coordination |
| `test_generation.py` | LLM test generation |
| `stagehand_factory.py` / adapters | Stagehand browser automation |
| `reqiq_client.py` | ReqIQ HTTP client |
| `kb_context.py` | KB document context for generation |

## Agents (`backend/agents/`)

| Agent | Module |
|---|---|
| Base | `base_agent.py` |
| Observation | `observation_agent.py` |
| Requirements | `requirements_agent.py` |
| Analysis | `analysis_agent.py` |
| Evolution | `evolution_agent.py` |
| Browser-use tool | `browser_use_signature_tool.py` |

## Related Areas

- [Database](./database.md)
- [Execution Engine](./execution-engine.md)
- [Integrations](./integrations.md)
- [Workers](./workers.md)
