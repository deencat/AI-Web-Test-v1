# Git Workflow Scripts

This directory contains automation scripts to help manage your multi-developer Git workflow with separate backend and frontend branches.

## Quick Start

### For Windows (PowerShell)
1. **Set execution policy (if needed):**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Set up Git aliases (optional but recommended):**
   ```powershell
   .\.git-workflow\setup-aliases.ps1
   ```

### For Linux/Mac (Bash)
1. **Make scripts executable:**
   ```bash
   chmod +x .git-workflow/*.sh
   ```

2. **Set up Git aliases (optional but recommended):**
   ```bash
   ./.git-workflow/setup-aliases.sh
   ```

## Available Scripts

### 1. View Branches
See all your branches with useful information.

**PowerShell:**
```powershell
# Basic view
.\.git-workflow\view-branches.ps1

# View with commit graph
.\.git-workflow\view-branches.ps1 -Graph
```

**Bash:**
```bash
# Basic view
./.git-workflow/view-branches.sh

# View with commit graph
./.git-workflow/view-branches.sh --graph
```

**Shows:**
- Current branch
- All local and remote branches
- Which branches are merged/unmerged
- Last commit on each branch
- Remote tracking status

---

### 2. Compare Branches
Compare two branches to see differences.

**PowerShell:**
```powershell
# Compare current branch with main
.\.git-workflow\compare-branches.ps1 main

# Compare two specific branches
.\.git-workflow\compare-branches.ps1 backend-dev-sprint-2 frontend-dev
```

**Bash:**
```bash
# Compare current branch with main
./.git-workflow/compare-branches.sh main

# Compare two specific branches
./.git-workflow/compare-branches.sh backend-dev-sprint-2 frontend-dev
```

**Shows:**
- Unique commits in each branch
- Files changed
- Statistics
- Potential merge conflicts

---

### 3. Sync with Main
Keep your development branch up to date with main.

**PowerShell:**
```powershell
# Regular merge (recommended for shared branches)
.\.git-workflow\sync-with-main.ps1

# Using rebase (cleaner history, use only for personal branches)
.\.git-workflow\sync-with-main.ps1 -Rebase
```

**Bash:**
```bash
# Regular merge (recommended for shared branches)
./.git-workflow/sync-with-main.sh

# Using rebase (cleaner history, use only for personal branches)
./.git-workflow/sync-with-main.sh --rebase
```

**Features:**
- Automatically stashes uncommitted changes
- Syncs with latest main
- Restores your changes
- Handles conflicts gracefully

---

### 4. Merge to Main
Safely merge both backend and frontend branches via an integration branch.

**PowerShell:**
```powershell
# Use default branch names (backend-dev-sprint-2 and frontend-dev)
.\.git-workflow\merge-to-main.ps1

# Or specify custom branches
.\.git-workflow\merge-to-main.ps1 my-backend-branch my-frontend-branch
```

**Bash:**
```bash
# Use default branch names (backend-dev-sprint-2 and frontend-dev)
./.git-workflow/merge-to-main.sh

# Or specify custom branches
./.git-workflow/merge-to-main.sh my-backend-branch my-frontend-branch
```

**Process:**
1. Fetches latest changes
2. Creates integration branch from main
3. Merges backend branch
4. Merges frontend branch
5. Provides instructions for testing and finalizing

---

### 5. Finalize Merge
After testing the integration branch, finalize the merge to main.

**PowerShell:**
```powershell
# Replace with your integration branch name
.\.git-workflow\finalize-merge.ps1 integration-20241120-143022
```

**Bash:**
```bash
# Replace with your integration branch name
./.git-workflow/finalize-merge.sh integration-20241120-143022
```

**Process:**
1. Confirms you've tested
2. Merges integration branch to main
3. Pushes to remote
4. Cleans up integration branch

---

## Typical Workflow

### Daily Development

1. **Start your day** - Sync your branch with main:
   ```powershell
   git checkout backend-dev-sprint-2
   .\.git-workflow\sync-with-main.ps1
   ```

2. **Check branch status:**
   ```powershell
   .\.git-workflow\view-branches.ps1
   ```

3. **Work on your code** and commit regularly:
   ```powershell
   git add .
   git commit -m "feat(api): add user authentication endpoint"
   git push origin backend-dev-sprint-2
   ```

### When Ready to Merge

1. **Compare your branch with main:**
   ```powershell
   .\.git-workflow\compare-branches.ps1 main backend-dev-sprint-2
   ```

2. **Coordinate with frontend developer:**
   - Both sync with main
   - Both push latest changes
   - Agree on merge timing

3. **Create integration branch:**
   ```powershell
   .\.git-workflow\merge-to-main.ps1 backend-dev-sprint-2 frontend-dev
   ```

4. **Test the integration branch thoroughly:**
   - Run all tests
   - Check API compatibility
   - Verify frontend-backend integration

5. **Finalize the merge:**
   ```powershell
   .\.git-workflow\finalize-merge.ps1 integration-20241120-143022
   ```

6. **Both developers sync their branches:**
   ```powershell
   .\.git-workflow\sync-with-main.ps1
   ```

## Git Aliases

After running `setup-aliases.sh`, you can use short commands:

```bash
# View branches
git branches

# Sync with main
git sync

# View pretty log
git lg

# Quick commits (following your project's convention)
git feat api "add user authentication"
git fix database "resolve connection timeout"
```

## Handling Merge Conflicts

If conflicts occur during any operation:

1. **Check which files have conflicts:**
   ```bash
   git status
   ```

2. **Open conflicted files and look for markers:**
   ```
   <<<<<<< HEAD
   Your changes
   =======
   Their changes
   >>>>>>> branch-name
   ```

3. **Resolve conflicts** by editing the file to keep what you want

4. **Stage resolved files:**
   ```bash
   git add <resolved-file>
   ```

5. **Complete the merge:**
   ```bash
   git commit
   ```

## Tips

- **Commit often** - Small, frequent commits are easier to merge
- **Sync regularly** - Pull from main daily to avoid large conflicts
- **Communicate** - Coordinate with your teammate before merging
- **Test integration** - Always test the integration branch before merging to main
- **Use meaningful commits** - Follow the conventional commit format in your project rules

## Troubleshooting

### "Script cannot be loaded" on Windows
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Permission denied" when running bash scripts (Linux/Mac)
```bash
chmod +x .git-workflow/*.sh
```

### "Detached HEAD state"
```bash
git checkout backend-dev-sprint-2
```

### "Your branch is behind origin"
```bash
git pull origin backend-dev-sprint-2
```

### Need to abort a merge
```bash
git merge --abort
```

### Need to abort a rebase
```bash
git rebase --abort
```

## Platform Notes

- **Windows users**: Use the `.ps1` PowerShell scripts
- **Linux/Mac users**: Use the `.sh` Bash scripts
- Both versions provide identical functionality
- Git commands work the same across all platforms

