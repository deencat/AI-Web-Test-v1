# AI Web Test — Codemap Index

**Last Updated:** 2026-06-30  
**Repository:** `AI-Web-Test-v1`  
**Canonical architecture decisions:** [`documentation/ADR-002-test-execution-engine.md`](../../documentation/ADR-002-test-execution-engine.md) (Accepted, March 2026)

## Overview

AI Web Test is an AI-powered web testing platform: FastAPI backend, React/Vite frontend, PostgreSQL (production) or SQLite (dev), and a **three-tier test execution engine** (Playwright → Hybrid observe → Stagehand act). It integrates with **ReqIQ** (requirements hub) and **Hermes** (multi-agent orchestration).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI Web Test Platform                             │
├─────────────────────────────────────────────────────────────────────────┤
│  frontend/ (:5173)          backend/ (:8000)         stagehand-service/ │
│  React + TypeScript    →    FastAPI + SQLAlchemy  →  (optional TS proxy) │
│  Execution UI, KB,          Three-tier engine,         Session API       │
│  agent workflow             queue, agents, ReqIQ proxy                   │
└─────────────────────────────────────────────────────────────────────────┘
         │                              │                    │
         │                              ▼                    │
         │                    PostgreSQL / SQLite              │
         │                              │                    │
         └──────────────────────────────┼────────────────────┘
                                        ▼
                              ReqIQ (:3001) · Hermes · LLM providers
```

## Codemaps

| Codemap | Scope |
| --- | --- |
| [backend.md](./backend.md) | FastAPI app, API v1/v2 routers, services, agents |
| [frontend.md](./frontend.md) | React pages, services, features, routing |
| [execution-engine.md](./execution-engine.md) | Three-tier execution flow, tiers, supporting services |
| [database.md](./database.md) | SQLAlchemy models and persistence |
| [integrations.md](./integrations.md) | ReqIQ, Hermes, Stagehand, LLM providers |

## Entry Points

| Component | Path | Dev URL |
| --- | --- | --- |
| Backend API | `backend/app/main.py` | `http://127.0.0.1:8000` |
| Swagger UI | `backend/app/main.py` (FastAPI) | `http://127.0.0.1:8000/api/v1/docs` |
| OpenAPI JSON (AI Web Test) | Generated at runtime | `http://127.0.0.1:8000/api/v1/openapi.json` |
| OpenAPI JSON (static export) | `backend/openapi_spec.json` | Import into Postman |
| Frontend SPA | `frontend/src/main.tsx` | `http://localhost:5173` |
| Stagehand microservice | `stagehand-service/src/index.ts` | `http://localhost:3001` (when enabled) |

## Key Documentation (non-archive)

| Document | Purpose |
| --- | --- |
| [`documentation/ADR-002-test-execution-engine.md`](../../documentation/ADR-002-test-execution-engine.md) | **Accepted** three-tier execution decisions (52 ADRs) |
| [`documentation/ADR-004-agent-workflow.md`](../../documentation/ADR-004-agent-workflow.md) | Agent workflow architecture |
| [`docs/AI-Web-Test-Developer-Handoff.md`](../AI-Web-Test-Developer-Handoff.md) | ReqIQ ↔ AI Web Test integration handoff |
| [`docs/ReqIQ-API-Integration-Guide.md`](../ReqIQ-API-Integration-Guide.md) | External integrator API guide (Hermes, ReqIQ) |
| [`docs/AGENTS.md`](../AGENTS.md) | Agent/developer orientation for this repo |
| [`docs/openapi/reqiq-api-v1.yaml`](../openapi/reqiq-api-v1.yaml) | **ReqIQ** OpenAPI contract (companion system) |

## Related Areas Outside This Repo

- **ReqIQ** ships its own `apps/api`, `apps/web`, and sprint docs — referenced from `docs/` but not built in this repository.
- **`documentation/archive/`** — historical sprint notes; do not treat as current architecture.
