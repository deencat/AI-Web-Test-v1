# Shared Hermes profile assets (HF-2.7)

Templates used across `docs/hermes-profiles/*` — copy into each profile's `config.yaml`.

## Files

| File | Use |
|------|-----|
| [mcp_servers.yaml.example](mcp_servers.yaml.example) | `mcp_servers:` blocks for orchestrator, test-gen, dispatcher |
| [MCP_CONNECTIVITY.md](MCP_CONNECTIVITY.md) | Verify MCP from Ubuntu Node 1 |

## Deploy to Node 1

```bash
# From AI Web Test repo (dev or prod)
rsync -av docs/hermes-profiles/ user@hermes-host:~/.hermes/profiles/

# Or migration scripts
cd scripts/hermes-migrate
./deploy-profiles.sh --from-git /path/to/AI-Web-Test-v1-2
```

Then set `~/.hermes/.env` from `scripts/hermes-migrate/hermes.env.dev.example` or `.prod.example`.

## Which profiles need MCP?

| Profile | MCP `ai-web-test` |
|---------|-------------------|
| qa-orchestrator | ✅ |
| qa-journey-planner | ✅ (coverage, backlog tools) |
| qa-test-gen | ✅ (crawl_and_save, workflows) |
| qa-dispatcher | ✅ |
| qa-change-detector | ✅ (snapshot tools) |
| qa-healer | ✅ (heal, xpath cache) |
| qa-reporter | Optional (stats) |

ReqIQ is reached via **AWT MCP proxy** (`get_coverage_matrix`, `get_reqiq_readiness`) using `REQIQ_PROJECT_ID` in `~/.hermes/.env`.
