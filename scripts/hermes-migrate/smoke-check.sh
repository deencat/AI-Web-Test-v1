#!/usr/bin/env bash
# HF-7.4 — Post-deploy smoke checks for Hermes ↔ AWT
set -euo pipefail

ENV_LABEL="dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) ENV_LABEL="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--env dev|prod]"; exit 0 ;;
    *) echo "Unknown: $1" >&2; exit 1 ;;
  esac
done

if [[ -f "${HERMES_HOME}/.env" ]]; then
  # shellcheck disable=SC1090
  set -a && source "${HERMES_HOME}/.env" && set +a
fi

AWT_MCP_URL="${AWT_MCP_URL:-http://localhost:8001}"
HERMES_BRIDGE_PORT="${HERMES_BRIDGE_PORT:-8790}"
FAIL=0

check() {
  local name="$1"
  shift
  printf "[%s] %s ... " "${ENV_LABEL}" "${name}"
  if "$@"; then
    echo "OK"
  else
    echo "FAIL"
    FAIL=1
  fi
}

curl_ok() {
  local url="$1"
  local extra_args=()
  if [[ -n "${AWT_MCP_SECRET:-}" && "${url}" == *":8001"* ]]; then
    extra_args=(-H "Authorization: Bearer ${AWT_MCP_SECRET}")
  fi
  curl -sf "${extra_args[@]}" "${url}" >/dev/null
}

check "MCP health ${AWT_MCP_URL}/health" curl_ok "${AWT_MCP_URL}/health"
check "Bridge health localhost:${HERMES_BRIDGE_PORT}/health" curl_ok "http://127.0.0.1:${HERMES_BRIDGE_PORT}/health"

if [[ -n "${AWT_AGENT_EVENTS_URL:-}" && -n "${HERMES_BRIDGE_SECRET:-}" ]]; then
  echo "[${ENV_LABEL}] Bridge → AWT event ingest: manual — use hermes_bridge.py post-event with a real job_id"
else
  echo "[${ENV_LABEL}] Skip event ingest smoke (set AWT_AGENT_EVENTS_URL + HERMES_BRIDGE_SECRET in ~/.hermes/.env)"
fi

if [[ "${FAIL}" -ne 0 ]]; then
  echo "Smoke check FAILED — see Hermes_Environment_Migration_Guide.md §4"
  exit 1
fi

echo "Smoke check passed (${ENV_LABEL})."
