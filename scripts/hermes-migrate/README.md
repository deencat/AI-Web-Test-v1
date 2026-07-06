# Hermes migration scripts (HF-7)

Package Hermes profiles from a **dev Ubuntu mini PC** and deploy to **production Ubuntu** with env-only changes.

**Full guide:** [docs/hermes-profiles/Hermes_Environment_Migration_Guide.md](../../docs/hermes-profiles/Hermes_Environment_Migration_Guide.md)  
**First-time Ubuntu mini PC:** [UBUNTU_DEV_SETUP.md](../../docs/hermes-profiles/UBUNTU_DEV_SETUP.md)

## Scripts

| Script | Purpose | When to use |
|--------|---------|-------------|
| `pack-factory-bundle.sh` | **ZIP** with profiles + install script + smoke (no secrets) | Clone to another Ubuntu PC |
| `install-ubuntu-factory.sh` | One-shot install from unpacked bundle | Target PC after `unzip` |
| `pack-profiles.sh` | Tarball `~/.hermes/profiles` (no memories, no `.env`) | After dev smoke passes |
| `deploy-profiles.sh` | Restore from tarball or git `docs/hermes-profiles/` | New prod (or DR) Ubuntu |
| `smoke-check.sh` | MCP + Bridge + optional AWT event POST | After deploy |
| `smoke-integration-3.1d.sh` | HF-3.1d orchestrator → planner → test-gen | After 3 profiles deployed |
| `smoke-awt-prereq-3.1d.ps1` | AWT MCP + backlog prereq (Windows) | Before Ubuntu full smoke |

## Clone to another Ubuntu PC (recommended)

On the **source** PC (after smoke passes):

```bash
cd scripts/hermes-migrate
chmod +x pack-factory-bundle.sh install-ubuntu-factory.sh
./pack-factory-bundle.sh
# Optional: pack live ~/.hermes/profiles instead of git templates:
# ./pack-factory-bundle.sh --from-runtime

scp dist/hermes-factory-bundle-*.zip user@other-pc:~/
```

On the **target** PC:

```bash
unzip hermes-factory-bundle-*.zip
cd hermes-factory-bundle-*
./install-ubuntu-factory.sh
nano ~/.hermes/.env          # AWT IP, secrets, LLM keys (per host)
source ~/.hermes/env.sh
./scripts/smoke-check.sh --env dev
```

Install Hermes CLI on the target first — see [UBUNTU_DEV_SETUP.md](../../docs/hermes-profiles/UBUNTU_DEV_SETUP.md) Part 2.

## Quick start (dev)

```bash
chmod +x *.sh
cp hermes.env.dev.example ~/.hermes/.env
# Edit ~/.hermes/.env — set AWT dev host, secrets

./smoke-check.sh --env dev
./pack-profiles.sh
ls -la dist/
```

## Quick start (prod)

```bash
cp hermes.env.prod.example ~/.hermes/.env
nano ~/.hermes/.env

./deploy-profiles.sh --from-git "$(pwd)/../.."   # repo root
./smoke-check.sh --env prod
```

## Env templates

| File | Use on |
|------|--------|
| `hermes.env.dev.example` | Hermes dev mini PC → copy to `~/.hermes/.env` |
| `hermes.env.prod.example` | Hermes prod PC → copy to `~/.hermes/.env` |
| `awt-bridge.env.patch.example` | Snippet for AWT `backend/.env` (bridge URL + secret) |

## Status (HF-7)

| Story | Status |
|-------|--------|
| HF-7.1 Guide + templates | ✅ |
| HF-7.2–7.4 Scripts | 🔜 Initial version — extend after first dev smoke |
| HF-7.5 Security sign-off checklist | ⬜ |

## Notes

- Run scripts on **Ubuntu** (Hermes host). Paths assume `~/.hermes/profiles/`.
- Never commit real `.env` files.
- Prefer **`--from-git`** when profiles are merged to `feat/hermes-qa-factory`.
