# Customer Export Tooling

One-way sync from the private dev repo (`AI-Web-Test-v1-2`) to the customer
release folder (`Agentic_QA_v1`) for
[github.com/andrewchw/Agentic_QA_v1](https://github.com/andrewchw/Agentic_QA_v1).

This folder is **dev-only** and is excluded from the customer export.

## First-time setup

1. Enable GitHub no-reply email on the `andrewchw` account:
   https://github.com/settings/emails
2. Log in as `andrewchw`:
   ```powershell
   gh auth logout
   gh auth login
   gh auth status
   ```
3. Preview the export:
   ```powershell
   cd scripts\customer-export
   .\sync-customer-package.ps1 -DryRun
   ```
4. Run the export and initialize git:
   ```powershell
   .\sync-customer-package.ps1 -InitGit
   ```
5. Push to GitHub:
   ```powershell
   cd ..\..\..\Agentic_QA_v1
   git push -u origin main
   ```

## Ongoing updates

After committing changes in the dev repo:

```powershell
cd scripts\customer-export
.\sync-customer-package.ps1 -Force
cd ..\..\..\Agentic_QA_v1
git add -A
git status
git commit -m "Release vX.Y - description"
git push
```

## Configuration

Edit `export-config.json` to adjust:

- `excludeDirs` / `excludeFiles` — internal paths to omit (includes `scripts`, `gan-harness`, `.cursorrules`, and other dev-only items)
- `includeDocWhitelist` — documentation files to keep
- `secretScanPatterns` — patterns flagged before export
- `overlay/` — customer README, LICENSE, and other files copied last

## Script options

| Flag | Purpose |
|------|---------|
| `-DryRun` | Preview robocopy actions without changing files |
| `-InitGit` | Init git, set andrewchw identity, create first commit |
| `-SkipSecretScan` | Skip pattern scan |
| `-Force` | Continue even if secret scan finds matches (recommended for routine syncs) |

**Step 5 note:** The secret scan may pause with `Continue anyway? (y/N)` when matches are found.
Type `y` to proceed, or use `-Force` to skip the prompt.
