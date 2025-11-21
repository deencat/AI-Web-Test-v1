# Git Workflow Quick Start Guide

## 🚀 Getting Started (Windows PowerShell)

### 1️⃣ First Time Setup (Do Once)

```powershell
# Enable PowerShell scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Set up helpful Git aliases
.\.git-workflow\setup-aliases.ps1
```

---

## 📊 Daily Commands

### View Your Branches
```powershell
# See all branches and their status
.\.git-workflow\view-branches.ps1

# With a visual graph
.\.git-workflow\view-branches.ps1 -Graph
```

### Keep Your Branch Updated
```powershell
# Make sure you're on your branch first
git checkout backend-dev-sprint-2

# Sync with main
.\.git-workflow\sync-with-main.ps1
```

### Compare Branches
```powershell
# See what's different between your branch and main
.\.git-workflow\compare-branches.ps1 main backend-dev-sprint-2

# Or compare backend and frontend branches
.\.git-workflow\compare-branches.ps1 backend-dev-sprint-2 frontend-dev
```

---

## 🔄 When Ready to Merge Both Branches

### Step 1: Prepare
```powershell
# Both you and frontend developer: sync with main
git checkout backend-dev-sprint-2
.\.git-workflow\sync-with-main.ps1

# Push your latest changes
git push origin backend-dev-sprint-2
```

### Step 2: Create Integration Branch
```powershell
# This merges both backend and frontend into a test branch
.\.git-workflow\merge-to-main.ps1 backend-dev-sprint-2 frontend-dev
```

### Step 3: Test Everything
- Run all backend tests
- Run all frontend tests
- Test API endpoints
- Check frontend-backend integration
- Manual testing

### Step 4: Finalize to Main
```powershell
# Once testing is complete (replace with actual branch name from step 2)
.\.git-workflow\finalize-merge.ps1 integration-20241120-143022
```

### Step 5: Update Your Branches
```powershell
# Both developers should sync with the new main
git checkout backend-dev-sprint-2
.\.git-workflow\sync-with-main.ps1
```

---

## 🎯 Common Git Commands

### Basic Operations
```powershell
# Check which branch you're on
git branch

# Switch to your branch
git checkout backend-dev-sprint-2

# See what's changed
git status

# Stage all changes
git add .

# Commit with proper format
git commit -m "feat(api): add user authentication endpoint"

# Push to remote
git push origin backend-dev-sprint-2
```

### Using Git Aliases (after setup)
```powershell
# Instead of typing full commands:
git st                  # git status
git co backend-dev-sprint-2   # git checkout
git branches            # see all branches
git lg                  # pretty log graph
git sync                # sync with main quickly
```

---

## 🆘 Emergency Commands

### Undo Last Commit (Keep Changes)
```powershell
git undo  # or git reset --soft HEAD~1
```

### Discard All Local Changes
```powershell
git checkout .
```

### Cancel a Merge
```powershell
git merge --abort
```

### See What Changed in Last Commit
```powershell
git last  # or git log -1 HEAD --stat
```

---

## ✅ Best Practices Checklist

**Before Starting Work:**
- [ ] Switch to your branch: `git checkout backend-dev-sprint-2`
- [ ] Sync with main: `.\.git-workflow\sync-with-main.ps1`
- [ ] Pull latest from your branch: `git pull origin backend-dev-sprint-2`

**While Working:**
- [ ] Commit frequently with descriptive messages
- [ ] Use conventional commit format: `feat(scope): description`
- [ ] Push regularly: `git push origin backend-dev-sprint-2`

**Before Merging:**
- [ ] Coordinate with frontend developer
- [ ] Both sync with main
- [ ] Compare branches to check for conflicts
- [ ] Test integration branch thoroughly
- [ ] Get approval from team before finalizing

---

## 📝 Commit Message Format

Use this format (from your project rules):

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```powershell
git commit -m "feat(api): add user registration endpoint"
git commit -m "fix(database): resolve connection timeout issue"
git commit -m "docs(readme): update installation instructions"
```

---

## 🔍 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't run PowerShell scripts | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Merge conflicts | Open files, resolve conflicts between `<<<<<<<` and `>>>>>>>`, then `git add .` and `git commit` |
| Behind remote branch | `git pull origin backend-dev-sprint-2` |
| Accidentally committed to wrong branch | `git undo`, then `git checkout correct-branch` |
| Need to switch branches but have uncommitted changes | `git stash`, switch branches, then `git stash pop` |

---

## 📞 Get Help

```powershell
# View all branches and status
.\.git-workflow\view-branches.ps1

# See the README for detailed info
Get-Content .git-workflow\README.md

# Git's built-in help
git help <command>
```

---

## 🎓 Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│                    Your Daily Workflow                   │
└─────────────────────────────────────────────────────────┘

1. Start Day:
   git checkout backend-dev-sprint-2
   .\.git-workflow\sync-with-main.ps1

2. Work & Commit:
   [make changes]
   git add .
   git commit -m "feat(api): your changes"
   git push origin backend-dev-sprint-2

3. Before Merge:
   .\.git-workflow\compare-branches.ps1 main backend-dev-sprint-2
   [coordinate with frontend dev]

4. Merge Process:
   .\.git-workflow\merge-to-main.ps1
   [test integration]
   .\.git-workflow\finalize-merge.ps1 integration-xxxxx

5. After Merge:
   .\.git-workflow\sync-with-main.ps1
```

**Remember:** When in doubt, check branch status with `.\.git-workflow\view-branches.ps1` !

