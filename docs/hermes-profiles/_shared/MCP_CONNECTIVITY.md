# MCP connectivity — Node 1 → AI Web Test (HF-2.7)

Verify Hermes Ubuntu can reach the AI Web Test MCP server before deploying profiles.

## Prerequisites

On **AI Web Test** host (`backend/.env`):

```env
AWT_MCP_SECRET=your-shared-secret
AWT_MCP_PORT=8001
```

Start MCP (included in `start_server.py` when secret is set, or manually):

```bash
cd backend
python mcp_server.py
```

On **Hermes Ubuntu** (`~/.hermes/.env`):

```env
AWT_MCP_URL=http://<awt-host-ip>:8001
AWT_MCP_SECRET=<same secret as AWT>
```

Use LAN IP reachable from Ubuntu (not `localhost` unless Hermes runs on same machine).

## Step 1 — HTTP health (no MCP session)

```bash
source ~/.hermes/.env
curl -v -H "Authorization: Bearer ${AWT_MCP_SECRET}" "${AWT_MCP_URL}/health"
```

Expected: HTTP 200, JSON body indicating API healthy.

## Step 2 — MCP Bearer on streamable endpoint

```bash
curl -sf -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer ${AWT_MCP_SECRET}" \
  -H "Content-Type: application/json" \
  "${AWT_MCP_URL}/mcp"
```

Expected: not 401 (401 = wrong `AWT_MCP_SECRET`).

## Step 3 — `health_check` MCP tool (via Hermes)

After copying `qa-orchestrator/config.yaml`:

```bash
hermes profile create "qa-orchestrator"   # if not exists
cp docs/hermes-profiles/qa-orchestrator/* ~/.hermes/profiles/qa-orchestrator/

qa-orchestrator
```

Prompt:

```text
Call the ai-web-test MCP tool health_check and report the result as JSON.
```

Expected: tool returns AWT `/health` response.

## Step 4 — Factory MCP tools smoke (optional)

From orchestrator chat or test-gen profile:

```text
Use MCP list_journey_backlog with status pending and limit 5.
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Connection refused | Firewall; AWT MCP not running; wrong IP/port |
| 401 Unauthorized | `AWT_MCP_SECRET` mismatch between Ubuntu and AWT |
| Tool timeout | Increase `timeout` in `mcp_servers.yaml.example` block |
| `localhost` fails | Use AWT machine LAN IP from Ubuntu |

## Automation

```bash
cd scripts/hermes-migrate
./smoke-check.sh --env dev    # Bridge + MCP /health
```

MCP tool-level check remains manual or via `qa-orchestrator` until HF-7.4 extended.
