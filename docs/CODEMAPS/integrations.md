# Integrations Codemap

**Last Updated:** 2026-07-02
**Entry Points:** `backend/app/core/config.py`, `backend/agents/*`, `backend/app/services/*`

## External Integrations

| Integration | Config Surface | Primary Use |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | LLM-based test generation |
| Google AI Studio | `GOOGLE_API_KEY`, `GOOGLE_MODEL` | Alternate model provider |
| Cerebras | `CEREBRAS_API_KEY`, `CEREBRAS_MODEL` | Fast inference provider |
| Azure OpenAI | `AZURE_OPENAI_*` | Enterprise model hosting |
| Local vLLM endpoints | `LOCAL_VLLM_*` | On-prem OpenAI-compatible models |
| Playwright/Stagehand | backend services + test execution pipeline | Browser automation and action execution |
| ReqIQ service | `REQIQ_*` | Requirements ingestion/integration |
| Telegram bot | `TELEGRAM_BOT_TOKEN`, `QA_MANAGER_TELEGRAM_CHAT_ID` | Hermes-triggered workflows |

## Integration Flow

```text
API request
  -> service/agent orchestration
  -> model-provider selection from config
  -> external API/browser automation call
  -> normalized response persisted to DB
```

## Operational Notes

- Provider selection is controlled by `MODEL_PROVIDER`.
- Secrets are server-side only (`backend/.env`) and should not be exposed in frontend code.
- Browser automation relies on Playwright-compatible runtime and installed browser binaries.

## Related Areas

- [Backend](./backend.md)
- [Workers](./workers.md)
