# Next Steps - Sprint 4 Implementation

**Current Status:** 
- ✅ Infrastructure: Database collaboration solution complete (committed to `main`)
- ✅ Backend: Sprint 4 test versioning complete (committed to `feature/sprint-4-test-versioning`)
- 📋 Next: Frontend implementation and integration

---

## Immediate Actions

### 1. Commit Documentation Files (Optional)

You have 3 new documentation files that should be committed to help Developer B:

```powershell
# Switch to main branch to commit docs
git checkout main

# Add documentation files
git add DEVELOPER-B-SYNC-GUIDE.md GIT-COMMIT-SUCCESS.md WHY-DATABASE-NOT-IN-GIT.md

# Commit
git commit -m "docs: Add database collaboration guides

- Add Developer B sync guide for merging infrastructure
- Add Git commit success summary
- Add explanation of why database files aren't in Git

These guides help Developer B understand and use the new database collaboration workflow."

# Push to main
git push origin main

# Switch back to Sprint 4 branch
git checkout feature/sprint-4-test-versioning

# Merge the new docs into feature branch
git merge main
```

**Note:** The database file (`backend/aiwebtest.db`) will always show as "modified" - this is correct and intentional. It's ignored by Git.

---

## Sprint 4 Implementation Plan

### Phase 1: Frontend Components (Developer A - You)

**Location:** `frontend/src/components/`

#### Component 1: TestStepEditor.tsx (4-6 hours)
**Purpose:** Allow editing test steps with automatic version creation

```typescript
// Features to implement:
- Rich text editor for test steps
- Real-time auto-save
- Version creation on save
- "Discard changes" option
- Show "last saved" timestamp
- Show current version number
```

**API Integration:**
- PUT `/api/v1/tests/{id}/steps` - Update steps and create version

#### Component 2: VersionHistoryPanel.tsx (3-4 hours)
**Purpose:** Display version history in a side panel

```typescript
// Features to implement:
- List all versions (newest first)
- Show version number, date, author, change reason
- Highlight current version
- "View" button to see version details
- "Rollback" button to restore version
- "Compare" button to compare two versions
- Pagination (50 versions max initially)
```

**API Integration:**
- GET `/api/v1/tests/{id}/versions` - Get version history
- GET `/api/v1/tests/{id}/versions/{version_id}` - Get specific version

#### Component 3: VersionCompareDialog.tsx (2-3 hours)
**Purpose:** Side-by-side diff view of two versions

```typescript
// Features to implement:
- Split view (left: old version, right: new version)
- Highlighted differences (additions in green, deletions in red)
- Field-by-field comparison (steps, expected_result, test_data)
- Summary of changes
- "Close" button
```

**API Integration:**
- GET `/api/v1/tests/{id}/versions/compare/{v1}/{v2}` - Compare versions

#### Component 4: RollbackConfirmDialog.tsx (1-2 hours)
**Purpose:** Confirmation dialog before rollback

```typescript
// Features to implement:
- Show current version vs. rollback target
- Warn that this creates a NEW version (not destructive)
- Input field for "reason for rollback"
- "Confirm" and "Cancel" buttons
- Success/error notification
```

**API Integration:**
- POST `/api/v1/tests/{id}/versions/rollback` - Rollback to version

---

### Phase 2: Integration (Developer A - 2-3 hours)

#### Update TestDetailPage.tsx
```typescript
// Add version control UI:
1. Add "Version History" button/tab
2. Show current version number in header
3. Integrate TestStepEditor component
4. Integrate VersionHistoryPanel component
5. Wire up all API calls
```

#### Update TestListPage.tsx (Optional)
```typescript
// Show version info in test list:
- Display current version number badge
- Show "last modified" timestamp
- Add "View Versions" quick action
```

---

### Phase 3: Testing (Developer A - 2-3 hours)

#### Manual Testing Checklist

```
✅ Create test case
✅ Edit steps → verify new version created
✅ View version history → verify versions listed
✅ Click specific version → verify details shown
✅ Compare two versions → verify diff shown correctly
✅ Rollback to old version → verify new version created with old content
✅ Edit after rollback → verify continues versioning
✅ Test with multiple users → verify "created_by" tracking
```

#### Edge Cases to Test

```
✅ Rapid edits (multiple saves quickly)
✅ Large test cases (100+ steps)
✅ Empty version history (new test case)
✅ Version limit (keep 50 versions, cleanup old ones)
✅ Concurrent edits (two users editing same test)
```

---

### Phase 4: Developer B Integration (Parallel Work)

**While you work on frontend, Developer B can:**

#### Option A: Work on Different Sprint 4 Features
```
According to project plan, Sprint 4 includes:
- Test versioning (you're doing this)
- Advanced KB search (Developer B could do this)
- Test analytics dashboard (Developer B could do this)
```

#### Option B: Setup Database Collaboration
```powershell
# Developer B syncs infrastructure
git checkout main
git pull origin main

# Setup database
cd backend
python run_migrations.py
python db_seed_simple.py

# Now Developer B has same schema and test data as you!
```

#### Option C: Review and Test Your Work
```
- Pull your feature branch
- Test the version control endpoints via API
- Provide feedback on edge cases
- Test integration scenarios
```

---

## Detailed Step-by-Step: Frontend Development

### Step 1: Create TestStepEditor Component

```bash
# Create component file
cd frontend/src/components
# Create TestStepEditor.tsx
```

**Key Features:**
1. Textarea or rich text editor for steps
2. Auto-save (debounced, 2 seconds after typing stops)
3. Save button (manual save)
4. Show "Saving..." indicator
5. Show "Saved at [timestamp]" after save
6. Show current version number

**API Call:**
```typescript
const updateSteps = async (testId: number, steps: string) => {
  const response = await fetch(`/api/v1/tests/${testId}/steps`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      steps: steps,
      change_reason: 'User edit' // Optional
    })
  });
  return await response.json();
};
```

---

### Step 2: Create VersionHistoryPanel Component

```bash
# Create component file
# Create VersionHistoryPanel.tsx
```

**Key Features:**
1. Sidebar panel (drawer/modal)
2. List of versions with:
   - Version number (v1, v2, v3...)
   - Created date (formatted)
   - Created by (user name)
   - Change reason (if provided)
3. Actions per version:
   - "View" - Show version details
   - "Rollback" - Restore this version
   - "Compare" - Compare with another version

**API Call:**
```typescript
const getVersionHistory = async (testId: number) => {
  const response = await fetch(`/api/v1/tests/${testId}/versions`);
  return await response.json();
};
```

---

### Step 3: Wire Up Rollback

**Flow:**
1. User clicks "Rollback" on version
2. Show RollbackConfirmDialog
3. User confirms with reason
4. Call API to rollback
5. Refresh test details
6. Show success notification
7. Version number increments (e.g., v10 → v11 with content from v5)

**API Call:**
```typescript
const rollbackToVersion = async (testId: number, versionId: number, reason: string) => {
  const response = await fetch(`/api/v1/tests/${testId}/versions/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      version_id: versionId,
      change_reason: reason
    })
  });
  return await response.json();
};
```

---

### Step 4: Add Version Compare

**Flow:**
1. User selects two versions (checkboxes)
2. Clicks "Compare"
3. Shows VersionCompareDialog with diff
4. Highlighted changes:
   - Green for additions
   - Red for deletions
   - Yellow for modifications

**API Call:**
```typescript
const compareVersions = async (testId: number, v1: number, v2: number) => {
  const response = await fetch(
    `/api/v1/tests/${testId}/versions/compare/${v1}/${v2}`
  );
  return await response.json();
};
```

---

## Testing Your Implementation

### Backend Testing (Verify APIs Work)

```powershell
cd backend
.\venv\Scripts\activate

# Start backend
python -m uvicorn app.main:app --reload

# Open Swagger UI
# http://localhost:8000/docs

# Test each endpoint:
# 1. PUT /tests/{id}/steps - Update steps
# 2. GET /tests/{id}/versions - List versions
# 3. GET /tests/{id}/versions/{version_id} - Get version
# 4. POST /tests/{id}/versions/rollback - Rollback
# 5. GET /tests/{id}/versions/compare/{v1}/{v2} - Compare
```

### Frontend Testing

```bash
cd frontend
npm run dev

# Open http://localhost:3000
# Test version control features:
# - Create test case
# - Edit steps multiple times
# - View version history
# - Compare versions
# - Rollback to old version
```

---

## Timeline Estimate

### Developer A (You) - Frontend

| Task | Time | Status |
|------|------|--------|
| TestStepEditor component | 4-6 hours | ⏳ Pending |
| VersionHistoryPanel component | 3-4 hours | ⏳ Pending |
| VersionCompareDialog component | 2-3 hours | ⏳ Pending |
| RollbackConfirmDialog component | 1-2 hours | ⏳ Pending |
| Integration with TestDetailPage | 2-3 hours | ⏳ Pending |
| Testing and bug fixes | 2-3 hours | ⏳ Pending |
| **Total** | **14-21 hours** | **~2-3 days** |

### Developer B - Database Setup + Testing

| Task | Time | Status |
|------|------|--------|
| Sync database collaboration infrastructure | 30 min | ⏳ Pending |
| Run migrations and seed data | 15 min | ⏳ Pending |
| Test backend APIs (Swagger UI) | 1-2 hours | ⏳ Pending |
| Work on other Sprint 4 features (parallel) | Varies | ⏳ Pending |
| **Total Setup Time** | **1 hour** | |

---

## Coordination Points

### Daily Sync (15-30 minutes)

**Developer A & B should sync on:**
1. What you completed today
2. Any blockers or issues
3. What you're working on next
4. Any API changes needed
5. Testing coordination

### When to Merge Sprint 4 Feature Branch

**Merge to `main` when:**
- ✅ Backend complete (done!)
- ✅ Frontend complete
- ✅ Integration tested
- ✅ Both developers approve
- ✅ No breaking changes
- ✅ Documentation updated

**Steps to merge:**
```powershell
# Ensure feature branch is up to date
git checkout feature/sprint-4-test-versioning
git merge origin/main

# Run all tests
cd backend && pytest
cd frontend && npm test

# Create Pull Request on GitHub
# Get Developer B to review
# Merge to main after approval
```

---

## What Developer B Should Do Now

### Option 1: Setup Database Collaboration (Recommended First)

```powershell
# 1. Sync main branch
git checkout main
git pull origin main

# 2. Setup database
cd backend
python run_migrations.py      # Creates tables
python db_seed_simple.py      # Seeds test data

# 3. Verify backend works
python -m uvicorn app.main:app --reload
# Test at http://localhost:8000/docs
# Login: admin / admin123

# 4. You now have same database as Developer A!
```

**Benefit:** Developer B can now:
- Test your version control endpoints
- Create their own test cases
- Share test cases via export/import
- No database conflicts!

---

### Option 2: Pull Sprint 4 Feature Branch (Test Backend)

```powershell
# Pull Sprint 4 branch
git checkout feature/sprint-4-test-versioning
git pull origin feature/sprint-4-test-versioning

# Test version control endpoints via Swagger
python -m uvicorn app.main:app --reload
# Open http://localhost:8000/docs

# Test endpoints:
# 1. Create a test case
# 2. Update steps (PUT /tests/{id}/steps)
# 3. View versions (GET /tests/{id}/versions)
# 4. Compare versions
# 5. Rollback
```

---

### Option 3: Work on Other Sprint 4 Features (Parallel)

**According to project plan, Sprint 4 includes:**
- ✅ Test versioning (you're doing frontend)
- ⏳ KB integration with test generation (Developer B could do this)
- ⏳ Advanced search (Developer B could do this)
- ⏳ Test analytics dashboard (Developer B could do this)

Developer B can start a new feature branch:
```powershell
git checkout main
git checkout -b feature/sprint-4-kb-integration
# Start working on KB integration
```

---

## Troubleshooting

### Issue: "Cannot run migrations"

```powershell
# Check if you're in backend folder
cd backend

# Check if virtual environment is activated
.\venv\Scripts\activate

# Run migrations
python run_migrations.py
```

---

### Issue: "Database file keeps showing as modified"

**This is normal!** The database file is in `.gitignore` so it's never committed.

```powershell
git status
# Shows: modified: backend/aiwebtest.db

# This is CORRECT - it's ignored and won't be committed
```

---

### Issue: "How do I share my test cases with Developer B?"

```powershell
# Export your test cases
cd backend
python db_seed.py --export

# Commit the seed file
git add seed_test_cases.json
git commit -m "Export test cases"
git push

# Developer B imports them
git pull
python db_seed.py --import
```

---

## Success Criteria

### Sprint 4 Test Versioning Complete When:

- ✅ Backend API endpoints working (DONE!)
- ✅ Frontend components implemented
- ✅ Integration complete (edit, view history, rollback, compare)
- ✅ Tested by both developers
- ✅ No critical bugs
- ✅ Documentation updated
- ✅ Pull request approved
- ✅ Merged to main

---

## Quick Reference

### Your Current State

```
✅ Main branch: Database collaboration infrastructure
✅ Feature branch: Sprint 4 test versioning backend
⏳ Next: Sprint 4 frontend implementation
📍 You are on: feature/sprint-4-test-versioning
```

### Commands You'll Use

```powershell
# Check what branch you're on
git branch

# Switch to main
git checkout main

# Switch to feature branch
git checkout feature/sprint-4-test-versioning

# Start frontend development
cd frontend
npm run dev

# Start backend (in separate terminal)
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload

# Test APIs
# Open http://localhost:8000/docs
```

---

## Ready to Start?

### Recommended Order:

1. ✅ **Commit documentation files** (optional, 5 minutes)
2. ✅ **Start frontend development** (14-21 hours over 2-3 days)
   - TestStepEditor.tsx
   - VersionHistoryPanel.tsx
   - VersionCompareDialog.tsx
   - RollbackConfirmDialog.tsx
   - Integration
3. ✅ **Test thoroughly** (2-3 hours)
4. ✅ **Coordinate with Developer B for review**
5. ✅ **Merge to main after approval**

---

**Ready to start Sprint 4 frontend implementation?** 🚀

Let me know if you need help with any specific component or have questions!
