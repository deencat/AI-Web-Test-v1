#!/usr/bin/env bash
# Install Hermes QA Factory profiles + bridge on a fresh Ubuntu PC.
# Run from an unpacked hermes-factory-bundle-*.zip (or from scripts/hermes-migrate in git).
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="${HERMES_HOME}/profiles"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_ROOT="${SCRIPT_DIR}"
PROFILES_SRC=""
INSTALL_SYSTEMD=0
SKIP_SMOKE=0
ENV_FILE=""

usage() {
  cat <<'EOF'
Usage: install-ubuntu-factory.sh [options]

Install Hermes QA Factory profiles, bridge, env template, and profile shells.

Options:
  --profiles-src <dir>   Source tree (default: ./profiles next to this script, or
                         ../docs/hermes-profiles when run from git)
  --env-file <path>      Copy this file to ~/.hermes/.env (skip interactive template)
  --systemd              Install user systemd unit for hermes-factory-bridge
  --skip-smoke           Do not run smoke-check.sh at the end
  -h, --help             Show this help

Prerequisites (manual):
  - Hermes Agent CLI installed (`hermes --version` works)
  - Edit ~/.hermes/.env after install (AWT IP, secrets, LLM keys)

Example (from unpacked zip):
  unzip hermes-factory-bundle-20260706.zip -d ~/hermes-bundle
  cd ~/hermes-bundle
  ./install-ubuntu-factory.sh
  nano ~/.hermes/.env
  ./scripts/smoke-check.sh --env dev
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profiles-src) PROFILES_SRC="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --systemd) INSTALL_SYSTEMD=1; shift ;;
    --skip-smoke) SKIP_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "${PROFILES_SRC}" ]]; then
  if [[ -d "${SCRIPT_DIR}/profiles" ]]; then
    PROFILES_SRC="${SCRIPT_DIR}/profiles"
  elif [[ -d "${SCRIPT_DIR}/../../docs/hermes-profiles" ]]; then
    PROFILES_SRC="$(cd "${SCRIPT_DIR}/../../docs/hermes-profiles" && pwd)"
  else
    echo "ERROR: profiles source not found. Use --profiles-src <dir>" >&2
    exit 1
  fi
fi

if [[ ! -d "${PROFILES_SRC}" ]]; then
  echo "ERROR: ${PROFILES_SRC} is not a directory" >&2
  exit 1
fi

log() { printf '[install] %s\n' "$*"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1" >&2
    exit 1
  fi
}

log "Hermes home: ${HERMES_HOME}"
log "Profiles source: ${PROFILES_SRC}"

require_cmd rsync
require_cmd python3

if ! command -v hermes >/dev/null 2>&1; then
  echo "ERROR: Hermes CLI not found. Install Hermes Agent first, then re-run." >&2
  echo "See docs/hermes-profiles/UBUNTU_DEV_SETUP.md Part 2." >&2
  exit 1
fi

log "Hermes version: $(hermes --version 2>/dev/null || echo unknown)"

# --- apt packages (optional but recommended) ---
if command -v apt-get >/dev/null 2>&1; then
  MISSING=()
  for pkg in git curl jq rsync python3; do
    command -v "${pkg/.*/$pkg}" >/dev/null 2>&1 || MISSING+=("$pkg")
  done
  if [[ ${#MISSING[@]} -gt 0 ]]; then
    log "Installing base packages: ${MISSING[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y git curl jq rsync python3 python3-venv build-essential
  fi
fi

mkdir -p "${HERMES_HOME}" "${PROFILES_DIR}"

# --- deploy profiles ---
log "Deploying profiles → ${PROFILES_DIR}"
rsync -a --delete --exclude='*/memories' --exclude='*/memories/*' \
  --exclude='.env' --exclude='*.log' \
  "${PROFILES_SRC}/" "${PROFILES_DIR}/"

# Ensure bridge script is executable
if [[ -f "${PROFILES_DIR}/bridge/hermes_bridge.py" ]]; then
  chmod +x "${PROFILES_DIR}/bridge/hermes_bridge.py" 2>/dev/null || true
fi

# --- env template ---
if [[ -n "${ENV_FILE}" ]]; then
  log "Copying env from ${ENV_FILE}"
  cp "${ENV_FILE}" "${HERMES_HOME}/.env"
elif [[ ! -f "${HERMES_HOME}/.env" ]]; then
  TEMPLATE=""
  for candidate in \
    "${SCRIPT_DIR}/env/hermes.env.template.example" \
    "${SCRIPT_DIR}/hermes.env.dev.example" \
    "${SCRIPT_DIR}/hermes.env.prod.example"; do
    if [[ -f "${candidate}" ]]; then
      TEMPLATE="${candidate}"
      break
    fi
  done
  if [[ -n "${TEMPLATE}" ]]; then
    cp "${TEMPLATE}" "${HERMES_HOME}/.env"
    log "Created ${HERMES_HOME}/.env from template — EDIT before use"
  else
    log "WARN: no env template found; create ${HERMES_HOME}/.env manually"
  fi
else
  log "Keeping existing ${HERMES_HOME}/.env"
fi

# --- env.sh + bashrc ---
ENV_SH="${HERMES_HOME}/env.sh"
if [[ ! -f "${ENV_SH}" ]]; then
  cat >"${ENV_SH}" <<'EOF'
#!/usr/bin/env bash
# Load ~/.hermes/.env for Hermes CLI and factory profiles.
set -a
# shellcheck disable=SC1091
[ -f "${HERMES_HOME:-$HOME/.hermes}/.env" ] && source "${HERMES_HOME:-$HOME/.hermes}/.env"
set +a
EOF
  chmod +x "${ENV_SH}"
  log "Created ${ENV_SH}"
fi

if ! grep -q 'hermes/env.sh' "${HOME}/.bashrc" 2>/dev/null; then
  {
    echo ''
    echo '# Hermes QA Factory env'
    echo '[ -f "$HOME/.hermes/env.sh" ] && source "$HOME/.hermes/env.sh"'
  } >>"${HOME}/.bashrc"
  log "Added env.sh source to ~/.bashrc"
fi

# --- register Hermes profiles ---
FACTORY_PROFILES=(qa-orchestrator qa-journey-planner qa-test-gen)
for name in "${FACTORY_PROFILES[@]}"; do
  if [[ ! -d "${PROFILES_DIR}/${name}" ]]; then
    log "WARN: missing profile dir ${PROFILES_DIR}/${name} — skipped"
    continue
  fi
  if hermes profile list 2>/dev/null | grep -q "^${name}[[:space:]]"; then
    log "Profile exists: ${name}"
  else
    log "Creating Hermes profile: ${name}"
    hermes profile create "${name}" || true
  fi
done

# --- per-profile .env (MCP vars for named profiles) ---
if [[ -f "${HERMES_HOME}/.env" ]]; then
  log "Backfilling per-profile .env from ${HERMES_HOME}/.env"
  for name in "${FACTORY_PROFILES[@]}"; do
    if [[ -d "${PROFILES_DIR}/${name}" ]]; then
      cp "${HERMES_HOME}/.env" "${PROFILES_DIR}/${name}/.env"
    fi
  done
  if [[ -d "${PROFILES_DIR}/bridge" ]]; then
    cp "${HERMES_HOME}/.env" "${PROFILES_DIR}/bridge/.env"
  fi
fi

# --- optional systemd user service ---
if [[ "${INSTALL_SYSTEMD}" -eq 1 ]]; then
  UNIT_DIR="${HOME}/.config/systemd/user"
  mkdir -p "${UNIT_DIR}"
  cat >"${UNIT_DIR}/hermes-factory-bridge.service" <<EOF
[Unit]
Description=Hermes QA Factory Bridge (AWT job runner)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${PROFILES_DIR}/bridge
EnvironmentFile=${HERMES_HOME}/.env
ExecStart=/usr/bin/python3 ${PROFILES_DIR}/bridge/hermes_bridge.py serve --port 8790
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable hermes-factory-bridge.service
  log "Installed user systemd unit (start: systemctl --user start hermes-factory-bridge)"
fi

log "Install complete."
echo
echo "Next steps:"
echo "  1. Edit secrets and LAN IPs:  nano ${HERMES_HOME}/.env"
echo "  2. Reload env:                source ${HERMES_HOME}/env.sh"
echo "  3. Verify profiles:           hermes profile list"
echo "  4. Start bridge:              source ${HERMES_HOME}/env.sh && python3 ${PROFILES_DIR}/bridge/hermes_bridge.py serve --port 8790"
echo "  5. On Windows AWT backend/.env set HERMES_BRIDGE_URL=http://<THIS-UBUNTU-IP>:8790"
echo

if [[ "${SKIP_SMOKE}" -eq 0 && -f "${SCRIPT_DIR}/smoke-check.sh" ]]; then
  log "Running smoke-check (edit .env first if this fails)..."
  # shellcheck disable=SC1091
  set -a && [[ -f "${HERMES_HOME}/.env" ]] && source "${HERMES_HOME}/.env" && set +a
  bash "${SCRIPT_DIR}/smoke-check.sh" --env dev || true
fi
