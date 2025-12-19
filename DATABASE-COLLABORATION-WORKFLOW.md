# Database Collaboration Workflow

## Problem We're Solving

When two developers work on the same project with SQLite databases, we need to:
1. ✅ Share the database **schema** (structure)
2. ✅ Share **seed data** (common test cases both developers need)
3. ❌ **NOT share** individual database files (binary files cause Git conflicts)
4. ✅ Allow each developer to have **local-only test data** for their work

## Solution: Migrations + Seed Scripts (Best Practice)

### What Gets Shared via Git ✅

```
backend/
  ├── migrations/              # ✅ Shared (schema changes)
  │   ├── add_test_versions_table.py
  │   ├── add_execution_feedback_table.py
  │   └── ...
  ├── db_seed.py              # ✅ Shared (common seed data)
  ├── seed_test_cases.json    # ✅ Shared (exportable test cases)
  └── aiwebtest.db            # ❌ NOT shared (in .gitignore)
```

### What's Local Only ❌

```
backend/
  └── aiwebtest.db            # ❌ Local database file (each dev has their own)
```

---

## Developer Workflow

### Initial Setup (Both Developers)

**Step 1: Clone Repository**
```powershell
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1-1/backend
```

**Step 2: Run All Migrations (Creates Tables)**
```powershell
# Run each migration in order
python migrations/create_initial_schema.py
python migrations/add_test_versions_table.py
python migrations/add_execution_feedback_table.py
# ... run all migrations
```

**Step 3: Seed Database (Loads Common Data)**
```powershell
# Load default users, test cases, KB documents
python db_seed.py
```

**Result:** Both developers now have:
- ✅ Identical database schema
- ✅ Same base test cases (Google Search, GitHub Login, etc.)
- ✅ Same users (admin, qa_user)
- ✅ Same KB documents (best practices, patterns, lessons)

---

### Daily Workflow

#### Developer A Creates New Feature

**1. Write Code + Migration (if schema changes)**
```python
# backend/migrations/add_my_new_feature_table.py
def upgrade():
    # Create new table or add columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_feature (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
```

**2. Commit Migration Script (NOT database file)**
```powershell
git add migrations/add_my_new_feature_table.py
git commit -m "Add migration for new feature"
git push origin feature/my-feature
```

**3. Create Test Cases Locally**
```python
# Developer A creates test cases in their local database
# These are NOT committed yet
```

**4. Export Seed Data When Test Cases Are Stable**
```powershell
# Export current test cases to shareable JSON file
python db_seed.py --export
# This creates/updates seed_test_cases.json

git add seed_test_cases.json
git commit -m "Add seed data for my feature test cases"
git push origin feature/my-feature
```

---

#### Developer B Syncs With Developer A's Changes

**1. Pull Latest Code**
```powershell
git pull origin main
```

**2. Run New Migrations**
```powershell
# Run Developer A's new migration
python migrations/add_my_new_feature_table.py
```

**3. Import Shared Seed Data**
```powershell
# Import Developer A's test cases
python db_seed.py --import
```

**Result:** Developer B now has:
- ✅ Same schema as Developer A
- ✅ Same test cases as Developer A
- ✅ Can test integration between features

---

## Collaboration Scenarios

### Scenario 1: Developer A Creates New Test Cases

**Developer A:**
```powershell
# 1. Create test cases via UI or API
# 2. Export to seed file when stable
python db_seed.py --export

# 3. Commit seed file
git add seed_test_cases.json
git commit -m "Add login flow test cases"
git push
```

**Developer B:**
```powershell
# 1. Pull latest changes
git pull

# 2. Import shared test cases
python db_seed.py --import

# 3. Now has same test cases as Developer A
```

---

### Scenario 2: Developer B Adds Database Column

**Developer B:**
```powershell
# 1. Create migration script
# backend/migrations/add_priority_to_tests.py
def upgrade():
    cursor.execute("ALTER TABLE test_cases ADD COLUMN priority INTEGER DEFAULT 5")

# 2. Commit migration (NOT database)
git add migrations/add_priority_to_tests.py
git commit -m "Add priority column to test_cases"
git push
```

**Developer A:**
```powershell
# 1. Pull latest code
git pull

# 2. Run migration on local database
python migrations/add_priority_to_tests.py

# 3. Database now has new column
```

---

### Scenario 3: Both Developers Need Same Initial Data

**Setup (Once):**
```powershell
# Both developers run the same seed script after initial setup
python db_seed.py

# This creates:
# - 2 users (admin, qa_user)
# - 3 sample test cases
# - 3 KB documents
# - 2 test suites
```

**Result:**
- ✅ Both have identical starting data
- ✅ Can test features together
- ✅ No manual data entry needed

---

### Scenario 4: Reset Database to Clean State

**When Needed:**
- Database corrupted
- Want to start fresh
- Testing migration scripts

**Command:**
```powershell
python db_seed.py --reset
# ⚠️  WARNING: This DELETES all data!
```

**Steps:**
1. Confirms with user (type "yes")
2. Drops all tables
3. Runs all migrations (recreates schema)
4. Seeds default data

---

## Commands Reference

### Seed Commands

```powershell
# Default: Seed all data (users, tests, KB, suites)
python db_seed.py

# Reset database (drop all + reseed)
python db_seed.py --reset

# Export current test cases to seed file
python db_seed.py --export

# Import test cases from seed file
python db_seed.py --import
```

### Migration Commands

```powershell
# Run specific migration
python migrations/my_migration.py

# Run all migrations (in order)
# (We'll create a script for this)
python run_migrations.py
```

---

## What's in .gitignore

```gitignore
# SQLite databases (each developer has their own local database)
*.db
*.sqlite
*.sqlite3
backend/*.db
backend/*.sqlite
backend/*.sqlite3

# BUT we DO commit these:
# ✅ migrations/*.py          (schema changes)
# ✅ db_seed.py               (seed script)
# ✅ seed_test_cases.json     (shared test data)
```

---

## Benefits of This Approach

### ✅ Advantages

1. **No Git Conflicts** - Binary database files never in Git
2. **Schema Sync** - Migrations keep structure identical
3. **Data Sharing** - Seed scripts share common test cases
4. **Local Freedom** - Each dev can add local-only test data
5. **Reset Anytime** - Easy to start fresh with `--reset`
6. **Portable** - Works on Windows, Mac, Linux
7. **Standard Practice** - This is how professional teams work

### ❌ What We Avoid

1. ~~Binary merge conflicts~~ - Never happens (db not in Git)
2. ~~Data overwrite~~ - Each dev has separate database
3. ~~Manual data entry~~ - Seed script automates it
4. ~~Schema drift~~ - Migrations keep everyone in sync
5. ~~Lost work~~ - Export/import preserves test cases

---

## Migration to Production

When deploying to production:

```powershell
# 1. Run all migrations on production database
python run_migrations.py

# 2. Optionally seed initial data (admin user, etc.)
python db_seed.py

# 3. Production database is now ready
```

**Note:** Production uses PostgreSQL, not SQLite. Same migrations work for both!

---

## FAQ

### Q: What if I want to share a specific test case?

**A:** Export it to seed file:
```powershell
python db_seed.py --export
git add seed_test_cases.json
git commit -m "Add new test case for feature X"
git push
```

Other developer imports it:
```powershell
git pull
python db_seed.py --import
```

---

### Q: What if my database gets corrupted?

**A:** Reset to clean state:
```powershell
python db_seed.py --reset
```

This drops everything and recreates with seed data.

---

### Q: Can I have local-only test data?

**A:** Yes! Just don't export it. Your local database can have:
- ✅ Shared test cases (from seed file)
- ✅ Your own local test cases (not exported)
- ✅ Your own execution history
- ✅ Your own debug data

Only export test cases when you want to share them.

---

### Q: What about execution history and feedback?

**A:** Those are local only:
- ❌ **NOT shared** - Each developer has their own execution history
- ❌ **NOT shared** - Each developer has their own feedback records
- ✅ **Shared** - Test cases, users, KB documents (via seed file)

This makes sense because execution history is environment-specific.

---

### Q: How do I know which migrations to run?

**A:** We'll create a migration tracker:
```powershell
# Run all pending migrations
python run_migrations.py

# It tracks which migrations are already applied
```

(Coming in next file...)

---

## Summary

**What This Solves:**
- ✅ Both developers have identical schema
- ✅ Both developers have same base test cases
- ✅ No Git conflicts from binary files
- ✅ Easy to share new test cases
- ✅ Easy to reset and start fresh

**Developer Workflow:**
1. Clone repo
2. Run migrations (schema)
3. Run seed script (data)
4. Work locally
5. Export test cases when ready to share
6. Commit seed file (NOT database)
7. Other dev imports your test cases

**This is industry standard practice** and solves your collaboration problem! 🎉
