# Integrations Codemap

**Last Updated:** 2026-07-03
**Entry Points:** `backend/app/core/config.py`, `backend/agents/*`, `backend/app/services/*`

## External Integrations

| Integration | Config Surface | Primary Use |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Default LLM test generation |
| Google AI Studio | `GOOGLE_API_KEY`, `GOOGLE_MODEL` | Alternate model provider |
| Cerebras | `CEREBRAS_API_KEY`, `CEREBRAS_MODEL` | Fast inference (agents) |
| Azure OpenAI | `AZURE_OPENAI_*`, `AZURE_OPENAI_GPT52_*` | Enterprise / agent models |
| Local vLLM | `LOCAL_VLLM_*_ENDPOINT` | On-prem OpenAI-compatible models |
| LiteLLM | `litellm` package | Unified LLM routing for Stagehand |
| Playwright | `playwright==1.56.0` | Tier 1 browser automation |
| Stagehand | `stagehand==0.5.6` | Tier 3 AI browser actions |
| Browser-Use | `browser-use>=0.12.1` | Crawl-and-save flow navigation |
| ReqIQ | `REQIQ_URL`, `REQIQ_SERVICE_TOKEN` | Requirements/wiki/RAG proxy |
| Telegram | `TELEGRAM_BOT_TOKEN`, `QA_MANAGER_TELEGRAM_CHAT_ID` | Hermes notifications |
| Redis | `redis:7-alpine` (docker-compose) | Cache/queue (future multi-worker cancel) |
| MCP | `mcp>=1.8.0` | Hermes agent HTTP tools |

## Provider Selection

- `MODEL_PROVIDER`: `openrouter` | `google` | `cerebras` | `azure` | `local_vllm`
- Per-user overrides via `/api/v1/settings/provider`
- Stagehand provider separate: `/api/v1/settings/stagehand-provider`

## Integration Flow

```text
API request
  -> service or agent orchestration
  -> provider selection (config + user settings)
  -> external LLM / browser / ReqIQ call
  -> normalized response persisted to DB
```

## ReqIQ Proxy (`/api/v1/requirements/*`)

Server-side proxy to ReqIQ API — credentials never exposed to browser. Covers projects, sources, requirements, wiki compile, RAG query, coverage matrix, export. See `docs/AI-Web-Test-Developer-Handoff.md`.

## Hermes Integration

- `POST /api/v1/hermes/trigger` — webhook entry for autonomous QA workflows
- MCP tool URLs documented in `docs/Hermes_QA_MultiAgent_Profiles_v*.md`

## Browser Automation Stack

```text
Tier 1: tier1_playwright.py (CSS/XPath selectors)
Tier 2: tier2_hybrid.py (XPath cache fallback)
Tier 3: tier3_stagehand.py (Stagehand AI actions)
Crawl: browser-use via crawl_and_save endpoint
```

## Operational Notes

- Secrets are server-side only (`backend/.env`).
- Playwright requires `playwright install chromium` in backend venv.
- Windows: use `WindowsProactorEventLoopPolicy` for subprocess support (see `main.py`).
- Flow recordings: `FLOW_RECORDINGS_ENABLED`, `FLOW_RECORDINGS_DIR`.

## Related Areas

- [Backend](./backend.md)
- [Execution Engine](./execution-engine.md)
- [Workers](./workers.md)
