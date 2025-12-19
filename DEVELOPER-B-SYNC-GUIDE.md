# Developer B - How to Sync Database Collaboration Features

## Scenario

Developer A (you) just pushed database collaboration infrastructure to the `main` branch.  
Developer B is working on a different branch (e.g., `feature/their-feature`).  
Developer B needs to get the database collaboration features into their branch.

---

## Option 1: Merge Main into Feature Branch (Recommended)

This is the **standard approach** - bring the latest infrastructure from `main` into your feature branch.

### Step-by-Step for Developer B

```powershell
# 1. Save current work (if any uncommitted changes)
git add .
git commit -m "WIP: Save current work before merge"

# 2. Switch to main branch and pull latest changes
git checkout main
git pull origin main

# 3. Switch back to your feature branch
git checkout feature/their-feature

# 4. Merge main into your feature branch
git merge main
```

**What happens:**
- ✅ Your feature branch now has all the database collaboration infrastructure
- ✅ Your existing feature code is preserved
- ✅ If there are conflicts, Git will tell you (resolve them manually)

### After Merge: Setup Database

```powershell
# 5. Navigate to backend folder
cd backend

# 6. Run migrations (creates/updates database schema)
python run_migrations.py

# 7. Seed database with test data
python db_seed_simple.py
# OR for full seed:
python db_seed.py

# 8. Verify backend works
python -m uvicorn app.main:app --reload
# Test at http://localhost:8000
```

### Push Updated Feature Branch

```powershell
# 9. Push your updated feature branch
git push origin feature/their-feature
```

---

## Option 2: Rebase Feature Branch onto Main (Advanced)

This **rewrites history** to make it look like your feature was built on top of the latest main.  
⚠️ Only use if you're comfortable with rebasing and no one else is working on your branch.

### Step-by-Step for Developer B

```powershell
# 1. Save current work (if any uncommitted changes)
git add .
git commit -m "WIP: Save current work before rebase"

# 2. Switch to main and pull latest
git checkout main
git pull origin main

# 3. Switch back to feature branch
git checkout feature/their-feature

# 4. Rebase feature branch onto main
git rebase main
```

**What happens:**
- ✅ Your feature commits are replayed on top of main
- ✅ Cleaner history (linear)
- ⚠️ May have conflicts to resolve
- ⚠️ Requires force-push if already pushed to remote

### If Conflicts Occur

```powershell
# Git will pause at conflicts
# 1. Open conflicted files and resolve manually
# 2. Mark as resolved
git add <resolved-files>
# 3. Continue rebase
git rebase --continue

# If it gets too messy, abort and use Option 1 instead
git rebase --abort
```

### Push Rebased Branch (Force Push Required)

```powershell
# ⚠️ WARNING: This rewrites history on remote
git push origin feature/their-feature --force-with-lease
```

### After Rebase: Setup Database

```powershell
cd backend
python run_migrations.py
python db_seed_simple.py
python -m uvicorn app.main:app --reload
```

---

## Option 3: Cherry-Pick Specific Commits (Selective)

If Developer B only wants **specific files** from main (not recommended for infrastructure).

```powershell
# 1. Find the commit hash from main
git log origin/main --oneline
# Look for: 4458e60 feat: Add database collaboration infrastructure

# 2. Switch to your feature branch
git checkout feature/their-feature

# 3. Cherry-pick the commit
git cherry-pick 4458e60
```

**What happens:**
- ✅ Only that specific commit is applied
- ⚠️ May miss related changes from other commits

---

## Recommended Workflow (Best Practice)

### For Developer B

**When to Merge Main into Your Feature Branch:**
1. **Before starting new work** - Always sync with main first
2. **When main has important updates** - Like this database collaboration infrastructure
3. **Before creating a Pull Request** - Ensure no conflicts with main
4. **Regularly (e.g., daily/weekly)** - Keep feature branch up-to-date

### Complete Workflow

```powershell
# === STEP 1: Get Latest Infrastructure ===
git checkout main
git pull origin main

# === STEP 2: Update Your Feature Branch ===
git checkout feature/your-feature
git merge main
# Resolve any conflicts if they appear

# === STEP 3: Setup Database (First Time Only) ===
cd backend

# Run migrations (creates tables)
python run_migrations.py

# Seed database (loads test data)
python db_seed_simple.py

# === STEP 4: Verify Everything Works ===
python -m uvicorn app.main:app --reload
# Test at http://localhost:8000/docs

# === STEP 5: Continue Your Work ===
# Now you can use the database collaboration features!
# - Your database is in sync with Developer A
# - You have the same test data
# - Schema changes are tracked via migrations

# === STEP 6: When Ready, Push Your Work ===
git add .
git commit -m "Your feature changes"
git push origin feature/your-feature
```

---

## What Developer B Gets After Sync

### New Files Available

```
✅ .gitignore (updated)              - Database files excluded
✅ backend/run_migrations.py         - Migration runner
✅ backend/db_seed_simple.py         - Simple seed script
✅ backend/db_seed.py                - Full seed script
✅ DATABASE-COLLABORATION-WORKFLOW.md - Complete guide
✅ DATABASE-QUICK-START.md           - Quick reference
✅ DATABASE-COLLABORATION-SOLUTION.md - Implementation summary
```

### New Capabilities

1. **Run Migrations**
   ```powershell
   python run_migrations.py
   # Shows which migrations are applied
   # Runs any pending migrations
   ```

2. **Seed Database**
   ```powershell
   python db_seed_simple.py
   # Creates: admin, qa_user
   ```

3. **Export/Import Test Cases**
   ```powershell
   # Export your test cases to share
   python db_seed.py --export
   
   # Import someone else's test cases
   python db_seed.py --import
   ```

4. **Reset Database**
   ```powershell
   python db_seed.py --reset
   # Fresh start (drops all tables, runs migrations, seeds data)
   ```

---

## Common Scenarios After Sync

### Scenario 1: Developer B Starts Fresh on New PC

```powershell
# 1. Clone repo
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1-1

# 2. Checkout your feature branch
git checkout feature/your-feature

# 3. Setup database
cd backend
python run_migrations.py
python db_seed_simple.py

# 4. Start coding!
```

---

### Scenario 2: Developer A Created New Test Cases

**Developer A:**
```powershell
# 1. Create test cases via UI
# 2. Export to seed file
python db_seed.py --export

# 3. Commit and push
git add seed_test_cases.json
git commit -m "Add new test cases for login flow"
git push origin main
```

**Developer B:**
```powershell
# 1. Merge main into your branch
git checkout feature/your-feature
git merge origin/main

# 2. Import the new test cases
cd backend
python db_seed.py --import

# 3. Now you have the same test cases!
```

---

### Scenario 3: Developer B Adds Database Column

**Developer B:**
```powershell
# 1. Create migration script
# backend/migrations/add_tags_to_tests.py

# 2. Run migration locally
python migrations/add_tags_to_tests.py

# 3. Commit migration script (NOT database)
git add migrations/add_tags_to_tests.py
git commit -m "Add tags column to test_cases"
git push origin feature/your-feature

# 4. When feature is merged to main, Developer A will run:
python migrations/add_tags_to_tests.py
```

---

### Scenario 4: Both Developers Working on Different Features

**Setup (Both Developers):**
```powershell
# Both merge main regularly
git checkout feature/my-feature
git merge origin/main

# Both run migrations when new ones are added
cd backend
python run_migrations.py

# Both can share test cases via export/import
python db_seed.py --export  # Developer A
python db_seed.py --import  # Developer B
```

**Result:**
- ✅ Both have identical schema (via migrations)
- ✅ Both have shared test data (via seed files)
- ✅ No database conflicts (each has their own *.db file)
- ✅ Features developed independently

---

## Troubleshooting

### Problem: Merge Conflicts

```powershell
# When git merge main shows conflicts:

# 1. See which files have conflicts
git status

# 2. Open conflicted files in VS Code
# Look for conflict markers:
# <<<<<<< HEAD
# Your code
# =======
# Code from main
# >>>>>>> main

# 3. Resolve manually (choose which code to keep)

# 4. Mark as resolved
git add <resolved-file>

# 5. Complete the merge
git commit
```

---

### Problem: Database Out of Sync

```powershell
# Quick fix: Reset database
cd backend
python db_seed.py --reset

# This will:
# 1. Drop all tables
# 2. Run all migrations (recreate schema)
# 3. Seed default data
```

---

### Problem: Missing Migrations

```powershell
# Check migration status
cd backend
python run_migrations.py

# Output shows:
# ✅ Applied: migration1.py
# ✅ Applied: migration2.py
# ⏳ Pending: migration3.py

# Run pending migrations
# (They'll auto-run when you execute run_migrations.py)
```

---

### Problem: Different Python Dependencies

```powershell
# After merging, always update dependencies
cd backend
pip install -r requirements.txt

# Or if using virtual environment:
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## Quick Reference Card for Developer B

### First Time Setup (After Sync)
```powershell
git checkout main && git pull
git checkout feature/my-feature
git merge main
cd backend
python run_migrations.py
python db_seed_simple.py
```

### Daily Workflow
```powershell
# Pull latest from main (once a day/week)
git checkout main && git pull
git checkout feature/my-feature && git merge main

# Run new migrations (if any)
cd backend && python run_migrations.py

# Continue working...
```

### When You Need Fresh Database
```powershell
cd backend
python db_seed.py --reset
```

### When Sharing Test Cases
```powershell
# Export yours
python db_seed.py --export
git add seed_test_cases.json && git commit -m "Add test cases"

# Import someone else's
git pull && python db_seed.py --import
```

---

## Summary

**Recommended Approach for Developer B:**

1. ✅ **Merge main into feature branch** (Option 1)
2. ✅ **Run migrations** to update database schema
3. ✅ **Run seed script** to get test data
4. ✅ **Continue working** on your feature
5. ✅ **Regularly sync** with main to avoid big conflicts later

**Key Benefits:**
- 🚀 No manual database sharing needed
- 🔄 Always in sync with latest schema
- 🤝 Easy collaboration via seed files
- 🔧 Simple reset when things go wrong

**Next Steps:**
- Read `DATABASE-COLLABORATION-WORKFLOW.md` for detailed scenarios
- Read `DATABASE-QUICK-START.md` for quick commands
- Start using migrations for schema changes
- Use export/import for sharing test cases

---

**You're all set!** Both developers can now work independently without database conflicts. 🎉
