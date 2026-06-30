# Backend Codemap

**Last Updated:** 2026-06-30  
**Entry Points:** `backend/app/main.py`, `backend/start_server.py`

## Architecture

```
                    ┌──────────────────────────────────────┐
                    │           FastAPI (main.py)           │
                    │  CORS · rate limit · security · timing │
                    └───────────────┬──────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
     /api/v1 (api.py)                            /api/v2 (api.py)
     CRUD · execution · KB · settings            Agent workflow · crawl-and-save
              │                                           │
              ▼                                           ▼
     endpoints/*.py                              endpoints/*.py
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    ▼
                          services/ · crud/ · models/
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            execution_service   agents/      reqq_client
            three_tier_*        orchestration  openrouter
            queue_manager       workflow_store universal_llm
```

## API Routers

### v1 — `backend/app/api/v1/api.py` (`/api/v1`)

| Prefix / Tag | Module | Purpose |
| --- | --- | --- |
| `health` | `endpoints/health.py` | Liveness, DB health |
| `/auth` | `endpoints/auth.py` | JWT login, register |
| `/users` | `endpoints/users.py` | User profile |
| `/tests` | `endpoints/tests.py`, `test_generation.py`, `versions.py` | Test CRUD, AI generation, versioning |
| `/executions` | `endpoints/executions.py` | Run tests, queue, history, resume |
| `execution-feedback` | `endpoints/execution_feedback.py` | Human feedback on failures |
| `/kb` | `endpoints/kb.py` | Native knowledge base |
| `/test-templates` | `endpoints/test_templates.py` | Template library |
| `/scenarios` | `endpoints/test_scenarios.py` | Scenario management |
| `/suites` | `endpoints/test_suites.py` | Test suite grouping |
| `/settings` | `endpoints/settings.py` | Execution settings, XPath cache |
| `debug` | `endpoints/debug.py` | Interactive debug sessions |
| `browser-profiles` | `endpoints/browser_profiles.py` | Browser profile CRUD |
| `uploads` | `endpoints/uploads.py` | File uploads |
| `email-credentials` | `endpoints/email_credentials.py` | IMAP OTP credentials (ADR-002-38) |
| `step-library` | `endpoints/step_library.py` | Reusable step modules (ADR-002-42) |
| `/requirements` | `endpoints/requirements.py` | ReqIQ proxy |
| `hermes` | `endpoints/hermes.py` | Hermes webhook helpers |
| `schedules` | `endpoints/schedules.py` | Scheduled test runs |

### v2 — `backend/app/api/v2/api.py` (`/api/v2`)

| Router | Module | Purpose |
| --- | --- | --- |
| Agent workflow | `endpoints/generate_tests.py` | Full pipeline entry |
| Observation | `endpoints/observation.py` | Observation agent |
| Requirements | `endpoints/requirements.py` | Requirements agent |
| Analysis | `endpoints/analysis.py` | Analysis agent |
| Evolution | `endpoints/evolution.py` | Evolution agent |
| Improve tests | `endpoints/improve_tests.py` | Test improvement |
| Crawl and save | `endpoints/crawl_and_save.py` | URL crawl → saved test |
| Workflows | `endpoints/workflows.py`, `sse_stream.py` | Status, SSE progress, cancel |

## Key Services

| Module | Purpose | Key Exports |
| --- | --- | --- |
| `execution_service.py` | Browser lifecycle, step loop, delegates to three-tier | `ExecutionService`, `ExecutionConfig` |
| `three_tier_execution_service.py` | Tier dispatch, fallback strategies A/B/C | `ThreeTierExecutionService` |
| `tier1_playwright.py` | CSS/XPath direct Playwright | `Tier1PlaywrightExecutor` |
| `tier2_hybrid.py` | Stagehand `observe()` + Playwright | `Tier2HybridExecutor` |
| `tier3_stagehand.py` | Full Stagehand `act()` | `Tier3StagehandExecutor` |
| `xpath_extractor.py` | XPath via observe | `XPathExtractor` |
| `xpath_cache_service.py` | PostgreSQL-backed selector cache | Cache read/write/invalidate |
| `post_click_readiness.py` | Post-click/navigation waits | Payment, SPA, modal handling |
| `step_progress_guard.py` | Repeated-step progress detection | Confirm-step guard |
| `stagehand_factory.py` | Python vs TypeScript Stagehand adapter | `StagehandFactory` |
| `stagehand_service.py` | Stagehand session management | CDP connect, act/observe |
| `queue_manager.py` | Concurrent execution queue | `start_queue_manager` |
| `execution_queue.py` | Execution job queue | Background workers |
| `scheduler_service.py` | In-process cron schedules | Scheduled runs |
| `orchestration_service.py` | Multi-agent workflow orchestration | Agent pipeline |
| `workflow_store.py` | Workflow state persistence | SSE/progress backing |
| `reqiq_client.py` | ReqIQ HTTP client | Server-side proxy |
| `root_cause_analysis_service.py` | AI failure RCA | Post-execution analysis |
| `email_otp_service.py` | IMAP OTP retrieval | JIT OTP expansion |
| `preprod_otp_service.py` | HTTP OTP for preprod | Non-browser OTP |
| `step_module_resolver.py` | `@module:` step expansion | Step library |
| `universal_llm.py` | Multi-provider LLM routing | Azure, OpenRouter, etc. |
| `debug_session_service.py` | Interactive debug mode | Step-range replay |

## Agents — `backend/agents/`

| Agent | Module | Role |
| --- | --- | --- |
| Requirements | `requirements_agent.py` | PRD/requirements analysis |
| Observation | `observation_agent.py` | Page observation |
| Analysis | `analysis_agent.py` | Failure analysis |
| Evolution | `evolution_agent.py` | Test improvement |
| Base | `base_agent.py` | Shared agent interface |

## Core & Infrastructure

| Path | Purpose |
| --- | --- |
| `app/core/config.py` | Settings (`API_V1_STR`, `API_V2_STR`, CORS, queue limits) |
| `app/core/security.py` | JWT, password hashing |
| `app/core/rate_limit.py` | SlowAPI rate limiting |
| `app/db/session.py` | SQLAlchemy engine/session |
| `app/db/init_db.py` | Seed data |
| `app/middleware/` | Security headers, request timing |
| `backend/migrations/` | Auto-run column/table migrations |
| `backend/run_migrations.py` | Migration runner (called from `main.py`) |

## Data Flow — Test Execution Request

```
POST /api/v1/executions/tests/{id}/execute
    → executions.py validates user, loads test case
    → queue_manager enqueues job
    → execution_service.run_test()
        → Playwright browser + optional Stagehand CDP
        → ThreeTierExecutionService.execute_step() per step
        → Persist TestExecutionStep + screenshots
    → root_cause_analysis_service (on failure, if enabled)
```

## External Dependencies

| Package | Purpose |
| --- | --- |
| FastAPI / Uvicorn | HTTP API |
| SQLAlchemy | ORM |
| Playwright | Browser automation (Tier 1) |
| stagehand (Python) | AI browser control (Tier 2/3) |
| slowapi | Rate limiting |
| cryptography (Fernet) | Email credential encryption |

## Related Codemaps

- [execution-engine.md](./execution-engine.md) — tier details and ADR-002
- [database.md](./database.md) — models
- [integrations.md](./integrations.md) — ReqIQ, Stagehand microservice
