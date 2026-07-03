# Hermes Bridge — Ubuntu deploy checklist

Deploy the bridge on the QA Factory node so Agent Console open chat works with **session resume** (conversation memory).

## Branch

```bash
cd ~/AI-Web-Test-v1-2   # or your clone path
git fetch origin
git checkout feat/hermes-qa-factory
git pull origin feat/hermes-qa-factory
```

## Bridge script

```bash
cp docs/hermes-profiles/bridge/hermes_bridge.py ~/.hermes/profiles/bridge/hermes_bridge.py
```

Critical behaviors in this branch:

- `hermes --resume <session> -p qa-orchestrator chat -q` for follow-up messages
- `hermes_resume_session` in event `payload_summary`
- Live CLI output in `llm_turns` for chat replies

## Environment (`~/.hermes/.env`)

| Variable | Example | Notes |
|----------|---------|--------|
| `AWT_AGENT_EVENTS_URL` | `http://<WINDOWS-IP>:8000/api/v1/agent/hermes/events` | Windows backend must be reachable |
| `HERMES_BRIDGE_SECRET` | same as Windows `HERMES_BRIDGE_SECRET` | Bearer token for event POSTs |
| `HERMES_ORCHESTRATOR_CMD` | `qa-orchestrator` | CLI entry for orchestrator |

Windows backend `.env` must set the same `HERMES_BRIDGE_SECRET` and factory node URL if used.

## Restart bridge

```bash
# however you run the bridge, e.g.:
pkill -f hermes_bridge.py || true
python ~/.hermes/profiles/bridge/hermes_bridge.py &
```

Or restart the systemd service if you use one.

## Verify

1. From Windows UI: Agent Console → send a message → reply shows JSON `summary` text only.
2. UI shows: *Hermes session active — follow-up messages keep chat context.*
3. Send a follow-up (e.g. “what did I just ask?”) — orchestrator should remember prior turn.
4. Refresh the page — conversation bubbles restore from server (`/api/v1/agent/conversations/active`).
5. Optional: uncheck **Chat only** to see Job Monitor; events should stream via SSE (`/agent/jobs/{id}/stream`).

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No reply / only “Job queued” | Bridge running? `AWT_AGENT_EVENTS_URL` correct? Firewall to Windows :8000 |
| No memory between messages | Bridge updated? `hermes_resume_session` in job params and bridge logs |
| 401 on events | `HERMES_BRIDGE_SECRET` mismatch |
| Stale bridge code | `git log -1` on `feat/hermes-qa-factory`; re-copy `hermes_bridge.py` |

## Windows backend migration

After pulling this branch on Windows:

```bash
cd backend
python migrations/add_agent_conversations.py
```

Restart the FastAPI server so conversation APIs are available.
