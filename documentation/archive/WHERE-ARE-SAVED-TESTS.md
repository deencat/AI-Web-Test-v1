# Where Are Saved Tests and How to Find Them

## 📍 Storage Location

### Database:
```
backend/aiwebtest.db
Table: test_cases
```

All tests are permanently stored in the SQLite database in the `test_cases` table.

---

## 🔍 How to View Saved Tests

### Option 1: In the Tests Page UI (Recommended)

1. **Navigate to Tests Page**:
   ```
   http://localhost:5173/tests
   ```

2. **After Saving Tests**:
   - Click "Save All Tests" or "Save to Tests"
   - The page automatically switches to "Saved Tests" view
   - You'll see all your saved tests listed

3. **If You See Generated Tests Instead**:
   - Scroll down past the generated tests
   - OR click "Generate New Tests" button (will show saved tests after)
   - OR refresh the page

### Visual Flow:
```
┌─────────────────────────────────────────────────────┐
│ Test Cases                          [Generate New]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Filters: [All] [Passed] [Failed] [Pending]         │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 🟢 Three.com.hk 5G Broadband Flow    #1     │   │
│ │    High Priority | e2e                      │   │
│ │    Test subscription flow...                │   │
│ │                    [Run Test] [View Details]│   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 🟡 Login Flow Test                   #2     │   │
│ │    Medium Priority | e2e                    │   │
│ │    Test login functionality...              │   │
│ │                    [Run Test] [View Details]│   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Test Information Displayed

For each saved test, you'll see:

| Field | Description | Example |
|-------|-------------|---------|
| **Status Indicator** | Color dot showing test status | 🟢 Passed, 🔴 Failed, 🟡 Pending |
| **Title** | Test name | "Three.com.hk 5G Broadband Flow" |
| **ID** | Database ID | #1, #2, #3... |
| **Priority** | High/Medium/Low | High |
| **Description** | What the test does | "Test subscription flow..." |
| **Status Text** | Current status | passed/failed/pending |
| **Actions** | What you can do | Run Test, View Details |

---

## 🔄 Test States

### After "Save All Tests":
```
1. Generated tests cleared from view ✅
2. Tests saved to database ✅
3. Page switches to "Saved Tests" view ✅
4. Tests appear with status "pending" ✅
5. Can click "Run Test" to execute ✅
```

### If Page Shows "No tests found":
This means:
- Database is empty, OR
- Backend not running, OR
- API call failed

**Solution**:
1. Check backend is running: `http://localhost:8000`
2. Refresh the page
3. Check browser console for errors

---

## 📊 Filtering Saved Tests

Use filter buttons to view specific tests:

### Filters Available:
- **All**: Shows all tests (default)
- **Passed**: Only tests that passed ✅
- **Failed**: Only tests that failed ❌
- **Pending**: Tests not yet run 🟡

### Example:
```
You have 10 tests total:
- 3 Passed
- 2 Failed
- 5 Pending

Click "Passed" → See only 3 tests
Click "Failed" → See only 2 tests
Click "Pending" → See only 5 tests
Click "All" → See all 10 tests
```

---

## 🗄️ Database Query (Advanced)

If you want to check the database directly:

### Using SQLite CLI:
```bash
cd backend

# Open database
sqlite3 aiwebtest.db

# View all tests
SELECT id, title, status, priority FROM test_cases;

# View specific test
SELECT * FROM test_cases WHERE id = 1;

# Count tests
SELECT COUNT(*) FROM test_cases;

# Exit
.exit
```

### Using Python:
```python
import sqlite3

# Connect to database
conn = sqlite3.connect('backend/aiwebtest.db')
cursor = conn.cursor()

# Get all tests
cursor.execute("SELECT id, title, status FROM test_cases")
tests = cursor.fetchall()

for test in tests:
    print(f"ID: {test[0]}, Title: {test[1]}, Status: {test[2]}")

conn.close()
```

---

## 🔧 API Endpoint

### Get All Tests:
```bash
GET http://localhost:8000/api/v1/tests
```

### Example Response:
```json
[
  {
    "id": 1,
    "title": "Three.com.hk 5G Broadband Flow",
    "description": "Test subscription flow",
    "status": "pending",
    "priority": "high",
    "test_type": "e2e",
    "steps": ["Step 1", "Step 2", ...],
    "expected_result": "Success",
    "created_at": "2025-12-04T10:30:00",
    "updated_at": "2025-12-04T10:30:00"
  },
  ...
]
```

---

## 🚀 Common Workflows

### Workflow 1: Generate → Save → View → Run
```
1. Navigate to Tests Page
2. Enter test requirement
3. Click "Generate Test Cases"
4. Review generated tests
5. Click "Save All Tests"
   ↓
   Page shows saved tests ✅
6. Click "Run Test" on any test
7. Navigate to Executions to see results
```

### Workflow 2: View Existing Tests
```
1. Navigate to Tests Page
2. Already shows saved tests (if you have any)
3. Use filters to find specific tests
4. Click "View Details" to see test steps
5. Click "Run Test" to execute
```

### Workflow 3: Generate More Tests
```
1. In Saved Tests view
2. Click "Generate New Tests" button
3. Enter new requirement
4. Generate and save
5. Back to Saved Tests view (now with more tests)
```

---

## 📝 What Happens After Saving

### Immediate Effects:
1. ✅ Test saved to database (`test_cases` table)
2. ✅ Test gets unique ID
3. ✅ Status set to "pending"
4. ✅ Timestamps recorded (created_at, updated_at)
5. ✅ Test appears in "Saved Tests" view
6. ✅ Can be run immediately

### Test Data Saved:
- Title
- Description
- Test Type (e2e, unit, api, integration)
- Priority (high, medium, low)
- Steps (array of step descriptions)
- Expected Result
- Preconditions
- Test Data (if any)
- Metadata (if any)

---

## 🎯 Quick Reference

| What You Want | Where to Find It |
|---------------|------------------|
| **View all saved tests** | Tests Page → Shows automatically |
| **Filter by status** | Tests Page → Filter buttons (All/Passed/Failed/Pending) |
| **Run a test** | Tests Page → "Run Test" button |
| **See test details** | Tests Page → "View Details" button |
| **Generate more tests** | Tests Page → "Generate New Tests" button |
| **Check database** | `backend/aiwebtest.db` → `test_cases` table |
| **API access** | `GET http://localhost:8000/api/v1/tests` |

---

## 🐛 Troubleshooting

### Problem: Can't see saved tests
**Solutions**:
1. ✅ Refresh the page (Ctrl+R)
2. ✅ Check backend is running
3. ✅ Check browser console for errors
4. ✅ Verify tests saved: Check database or API endpoint

### Problem: Tests show but status is wrong
**Solution**:
- Status updates after test runs
- "pending" = not yet executed
- Run the test to update status

### Problem: Want to delete a test
**Solution**:
- Currently no delete button in UI
- Can delete via API: `DELETE /api/v1/tests/{id}`
- Or directly in database

### Problem: Generated tests disappeared
**Solution**:
- Did you save them? (Click "Save All Tests")
- If not saved, they're lost
- Generate again and save this time

---

## 💡 Pro Tips

1. **Always Save Tests**:
   - Generated tests are temporary
   - Must click "Save to Tests" or "Save All Tests"
   - Saved tests are permanent

2. **Use Filters Effectively**:
   - "Pending" to find tests not yet run
   - "Failed" to find tests that need fixing
   - "Passed" to see what's working

3. **Check After Saving**:
   - Always verify tests appear in saved list
   - Check the count matches what you saved

4. **Run Tests Immediately**:
   - Click "Run Test" to verify they work
   - Check Executions page for results

5. **Organize Tests**:
   - Use clear titles
   - Set proper priorities
   - Add good descriptions

---

## 📚 Related Documentation

- `TESTS-PAGE-SAVE-GUIDE.md` - Complete save guide
- `TESTS-PAGE-UI-TESTING-GUIDE.md` - UI testing guide
- `HOW-TO-GENERATE-THREE-HK-TEST.md` - Example test
- `FIX-422-FIELD-NAME-MISMATCH.md` - Troubleshooting saves

---

## ✨ Summary

**Where tests are saved**: `backend/aiwebtest.db` (database)

**How to see them**: 
1. Go to Tests Page (`http://localhost:5173/tests`)
2. Tests automatically displayed in "Saved Tests" view
3. Use filters to find specific tests

**What you can do**:
- ✅ View all tests
- ✅ Filter by status
- ✅ Run tests
- ✅ View details
- ✅ Generate more tests

The Tests Page is your central hub for managing all saved tests! 🎉
