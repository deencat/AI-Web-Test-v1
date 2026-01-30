# EvolutionAgent Frontend Integration Solution

**Problem Identified:** EvolutionAgent generates standalone Playwright `.spec.ts` files that are NOT integrated with the Phase 1/2 frontend system.

**Status:** 🔴 Critical Architecture Issue - Needs Resolution  
**Last Updated:** January 29, 2026

---

## 🚨 The Problem

### Current State:

**Phase 1/2 Frontend System:**
```
Test Generation → TestCase (database) → Frontend Display → "Run Test" Button → Phase 2 Execution Engine
```

- Tests stored in database as `TestCase` objects with `steps` (JSON array of strings)
- Frontend displays tests in UI
- User clicks "Run Test" → Executes via Phase 2 engine (`StagehandExecutionService`)
- Results tracked in database, visible in frontend

**EvolutionAgent Current Output:**
```
EvolutionAgent → Playwright .spec.ts file → Saved to disk → ❌ NOT in database → ❌ NOT in frontend
```

- Generates standalone Playwright code files
- Files saved to `backend/artifacts/generated_tests/`
- **NOT stored in database**
- **NOT visible in frontend**
- **CANNOT be executed via "Run Test" button**
- **CANNOT be reviewed/scored/improved through existing system**

### The Misalignment:

1. **RequirementsAgent** generates BDD scenarios for **AnalysisAgent** to execute
2. **AnalysisAgent** executes tests via Phase 2 engine (integrated with frontend)
3. **EvolutionAgent** generates separate Playwright code (NOT integrated with frontend)

**Question:** Who runs EvolutionAgent's generated code? Who reviews it? Who scores it?

---

## ✅ Solution Options

### Option 1: Convert Playwright Code to Test Steps (Recommended)

**Approach:** EvolutionAgent generates Playwright code, then converts it to test steps and stores in database.

**Flow:**
```
EvolutionAgent → Generate Playwright Code → Parse Code → Extract Steps → Store as TestCase → Frontend Display
```

**Implementation:**
1. EvolutionAgent generates Playwright code (as it does now)
2. **NEW:** Parse Playwright code to extract test steps
3. **NEW:** Convert steps to database format (array of strings)
4. **NEW:** Store as `TestCase` objects in database
5. Frontend automatically displays them (existing functionality)
6. User can click "Run Test" (existing functionality)

**Pros:**
- ✅ Integrates with existing frontend
- ✅ Uses existing execution engine
- ✅ Can be reviewed/scored/improved
- ✅ Maintains Playwright code as artifact (for reference)

**Cons:**
- ⚠️ Requires parsing Playwright code (complexity)
- ⚠️ May lose some code-level details

**Code Example:**
```python
# In EvolutionAgent
async def execute_task(self, task: TaskContext) -> TaskResult:
    # ... generate Playwright code ...
    test_file_content = self._combine_tests_to_file(generated_tests, page_context)
    
    # NEW: Convert Playwright code to test steps
    test_cases = self._parse_playwright_to_test_cases(test_file_content, scenarios)
    
    # NEW: Store in database
    db_test_cases = []
    for test_case_data in test_cases:
        db_test_case = TestCase(
            title=test_case_data["title"],
            description=test_case_data["description"],
            test_type=TestType.E2E,
            priority=Priority.HIGH,
            steps=test_case_data["steps"],  # Array of strings
            expected_result=test_case_data["expected_result"],
            user_id=task.user_id
        )
        db.add(db_test_case)
        db_test_cases.append(db_test_case)
    
    db.commit()
    
    return TaskResult(
        success=True,
        result={
            "test_file": test_filename,
            "test_file_path": test_file_path,
            "code": test_file_content,
            "test_cases": [tc.id for tc in db_test_cases],  # Database IDs
            "test_count": len(db_test_cases)
        }
    )
```

---

### Option 2: Generate Test Steps Directly (Simpler)

**Approach:** EvolutionAgent generates test steps directly (not Playwright code), stores in database.

**Flow:**
```
EvolutionAgent → Generate Test Steps → Store as TestCase → Frontend Display
```

**Implementation:**
1. EvolutionAgent generates test steps (array of strings) directly
2. Store as `TestCase` objects in database
3. Frontend displays them (existing functionality)
4. User can click "Run Test" (existing functionality)

**Pros:**
- ✅ Simple - no parsing needed
- ✅ Direct integration with frontend
- ✅ Uses existing execution engine
- ✅ Can be reviewed/scored/improved

**Cons:**
- ⚠️ No Playwright code artifact (but not needed if steps work)

**Code Example:**
```python
# In EvolutionAgent
async def execute_task(self, task: TaskContext) -> TaskResult:
    # Generate test steps directly (not Playwright code)
    test_cases = []
    for scenario in scenarios:
        steps = self._convert_scenario_to_steps(scenario, page_context)
        test_cases.append({
            "title": scenario["title"],
            "description": scenario.get("given", ""),
            "steps": steps,  # Array of strings like "Click login button"
            "expected_result": scenario.get("then", "")
        })
    
    # Store in database
    db_test_cases = []
    for test_case_data in test_cases:
        db_test_case = TestCase(
            title=test_case_data["title"],
            description=test_case_data["description"],
            test_type=TestType.E2E,
            priority=Priority.HIGH,
            steps=test_case_data["steps"],
            expected_result=test_case_data["expected_result"],
            user_id=task.user_id
        )
        db.add(db_test_case)
        db_test_cases.append(db_test_case)
    
    db.commit()
    
    return TaskResult(
        success=True,
        result={
            "test_cases": [tc.id for tc in db_test_cases],
            "test_count": len(db_test_cases)
        }
    )
```

---

### Option 3: Hybrid Approach (Best of Both Worlds)

**Approach:** EvolutionAgent generates both Playwright code AND test steps, stores steps in database.

**Flow:**
```
EvolutionAgent → Generate Playwright Code + Test Steps → Store Steps in DB → Frontend Display
                                                          Save Code as Artifact
```

**Implementation:**
1. EvolutionAgent generates Playwright code (for reference/CI/CD)
2. **ALSO** generates test steps (for frontend integration)
3. Store steps as `TestCase` objects in database
4. Save Playwright code as artifact (optional, for external use)
5. Frontend displays database tests (existing functionality)

**Pros:**
- ✅ Integrates with frontend (via steps)
- ✅ Provides Playwright code (for CI/CD/external use)
- ✅ Best of both worlds

**Cons:**
- ⚠️ More complex (generates both formats)

---

## 🎯 Recommended Solution: Option 2 (Generate Test Steps Directly)

### Why Option 2?

1. **Simplest** - No parsing complexity
2. **Direct Integration** - Works with existing frontend immediately
3. **Consistent** - Matches Phase 2 test generation pattern
4. **Sufficient** - Test steps are what the frontend needs

### Implementation Plan:

#### Step 1: Modify EvolutionAgent to Generate Test Steps

```python
# backend/agents/evolution_agent.py

async def execute_task(self, task: TaskContext) -> TaskResult:
    """
    Generate test cases from BDD scenarios.
    
    NEW: Generates test steps (not Playwright code) and stores in database.
    """
    # ... existing code to get scenarios ...
    
    # Generate test steps for each scenario
    test_cases = []
    for scenario in prioritized_scenarios:
        # Convert BDD scenario to test steps
        steps = self._convert_scenario_to_steps(scenario, page_context)
        
        test_cases.append({
            "title": scenario.get("title", f"Test: {scenario.get('scenario_id')}"),
            "description": scenario.get("given", ""),
            "steps": steps,  # Array of strings
            "expected_result": scenario.get("then", ""),
            "priority": scenario.get("priority", "medium"),
            "scenario_id": scenario.get("scenario_id"),
            "risk_score": next(
                (rs.get("rpn", 0) for rs in risk_scores 
                 if rs["scenario_id"] == scenario.get("scenario_id")), 
                0
            )
        })
    
    # Store in database
    db = task.payload.get("db")  # Get database session from task
    if not db:
        # Fallback: return steps without storing
        return TaskResult(
            success=True,
            result={
                "test_cases": test_cases,
                "test_count": len(test_cases),
                "note": "Database not available - test cases not stored"
            }
        )
    
    # Store each test case
    from app.models.test_case import TestCase, TestType, Priority, TestStatus
    from app.models.user import User
    
    db_test_cases = []
    for test_case_data in test_cases:
        # Map priority string to enum
        priority_map = {
            "critical": Priority.HIGH,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW
        }
        priority = priority_map.get(test_case_data["priority"].lower(), Priority.MEDIUM)
        
        db_test_case = TestCase(
            title=test_case_data["title"],
            description=test_case_data["description"],
            test_type=TestType.E2E,
            priority=priority,
            status=TestStatus.PENDING,
            steps=test_case_data["steps"],
            expected_result=test_case_data["expected_result"],
            user_id=task.user_id or 1,  # Default to user 1 if not provided
            test_metadata={
                "scenario_id": test_case_data.get("scenario_id"),
                "risk_score": test_case_data.get("risk_score"),
                "generated_by": "EvolutionAgent",
                "generation_id": generation_id
            }
        )
        db.add(db_test_case)
        db_test_cases.append(db_test_case)
    
    db.commit()
    
    # Refresh to get IDs
    for tc in db_test_cases:
        db.refresh(tc)
    
    return TaskResult(
        success=True,
        result={
            "test_cases": [
                {
                    "id": tc.id,
                    "title": tc.title,
                    "scenario_id": tc.test_metadata.get("scenario_id")
                }
                for tc in db_test_cases
            ],
            "test_count": len(db_test_cases),
            "generation_id": generation_id
        }
    )

def _convert_scenario_to_steps(
    self, 
    scenario: Dict, 
    page_context: Dict
) -> List[str]:
    """
    Convert BDD scenario to test steps (array of strings).
    
    This is similar to AnalysisAgent._convert_scenario_to_steps but
    generates steps for database storage.
    """
    steps = []
    
    # Given: Preconditions → Navigation
    given = scenario.get("given", "")
    if given and page_context.get("url"):
        steps.append(f"Navigate to {page_context['url']}")
    
    # When: Actions → Click, type, navigate
    when = scenario.get("when", "")
    if when:
        # Split by commas for multiple actions
        when_parts = [p.strip() for p in when.split(",")]
        for part in when_parts:
            if part:
                # Clean up action text
                step = part.strip()
                if not step.lower().startswith("user"):
                    step = f"User {step.lower()}"
                steps.append(step)
    
    # Then: Assertions → Verify, check
    then = scenario.get("then", "")
    if then:
        if not then.lower().startswith("verify"):
            steps.append(f"Verify: {then}")
        else:
            steps.append(then)
    
    return steps
```

#### Step 2: Update Task Context to Include Database Session

```python
# In test_four_agent_e2e_real.py or orchestration

evolution_task = TaskContext(
    conversation_id=conversation_id,
    task_id="evolution-task-001",
    task_type="test_code_generation",
    payload={
        "scenarios": prioritized_scenarios,
        "risk_scores": analysis_result.result["risk_scores"],
        "prioritization": analysis_result.result["final_prioritization"],
        "page_context": observation_data["page_context"],
        "db": db_session  # Pass database session
    },
    user_id=1  # Or get from current user
)
```

#### Step 3: Frontend Integration (Automatic)

Once test cases are stored in database:
- ✅ Frontend automatically displays them (existing `GET /api/v1/tests` endpoint)
- ✅ User can click "Run Test" (existing functionality)
- ✅ Execution tracked in database (existing functionality)
- ✅ Results visible in frontend (existing functionality)

---

## 🔄 Updated Workflow

### Before (Current - Misaligned):
```
ObservationAgent → RequirementsAgent → AnalysisAgent → EvolutionAgent
                                                          ↓
                                                    Playwright .spec.ts
                                                    (NOT in database)
                                                    (NOT in frontend)
```

### After (Fixed - Integrated):
```
ObservationAgent → RequirementsAgent → AnalysisAgent → EvolutionAgent
                                                          ↓
                                                    Test Steps
                                                          ↓
                                                    Database (TestCase)
                                                          ↓
                                                    Frontend Display
                                                          ↓
                                                    "Run Test" Button
                                                          ↓
                                                    Phase 2 Execution
```

---

## 📊 Comparison: Current vs. Recommended

| Aspect | Current (Playwright Code) | Recommended (Test Steps) |
|--------|---------------------------|-------------------------|
| **Output Format** | `.spec.ts` files | Test steps (array of strings) |
| **Storage** | File system | Database (`test_cases` table) |
| **Frontend Integration** | ❌ Not visible | ✅ Visible in Tests page |
| **Execution** | Manual (`npx playwright test`) | ✅ Via "Run Test" button |
| **Review/Scoring** | ❌ Not possible | ✅ Via frontend UI |
| **Improvement Loop** | ❌ No feedback | ✅ Via execution feedback |
| **Consistency** | Different from Phase 2 | ✅ Matches Phase 2 pattern |

---

## 🎯 Key Benefits of Recommended Solution

1. **Frontend Integration** - Tests appear in existing UI automatically
2. **Execution Integration** - Can run via "Run Test" button
3. **Review/Scoring** - Can be reviewed and scored through frontend
4. **Improvement Loop** - Execution feedback can improve future generations
5. **Consistency** - Matches Phase 2 test generation pattern
6. **Simplicity** - No parsing complexity, direct database storage

---

## 📝 Next Steps

1. **Modify EvolutionAgent** to generate test steps instead of (or in addition to) Playwright code
2. **Update `execute_task`** to store test cases in database
3. **Update test fixtures** to pass database session to EvolutionAgent
4. **Verify frontend integration** - Tests should appear automatically
5. **Test execution** - Verify "Run Test" button works with generated tests

---

## ❓ Questions to Resolve

1. **Should we keep Playwright code generation?**
   - Option A: Remove it (simpler)
   - Option B: Keep it as optional artifact (for CI/CD)
   - **Recommendation:** Keep as optional artifact, but primary output is test steps

2. **How to handle test metadata?**
   - Store `scenario_id`, `risk_score`, `generation_id` in `test_metadata` JSON field
   - Link to original BDD scenario if needed

3. **What about test execution results?**
   - Use existing Phase 2 execution engine (no changes needed)
   - Results stored in `test_executions` table (existing)
   - Feedback can be used to improve future generations (Sprint 10-12)

---

## ✅ Summary

**Problem:** EvolutionAgent generates standalone Playwright code that's not integrated with frontend.

**Solution:** Modify EvolutionAgent to generate test steps and store them in database (matching Phase 2 pattern).

**Result:** Generated tests appear in frontend, can be executed via "Run Test" button, and can be reviewed/scored/improved through existing system.

**Implementation:** Change EvolutionAgent to generate test steps (array of strings) instead of Playwright code, store as `TestCase` objects in database.

