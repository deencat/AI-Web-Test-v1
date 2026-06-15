# Hermes QA Factory — Profile Templates (v5)

Version-controlled SOUL.md and config templates for Node 1 deployment.

**Parent plan:** [Hermes_QA_Factory_Agile_Development_Plan.md](../Hermes_QA_Factory_Agile_Development_Plan.md) §4.1, §4.3, §18  
**Design:** [Hermes_QA_Autonomous_Workflow_v5.md](../Hermes_QA_Autonomous_Workflow_v5.md)  
**Migration (dev → prod):** [Hermes_Environment_Migration_Guide.md](Hermes_Environment_Migration_Guide.md) · [scripts/hermes-migrate/](../../scripts/hermes-migrate/)  
**Ubuntu mini PC first-time setup:** [UBUNTU_DEV_SETUP.md](UBUNTU_DEV_SETUP.md) ← **start here on Node 1**  
**v4 templates:** [Hermes_QA_MultiAgent_Profiles_v4.md](../Hermes_QA_MultiAgent_Profiles_v4.md)

## Environment strategy (HF-7)

1. **Dev** — small Ubuntu mini PC: install Hermes, copy profiles, smoke test.  
2. **Package** — `scripts/hermes-migrate/pack-profiles.sh` or commit to this folder.  
3. **Prod** — bigger Ubuntu PC: `deploy-profiles.sh` + prod `~/.hermes/.env` only (URLs + rotated secrets).

Do **not** clone the whole machine. Do **not** copy `memories/` or dev secrets to prod.

## Profiles (all required before launch)

| Profile | Folder | Sprint |
|---------|--------|--------|
| qa-orchestrator | `qa-orchestrator/` | HF-2.6 ✅ · HF-3 deploy |
| qa-journey-planner | `qa-journey-planner/` | HF-3.1b ✅ · deploy |
| qa-test-gen | `qa-test-gen/` | HF-3.1c ✅ · deploy |
| qa-dispatcher | `qa-dispatcher/` | HF-3 |
| qa-reporter | `qa-reporter/` | HF-3 draft · HF-6 webapp |
| qa-change-detector | `qa-change-detector/` | HF-4 |
| qa-healer | `qa-healer/` | HF-5 |
| Hermes Bridge | `bridge/` | HF-6.2 ingest · HF-6.6 service |
| Shared MCP | `_shared/` | HF-2.7 ✅ |

## qa-orchestrator (HF-2.6) — deploy first

[qa-orchestrator/README.md](qa-orchestrator/README.md) · [SOUL.md](qa-orchestrator/SOUL.md)

## qa-journey-planner (HF-3.1b)

[qa-journey-planner/README.md](qa-journey-planner/README.md) · [SOUL.md](qa-journey-planner/SOUL.md)

## qa-test-gen (HF-3.1c)

[qa-test-gen/README.md](qa-test-gen/README.md) · [SOUL.md](qa-test-gen/SOUL.md)

## HF-3.1d integration smoke

[HF-3.1d_Integration_Smoke.md](HF-3.1d_Integration_Smoke.md) — orchestrator → planner → test-gen acceptance.

```bash
# Ubuntu (after deploy)
./scripts/hermes-migrate/smoke-integration-3.1d.sh --planner-only   # fast
./scripts/hermes-migrate/smoke-integration-3.1d.sh                # full (15–45 min)
```

## Shared MCP template (HF-2.7)

[_shared/README.md](_shared/README.md) · [MCP_CONNECTIVITY.md](_shared/MCP_CONNECTIVITY.md) · [mcp_servers.yaml.example](_shared/mcp_servers.yaml.example)

## Deploy to Node 1 (first time)

```bash
# From repo on dev machine — copy templates to Ubuntu Hermes host
rsync -av docs/hermes-profiles/ user@hermes-dev:~/.hermes/profiles/

# Or use migration script (on Ubuntu)
cd scripts/hermes-migrate
cp hermes.env.dev.example ~/.hermes/.env   # edit hosts + secrets
./deploy-profiles.sh --from-git /path/to/AI-Web-Test-v1-2
./smoke-check.sh --env dev
```

Verify MCP:

```bash
curl -s -H "Authorization: Bearer $AWT_MCP_SECRET" $AWT_MCP_URL/health
```

Set on Node 1 `~/.hermes/.env` (never commit) — use `scripts/hermes-migrate/hermes.env.dev.example` as template.

## Master checklist

See agile plan §4.1 — tick each profile before HF-6 launch.  
See §4.3 + [Hermes_Environment_Migration_Guide.md](Hermes_Environment_Migration_Guide.md) before prod cutover.
