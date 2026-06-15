# Hermes Factory Bridge (HF-6.6 + HF-3.7)

Thin service on **Node 1** (or local dev) that:

1. Receives job JSON from AWT **`POST /run`**
2. Runs `qa-orchestrator` CLI **or** demo delegate simulation
3. **POSTs progress events** to `POST /api/v1/agent/hermes/events` (HF-6.2)

## Quick start (local dev)

**Terminal 1 — Bridge server (demo mode, no Hermes CLI required):**

```bash
export HERMES_BRIDGE_SECRET=dev-bridge-secret
export AWT_AGENT_EVENTS_URL=http://localhost:8000/api/v1/agent/hermes/events
export HERMES_BRIDGE_DEMO_MODE=1
cd docs/hermes-profiles/bridge
python hermes_bridge.py serve --port 8790
```

**`backend/.env` (AWT):**

```env
HERMES_BRIDGE_SECRET=dev-bridge-secret
HERMES_BRIDGE_URL=http://localhost:8790
```

Restart AWT backend. Log in as **superadmin** → Agent Console → type **Full cycle**. Job timeline should show delegate events from the bridge.

## Environment

| Variable | Where | Purpose |
|----------|-------|---------|
| `HERMES_BRIDGE_SECRET` | AWT + Bridge | Auth both directions |
| `HERMES_BRIDGE_URL` | AWT | Chat → `POST {url}/run` (HF-3.7) |
| `AWT_AGENT_EVENTS_URL` | Bridge | Event ingest endpoint |
| `HERMES_BRIDGE_PORT` | Bridge | Default `8790` |
| `HERMES_ORCHESTRATOR_CMD` | Bridge | e.g. `qa-orchestrator` (production) |
| `HERMES_BRIDGE_DEMO_MODE` | Bridge | `1` = simulate delegates without CLI |

## HTTP API

```http
GET  /health
POST /run
Authorization: Bearer <HERMES_BRIDGE_SECRET>
Content-Type: application/json

{ "job_id": "uuid", "job_type": "full_cycle", "project": "Three-HK", "params": {} }
```

Returns `202 {"accepted": true, "job_id": "..."}` — execution runs in background.

## Production (Node 1)

```bash
# Copy to Node 1
rsync -av docs/hermes-profiles/bridge/ user@node1:~/.hermes/profiles/bridge/

# ~/.hermes/.env
HERMES_BRIDGE_SECRET=...
AWT_AGENT_EVENTS_URL=https://awt.example.com/api/v1/agent/hermes/events
HERMES_ORCHESTRATOR_CMD=qa-orchestrator

sudo cp hermes-factory-bridge.service /etc/systemd/system/
sudo systemctl enable --now hermes-factory-bridge
```

## CLI smoke test

```bash
python hermes_bridge.py post-event --job-id <uuid> --type delegate_complete --profile qa-test-gen
```

Demo `drain_backlog` events include placeholder `test_case_id` in `payload_summary` for UI timeline smoke — **not** HF-3.1d acceptance (requires real Hermes orchestrator crawl).

See [HF-3.1d_Integration_Smoke.md](../HF-3.1d_Integration_Smoke.md) for full integration acceptance.
