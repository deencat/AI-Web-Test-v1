# qa-orchestrator

Single chat entry for Hermes QA Factory (replaces v4 `qa-manager`).

| File | Purpose |
|------|---------|
| `SOUL.md` | System prompt — job routing, delegate tree |
| `config.yaml` | MCP connection to AI Web Test (`:8001`) |

## Install on Ubuntu (Hermes Node)

```bash
hermes profile create "qa-orchestrator"
cp SOUL.md ~/.hermes/profiles/qa-orchestrator/
cp config.yaml ~/.hermes/profiles/qa-orchestrator/
# Ensure ~/.hermes/.env has AWT_MCP_URL and AWT_MCP_SECRET
qa-orchestrator model   # pick orchestrator model (e.g. Claude Sonnet)
```

## Smoke

```bash
# MCP from Ubuntu
source ~/.hermes/.env
curl -sf -H "Authorization: Bearer $AWT_MCP_SECRET" "${AWT_MCP_URL}/health"

# Via Hermes (calls MCP health_check tool)
qa-orchestrator
# > Run health_check on ai-web-test MCP
```

## Bridge job run (production path)

AWT Agent Console → Bridge `POST /run` with `job_type` — orchestrator receives JSON.
See `docs/hermes-profiles/bridge/README.md`.
