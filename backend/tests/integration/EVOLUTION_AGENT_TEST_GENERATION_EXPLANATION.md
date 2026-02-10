# EvolutionAgent Test Generation: Criteria and Requirements

## Key Difference: 3-Agent vs 4-Agent Test

### 3-Agent Test (`test_three_hk_unlimited_48m_plan_flow`)
**Purpose:** Tests a **specific, manually-defined business flow**

- **Manually defines** a specific scenario:
  ```python
  specific_scenario = {
      "scenario_id": "THREE-5G-UNLIMITED-48M-182",
      "title": "Subscribe 5G寬頻數據無限任用 48個月 plan at $182",
      "when": (
          "Click on plan with text '5G寬頻數據無限任用', "
          "Click on contract term '48個月', "
          "Verify: price shows '$182', "
          "Click on button '立即登記', "
          "Click on button '下一步'"
      ),
      ...
  }
  ```
- **Directly executes** this specific scenario via `AnalysisAgent._execute_scenario_real_time()`
- **Does NOT use EvolutionAgent** - it's a 3-agent workflow (Observation → Requirements → Analysis)

### 4-Agent Test (`test_four_agent_e2e_real`)
**Purpose:** Tests the **full automated workflow** including EvolutionAgent

- **Uses automatically-generated scenarios** from RequirementsAgent
- **EvolutionAgent converts** those generic BDD scenarios to executable test steps
- **Stores test cases in database** for frontend visibility
- **No specific business flow** - it tests the system's ability to generate test cases from generic scenarios

## Why 4-Agent Test Doesn't Have Specific Business Flow

The 4-agent test is designed to verify:
1. ✅ **Automated scenario generation** (RequirementsAgent creates scenarios from UI elements)
2. ✅ **Risk analysis and prioritization** (AnalysisAgent scores and prioritizes)
3. ✅ **Test step generation** (EvolutionAgent converts BDD to executable steps)
4. ✅ **Database storage** (Test cases stored for frontend)

It's **not designed** to test a specific business flow - that's what the 3-agent test does.

## EvolutionAgent: Criteria and Requirements for Test Generation

### Input Sources (What EvolutionAgent Receives)

EvolutionAgent generates test steps from:

1. **BDD Scenarios** (from RequirementsAgent)
   - `given`: Preconditions (e.g., "User is on the Three HK 5G Broadband plan page")
   - `when`: Actions (e.g., "Click on plan 'Plan A', Select contract term '12 months'")
   - `then`: Expected outcomes (e.g., "User is taken to subscription flow")

2. **Risk Scores** (from AnalysisAgent)
   - RPN (Risk Priority Number)
   - Severity, Occurrence, Detection scores
   - Used to prioritize and inform test step quality

3. **Prioritization** (from AnalysisAgent)
   - Composite scores
   - Priority levels (critical, high, medium, low)
   - Used to determine test case priority in database

4. **Page Context** (from ObservationAgent)
   - URL (for navigation steps)
   - Page type, framework, complexity
   - UI elements (for selectors)

5. **Test Data** (from RequirementsAgent)
   - Test data values (e.g., email addresses, passwords)
   - Used to populate input fields in test steps

### Generation Process

#### Step 1: LLM-Based Generation (Primary Method)
```python
async def _generate_test_steps_with_llm(...)
```

**Prompt includes:**
- Scenario information (ID, title, priority, RPN, composite score, type)
- BDD scenario (Given/When/Then)
- Page context (URL, page type)
- Requirements:
  1. Generate array of executable test steps (as strings)
  2. Each step should be clear, actionable instruction
  3. Steps should be in execution order
  4. Include navigation, actions, and assertions
  5. Use natural language executable by test automation engine
  6. Be specific with selectors and values where applicable

**Output Format:**
```json
{
  "steps": [
    "Navigate to https://example.com/login",
    "Enter email: test@example.com",
    "Enter password: password123",
    "Click Login button",
    "Verify URL contains /dashboard"
  ]
}
```

#### Step 2: Template-Based Fallback
```python
def _generate_test_steps_from_template(...)
```

If LLM generation fails, uses `_convert_scenario_to_steps()`:

**Conversion Rules:**

1. **Navigation** (from `page_context.url` or `given`):
   - If URL exists: `"Navigate to {url}"`
   - If `given` contains "on {page} page": `"Navigate to {page} page"`

2. **Actions** (from `when` clause):
   - Splits by commas: `"Click A, Enter B, Click C"` → 3 steps
   - Detects action verbs: `click`, `select`, `press`, `enter`, `type`, `navigate`
   - Removes "User" prefix: `"User clicks button"` → `"Click button"`
   - Handles "and"/"then" connectors: `"User does X and Y"` → 2 steps

3. **Assertions** (from `then` clause):
   - Adds "Verify:" prefix if not present: `"User sees dashboard"` → `"Verify: User sees dashboard"`

**Example Conversion:**
```
Given: "User is on login page"
When: "User enters email and password, clicks Login"
Then: "User is redirected to dashboard"

Converts to:
- Navigate to login page
- Enter email: test@example.com
- Enter password: password123
- Click Login button
- Verify: User is redirected to dashboard
```

### Quality Criteria

EvolutionAgent evaluates generated steps using:

1. **Confidence Score** (`_calculate_steps_confidence()`):
   - Based on steps count (more steps = higher confidence for complex scenarios)
   - Based on action verbs detected (click, enter, verify, etc.)
   - Based on scenario completeness (has given/when/then)

2. **Validation**:
   - Steps must be non-empty array
   - Each step must be a string
   - Steps should include navigation, actions, and assertions

3. **Database Storage Requirements**:
   - `title`: From scenario title
   - `description`: From scenario `given`
   - `steps`: Array of executable step strings
   - `expected_result`: From scenario `then`
   - `preconditions`: From scenario `given`
   - `priority`: Mapped from scenario priority (critical/high → HIGH, medium → MEDIUM, low → LOW)
   - `test_metadata`: Includes scenario_id, generation_id, RPN, scenario_type

### Example: How EvolutionAgent Would Handle the 3-Agent Test Scenario

If the 3-agent test's specific scenario were passed to EvolutionAgent:

**Input:**
```python
scenario = {
    "scenario_id": "THREE-5G-UNLIMITED-48M-182",
    "given": "User is on the Three HK 5G Broadband plan page",
    "when": (
        "Click on plan with text '5G寬頻數據無限任用', "
        "Click on contract term '48個月', "
        "Verify: price shows '$182', "
        "Click on button '立即登記', "
        "Click on button '下一步'"
    ),
    "then": "User is taken to subscription flow for 5G寬頻數據無限任用 48個月 plan with monthly fee $182"
}
```

**EvolutionAgent Output:**
```python
{
    "steps": [
        "Navigate to https://web.three.com.hk/5gbroadband/plan-monthly.html",
        "Click on plan with text '5G寬頻數據無限任用'",
        "Click on contract term '48個月'",
        "Verify: price shows '$182'",
        "Click on button '立即登記'",
        "Click on button '下一步'",
        "Verify: User is taken to subscription flow for 5G寬頻數據無限任用 48個月 plan with monthly fee $182"
    ],
    "confidence": 0.85
}
```

## Summary

| Aspect | 3-Agent Test | 4-Agent Test |
|--------|-------------|--------------|
| **Purpose** | Test specific business flow | Test automated workflow |
| **Scenario Source** | Manually defined | Auto-generated by RequirementsAgent |
| **EvolutionAgent** | ❌ Not used | ✅ Converts scenarios to test steps |
| **Database Storage** | ❌ No | ✅ Yes (TestCase objects) |
| **Test Steps** | Direct execution via AnalysisAgent | Generated by EvolutionAgent, stored in DB |

**EvolutionAgent Criteria:**
- ✅ Converts BDD scenarios (Given/When/Then) to executable test steps
- ✅ Uses LLM for intelligent step generation (with template fallback)
- ✅ Incorporates risk scores, prioritization, and page context
- ✅ Stores test cases in database for frontend visibility
- ✅ Generates steps as array of strings (compatible with Phase 2 execution engine)

