#!/usr/bin/env bash
# Smoke-test Bridge → AWT event ingest from Ubuntu factory node.
# Usage: ./smoke-bridge-events.sh [WINDOWS_LAN_IP]
set -euo pipefail

WINDOWS_IP="${1:-}"
if [[ -z "$WINDOWS_IP" ]]; then
  echo "Usage: $0 <WINDOWS_LAN_IP>"
  echo "Example: $0 192.168.1.227"
  exit 1
fi

set -a
# shellcheck disable=SC1091
[[ -f "$HOME/.hermes/.env" ]] && source "$HOME/.hermes/.env"
set +a

EVENTS_URL="${AWT_AGENT_EVENTS_URL:-http://${WINDOWS_IP}:8000/api/v1/agent/hermes/events}"
SECRET="${HERMES_BRIDGE_SECRET:-}"

if [[ -z "$SECRET" ]]; then
  echo "FAIL: HERMES_BRIDGE_SECRET not set in ~/.hermes/.env"
  exit 1
fi

echo "Testing POST $EVENTS_URL"
CURL_EXIT=0
HTTP_CODE=$(curl -s -o /tmp/awt-events-smoke.json -w "%{http_code}" \
  --connect-timeout 10 \
  -X POST "$EVENTS_URL" \
  -H "Authorization: Bearer $SECRET" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"00000000-0000-0000-0000-000000000099","event_type":"error","message":"ubuntu bridge smoke test"}') || CURL_EXIT=$?

if [[ "$CURL_EXIT" -ne 0 ]]; then
  echo "FAIL: curl could not reach $EVENTS_URL (exit $CURL_EXIT)"
  case "$CURL_EXIT" in
    7)  echo "  → No route / connection refused — on Windows: start AWT with --host 0.0.0.0:8000 and allow inbound TCP 8000 in firewall" ;;
    28) echo "  → Connection timed out after 10s" ;;
    *)  echo "  → See: curl --help (exit codes)" ;;
  esac
  exit 1
fi

echo "HTTP $HTTP_CODE"
cat /tmp/awt-events-smoke.json
echo

if [[ "$HTTP_CODE" == "404" ]]; then
  echo "PASS (auth OK, job not found is expected for fake job_id)"
  echo "Ubuntu can reach Agentic QA. Set AWT_AGENT_EVENTS_URL=$EVENTS_URL in ~/.hermes/.env and restart bridge."
  exit 0
fi

if [[ "$HTTP_CODE" == "201" ]]; then
  echo "PASS (event accepted)"
  exit 0
fi

if [[ "$HTTP_CODE" == "401" ]]; then
  echo "FAIL: 401 — HERMES_BRIDGE_SECRET does not match Windows backend/.env"
  exit 1
fi

echo "FAIL: expected 404 or 201, got $HTTP_CODE — check Windows firewall (TCP 8000) and server host 0.0.0.0:8000"
exit 1
