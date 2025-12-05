# Test Suites Feature - Group and Run Multiple Tests

## 🎯 **What Are Test Suites?**

**Test Suites** (also called **Test Sets** or **Test Collections**) allow you to:
- ✅ Group multiple test cases together
- ✅ Run them as a single batch
- ✅ Define execution order
- ✅ Reuse test cases across multiple suites
- ✅ Track suite-level results

---

## 📋 **Use Cases**

### **Use Case 1: Sequential Flow Tests**
Group tests that must run in order:
- **Suite**: "Three.com.hk Complete Flow"
- **Tests**: #62 → #63 → #64 → #65 → #66
- **Why**: Each test builds on the previous step

### **Use Case 2: Smoke Tests**
Critical tests to verify basic functionality:
- **Suite**: "Smoke Tests"
- **Tests**: #60, #62, #64, #65, #66 (non-sequential)
- **Why**: Quick health check after deployment

### **Use Case 3: Regression Tests**
All tests for a feature:
- **Suite**: "5G Broadband Regression"
- **Tests**: #50-#70 (all broadband-related tests)
- **Why**: Ensure no bugs were reintroduced

### **Use Case 4: Cross-Feature Tests**
Tests from different features:
- **Suite**: "Critical User Journeys"
- **Tests**: Login (#10), Search (#25), Checkout (#62), Payment (#80)
- **Why**: End-to-end business flows

---

## 🏗️ **Database Structure**

### **Tables Created:**

```sql
-- Test Suites Table
CREATE TABLE test_suites (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSON,  -- ["smoke", "regression", "critical"]
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test Suite Items (Links tests to suites with order)
CREATE TABLE test_suite_items (
    id INTEGER PRIMARY KEY,
    suite_id INTEGER NOT NULL,
    test_case_id INTEGER NOT NULL,
    execution_order INTEGER NOT NULL,  -- 1, 2, 3, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE,
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
);

-- Suite Executions (Tracks suite runs)
CREATE TABLE suite_executions (
    id INTEGER PRIMARY KEY,
    suite_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    browser VARCHAR(50),
    environment VARCHAR(50),
    triggered_by VARCHAR(50),
    stop_on_failure INTEGER DEFAULT 0,  -- 0=False, 1=True
    total_tests INTEGER NOT NULL,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
);
```

---

## 🎨 **Frontend UI Design**

### **New "Test Suites" Page**

```
┌─────────────────────────────────────────────────────────────────┐
│ Test Suites                                       [+ New Suite] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 📦 Three.com.hk Complete Flow               [Run] [Edit]    ││
│ │ 5 tests • Created Dec 5, 2025                               ││
│ │ Tags: e2e, critical, three-hk                               ││
│ │                                                              ││
│ │ Tests in this suite:                                         ││
│ │  1. ✅ Navigate to 5G plan page (#62)                       ││
│ │  2. ✅ Select 30 months contract (#63)                      ││
│ │  3. ✅ Verify pricing (#64)                                 ││
│ │  4. ✅ Complete checkout (#65)                              ││
│ │  5. ✅ Login and confirm (#66)                              ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 🔥 Smoke Tests                                  [Run] [Edit] ││
│ │ 4 tests • Created Dec 4, 2025                               ││
│ │ Tags: smoke, quick, critical                                ││
│ │                                                              ││
│ │ Tests in this suite:                                         ││
│ │  1. ✅ Homepage loads (#60)                                 ││
│ │  2. ✅ Search works (#62)                                   ││
│ │  3. ✅ Login works (#64)                                    ││
│ │  4. ✅ Checkout works (#66)                                 ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### **Create Suite Modal**

```
┌─────────────────────────────────────────────────────────────────┐
│ Create Test Suite                                         [×]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Suite Name: *                                                   │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Three.com.hk Complete Flow                                │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Description:                                                    │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Full subscription flow from plan selection to confirmation│ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Tags: (comma-separated)                                         │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ e2e, critical, three-hk                                   │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Select Test Cases: *                                            │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Search tests...                                         🔍│ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Available Tests:                  Selected Tests (drag to order):│
│ ┌─────────────────────┐          ┌─────────────────────────┐ │
│ │ ☐ #60 Homepage      │          │ 1. #62 Navigate to plan │ │
│ │ ☐ #61 Search        │          │ 2. #63 Select contract  │ │
│ │ ☑ #62 Navigate      │          │ 3. #64 Verify pricing   │ │
│ │ ☑ #63 Select plan   │          │ 4. #65 Complete checkout│ │
│ │ ☑ #64 Verify price  │          │ 5. #66 Login & confirm  │ │
│ │ ☑ #65 Checkout      │          │                         │ │
│ │ ☑ #66 Login         │          │ [↑] [↓] [×] (reorder)   │ │
│ │ ☐ #67 Confirm       │          │                         │ │
│ └─────────────────────┘          └─────────────────────────┘ │
│                                                                 │
│                              [Cancel]  [Create Suite]          │
└─────────────────────────────────────────────────────────────────┘
```

### **Run Suite Modal**

```
┌─────────────────────────────────────────────────────────────────┐
│ Run Suite: Three.com.hk Complete Flow                     [×]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Browser: *                                                      │
│ ○ Chromium  ○ Firefox  ○ Webkit                               │
│                                                                 │
│ Environment: *                                                  │
│ ○ Development  ○ Staging  ○ Production                        │
│                                                                 │
│ Options:                                                        │
│ ☐ Stop execution if a test fails                              │
│ ☐ Run tests in parallel (coming soon)                         │
│                                                                 │
│ Tests to run (5 tests):                                         │
│  1. Navigate to 5G plan page (#62)                             │
│  2. Select 30 months contract (#63)                            │
│  3. Verify pricing (#64)                                       │
│  4. Complete checkout (#65)                                    │
│  5. Login and confirm (#66)                                    │
│                                                                 │
│ Estimated time: ~15 minutes                                     │
│                                                                 │
│                              [Cancel]  [Run Suite]             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 **API Endpoints**

### **Test Suite CRUD**

```http
# Create a test suite
POST /api/v1/suites
{
  "name": "Three.com.hk Complete Flow",
  "description": "Full subscription flow",
  "tags": ["e2e", "critical", "three-hk"],
  "test_case_ids": [62, 63, 64, 65, 66]  // In execution order
}

# List all suites
GET /api/v1/suites?tags=smoke&page=1&per_page=10

# Get suite details
GET /api/v1/suites/1

# Update suite
PUT /api/v1/suites/1
{
  "test_case_ids": [62, 63, 64, 65, 66, 67]  // Added test #67
}

# Delete suite
DELETE /api/v1/suites/1

# Run a suite
POST /api/v1/suites/1/run
{
  "browser": "chromium",
  "environment": "dev",
  "triggered_by": "manual",
  "stop_on_failure": false
}

# Get suite execution status
GET /api/v1/suite-executions/1

# List suite executions
GET /api/v1/suite-executions?suite_id=1
```

---

## 🚀 **How It Works**

### **Creating a Suite**

1. User creates suite "Three.com.hk Complete Flow"
2. Selects tests: #62, #63, #64, #65, #66
3. Database stores:
   ```sql
   test_suites: id=1, name="Three.com.hk Complete Flow"
   
   test_suite_items:
     id=1, suite_id=1, test_case_id=62, execution_order=1
     id=2, suite_id=1, test_case_id=63, execution_order=2
     id=3, suite_id=1, test_case_id=64, execution_order=3
     id=4, suite_id=1, test_case_id=65, execution_order=4
     id=5, suite_id=1, test_case_id=66, execution_order=5
   ```

### **Running a Suite**

1. User clicks "Run Suite"
2. Backend creates suite execution record
3. For each test in order:
   - Queue individual test execution
   - Wait for completion (or run in parallel)
   - Update suite execution stats
4. Return list of execution IDs
5. Frontend shows progress for all tests

### **Execution Flow**

```
User clicks "Run Suite" (5 tests)
    ↓
Create suite_execution record (status=pending)
    ↓
Loop through test_suite_items (ordered):
    ↓
  Test #62 → Queue execution → execution_id=100
    ↓
  Test #63 → Queue execution → execution_id=101
    ↓
  Test #64 → Queue execution → execution_id=102
    ↓
  Test #65 → Queue execution → execution_id=103
    ↓
  Test #66 → Queue execution → execution_id=104
    ↓
Update suite_execution:
  status=running
  queued_executions=[100, 101, 102, 103, 104]
    ↓
Monitor all executions:
  When execution completes → Update passed/failed count
  If stop_on_failure=True and test fails → Stop queue
    ↓
When all complete:
  suite_execution.status=completed
  suite_execution.completed_at=now()
    ↓
Show suite results with aggregated stats
```

---

## 📊 **Suite Execution Results**

```
┌─────────────────────────────────────────────────────────────────┐
│ Suite Execution #45                                             │
│ Three.com.hk Complete Flow                                      │
├─────────────────────────────────────────────────────────────────┤
│ Status: ✅ Completed                                            │
│ Duration: 14m 32s                                               │
│ Browser: Chromium                                               │
│ Environment: Development                                        │
│                                                                 │
│ Results:                                                        │
│ ✅ Passed: 4 tests                                             │
│ ❌ Failed: 1 test                                              │
│ ⏭️  Skipped: 0 tests                                           │
│                                                                 │
│ Test Executions:                                                │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ 1. ✅ Navigate to plan page (#62) - 2m 15s   [View]      │ │
│ │ 2. ✅ Select contract (#63) - 1m 45s         [View]      │ │
│ │ 3. ✅ Verify pricing (#64) - 0m 30s          [View]      │ │
│ │ 4. ❌ Complete checkout (#65) - 5m 12s       [View]      │ │
│ │    Error: Could not find "Confirm" button                 │ │
│ │ 5. ✅ Login & confirm (#66) - 4m 50s         [View]      │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [Re-run Failed Tests]  [Re-run Entire Suite]  [Export Results] │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💡 **Advanced Features**

### **1. Test Reusability**
Same test can be in multiple suites:
- Test #62 in "Complete Flow" suite
- Test #62 in "Smoke Tests" suite
- Test #62 in "Regression Tests" suite

### **2. Dynamic Ordering**
Change execution order without recreating suite:
```http
PUT /api/v1/suites/1
{
  "test_case_ids": [66, 65, 64, 63, 62]  // Reversed order!
}
```

### **3. Conditional Execution**
- **Stop on failure**: If test #63 fails, skip #64, #65, #66
- **Continue on failure**: Run all tests regardless of failures

### **4. Parallel Execution** (Future)
Run independent tests simultaneously:
- Test #62, #63, #64 in parallel
- Then #65, #66 sequentially

### **5. Suite Templates**
Create suite from template:
- "E2E Template" → Automatically include all e2e tests
- "Critical Path" → Auto-select high-priority tests

---

## 🎯 **Your Specific Use Cases**

### **Use Case 1: Sequential Tests #62-#66**

```json
{
  "name": "Three.com.hk Complete Flow",
  "description": "Full subscription flow in order",
  "tags": ["e2e", "sequential", "three-hk"],
  "test_case_ids": [62, 63, 64, 65, 66]
}
```

**Run**: All 5 tests in exact order

### **Use Case 2: Non-Sequential #60, #62, #64, #65, #66**

```json
{
  "name": "Critical User Journeys",
  "description": "Key tests from different features",
  "tags": ["critical", "smoke"],
  "test_case_ids": [60, 62, 64, 65, 66]
}
```

**Run**: Tests in specified order (60 → 62 → 64 → 65 → 66)

### **Use Case 3: Smoke Tests (Quick Health Check)**

```json
{
  "name": "Smoke Tests",
  "description": "Quick validation of core features",
  "tags": ["smoke", "quick"],
  "test_case_ids": [60, 62, 66]  // Just 3 critical tests
}
```

**Run**: Fast 5-minute health check

---

## 📝 **Summary**

**Benefits**:
- ✅ **Reusability**: Use same tests in multiple suites
- ✅ **Flexibility**: Mix any tests in any order
- ✅ **Efficiency**: Run batch tests with one click
- ✅ **Organization**: Group related tests logically
- ✅ **Tracking**: Suite-level results and history

**Next Steps**:
1. Implement database tables (test_suites, test_suite_items, suite_executions)
2. Create backend API endpoints
3. Build frontend UI (Test Suites page)
4. Add "Run Suite" functionality
5. Display suite execution results

This gives you a complete **Test Project Management** system! 🚀
