# Agent / developer notes — AI Web Test v1

**Last Updated:** 2026-06-30

## Product context

**AI Web Test** is a self-hosted AI-powered web testing platform: natural-language test generation, browser execution (Playwright + Stagehand), knowledge base, test suites, and multi-agent workflows. It integrates with **ReqIQ** (requirements hub) and **Hermes** (external multi-agent orchestration).

**Canonical execution architecture:** [`documentation/ADR-002-test-execution-engine.md`](../documentation/ADR-002-test-execution-engine.md) (Accepted, March 2026) — three-tier engine with 52 sub-decisions.

**Codemaps (generated from codebase):** [`docs/CODEMAPS/INDEX.md`](CODEMAPS/INDEX.md)

## Repo layout

| Path | Role |
| --- | --- |
| `backend/` | FastAPI API (`/api/v1`, `/api/v2`), three-tier execution engine, agents |
| `frontend/` | React 18 + Vite SPA (`:5173`) |
| `stagehand-service/` | Optional TypeScript Stagehand microservice |
| `backend/agents/` | Requirements, observation, analysis, evolution agents |
| `documentation/` | ADRs, architecture, PM plans (active — not `archive/`) |
| `docs/` | Developer handoff, Hermes profiles, ReqIQ OpenAPI, **CODEMAPS** |
| `tests/e2e/` | Playwright E2E tests |

## Quick start

```bash
# Backend
cd backend && python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt && playwright install chromium
python start_server.py           # http://127.0.0.1:8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

- **API docs:** `http://127.0.0.1:8000/api/v1/docs`
- **OpenAPI JSON:** `http://127.0.0.1:8000/api/v1/openapi.json` (static export: `backend/openapi_spec.json`)
- **Default login:** `admin@aiwebtest.com` / `admin123`

For LAN/Hermes access, run Uvicorn with `--host 0.0.0.0` and allow TCP **8000** in firewall.

## Three-tier test execution (ADR-002)

| Tier | Engine | Cost | When |
| --- | --- | --- | --- |
| **1** | Playwright direct (CSS/XPath) | Zero LLM | First attempt (~85–90%) |
| **2** | Stagehand `observe()` + Playwright | Low LLM | Tier 1 failure (Hybrid) |
| **3** | Stagehand `act()` full AI | High LLM | Tier 1+2 failure |

Fallback strategies (user-configurable): **A** T1→T2, **B** T1→T3, **C** T1→T2→T3.

Key modules: `backend/app/services/execution_service.py` → `three_tier_execution_service.py` → `tier1_playwright.py` / `tier2_hybrid.py` / `tier3_stagehand.py`.

See [`docs/CODEMAPS/execution-engine.md`](CODEMAPS/execution-engine.md) for full flow.

## API surfaces

| Version | Prefix | Purpose |
| --- | --- | --- |
| v1 | `/api/v1` | CRUD, execution, KB, settings, ReqIQ proxy, debug |
| v2 | `/api/v2` | Agent workflow, crawl-and-save, SSE progress |

Router entry: `backend/app/api/v1/api.py`, `backend/app/api/v2/api.py`.

## ReqIQ integration (companion system)

ReqIQ is a **separate** requirements/RAG product. AI Web Test proxies ReqIQ for standard users so they never need the ReqIQ UI directly.

| Document | Purpose |
| --- | --- |
| [`docs/AI-Web-Test-Developer-Handoff.md`](AI-Web-Test-Developer-Handoff.md) | **Primary** ReqIQ ↔ AI Web Test integration handoff |
| [`docs/ReqIQ-API-Integration-Guide.md`](ReqIQ-API-Integration-Guide.md) | AI Web Test API for external integrators (Hermes) |
| [`docs/openapi/reqiq-api-v1.yaml`](openapi/reqiq-api-v1.yaml) | ReqIQ OpenAPI contract (import to Postman) |
| [`docs/openapi/README.md`](openapi/README.md) | OpenAPI folder guide |

**Server config (backend `.env`):** `REQIQ_URL`, `REQIQ_SERVICE_EMAIL`, `REQIQ_SERVICE_PASSWORD`.

**Production split:** Use LAN IP/hostname in Hermes MCP tools — `127.0.0.1` is local to each machine only. Update `BACKEND_CORS_ORIGINS` when ReqIQ runs on a different host.

> **Note:** Some older docs reference ReqIQ files not present in this repo (`ReqIQ_Software_Requirements_Specification.md`, `Wiki-Compile-Strategy.md`, `apps/api`). Those live in the ReqIQ repository.

## Hermes / agentic QA

External Hermes setups call AI Web Test HTTP APIs for crawl, execute, and report. See:

- [`docs/Hermes_QA_MultiAgent_Profiles_v3.md`](Hermes_QA_MultiAgent_Profiles_v3.md)
- [`docs/Hermes_QA_Autonomous_Workflow_v5.md`](Hermes_QA_Autonomous_Workflow_v5.md)

Typical flow: ReqIQ RAG → `POST /api/v2/crawl-and-save-test` → `POST /api/v1/executions/tests/{id}/execute` → `GET /api/v1/executions/{id}/step-results`.

## Other ADRs

| ADR | Topic |
| --- | --- |
| [ADR-002](../documentation/ADR-002-test-execution-engine.md) | Three-tier execution engine |
| [ADR-003](../documentation/ADR-003-test-generation.md) | Test generation |
| [ADR-004](../documentation/ADR-004-agent-workflow.md) | Agent workflow |
| [ADR-005](../documentation/ADR-005-kb.md) | Knowledge base |
| [ADR-006](../documentation/ADR-006-crawl-and-save.md) | Crawl-and-save |
| [ADR-007](../documentation/ADR-007-test-suites.md) | Test suites |

## Traceability

Tag PRs/commits with requirement IDs when applicable. See project SRS in `documentation/AI-Web-Test-v1-SRS.md`.

## Commands

```bash
# Backend tests (activate venv first)
cd backend && python -m pytest tests/unit/ -q

# Frontend tests
cd frontend && npm run test

# E2E
npx playwright test tests/e2e/
```

See root [`README.md`](../README.md) for full setup and Phase 3 agent testing.
