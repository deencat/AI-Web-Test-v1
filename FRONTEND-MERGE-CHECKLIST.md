# Frontend Developer - Merge Checklist

## Pre-Merge Checklist for Your Friend

Before merging the `frontend-dev` branch to `main`, your friend should complete these steps:

### ✅ 1. Backup Current Work
```bash
# Create a backup branch (just in case)
git checkout frontend-dev
git branch frontend-dev-backup
```

### ✅ 2. Sync with Latest Main (includes backend changes)
```bash
# Get the latest main branch (with backend work)
git checkout main
git pull origin main

# Go back to frontend branch
git checkout frontend-dev

# Merge main into frontend-dev
git merge main
```

**Expected outcome:** If conflicts occur, resolve them now before merging to main.

### ✅ 3. Test Integration Locally

```bash
# Terminal 1 - Start Backend
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

# Terminal 2 - Start Frontend
cd frontend
npm install  # if needed
npm run dev

# Browser - Test the application
# Open: http://localhost:5173 (or your frontend port)
```

**Test these critical areas:**
- [ ] Frontend loads without errors
- [ ] API calls to backend work
- [ ] Authentication flows (login/register)
- [ ] All main features function correctly
- [ ] No console errors
- [ ] Build succeeds: `npm run build`

### ✅ 4. Commit Any Fixes from Integration Testing

```bash
# If you had to fix anything during testing
git add .
git commit -m "fix: Resolved integration issues with backend"
git push origin frontend-dev
```

### ✅ 5. Prepare for Merge

```bash
# Switch to main
git checkout main

# Ensure main is up-to-date
git pull origin main

# Merge frontend-dev into main (with merge commit)
git merge frontend-dev --no-ff -m "Merge frontend-dev into main: Add Sprint 1 frontend features"
```

### ✅ 6. Resolve Any Merge Conflicts

If conflicts appear, they're likely in:
- `README.md`
- `.gitignore`
- `package.json` (root level if exists)
- Documentation files

**How to resolve:**
```bash
# Git will tell you which files have conflicts
# For each conflicted file:
#   1. Open the file
#   2. Look for <<<<<<< HEAD and >>>>>>> frontend-dev markers
#   3. Edit to keep both changes or choose one
#   4. Remove the conflict markers

# After fixing all conflicts:
git add <resolved-file>
git add <another-resolved-file>
# ... for all conflicted files

# Complete the merge
git commit -m "Merge frontend-dev: Resolved conflicts with backend changes"
```

### ✅ 7. Final Test

```bash
# On the merged main branch, test again
# Terminal 1 - Backend
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Test everything one more time
```

### ✅ 8. Push to GitHub

```bash
# Push the merged main branch
git push origin main

# Optionally, update the remote frontend-dev branch
git checkout frontend-dev
git merge main  # Fast-forward frontend-dev to match main
git push origin frontend-dev
```

### ✅ 9. Notify Team

Send a message:
> "✅ Frontend merged to main! Please pull latest:
> ```
> git checkout main
> git pull origin main
> ```"

---

## For You (Backend Developer) - After Frontend Merges

### ✅ 1. Pull the Updated Main

```bash
# Switch to main
git checkout main

# Pull latest (now includes frontend changes)
git pull origin main
```

### ✅ 2. Test the Complete Application

```bash
# Terminal 1 - Backend
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install  # Install any new frontend dependencies
npm run dev

# Test everything together
```

### ✅ 3. Create New Branch for Next Sprint

```bash
# Don't work directly on main
# Create a new branch for your next features

git checkout -b backend-dev-sprint-3
# or
git checkout -b feature/new-backend-feature

# Start working on new features
```

---

## Alternative: Using Pull Requests (Recommended)

Instead of merging locally, your friend can use GitHub Pull Requests:

### Step-by-Step for Your Friend

1. **Push frontend branch to GitHub**
   ```bash
   git checkout frontend-dev
   git push origin frontend-dev
   ```

2. **Create Pull Request**
   - Go to: https://github.com/deencat/AI-Web-Test-v1/pulls
   - Click "New pull request"
   - Base: `main` ← Compare: `frontend-dev`
   - Title: "Merge frontend Sprint 1 features"
   - Description: List what was added/changed
   - Click "Create pull request"

3. **You Review the PR**
   - Click on the PR
   - Review the "Files changed" tab
   - Add comments if needed
   - Click "Approve" when ready

4. **Merge the PR**
   - Your friend clicks "Merge pull request"
   - Choose "Create a merge commit"
   - Click "Confirm merge"

5. **Both Pull Latest Main**
   ```bash
   git checkout main
   git pull origin main
   ```

**Benefits of Pull Requests:**
- ✅ See all changes before merging
- ✅ GitHub checks for conflicts automatically
- ✅ Can discuss changes in comments
- ✅ Keeps a clear history
- ✅ Can require approvals before merging

---

## Common Issues & Solutions

### Issue: "Cannot merge - unrelated histories"
```bash
# Solution:
git merge frontend-dev --allow-unrelated-histories
```

### Issue: "Your branch is ahead of origin/main by X commits"
```bash
# Solution: You need to push
git push origin main
```

### Issue: "Conflict in package-lock.json"
```bash
# Solution: Regenerate it
rm package-lock.json
npm install
git add package-lock.json
git commit -m "fix: Regenerate package-lock.json"
```

### Issue: "Frontend can't connect to backend"
```bash
# Check frontend .env or config files
# Ensure API URL is correct
# Example: VITE_API_URL=http://localhost:8000

# Backend should be running on: http://localhost:8000
# Frontend should be running on: http://localhost:5173
```

### Issue: "Merge conflicts in too many files"
```bash
# Consider using a GUI tool:
# - GitHub Desktop (https://desktop.github.com/)
# - VS Code built-in merge tool
# - GitKraken (https://www.gitkraken.com/)
```

---

## Coordination Tips

### Before Merging
1. **Pick a time to coordinate**: "Let's merge frontend at 3pm today"
2. **No one works on main**: Ensure no one is pushing to main
3. **Communicate**: "Starting frontend merge now"

### During Merge
1. **Share screen if needed**: Use Zoom/Discord to merge together
2. **Ask questions**: "Should we keep both README sections?"
3. **Test together**: Both run the app after merging

### After Merge
1. **Both pull main**: Update your local repositories
2. **Create new branches**: For new features
3. **Document changes**: Update docs if APIs changed

---

## Suggested Merge Schedule

```
Week 1:
  Day 1-3: Both work on separate branches
  Day 4: Integration testing (merge main into your branches)
  Day 5: Merge to main (one at a time)

Week 2:
  Day 1: Both pull latest main
  Day 2-4: Work on new features
  Day 5: Merge again
```

---

## Quick Command Reference

**For Frontend Developer:**
```bash
# Before merge
git checkout main && git pull origin main
git checkout frontend-dev && git merge main

# Test everything

# Merge
git checkout main
git merge frontend-dev --no-ff
git push origin main
```

**For Backend Developer (after frontend merges):**
```bash
# Pull latest
git checkout main && git pull origin main

# Test everything

# Create new branch for next work
git checkout -b backend-dev-sprint-3
```

**For Both (daily sync):**
```bash
# Get latest main into your working branch
git checkout <your-branch>
git merge main
```

---

## Success Criteria

✅ Frontend branch merged to main  
✅ No merge conflicts (or all resolved)  
✅ Application runs successfully  
✅ Both developers have latest main  
✅ New branches created for next sprint  
✅ Team is coordinated and informed  

---

**Need Help?** Don't hesitate to:
- Create an issue on GitHub
- Ask for review before merging
- Use "Draft Pull Request" to show work-in-progress
- Schedule a call to merge together

**Remember:** It's better to ask questions than to force-push and lose work!

