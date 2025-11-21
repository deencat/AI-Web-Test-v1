# Git Workflow Cheat Sheet

## 🏃‍♂️ Most Common Commands

### Daily Workflow
```powershell
# View all branches
.\.git-workflow\view-branches.ps1

# Sync your branch with main
.\.git-workflow\sync-with-main.ps1

# Check what changed
git status

# Commit and push
git add .
git commit -m "feat(api): your changes"
git push origin backend-dev-sprint-2
```

### Merging (When Ready)
```powershell
# Create integration branch (merges both backend & frontend)
.\.git-workflow\merge-to-main.ps1

# After testing, finalize
.\.git-workflow\finalize-merge.ps1 integration-XXXXXXXX
```

---

## 📋 Script Reference

| Script | What It Does |
|--------|--------------|
| `view-branches.ps1` | Show all branches and their status |
| `view-branches.ps1 -Graph` | Show branches with visual graph |
| `compare-branches.ps1 branch1 branch2` | See differences between branches |
| `sync-with-main.ps1` | Update your branch from main |
| `sync-with-main.ps1 -Rebase` | Update using rebase (cleaner history) |
| `merge-to-main.ps1` | Create integration branch |
| `finalize-merge.ps1 <branch>` | Merge integration to main |
| `setup-aliases.ps1` | Install Git shortcuts |

---

## 🎯 Git Basics

### Branch Operations
```powershell
git branch                          # List local branches
git branch -a                       # List all branches
git checkout backend-dev-sprint-2   # Switch to branch
git branch --show-current           # Show current branch
```

### Viewing Changes
```powershell
git status                          # What's changed
git diff                            # See exact changes
git log --oneline -10               # Last 10 commits
git log --graph --oneline -20       # Visual history
```

### Committing
```powershell
git add .                           # Stage all changes
git add file.txt                    # Stage specific file
git commit -m "message"             # Commit with message
git push origin backend-dev-sprint-2 # Push to remote
```

### Syncing
```powershell
git fetch origin                    # Get remote changes
git pull origin backend-dev-sprint-2 # Pull your branch
git merge origin/main               # Merge main into current
```

---

## 🛠️ Git Aliases (After Setup)

| Alias | Full Command | Use |
|-------|--------------|-----|
| `git st` | `git status` | Quick status |
| `git co <branch>` | `git checkout` | Switch branch |
| `git br` | `git branch` | List branches |
| `git lg` | Pretty log graph | Visual history |
| `git sync` | Fetch + merge main | Quick sync |
| `git last` | Show last commit | See recent work |
| `git undo` | Soft reset HEAD~1 | Undo last commit |

---

## 💾 Commit Message Format

```
<type>(<scope>): <description>

[optional body]
```

### Types
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

### Examples
```powershell
git commit -m "feat(api): add user registration"
git commit -m "fix(auth): resolve token expiration bug"
git commit -m "docs(readme): update installation steps"
```

---

## 🆘 Emergency Commands

### Undo Operations
```powershell
git undo                            # Undo commit, keep changes
git reset --hard HEAD               # Discard all changes
git checkout .                      # Discard unstaged changes
git clean -fd                       # Remove untracked files
```

### Cancel Operations
```powershell
git merge --abort                   # Cancel merge
git rebase --abort                  # Cancel rebase
git stash                           # Save changes temporarily
git stash pop                       # Restore stashed changes
```

### Fix Mistakes
```powershell
git commit --amend                  # Fix last commit
git reset HEAD file.txt             # Unstage file
git checkout -- file.txt            # Discard file changes
```

---

## 🔍 Inspection Commands

### Compare Branches
```powershell
# See what's in your branch not in main
git log main..backend-dev-sprint-2 --oneline

# See what's in main not in your branch
git log backend-dev-sprint-2..main --oneline

# See file differences
git diff main backend-dev-sprint-2
```

### Search History
```powershell
git log --grep="search term"        # Search commit messages
git log --author="Your Name"        # Your commits
git log --since="2 weeks ago"       # Recent commits
git log -- file.txt                 # Commits affecting file
```

---

## 📊 Branch Status Symbols

```
* = Current branch
✓ = Merged into main
⏱️ = Pending (not merged)
↑ = Ahead of remote
↓ = Behind remote
```

---

## 🤝 Coordination with Frontend Dev

### Before Merge Checklist
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Both synced with main
- [ ] Both pushed latest changes
- [ ] Agreed on merge timing
- [ ] API compatibility verified

### Merge Process
1. **Backend dev** runs: `.\.git-workflow\merge-to-main.ps1`
2. **Both** test integration branch
3. **Backend dev** runs: `.\.git-workflow\finalize-merge.ps1`
4. **Both** run: `.\.git-workflow\sync-with-main.ps1`

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't run PowerShell scripts | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Merge conflicts | Edit files, remove `<<<<`, `====`, `>>>>`, then `git add .` and `git commit` |
| Detached HEAD | `git checkout backend-dev-sprint-2` |
| Behind remote | `git pull origin backend-dev-sprint-2` |
| Ahead of remote | `git push origin backend-dev-sprint-2` |
| Uncommitted changes blocking | `git stash` → do operation → `git stash pop` |

---

## 📚 Learn More

```powershell
# View help for any command
git help <command>

# Examples:
git help merge
git help rebase
git help log
```

---

## 🎓 Pro Tips

1. **Commit often** - Small commits are easier to manage
2. **Pull before push** - Avoid conflicts
3. **Sync daily** - Stay up to date with main
4. **Test before merge** - Use integration branch
5. **Communicate** - Talk with your team before merging
6. **Use descriptive messages** - Future you will thank you
7. **Keep main stable** - Only merge tested code

---

**Quick Help:** Run `.\.git-workflow\view-branches.ps1` anytime to see your status!

