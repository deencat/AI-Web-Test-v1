#!/usr/bin/env bash
# HF-7.3 — Deploy Hermes profiles to Ubuntu (from tarball or git)
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PROFILES_DIR="${HERMES_HOME}/profiles"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FROM_TAR=""
FROM_GIT=""

usage() {
  echo "Usage: $0 --from-tar <archive.tar.gz> | --from-git <repo-root>"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-tar) FROM_TAR="$2"; shift 2 ;;
    --from-git) FROM_GIT="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

if [[ -z "${FROM_TAR}" && -z "${FROM_GIT}" ]]; then
  usage
fi

mkdir -p "${PROFILES_DIR}"

if [[ -n "${FROM_GIT}" ]]; then
  SRC="${FROM_GIT}/docs/hermes-profiles"
  if [[ ! -d "${SRC}" ]]; then
    echo "ERROR: ${SRC} not found" >&2
    exit 1
  fi
  echo "Deploying from git: ${SRC} → ${PROFILES_DIR}"
  rsync -av --exclude='*/memories' "${SRC}/" "${PROFILES_DIR}/"
elif [[ -n "${FROM_TAR}" ]]; then
  if [[ ! -f "${FROM_TAR}" ]]; then
    echo "ERROR: archive not found: ${FROM_TAR}" >&2
    exit 1
  fi
  echo "Deploying from tarball: ${FROM_TAR}"
  tar xzf "${FROM_TAR}" -C "${HERMES_HOME}"
fi

if [[ ! -f "${HERMES_HOME}/.env" ]]; then
  echo "WARN: ${HERMES_HOME}/.env missing — copy hermes.env.prod.example or hermes.env.dev.example"
fi

echo "Deploy complete. Run: ./smoke-check.sh"
