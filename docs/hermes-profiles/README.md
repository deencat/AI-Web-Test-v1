# Hermes QA Factory — Profile Templates (v5)

Version-controlled SOUL.md and config templates for Node 1 deployment.

**Parent plan:** [Hermes_QA_Factory_Agile_Development_Plan.md](../Hermes_QA_Factory_Agile_Development_Plan.md) §4.1, §18  
**Design:** [Hermes_QA_Autonomous_Workflow_v5.md](../Hermes_QA_Autonomous_Workflow_v5.md)  
**v4 templates:** [Hermes_QA_MultiAgent_Profiles_v4.md](../Hermes_QA_MultiAgent_Profiles_v4.md)

## Profiles (all required before launch)

| Profile | Folder | Sprint |
|---------|--------|--------|
| qa-orchestrator | `qa-orchestrator/` | HF-2 draft · HF-3 deploy |
| qa-journey-planner | `qa-journey-planner/` | HF-3 |
| qa-test-gen | `qa-test-gen/` | HF-3 |
| qa-dispatcher | `qa-dispatcher/` | HF-3 |
| qa-reporter | `qa-reporter/` | HF-3 draft · HF-6 webapp |
| qa-change-detector | `qa-change-detector/` | HF-4 |
| qa-healer | `qa-healer/` | HF-5 |
| Hermes Bridge | `bridge/` | HF-6.2 ingest · HF-6.6 service |

## Deploy to Node 1

```bash
# On dev machine — copy templates to Node 1 (adjust host/user)
rsync -av docs/hermes-profiles/ user@node1:~/.hermes/profiles/

# On Node 1 — verify MCP connectivity to AI Web Test
# (from any profile with MCP configured)
curl -s -H "Authorization: Bearer $AWT_MCP_SECRET" http://awt-host:8001/health
```

Set on Node 1 `~/.hermes/.env` (never commit):

- `AWT_MCP_SECRET` — same as backend `.env`
- `TELEGRAM_BOT_TOKEN` — dev only; `HERMES_TELEGRAM_ENABLED=false` in prod AWT

## Master checklist

See agile plan §4.1 — tick each profile before HF-6 launch.
