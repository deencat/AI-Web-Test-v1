# AI Test Generation to Execution Pipeline

## Overview
This document explains the complete workflow from AI-generated test cases to execution, using the Three.com.hk 5G Broadband example as reference.

## The Complete Pipeline

```
Step 1: AI Generation     Step 2: Save to DB       Step 3: Execute       Step 4: Monitor
    (LLM)              →   (Test Case)          →   (Stagehand)       →   (Results)
    
POST /tests/generate   →   POST /tests          →   POST /tests/{id}/run   →   GET /executions/{id}
```

## Comparison: Manual vs AI-Generated

### Manual Test Creation (test_three_5g_broadband.py)
```python
# Manually written test steps
test_data = {
    "title": "Three.com.hk - 5G Broadband Complete Subscription Flow",
    "description": "Complete end-to-end flow...",
    "steps": [
        "Scroll down the page slowly...",
        "Find and click the button that says exactly '30 months'...",
        "Verify that the '30 months' button now has a purple border...",
        # ... 24 more manually written steps
    ],
    "expected_result": "Successfully complete full subscription flow"
}

# Save to database
POST /api/v1/tests

# Execute with Stagehand
POST /api/v1/executions/tests/{test_id}/run
```

### AI-Generated Test Creation (NEW)
```python
# AI generates test steps from requirement description
generation_request = {
    "requirement": """
        Test the Three.com.hk 5G Broadband subscription flow...
        Should select 30 months, verify pricing, handle popups...
    """,
    "num_tests": 1
}

# AI generates the test
POST /api/v1/tests/generate
# Returns: { test_cases: [...], metadata: {...} }

# Save AI-generated test to database
POST /api/v1/tests

# Execute with Stagehand (same as manual)
POST /api/v1/executions/tests/{test_id}/run
```

## Deliverables from AI Generation

### 1. **Input: Test Requirement** (What you provide)
```json
{
  "requirement": "Test description with expected behavior",
  "num_tests": 1-10,
  "test_type": "e2e" (optional),
  "model": "deepseek/deepseek-chat" (optional)
}
```

### 2. **Output: Generated Test Cases** (What AI returns)
```json
{
  "test_cases": [
    {
      "title": "AI-generated test title",
      "description": "AI-generated description",
      "test_type": "e2e",
      "priority": "high|medium|low",
      "steps": [
        "Step 1: Navigate to...",
        "Step 2: Click...",
        "Step 3: Verify..."
      ],
      "expected_result": "What should happen",
      "preconditions": "Prerequisites (optional)",
      "test_data": {
        "key": "value"
      }
    }
  ],
  "metadata": {
    "model": "deepseek/deepseek-chat",
    "tokens_used": 1500,
    "generation_time": 2.5
  }
}
```

### 3. **Saved Test Case** (In database, ready for execution)
```json
{
  "id": 123,
  "title": "AI-generated test title",
  "description": "...",
  "test_type": "e2e",
  "priority": "high",
  "steps": [...],
  "expected_result": "...",
  "status": "pending",
  "created_by": "AI",
  "created_at": "2025-12-04T..."
}
```

### 4. **Execution Results** (After running with Stagehand)
```json
{
  "id": 456,
  "test_case_id": 123,
  "status": "completed",
  "result": "pass|fail",
  "duration_seconds": 45.2,
  "steps": [
    {
      "step_number": 1,
      "step_description": "Navigate to...",
      "result": "pass",
      "duration_seconds": 2.1,
      "screenshot_path": "screenshots/step1.png",
      "actual_result": "Successfully navigated"
    }
  ],
  "passed_steps": 10,
  "failed_steps": 0
}
```

## Key Differences: Manual vs AI

| Aspect | Manual (test_three_5g_broadband.py) | AI-Generated |
|--------|-------------------------------------|--------------|
| **Step Creation** | Manually write all 24+ steps | AI generates steps from description |
| **Time Required** | 30-60 minutes to write | 2-5 seconds to generate |
| **Consistency** | Depends on tester | AI follows patterns |
| **Flexibility** | Highly customizable | Customizable via prompt |
| **Execution** | ✅ Same - POST /tests/{id}/run | ✅ Same - POST /tests/{id}/run |
| **Monitoring** | ✅ Same - GET /executions/{id} | ✅ Same - GET /executions/{id} |

## Frontend Integration

### Tests Page UI Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. User Input (Generate Tests Section)                 │
│                                                         │
│  [Text Area: Describe what to test]                    │
│  "Test Three.com.hk 5G Broadband subscription flow..." │
│                                                         │
│  [Button: Generate Test Cases] ←────────────────────┐  │
└─────────────────────────────────────────────────────┘  │
                        │                                 │
                        ↓                                 │
┌─────────────────────────────────────────────────────┐  │
│ 2. AI Generation (Backend API)                      │  │
│                                                      │  │
│  POST /api/v1/tests/generate                        │  │
│  → LLM generates test steps                         │  │
│  → Returns GeneratedTestCase[]                      │  │
└─────────────────────────────────────────────────────┘  │
                        │                                 │
                        ↓                                 │
┌─────────────────────────────────────────────────────┐  │
│ 3. Generated Tests Display                          │  │
│                                                      │  │
│  ✅ Test 1: Three.com.hk - 5G Broadband Flow        │  │
│     Priority: High | Steps: 24                      │  │
│     [Edit] [Save to Tests] [Discard]                │  │
└─────────────────────────────────────────────────────┘  │
                        │                                 │
                        ↓ (User clicks Save)              │
┌─────────────────────────────────────────────────────┐  │
│ 4. Save to Database                                 │  │
│                                                      │  │
│  POST /api/v1/tests                                 │  │
│  → Creates test case record                         │  │
│  → Returns test ID                                  │  │
└─────────────────────────────────────────────────────┘  │
                        │                                 │
                        ↓                                 │
┌─────────────────────────────────────────────────────┐  │
│ 5. Saved Tests Section                              │  │
│                                                      │  │
│  🟢 Test #123: Three.com.hk - 5G Broadband          │  │
│     Status: Pending | Priority: High                │  │
│     [Run Test] [View] [Edit] [Delete]               │  │
└─────────────────────────────────────────────────────┘  │
                        │                                 │
                        ↓ (User clicks Run Test)          │
┌─────────────────────────────────────────────────────┐  │
│ 6. Execute Test                                     │  │
│                                                      │  │
│  POST /api/v1/executions/tests/123/run              │  │
│  → Stagehand executes steps                         │  │
│  → Returns execution ID                             │  │
└─────────────────────────────────────────────────────┘  │
                        │                                 │
                        ↓ (Navigate to execution)         │
┌─────────────────────────────────────────────────────┐  │
│ 7. Execution Details Page                           │  │
│                                                      │  │
│  Status: Running... → Completed                     │  │
│  Result: ✅ Pass                                     │  │
│  Duration: 45.2s                                    │  │
│                                                      │  │
│  ✅ Step 1: Navigate to page (2.1s)                 │  │
│  ✅ Step 2: Select 30 months (1.5s)                 │  │
│  ✅ Step 3: Click Subscribe (0.8s)                  │  │
│  📸 Screenshots available                           │  │
└─────────────────────────────────────────────────────┘  │
                                                          │
          [Generate More Tests] ─────────────────────────┘
```

## Code Example: Complete Flow

```typescript
// frontend/src/pages/TestsPage.tsx

// 1. Generate tests with AI
const handleGenerateTests = async () => {
  const result = await testsService.generateTests({
    prompt: userInput,
    count: 5
  });
  setGeneratedTests(result.test_cases); // Display for review
};

// 2. Save generated test to database
const handleSaveGeneratedTest = async (testCase) => {
  const savedTest = await testsService.createTest({
    title: testCase.title,
    description: testCase.description,
    test_type: testCase.test_type,
    priority: testCase.priority,
    steps: testCase.steps,
    expected_result: testCase.expected_result
  });
  // Test now in database with ID
};

// 3. Execute saved test
const handleRunTest = async (testId) => {
  const execution = await testsService.runTest(testId, {
    browser: 'chromium',
    environment: 'production',
    base_url: 'https://web.three.com.hk/5gbroadband/plan-hsbc-en.html',
    triggered_by: 'manual'
  });
  // Navigate to execution details
  navigate(`/executions/${execution.id}`);
};
```

## Real Example: Three.com.hk Test

### Requirement Input
```
Test the Three.com.hk 5G Broadband subscription flow at 
https://web.three.com.hk/5gbroadband/plan-hsbc-en.html

The test should select the 30 months contract, verify pricing ($135/month), 
handle popups, proceed through checkout, and complete login.
```

### AI Generates (in 2-5 seconds)
```
✅ Test Case: "Three.com.hk - 5G Broadband Complete Subscription Flow"
   Priority: High
   Type: E2E
   Steps: 24 detailed steps
   - "Scroll down the page slowly to see all the 5G Broadband plans..."
   - "Find and click the button that says exactly '30 months'..."
   - "Verify that the '30 months' button now has a purple border..."
   - ... 21 more steps
```

### Save to Database
```
Test ID: 123
Status: Pending
Created: 2025-12-04T10:30:00Z
```

### Execute with Stagehand
```
Execution ID: 456
Status: Running → Completed
Result: Pass
Duration: 45.2s
Screenshots: 24 screenshots captured
```

## Summary

**The Deliverable is:** A complete, executable test case that can be run with Stagehand, exactly like the manual test in `test_three_5g_broadband.py`, but generated automatically by AI.

**Key Advantage:** 
- Manual: 30-60 minutes to write 24 test steps
- AI: 2-5 seconds to generate same 24 test steps
- Execution: IDENTICAL for both (same Stagehand engine)
