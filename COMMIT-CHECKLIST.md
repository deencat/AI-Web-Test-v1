# Files to Commit - Test Suite Merged Execution Feature

## Core Feature Files (Must Commit)

### Backend - Suite Execution (NEW)
✅ **backend/app/services/suite_execution_service.py**
   - New file with execute_test_suite_merged() function
   - Merges test steps at runtime
   - Creates temporary merged test
   - ~500 lines

✅ **backend/app/api/v1/endpoints/test_suites.py**
   - New endpoint file for test suites
   - POST /api/v1/suites/{id}/run
   - ~200 lines

✅ **backend/app/crud/crud_test_suite.py**
   - New CRUD operations for suites
   - ~300 lines

✅ **backend/app/models/test_suite.py**
   - New models: TestSuite, TestSuiteItem, SuiteExecution
   - ~150 lines

✅ **backend/app/schemas/test_suite.py**
   - New Pydantic schemas for suites
   - ~150 lines

### Backend - Bug Fix (CRITICAL)
✅ **backend/app/services/stagehand_service.py**
   - Fixed JSON step parsing (line 173)
   - Added import json
   - Critical for merged execution

### Backend - Integration
✅ **backend/app/api/v1/api.py**
   - Added test_suites router
   - ~5 lines

✅ **backend/app/models/__init__.py**
   - Imported test suite models
   - ~3 lines

### Frontend - Suite Management (NEW)
✅ **frontend/src/pages/TestSuitesPage.tsx**
   - New page for managing suites
   - ~400 lines

✅ **frontend/src/components/CreateSuiteModal.tsx**
   - New modal for creating suites
   - ~300 lines

✅ **frontend/src/services/testSuitesService.ts**
   - New API service for suites
   - ~100 lines

### Frontend - Integration
✅ **frontend/src/App.tsx**
   - Added /test-suites route
   - ~5 lines

✅ **frontend/src/components/layout/Sidebar.tsx**
   - Added "Test Suites" navigation link
   - ~3 lines

### Documentation (MUST COMMIT)
✅ **TEST-SUITE-MERGED-EXECUTION-COMPLETE.md**
   - Comprehensive feature documentation
   - Problem, solution, code changes
   - ~300 lines

✅ **GIT-COMMIT-MESSAGE-SUITE-MERGE.md**
   - Detailed commit message with all context
   - ~200 lines

✅ **SPRINT-3-TEST-SUITE-MERGE-UPDATE.md**
   - Project management update
   - Feature status, known limitations
   - ~400 lines

✅ **SUITE-VS-SINGLE-TEST-SOLUTION.md**
   - Solution explanation
   - Why merged approach works

✅ **SHARED-BROWSER-SESSION-LIMITATION.md**
   - Windows limitation documentation
   - Why original approach failed

✅ **TEST-SUITE-MERGED-EXECUTION.md**
   - Technical implementation guide

---

## Support Files (Existing, Modified)

### Previously Modified (Sprint 1-2)
⚠️ **backend/app/services/execution_service.py**
   - Previous changes (not part of this feature)

⚠️ **backend/app/services/test_generation.py**
   - Previous changes (not part of this feature)

⚠️ **frontend/src/pages/TestsPage.tsx**
   - Previous changes (not part of this feature)

⚠️ **frontend/src/components/RunTestButton.tsx**
   - Previous changes (not part of this feature)

⚠️ **frontend/src/services/executionService.ts**
   - Previous changes (not part of this feature)

⚠️ **frontend/src/services/testsService.ts**
   - Previous changes (not part of this feature)

⚠️ **frontend/src/types/api.ts**
   - Previous changes (not part of this feature)

### Documentation (Support)
📄 **TEST-SUITES-FEATURE-DESIGN.md**
   - Original feature design

📄 **TEST-SUITES-IMPLEMENTATION-STATUS.md**
   - Implementation progress tracking

📄 **SUITE-DEBUGGING-GUIDE.md**
   - Debugging guide for suites

📄 **TEST-SUITE-BROWSER-FLOW-VISUAL.md**
   - Flow diagrams

📄 **Other support docs...**
   - Various troubleshooting and guide documents

---

## Files NOT to Commit (Temporary/Test)

❌ **backend/clean_test_docs.py** - Empty test file
❌ **backend/clear_kb_docs.py** - Empty test file  
❌ **backend/test_api.py** - Empty test file
❌ **backend/test_ai_generation_to_execution.py** - Test script
❌ **backend/test_complete_ui_flow.py** - Test script
❌ **backend/test_generation_debug.py** - Debug script
❌ **backend/test_tests_page_integration.py** - Test script

---

## Recommended Commit Strategy

### Option 1: Single Comprehensive Commit (RECOMMENDED)
**Commit all files for this feature together**

**Pros:**
- Complete feature in one commit
- Easy to track and review
- Clear history

**Files to commit:**
```
# Core backend
backend/app/services/suite_execution_service.py
backend/app/api/v1/endpoints/test_suites.py
backend/app/crud/crud_test_suite.py
backend/app/models/test_suite.py
backend/app/schemas/test_suite.py
backend/app/services/stagehand_service.py (bug fix)
backend/app/api/v1/api.py (integration)
backend/app/models/__init__.py (integration)

# Core frontend
frontend/src/pages/TestSuitesPage.tsx
frontend/src/components/CreateSuiteModal.tsx
frontend/src/services/testSuitesService.ts
frontend/src/App.tsx (routing)
frontend/src/components/layout/Sidebar.tsx (nav)

# Documentation
TEST-SUITE-MERGED-EXECUTION-COMPLETE.md
GIT-COMMIT-MESSAGE-SUITE-MERGE.md
SPRINT-3-TEST-SUITE-MERGE-UPDATE.md
SUITE-VS-SINGLE-TEST-SOLUTION.md
SHARED-BROWSER-SESSION-LIMITATION.md
TEST-SUITE-MERGED-EXECUTION.md
TEST-SUITE-BROWSER-FLOW-VISUAL.md
TEST-SUITES-FEATURE-DESIGN.md
TEST-SUITES-IMPLEMENTATION-STATUS.md
```

### Option 2: Separate Commits by Layer
**1. Backend commit**
- All backend files

**2. Frontend commit**
- All frontend files

**3. Documentation commit**
- All documentation files

---

## Git Commands

### Single Commit (RECOMMENDED):
```powershell
cd c:\Users\andrechw\Documents\AI-Web-Test-v1-1

# Stage core backend files
git add backend/app/services/suite_execution_service.py
git add backend/app/api/v1/endpoints/test_suites.py
git add backend/app/crud/crud_test_suite.py
git add backend/app/models/test_suite.py
git add backend/app/schemas/test_suite.py
git add backend/app/services/stagehand_service.py
git add backend/app/api/v1/api.py
git add backend/app/models/__init__.py

# Stage core frontend files
git add frontend/src/pages/TestSuitesPage.tsx
git add frontend/src/components/CreateSuiteModal.tsx
git add frontend/src/services/testSuitesService.ts
git add frontend/src/App.tsx
git add frontend/src/components/layout/Sidebar.tsx

# Stage documentation
git add TEST-SUITE-MERGED-EXECUTION-COMPLETE.md
git add GIT-COMMIT-MESSAGE-SUITE-MERGE.md
git add SPRINT-3-TEST-SUITE-MERGE-UPDATE.md
git add SUITE-VS-SINGLE-TEST-SOLUTION.md
git add SHARED-BROWSER-SESSION-LIMITATION.md
git add TEST-SUITE-MERGED-EXECUTION.md
git add TEST-SUITE-BROWSER-FLOW-VISUAL.md
git add TEST-SUITES-FEATURE-DESIGN.md
git add TEST-SUITES-IMPLEMENTATION-STATUS.md

# Commit with message from GIT-COMMIT-MESSAGE-SUITE-MERGE.md
git commit -F GIT-COMMIT-MESSAGE-SUITE-MERGE.md

# Push to branch
git push origin integration/sprint-3
```

### Separate Commits:
```powershell
# Commit 1: Backend
git add backend/app/services/suite_execution_service.py backend/app/api/v1/endpoints/test_suites.py backend/app/crud/crud_test_suite.py backend/app/models/test_suite.py backend/app/schemas/test_suite.py backend/app/services/stagehand_service.py backend/app/api/v1/api.py backend/app/models/__init__.py
git commit -m "feat(backend): Add test suite merged execution service and API endpoints"

# Commit 2: Frontend
git add frontend/src/pages/TestSuitesPage.tsx frontend/src/components/CreateSuiteModal.tsx frontend/src/services/testSuitesService.ts frontend/src/App.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat(frontend): Add test suites page and suite management UI"

# Commit 3: Documentation
git add TEST-SUITE-MERGED-EXECUTION-COMPLETE.md GIT-COMMIT-MESSAGE-SUITE-MERGE.md SPRINT-3-TEST-SUITE-MERGE-UPDATE.md SUITE-VS-SINGLE-TEST-SOLUTION.md SHARED-BROWSER-SESSION-LIMITATION.md TEST-SUITE-MERGED-EXECUTION.md
git commit -m "docs: Add comprehensive test suite merged execution documentation"

# Push all
git push origin integration/sprint-3
```

---

## Verification Checklist

Before committing:
- [ ] All new files have proper imports
- [ ] No syntax errors in modified files
- [ ] Documentation is complete and accurate
- [ ] Commit message is clear and descriptive
- [ ] No sensitive data (passwords, keys) in files
- [ ] Test files excluded from commit
- [ ] .gitignore updated if needed

After committing:
- [ ] git log shows correct commit message
- [ ] git status shows clean working tree
- [ ] git push successful
- [ ] Branch updated on remote

---

## Next Steps After Commit

1. ✅ Update README.md (add test suites section)
2. ✅ Update API-CHANGELOG.md (document API changes)
3. 📋 Create Sprint 4 backlog items
4. 🧪 Test with larger suites (5-10 tests)
5. 🎯 Plan step attribution implementation
6. 🧹 Plan cleanup job for merged tests

---

**Ready to commit!** 🚀
