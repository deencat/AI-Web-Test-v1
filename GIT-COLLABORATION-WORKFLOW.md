# Git Collaboration Workflow - Backend & Frontend Teams

## Overview
This guide explains how to coordinate development when multiple developers are working on different parts of the codebase (backend and frontend) and need to merge their work into the main branch.

## Current Branch Structure

```
main (production-ready code)
├── backend-dev-sprint-2 (your backend work) ✅ MERGED
└── frontend-dev (your friend's frontend work) ⏳ PENDING
```

## Workflow for Your Friend (Frontend Developer)

### Step 1: Ensure Local Branch is Up to Date

```bash
# Switch to frontend-dev branch
git checkout frontend-dev

# Get latest changes from remote
git fetch origin

# Merge any remote changes
git merge origin/frontend-dev
```

### Step 2: Update with Latest Main

Before merging to main, sync with the latest main branch (which now includes your backend work):

```bash
# While on frontend-dev branch
git fetch origin main
git merge origin/main

# If there are merge conflicts, resolve them:
# 1. Open conflicted files
# 2. Fix conflicts manually
# 3. Stage resolved files: git add <filename>
# 4. Complete merge: git commit
```

### Step 3: Test Everything Together

```bash
# Test that frontend works with the new backend code
# Run backend: cd backend && ./start.ps1
# Run frontend: cd frontend && npm run dev
# Verify all features work together
```

### Step 4: Merge Frontend to Main

```bash
# Switch to main branch
git checkout main

# Pull latest main (includes your backend changes)
git pull origin main

# Merge frontend-dev into main
git merge frontend-dev --no-ff

# If conflicts occur, resolve them as in Step 2
```

### Step 5: Push to Remote

```bash
# Push merged main to GitHub
git push origin main

# Optionally, push updated frontend-dev
git push origin frontend-dev
```

## Workflow for Both of You (Ongoing Development)

### Daily Workflow Pattern

```
┌─────────────┐
│   Start     │
│   of Day    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  git checkout <your-branch> │
│  git pull origin main       │  ← Get latest from main
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Work on your features      │
│  Commit regularly           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  git push origin            │  ← Share your work
│  <your-branch>              │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Ready to merge to main?    │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Create Pull Request (PR)   │  ← Recommended approach
│  OR merge locally           │
└─────────────────────────────┘
```

### Best Practice: Use Pull Requests

Instead of merging directly, use GitHub Pull Requests for better collaboration:

#### For Your Friend (Frontend):
1. **Push frontend branch to GitHub**
   ```bash
   git push origin frontend-dev
   ```

2. **Create Pull Request on GitHub**
   - Go to: https://github.com/deencat/AI-Web-Test-v1
   - Click "Pull requests" → "New pull request"
   - Base: `main` ← Compare: `frontend-dev`
   - Add description of changes
   - Click "Create pull request"

3. **Review Together**
   - You can review the changes
   - Comment on code
   - Request changes if needed
   - Approve when ready

4. **Merge on GitHub**
   - Click "Merge pull request"
   - Choose merge type (usually "Create a merge commit")
   - Confirm merge

5. **Update Local Main**
   ```bash
   git checkout main
   git pull origin main
   ```

### For You (Backend):
Same process for future backend work:
1. Create a new branch for new features
2. Push to GitHub
3. Create Pull Request
4. Review and merge

## Handling Conflicts Between Backend & Frontend

### Common Conflict Scenarios

#### 1. Both Modified Same Files
**Example:** Both changed `README.md`

```bash
# During merge, Git will show:
# CONFLICT (content): Merge conflict in README.md

# Open the file, you'll see:
<<<<<<< HEAD
Backend changes here
=======
Frontend changes here
>>>>>>> frontend-dev

# Manually combine or choose:
Both backend and frontend changes combined here

# Then:
git add README.md
git commit -m "Merge: Resolved README conflict"
```

#### 2. Dependencies Conflict
**Example:** Both added different package versions

```bash
# package.json (frontend) or requirements.txt (backend)
# Choose the higher version or test both
# Update the file, then:
git add package.json  # or requirements.txt
git commit -m "Merge: Resolved dependency conflict"
```

#### 3. Configuration File Conflicts
**Example:** Both changed `.env.example` or config files

```bash
# Combine both sets of variables
# Backend env vars
# Frontend env vars

git add .env.example
git commit -m "Merge: Combined env configurations"
```

## Coordinated Merge Strategy

### Option 1: Sequential Merges (Recommended for now)
```
Step 1: Frontend merges to main (following steps above)
Step 2: You pull the updated main
Step 3: Test everything together
Step 4: Continue work on new branches
```

### Option 2: Feature Branch Integration
```bash
# Create integration branch for testing
git checkout -b integration-test
git merge backend-dev-sprint-2
git merge frontend-dev

# Test everything together
# If works, merge to main
git checkout main
git merge integration-test
git push origin main
```

### Option 3: Continuous Integration (Future)
Set up GitHub Actions to automatically test when PRs are created:
- Run backend tests
- Run frontend tests
- Check for merge conflicts
- Auto-merge if all tests pass

## Communication Best Practices

### Before Merging
- [ ] **Notify each other**: "I'm about to merge to main"
- [ ] **Confirm no one else is merging**: Avoid simultaneous merges
- [ ] **Pull latest main first**: Ensure you have latest code
- [ ] **Test locally**: Both backend and frontend should work

### After Merging
- [ ] **Notify team**: "Merged to main, please pull latest"
- [ ] **Update documentation**: If APIs or features changed
- [ ] **Tag releases** (optional): `git tag v1.1.0` for versions

## Quick Reference Commands

### For Your Friend (Frontend) - First Time Merge

```bash
# 1. Get latest main with your backend changes
git checkout main
git pull origin main

# 2. Switch to frontend branch and sync
git checkout frontend-dev
git merge main

# 3. Resolve any conflicts, test everything

# 4. Merge frontend to main
git checkout main
git merge frontend-dev --no-ff

# 5. Push to GitHub
git push origin main
```

### For Both - Daily Work

```bash
# Morning: Start with latest main
git checkout <your-branch>
git pull origin main

# During day: Commit often
git add .
git commit -m "feat: descriptive message"

# Evening: Push your branch
git push origin <your-branch>

# When ready to merge: Create Pull Request on GitHub
```

### For Both - After Someone Merges

```bash
# Update your main
git checkout main
git pull origin main

# Update your working branch
git checkout <your-branch>
git merge main

# Resolve conflicts if any, then continue working
```

## Troubleshooting

### "Your branch is behind origin/main"
```bash
git pull origin main
```

### "Merge conflict in <file>"
```bash
# 1. Open the file, look for <<<<<<< and >>>>>>>
# 2. Edit to resolve conflicts
# 3. git add <file>
# 4. git commit -m "Merge: Resolved conflicts"
```

### "I merged but it's not on GitHub"
```bash
git push origin main
```

### "I merged to main by accident"
```bash
# If not pushed yet:
git reset --hard HEAD~1

# If already pushed (dangerous, coordinate with team):
git revert <commit-hash>
```

### "Both of us merged at the same time"
```bash
# One person's push will fail
# The failed person should:
git pull origin main  # Gets the other person's merge
git push origin main  # Pushes again
```

## Directory Structure Awareness

Since backend and frontend are in separate directories, conflicts are less likely:

```
AI-Web-Test v1/
├── backend/              ← Your work mostly here
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── frontend/             ← Friend's work mostly here
│   ├── src/
│   ├── package.json
│   └── ...
├── .gitignore           ← Both might edit
├── README.md            ← Both might edit
└── documentation/       ← Both might add files
```

**Low conflict areas:** Code in backend/ vs frontend/  
**High conflict areas:** Root-level docs, .gitignore, shared configs

## Next Steps

1. **Share this guide** with your friend
2. **Choose a merge strategy** (I recommend Pull Requests)
3. **Coordinate a time** to do the frontend merge together
4. **Test everything** after merging
5. **Establish a routine** for daily syncs

## Need Help?

If you run into issues:
1. **Don't force push** (`git push -f`) unless you know what you're doing
2. **Communicate with your teammate** before resolving conflicts
3. **Ask for help** - show the conflict and discuss the solution
4. **Use Git GUI tools** like GitHub Desktop for visualizing merges

---

**Remember:** Git is about collaboration. When in doubt, communicate!

