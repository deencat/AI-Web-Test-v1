#!/usr/bin/env bash
# HF-3.1d — Orchestrator → planner → test-gen integration smoke (Ubuntu / Hermes host)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLANNER_ONLY=0
SKIP_ORCHESTRATOR=0
TIMEOUT_SEC="${HERMES_SMOKE_TIMEOUT:-2400}"
PROJECT="${HERMES_SMOKE_PROJECT:-Three-HK}"
MAX_ITEMS="${HERMES_SMOKE_MAX_ITEMS:-1}"

usage() {
  cat <<'EOF'
Usage: smoke-integration-3.1d.sh [options]

HF-3.1d acceptance: qa-orchestrator drain_backlog returns test_case_id.

Options:
  --planner-only     Run planner delegate only (no crawl; ~5 min)
  --skip-orchestrator  Preflight only (profiles + MCP); no Hermes CLI
  --project NAME     Project (default: Three-HK)
  --max-items N      max_items param (default: 1)
  --timeout SEC      Orchestrator chat timeout (default: 2400)
  -h, --help         This help

Requires: ~/.hermes/.env, qa-orchestrator (+ planner/test-gen for full run)
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --planner-only) PLANNER_ONLY=1; shift ;;
    --skip-orchestrator) SKIP_ORCHESTRATOR=1; shift ;;
    --project) PROJECT="$2"; shift 2 ;;
    --max-items) MAX_ITEMS="$2"; shift 2 ;;
    --timeout) TIMEOUT_SEC="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown: $1" >&2; usage ;;
  esac
done

if [[ -f "${HERMES_HOME}/.env" ]]; then
  # shellcheck disable=SC1090
  set -a && source "${HERMES_HOME}/.env" && set +a
fi

PROFILES_DIR="${HERMES_HOME}/profiles"
FAIL=0

log() { printf '[HF-3.1d] %s\n' "$*"; }
fail() { log "FAIL: $*"; FAIL=1; }
pass() { log "OK: $*"; }

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "found ${path}"
  else
    fail "missing ${path}"
  fi
}

check_cmd() {
  local cmd="$1"
  if command -v "${cmd}" >/dev/null 2>&1; then
    pass "command ${cmd}"
  else
    fail "command not found: ${cmd} (install Hermes profile)"
  fi
}

log "=== Preflight ==="
check_file "${PROFILES_DIR}/qa-orchestrator/SOUL.md"
check_file "${PROFILES_DIR}/qa-journey-planner/SOUL.md"
check_file "${PROFILES_DIR}/qa-test-gen/SOUL.md"
check_file "${PROFILES_DIR}/qa-orchestrator/config.yaml"

for cmd in qa-orchestrator qa-journey-planner qa-test-gen; do
  check_cmd "${cmd}"
done

if [[ -z "${AWT_MCP_URL:-}" || -z "${AWT_MCP_SECRET:-}" ]]; then
  fail "AWT_MCP_URL and AWT_MCP_SECRET must be set in ${HERMES_HOME}/.env"
else
  pass "AWT_MCP_URL configured"
fi

if [[ -z "${REQIQ_PROJECT_ID:-}" ]]; then
  log "WARN: REQIQ_PROJECT_ID unset — planner may return insufficient"
fi

log "=== MCP health ==="
if curl -sf -H "Authorization: Bearer ${AWT_MCP_SECRET}" "${AWT_MCP_URL}/health" >/dev/null; then
  pass "MCP ${AWT_MCP_URL}/health"
else
  fail "MCP health check failed"
fi

if [[ "${SKIP_ORCHESTRATOR}" -eq 1 ]]; then
  log "Skipping orchestrator (--skip-orchestrator)"
  [[ "${FAIL}" -eq 0 ]] && log "Preflight passed." || exit 1
  exit 0
fi

run_orchestrator_chat() {
  local prompt="$1"
  local outfile
  outfile="$(mktemp)"
  log "Running: qa-orchestrator chat (timeout ${TIMEOUT_SEC}s)"
  log "Prompt: ${prompt}"
  if timeout "${TIMEOUT_SEC}" qa-orchestrator chat -q "${prompt}" >"${outfile}" 2>&1; then
    :
  else
    local rc=$?
    log "--- orchestrator output (tail) ---"
    tail -n 40 "${outfile}" || true
    rm -f "${outfile}"
    fail "qa-orchestrator exited ${rc} (timeout or error)"
    return 1
  fi
  cat "${outfile}"
  if grep -qE 'test_case_id|"test_case_id"[[:space:]]*:[[:space:]]*[0-9]+' "${outfile}"; then
    pass "output contains test_case_id"
  else
    if [[ "${PLANNER_ONLY}" -eq 1 ]]; then
      if grep -qE 'items_for_test_gen|items_enqueued' "${outfile}"; then
        pass "planner output contains backlog items"
      else
        fail "planner output missing items_for_test_gen / items_enqueued"
      fi
    else
      fail "output missing test_case_id (HF-3.1d not satisfied)"
    fi
  fi
  rm -f "${outfile}"
}

log "=== Orchestrator delegate smoke ==="
if [[ "${PLANNER_ONLY}" -eq 1 ]]; then
  run_orchestrator_chat "delegate to qa-journey-planner: task_type drain_backlog project ${PROJECT} max_items ${MAX_ITEMS}. Return JSON only."
else
  run_orchestrator_chat "drain backlog for ${PROJECT} max_items ${MAX_ITEMS}"
fi

if [[ "${FAIL}" -ne 0 ]]; then
  log "HF-3.1d smoke FAILED — see docs/hermes-profiles/HF-3.1d_Integration_Smoke.md"
  exit 1
fi

log "HF-3.1d smoke PASSED."
