# Hermes Factory Bridge (HF-6.6)

Thin service on **Node 1** that receives job JSON from AWT (or runs `qa-orchestrator` locally) and **POSTs progress events** back to AI Web Test.

**AWT endpoint (HF-6.2):** `POST /api/v1/agent/hermes/events`  
**Auth:** `Authorization: Bearer <HERMES_BRIDGE_SECRET>` (same value in `backend/.env` and Node 1)

## Environment (Node 1)

```bash
export HERMES_BRIDGE_SECRET='same-as-awt-backend'
export AWT_AGENT_EVENTS_URL='https://awt-host/api/v1/agent/hermes/events'
export AWT_MCP_SECRET='same-as-awt-backend'
```

## Event payload (v5 §7.4)

```json
{
  "job_id": "uuid",
  "hermes_session_id": "sess_abc123",
  "profile": "qa-test-gen",
  "event_type": "delegate_complete",
  "parent_profile": "qa-orchestrator",
  "message": "Generated test case 1302",
  "payload_summary": { "test_case_id": 1302, "status": "success" },
  "payload_full": { "...": "..." },
  "llm_turns": [{ "role": "assistant", "content": "...", "tokens": 412 }]
}
```

Event types: `job_started` · `delegate_start` · `delegate_complete` · `mcp_tool_call` · `mcp_tool_result` · `llm_turn` · `error` · `job_complete`

## Quick test (curl)

```bash
curl -s -X POST "$AWT_AGENT_EVENTS_URL" \
  -H "Authorization: Bearer $HERMES_BRIDGE_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "<existing-factory-job-uuid>",
    "event_type": "delegate_complete",
    "profile": "qa-test-gen",
    "parent_profile": "qa-orchestrator",
    "hermes_session_id": "sess_test",
    "message": "Bridge smoke test",
    "payload_summary": { "status": "success" }
  }'
```

## Reference script

See `hermes_bridge.py` — minimal HTTP client helpers for posting events from orchestrator wrappers.

**Sprint map:** HF-6.2 (AWT ingest) ✅ · HF-6.6 (this service) · HF-3.7 (chat → bridge forward)
