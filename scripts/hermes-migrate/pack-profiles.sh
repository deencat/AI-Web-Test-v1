#!/usr/bin/env bash
# HF-7.2 — Pack Hermes profiles for dev → prod migration (no secrets, no memories)
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="${HERMES_HOME}/profiles"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
STAMP="$(date +%Y%m%d)"
ARCHIVE="${DIST_DIR}/hermes-factory-profiles-${STAMP}.tar.gz"

if [[ ! -d "${PROFILES_DIR}" ]]; then
  echo "ERROR: ${PROFILES_DIR} not found. Install Hermes profiles first." >&2
  exit 1
fi

mkdir -p "${DIST_DIR}"

echo "Packing ${PROFILES_DIR} → ${ARCHIVE}"
echo "Excluding: memories/, .env, logs"

tar czf "${ARCHIVE}" \
  --exclude='*/memories' \
  --exclude='*/memories/*' \
  --exclude='.env' \
  --exclude='*.log' \
  -C "${HERMES_HOME}" \
  profiles

# Include bridge systemd unit from repo if present
REPO_BRIDGE="${SCRIPT_DIR}/../../docs/hermes-profiles/bridge"
if [[ -d "${REPO_BRIDGE}" ]]; then
  tar czf "${DIST_DIR}/hermes-bridge-service-${STAMP}.tar.gz" \
    -C "${REPO_BRIDGE}" \
    hermes_bridge.py hermes-factory-bridge.service README.md 2>/dev/null || true
fi

echo "Done."
echo "  Profiles: ${ARCHIVE}"
echo "Next: copy dist/*.tar.gz to prod host, or commit docs/hermes-profiles/ to git and use deploy-profiles.sh --from-git"
