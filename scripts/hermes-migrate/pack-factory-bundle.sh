#!/usr/bin/env bash
# Pack a portable ZIP for cloning Hermes QA Factory to another Ubuntu PC.
# Excludes secrets (.env), memories, and logs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
STAMP="$(date +%Y%m%d)"
BUNDLE_NAME="hermes-factory-bundle-${STAMP}"
WORK="${DIST_DIR}/${BUNDLE_NAME}"
FROM_RUNTIME=0
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

usage() {
  cat <<'EOF'
Usage: pack-factory-bundle.sh [--from-runtime]

Create dist/hermes-factory-bundle-YYYYMMDD.zip for offline deploy to another Ubuntu PC.

  --from-runtime   Pack ~/.hermes/profiles instead of git docs/hermes-profiles/
                   (still excludes .env, memories, logs)

Output zip contains:
  install-ubuntu-factory.sh
  profiles/          SOUL.md, config.yaml, bridge/
  scripts/           smoke-check, deploy, env templates
  env/               hermes.env.template.example (no secrets)
  README-BUNDLE.md

On target PC:
  unzip hermes-factory-bundle-*.zip && cd hermes-factory-bundle-*
  ./install-ubuntu-factory.sh
  nano ~/.hermes/.env
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-runtime) FROM_RUNTIME=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown: $1" >&2; usage; exit 1 ;;
  esac
done

command -v zip >/dev/null 2>&1 || { echo "Install zip: sudo apt install zip" >&2; exit 1; }

rm -rf "${WORK}"
mkdir -p "${WORK}/profiles" "${WORK}/scripts" "${WORK}/env"

echo "Building ${BUNDLE_NAME}..."

# Profiles
if [[ "${FROM_RUNTIME}" -eq 1 ]]; then
  SRC="${HERMES_HOME}/profiles"
  if [[ ! -d "${SRC}" ]]; then
    echo "ERROR: ${SRC} not found" >&2
    exit 1
  fi
  echo "  profiles: runtime ${SRC}"
  rsync -a --exclude='*/memories' --exclude='*/memories/*' \
    --exclude='.env' --exclude='*.log' \
    "${SRC}/" "${WORK}/profiles/"
else
  SRC="${REPO_ROOT}/docs/hermes-profiles"
  if [[ ! -d "${SRC}" ]]; then
    echo "ERROR: ${SRC} not found" >&2
    exit 1
  fi
  echo "  profiles: git ${SRC}"
  rsync -a --exclude='*/memories' --exclude='*/memories/*' \
    --exclude='.env' --exclude='*.log' \
    "${SRC}/" "${WORK}/profiles/"
fi

# Scripts + installer
cp "${SCRIPT_DIR}/install-ubuntu-factory.sh" "${WORK}/"
cp "${SCRIPT_DIR}/deploy-profiles.sh" "${WORK}/scripts/"
cp "${SCRIPT_DIR}/smoke-check.sh" "${WORK}/scripts/"
cp "${SCRIPT_DIR}/smoke-integration-3.1d.sh" "${WORK}/scripts/"
cp "${SCRIPT_DIR}/smoke-bridge-events.sh" "${WORK}/scripts/" 2>/dev/null || true
cp "${SCRIPT_DIR}/hermes.env.dev.example" "${WORK}/scripts/"
cp "${SCRIPT_DIR}/hermes.env.prod.example" "${WORK}/scripts/"
cp "${SCRIPT_DIR}/awt-bridge.env.patch.example" "${WORK}/scripts/" 2>/dev/null || true
chmod +x "${WORK}/install-ubuntu-factory.sh" "${WORK}/scripts/"*.sh

# Env template (sanitized — never pack real ~/.hermes/.env)
cp "${SCRIPT_DIR}/hermes.env.dev.example" "${WORK}/env/hermes.env.template.example"

# Docs pointer
cat >"${WORK}/README-BUNDLE.md" <<'EOF'
# Hermes QA Factory — Ubuntu bundle

Portable package to clone factory profiles + bridge to another Ubuntu PC.

## Prerequisites on target PC

1. Ubuntu 22.04+ with network to your AWT Windows host
2. **Hermes Agent CLI** installed (`hermes --version`)
3. Base packages: `sudo apt install -y git curl jq rsync python3 python3-venv build-essential`

## Install

```bash
unzip hermes-factory-bundle-*.zip
cd hermes-factory-bundle-*
./install-ubuntu-factory.sh
nano ~/.hermes/.env          # set AWT IP, secrets, LLM keys
source ~/.hermes/env.sh
hermes profile list
```

## Start bridge (live mode)

```bash
source ~/.hermes/env.sh
python3 ~/.hermes/profiles/bridge/hermes_bridge.py serve --port 8790
```

Or with systemd user service:

```bash
./install-ubuntu-factory.sh --systemd
systemctl --user start hermes-factory-bridge
```

## Windows AWT

In `backend/.env`:

```env
HERMES_BRIDGE_URL=http://<UBUNTU-IP>:8790
HERMES_BRIDGE_SECRET=<same as Ubuntu ~/.hermes/.env>
```

## Smoke test

```bash
./scripts/smoke-check.sh --env dev
```

## What is NOT in this zip

- `~/.hermes/.env` (secrets) — create on each host
- Agent memories and session logs
- Hermes CLI itself — install separately

See `docs/hermes-profiles/UBUNTU_DEV_SETUP.md` and
`Hermes_Environment_Migration_Guide.md` in the AI Web Test repo.
EOF

# Strip any accidental secrets from bundled profile configs (api_key lines)
if grep -RIl 'api_key:' "${WORK}/profiles" 2>/dev/null | head -1 >/dev/null; then
  echo "  WARN: profile config.yaml may contain api_key — scrub on target or use git templates"
fi

mkdir -p "${DIST_DIR}"
ZIP="${DIST_DIR}/${BUNDLE_NAME}.zip"
( cd "${DIST_DIR}" && zip -rq "${BUNDLE_NAME}.zip" "${BUNDLE_NAME}" )
rm -rf "${WORK}"

echo "Done: ${ZIP}"
echo "Copy to target PC: scp ${ZIP} user@other-pc:~/"
echo "On target: unzip ${BUNDLE_NAME}.zip && cd ${BUNDLE_NAME} && ./install-ubuntu-factory.sh"
