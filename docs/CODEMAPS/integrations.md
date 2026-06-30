# Integrations Codemap

**Last Updated:** 2026-06-30

## System Context

```
┌──────────────┐     HTTP proxy      ┌──────────────────┐
│    ReqIQ     │◄───────────────────►│   AI Web Test    │
│  :3001 API   │  requirements.py    │   :8000 API      │
│  :8080 UI    │  reqq_client.py     │   :5173 UI       │
└──────────────┘                     └────────┬─────────┘
                                              │
┌──────────────┐     MCP / HTTP              │
│   Hermes     │─────────────────────────────┤
│  (external)  │  crawl-and-save, execute    │
└──────────────┘                             │
                                             ▼
                              ┌──────────────────────────┐
                              │  LLM Providers            │
                              │  OpenRouter · Azure ·     │
                              │  Google · Cerebras        │
                              └──────────────────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              ▼                             ▼
                    stagehand (Python)          stagehand-service (TS)
                    in-process CDP              :3001 optional proxy
```

## ReqIQ Integration

**Purpose:** ReqIQ is the requirements intelligence hub; AI Web Test proxies its API for standard users.

| Component | Path |
| --- | --- |
| HTTP client | `backend/app/services/reqiq_client.py` |
| Proxy routes | `backend/app/api/v1/endpoints/requirements.py` |
| Frontend | `frontend/src/services/requirementsService.ts` |
| Env vars | `REQIQ_URL`, `REQIQ_SERVICE_EMAIL`, `REQIQ_SERVICE_PASSWORD` |

**Documentation:**

- [`docs/AI-Web-Test-Developer-Handoff.md`](../AI-Web-Test-Developer-Handoff.md) — primary integration handoff
- [`docs/openapi/reqiq-api-v1.yaml`](../openapi/reqiq-api-v1.yaml) — ReqIQ OpenAPI (companion system, **not** AI Web Test API)
- [`docs/openapi/README.md`](../openapi/README.md) — OpenAPI folder guide

**Note:** ReqIQ ships in a separate repository (`apps/api`, `apps/web`). Files referenced in older docs (`ReqIQ_Software_Requirements_Specification.md`, `Wiki-Compile-Strategy.md`) are not in this repo.

## Hermes Multi-Agent QA

**Purpose:** External orchestrator calling AI Web Test and ReqIQ via HTTP/MCP.

| AI Web Test endpoint | Hermes agent | Guide section |
| --- | --- | --- |
| `POST /api/v2/crawl-and-save-test` | qa-test-gen | ReqIQ-API-Integration-Guide §3 |
| `POST /api/v1/executions/tests/{id}/execute` | qa-dispatcher | §7 |
| `GET /api/v1/executions/{id}/step-results` | qa-reporter | §8 |
| ReqIQ RAG/requirements | qa-requirements | ReqIQ side |

**Documentation:**

- [`docs/Hermes_QA_MultiAgent_Profiles_v3.md`](../Hermes_QA_MultiAgent_Profiles_v3.md)
- [`docs/Hermes_QA_MultiAgent_Profiles_v4.md`](../Hermes_QA_MultiAgent_Profiles_v4.md)
- [`docs/Hermes_QA_Autonomous_Workflow_v5.md`](../Hermes_QA_Autonomous_Workflow_v5.md)
- `backend/app/api/v1/endpoints/hermes.py` — webhook helpers

## Stagehand (Browser AI)

Two deployment modes selected by user setting (`stagehand_provider`):

### Python Stagehand (default)

| Component | Path |
| --- | --- |
| Adapter | `backend/app/services/python_stagehand_adapter.py` |
| Core service | `backend/app/services/stagehand_service.py` |
| Factory | `backend/app/services/stagehand_factory.py` |

Uses in-process `stagehand` Python package with CDP attachment to Playwright browser.

### TypeScript Microservice (optional)

| Component | Path |
| --- | --- |
| Service root | `stagehand-service/` |
| Entry | `stagehand-service/src/index.ts` |
| Sessions | `stagehand-service/src/routes/sessions.ts` |
| Execution | `stagehand-service/src/routes/execution.ts` |
| Adapter | `backend/app/services/typescript_stagehand_adapter.py` |

Default port: **3001** (conflicts with ReqIQ API if both run locally — configure via env).

## LLM Providers

Routed through `backend/app/services/universal_llm.py` and provider-specific modules:

| Provider | Module / config | Use |
| --- | --- | --- |
| OpenRouter | `openrouter.py`, `OPENROUTER_API_KEY` | Test generation, RCA |
| Azure OpenAI | `universal_llm.py` | Stagehand init (ADR-002-11) |
| Google Gemini | User settings | Test generation |
| Cerebras | User settings | Fast inference |

User-selectable models stored in `UserSetting` / execution AI config.

## Native Knowledge Base vs ReqIQ

| System | API prefix | Storage |
| --- | --- | --- |
| AI Web Test native KB | `/api/v1/kb/*` | Local DB + file storage |
| ReqIQ documents | Proxied `/api/v1/requirements/*` | ReqIQ Postgres |

Standard users typically use ReqIQ-sourced requirements via proxy; native KB remains for standalone deployments.

## OpenAPI Contracts

| Spec | Path | System |
| --- | --- | --- |
| AI Web Test (live) | `http://127.0.0.1:8000/api/v1/openapi.json` | This repo |
| AI Web Test (static) | `backend/openapi_spec.json` | Exported snapshot |
| ReqIQ | `docs/openapi/reqiq-api-v1.yaml` | Companion ReqIQ repo |

**Swagger UI:** `http://127.0.0.1:8000/api/v1/docs` (not `/docs` at root)

## Email / OTP Integrations

| Service | Path | ADR |
| --- | --- | --- |
| IMAP OTP | `email_otp_service.py` | ADR-002-38–41 |
| Preprod HTTP OTP | `preprod_otp_service.py` | ADR-002-47 |
| Router | `otp_source_router.py` | Step-context routing |
| Credentials UI | `EmailCredentialsSection.tsx` | Encrypted storage |

## Related Codemaps

- [backend.md](./backend.md) — integration service modules
- [execution-engine.md](./execution-engine.md) — Stagehand tier usage
- [INDEX.md](./INDEX.md) — documentation index
