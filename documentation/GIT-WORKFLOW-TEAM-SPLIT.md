# Git Workflow for Team Split Development

**Team Structure:**
- **Backend Developer (You):** `backend-dev-sprint-2` branch
- **Frontend Developer (Friend):** `frontend-dev` branch
- **Main Branch:** `main` (stable, production-ready code)

---

## 🌳 Branch Structure

```
main (production-ready)
├── backend-dev-sprint-2 (your backend work)
└── frontend-dev (friend's frontend work)
```

**Branch Purposes:**
- `main` - Stable, tested, production-ready code
- `backend-dev-sprint-2` - Your backend development (Sprint 2 work)
- `frontend-dev` - Friend's frontend development (Sprint 2 work)

---

## 👀 How to View All Branches

### **1. List All Local Branches**

```powershell
# See all local branches
git branch

# See all branches with latest commit
git branch -v

# See all branches (local + remote)
git branch -a
```

### **2. View Remote Branches**

```powershell
# Fetch latest info from remote (GitHub/GitLab/etc)
git fetch origin

# List all remote branches
git branch -r

# List all branches (local + remote)
git branch -a
```

### **3. View Branch Status**

```powershell
# See which branch you're on
git status

# See all branches with tracking info
git branch -vv
```

### **4. Visual Branch History**

```powershell
# See branch history (text-based)
git log --oneline --graph --all --decorate

# See last 10 commits across all branches
git log --oneline --graph --all --decorate -10

# See specific branches
git log --oneline --graph main backend-dev-sprint-2 frontend-dev
```

**Example Output:**
```
* 2d7a3ab (HEAD -> backend-dev-sprint-2) docs: Update all documentation
* 5149192 feat(backend): Complete Day 5 backend enhancements
* ff52f47 feat(backend): Complete Day 4 KB system
| * a1b2c3d (frontend-dev) feat(frontend): Connect test generation UI
| * d4e5f6g feat(frontend): Add KB upload form
|/
* 89abcde (main) feat: Sprint 1 complete
```

---

## 🔄 Keeping Branches in Sync

### **Option A: Keep Your Branch Updated with Main**

When `main` gets updated (e.g., after a merge), update your branch:

```powershell
# Switch to your branch
git checkout backend-dev-sprint-2

# Fetch latest changes
git fetch origin

# Merge main into your branch
git merge origin/main

# Or rebase (cleaner history)
git rebase origin/main
```

### **Option B: See Friend's Frontend Work**

To see what your friend is doing:

```powershell
# Fetch all branches
git fetch origin

# Create a local copy of frontend-dev
git checkout -b frontend-dev origin/frontend-dev

# Or just view commits
git log origin/frontend-dev --oneline -10

# Switch back to your branch
git checkout backend-dev-sprint-2
```

### **Option C: Test Both Branches Together (Locally)**

To test integration before merging:

```powershell
# Create a temporary integration branch
git checkout -b integration-test

# Merge backend work
git merge backend-dev-sprint-2

# Merge frontend work
git merge frontend-dev

# Test the integration
# (Start backend server, start frontend server, test end-to-end)

# If successful, continue to merge process
# If issues found, fix them first

# Delete temporary branch
git checkout backend-dev-sprint-2
git branch -D integration-test
```

---

## 🔀 Merging Branches (When Ready)

### **Strategy 1: Merge Both into Main (RECOMMENDED)**

**Use when:** Both backend and frontend are complete and tested

**Steps:**

```powershell
# 1. Make sure both branches are pushed to remote
git checkout backend-dev-sprint-2
git push origin backend-dev-sprint-2

# Friend does the same:
# git checkout frontend-dev
# git push origin frontend-dev

# 2. Switch to main
git checkout main

# 3. Update main with latest changes
git pull origin main

# 4. Merge backend first
git merge backend-dev-sprint-2

# 5. Test backend changes
# (Run backend tests, check for issues)

# 6. Merge frontend
git merge frontend-dev

# 7. Resolve any conflicts (if any)
# (Git will tell you which files have conflicts)
# (Edit files, then: git add . && git commit)

# 8. Test integration
# (Run both servers, test end-to-end)

# 9. Push to main
git push origin main
```

**Pros:**
- Clean, straightforward
- Both changes merged at once
- Easy to track

**Cons:**
- If conflicts arise, harder to debug
- Both developers need to coordinate timing

---

### **Strategy 2: Sequential Merging**

**Use when:** One developer finishes before the other

**Steps:**

```powershell
# Example: Backend finishes first

# 1. You merge backend to main
git checkout main
git pull origin main
git merge backend-dev-sprint-2
git push origin main

# 2. Friend updates their branch with new main
# (Friend runs):
# git checkout frontend-dev
# git pull origin main
# git merge origin/main
# (Resolve any conflicts)
# git push origin frontend-dev

# 3. Friend merges frontend to main
# (Friend runs):
# git checkout main
# git pull origin main
# git merge frontend-dev
# git push origin main
```

**Pros:**
- Less coordination needed
- Conflicts resolved incrementally
- Can merge when ready

**Cons:**
- Second merge might have more conflicts
- Requires good communication

---

### **Strategy 3: Pull Requests (RECOMMENDED for Teams)**

**Use when:** Using GitHub/GitLab/Bitbucket

**Steps:**

```powershell
# 1. Push your branch to remote
git checkout backend-dev-sprint-2
git push origin backend-dev-sprint-2

# 2. Create Pull Request on GitHub
# - Go to GitHub repository
# - Click "New Pull Request"
# - Base: main, Compare: backend-dev-sprint-2
# - Add description, reviewers
# - Create PR

# 3. Friend reviews your code (optional)
# 4. CI/CD runs tests (if set up)
# 5. Merge PR when approved

# Friend does the same for frontend-dev
```

**Pros:**
- Code review built-in
- CI/CD integration
- Conflict detection before merge
- Clear history

**Cons:**
- Requires GitHub/GitLab/etc
- More steps

---

## 🚨 Handling Merge Conflicts

### **What Causes Conflicts?**

Both branches modified the same file in the same place:

```
main: line 10 = "Hello"
backend-dev: line 10 = "Hello Backend"
frontend-dev: line 10 = "Hello Frontend"
```

### **How to Resolve:**

```powershell
# When git merge shows conflicts:
git status
# Shows: "both modified: file.txt"

# Open the file, you'll see:
<<<<<<< HEAD
Hello Backend
=======
Hello Frontend
>>>>>>> frontend-dev

# Edit to keep what you want:
Hello Backend and Frontend

# Stage the resolved file
git add file.txt

# Continue merge
git commit

# Push
git push origin main
```

### **Common Conflicts in Your Project:**

1. **`package.json`** (if both modify dependencies)
   - **Solution:** Keep both sets of dependencies, merge manually

2. **`.env`** files (if both add variables)
   - **Solution:** Keep both variables

3. **API contracts** (if both change same endpoint)
   - **Solution:** Communicate before merging

4. **Documentation** (if both update same docs)
   - **Solution:** Keep both changes, merge manually

---

## 🎯 Recommended Workflow for Your Team

### **Daily Workflow:**

**Backend Developer (You):**
```powershell
# Morning: Check for updates
git checkout backend-dev-sprint-2
git pull origin backend-dev-sprint-2

# Work on your tasks
# ... make changes ...

# Commit frequently
git add .
git commit -m "feat(backend): Add feature X"

# Evening: Push your work
git push origin backend-dev-sprint-2
```

**Frontend Developer (Friend):**
```powershell
# Same process, but on frontend-dev branch
git checkout frontend-dev
git pull origin frontend-dev
# ... work ...
git add .
git commit -m "feat(frontend): Add component Y"
git push origin frontend-dev
```

### **Weekly Sync:**

**Option 1: Sync through Main**
```powershell
# If main gets updated (e.g., hotfix)
git checkout backend-dev-sprint-2
git fetch origin
git merge origin/main
git push origin backend-dev-sprint-2
```

**Option 2: Create Integration Branch**
```powershell
# Test integration weekly
git checkout -b integration-week1
git merge backend-dev-sprint-2
git merge frontend-dev
# Test together
# If successful, prepare for merge to main
```

### **End of Sprint (Merge Time):**

```powershell
# 1. Both push final changes
git push origin backend-dev-sprint-2  # You
git push origin frontend-dev          # Friend

# 2. Create integration branch
git checkout main
git pull origin main
git checkout -b sprint-2-integration

# 3. Merge both branches
git merge backend-dev-sprint-2
git merge frontend-dev

# 4. Resolve any conflicts
# (Edit files, git add, git commit)

# 5. Test thoroughly
# - Start backend: cd backend && .\run_server.ps1
# - Start frontend: cd frontend && npm run dev
# - Run E2E tests: npm run test:e2e
# - Manual testing

# 6. If tests pass, merge to main
git checkout main
git merge sprint-2-integration
git push origin main

# 7. Tag the release
git tag -a v1.1.0 -m "Sprint 2 complete"
git push origin v1.1.0

# 8. Clean up branches (optional)
git branch -d sprint-2-integration
```

---

## 📋 Pre-Merge Checklist

Before merging to `main`, ensure:

- [ ] **Backend:** All tests passing (31/31)
- [ ] **Frontend:** All tests passing (69/69)
- [ ] **Integration:** End-to-end flows tested
- [ ] **Documentation:** All docs updated
- [ ] **No conflicts:** Both branches merge cleanly
- [ ] **Code review:** Both developers reviewed each other's code
- [ ] **Changelog:** Updated with new features
- [ ] **Version:** Updated in package.json and requirements.txt

---

## 🔧 Useful Git Commands

### **View Branch Differences:**

```powershell
# See what changed in backend-dev
git diff main..backend-dev-sprint-2

# See what changed in frontend-dev
git diff main..frontend-dev

# See files changed
git diff --name-only main..backend-dev-sprint-2

# See commits not in main
git log main..backend-dev-sprint-2 --oneline
```

### **Check What Will Be Merged:**

```powershell
# Dry-run merge
git merge --no-commit --no-ff backend-dev-sprint-2
git status
git merge --abort  # Cancel the dry-run
```

### **Visualize Branches (GUI Tools):**

```powershell
# Built-in Git GUI
gitk --all

# Or use VS Code / Cursor extensions:
# - GitLens
# - Git Graph
```

---

## 🚨 Emergency: Undo a Merge

If merge goes wrong:

```powershell
# Before pushing
git reset --hard HEAD~1

# After pushing (creates new commit)
git revert HEAD
git push origin main
```

---

## 🎯 Communication Protocol

### **Before Making Breaking Changes:**

1. **Announce in team chat:** "I'm changing the API endpoint from /tests to /api/tests"
2. **Update API contract document**
3. **Coordinate timing:** "Will merge tomorrow at 2pm"
4. **Test together:** "Can we do integration test today?"

### **When Pushing Major Changes:**

```powershell
git commit -m "BREAKING: Change API endpoint structure

- Renamed /tests to /api/v1/tests
- Updated documentation
- Frontend needs to update apiService.ts"

git push origin backend-dev-sprint-2
```

**Then notify friend:** "Pushed breaking change, see commit message"

---

## 📊 Current Branch Status

**As of Day 5 completion:**

```
main
├── Sprint 1 complete
├── 69/69 frontend tests passing
└── Backend authentication working

backend-dev-sprint-2 (You - Current)
├── Days 1-5 complete
├── 31/31 tests passing
├── 28 API endpoints
└── Ready to merge

frontend-dev (Friend - Unknown status)
├── Status: Check with friend
└── Ready to merge: TBD
```

---

## 🎉 Merge Success Criteria

Ready to merge when:

1. ✅ **Backend complete:** All Day 5 tasks done
2. ✅ **Frontend complete:** All Sprint 2 tasks done
3. ✅ **Tests passing:** Backend (31/31), Frontend (69/69)
4. ✅ **Integration tested:** End-to-end flows working
5. ✅ **No conflicts:** Clean merge
6. ✅ **Documentation:** All docs updated
7. ✅ **Code review:** Both developers approve
8. ✅ **Changelog:** Release notes written

---

## 🚀 Recommended Next Steps

1. **Check Friend's Status:**
   ```powershell
   git fetch origin
   git log origin/frontend-dev --oneline -10
   ```

2. **Coordinate Merge Timing:**
   - "When will frontend be ready?"
   - "Can we merge next week?"
   - "Let's test integration on Friday"

3. **Prepare for Merge:**
   - Both push latest changes
   - Create integration branch
   - Test together
   - Merge to main

4. **After Merge:**
   - Tag release (v1.1.0)
   - Update documentation
   - Celebrate! 🎉

---

## 📝 Quick Reference

```powershell
# View all branches
git branch -a

# Switch branch
git checkout <branch-name>

# Update your branch with main
git merge origin/main

# See friend's work
git log origin/frontend-dev

# Create integration branch
git checkout -b integration-test
git merge backend-dev-sprint-2
git merge frontend-dev

# Merge to main (when ready)
git checkout main
git merge backend-dev-sprint-2
git merge frontend-dev
git push origin main
```

---

**Questions? Ask your friend about their branch status and coordinate the merge!** 🤝

