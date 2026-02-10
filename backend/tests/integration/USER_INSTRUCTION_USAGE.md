# How to Use User Instruction Support in Tests

## Overview

RequirementsAgent now supports user instructions to generate specific test scenarios matching user intent. This allows you to test specific business flows without manually defining scenarios.

**NEW:** You can also provide login credentials via `LOGIN_EMAIL` and `LOGIN_PASSWORD` environment variables. The system will automatically include login steps in generated test flows. See [LOGIN_CREDENTIALS_USAGE.md](./LOGIN_CREDENTIALS_USAGE.md) for details.

## Usage Methods

### Method 1: Environment Variable (Recommended)

Set the `USER_INSTRUCTION` environment variable before running the test:

**PowerShell (CORRECT SYNTAX):**
```powershell
# Use $env:VARIABLE = "value" syntax (NOT 'set VARIABLE=value')
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**PowerShell (One Line):**
```powershell
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"; python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**PowerShell (With Special Characters - Use Double Quotes):**
```powershell
# If your instruction contains single quotes, wrap the whole thing in double quotes
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**Bash/Linux:**
```bash
export USER_INSTRUCTION="Test purchase flow for '5G寬頻數據無限任用' plan"
python -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s
```

**Windows CMD (NOT PowerShell):**
```cmd
set USER_INSTRUCTION=Test purchase flow for '5G寬頻數據無限任用' plan
python -u -m pytest tests\integration\test_four_agent_e2e_real.py -v -s
```

**⚠️ IMPORTANT:** 
- PowerShell uses `$env:VARIABLE = "value"` (with `$env:` prefix and `=` with spaces)
- Windows CMD uses `set VARIABLE=value` (no spaces around `=`)
- If you're in PowerShell (which you are, based on `(venv) PS`), use the PowerShell syntax!

### Method 2: Inline with PowerShell

**PowerShell (single line):**
```powershell
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"; python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**PowerShell (multi-line for readability):**
```powershell
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

### Method 3: Direct Code Modification (For Testing)

If you want to hardcode it for testing, modify the test file:

```python
# In test_four_agent_e2e_real.py, around line 278
user_instruction = "Test purchase flow for '5G寬頻數據無限任用' plan"  # Hardcoded for testing
```

## Example Instructions

### Specific Plan Purchase Flow
```powershell
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"
```

### Login Flow
```powershell
$env:USER_INSTRUCTION = "Test user login with email and password"
```

### Registration Flow
```powershell
$env:USER_INSTRUCTION = "Test user registration with form validation"
```

### Specific Button/Feature
```powershell
$env:USER_INSTRUCTION = "Test clicking the '立即登記' button and verify subscription form opens"
```

## What Happens

1. **RequirementsAgent receives user instruction** in task payload
2. **LLM prompt includes user instruction** with high priority
3. **Scenarios are generated** with at least one matching the instruction
4. **Matching scenarios get high/critical priority**
5. **Matching scenarios are tagged** with `"user-requirement"`
6. **Test output shows** which scenarios matched the instruction

## Expected Output

When you run the test with a user instruction, you'll see:

```
[INFO] User instruction provided: 'Test purchase flow for '5G寬頻數據無限任用' plan'
        RequirementsAgent will prioritize scenarios matching this requirement

Step 2: Generating test scenarios with RequirementsAgent...
        User instruction: 'Test purchase flow for '5G寬頻數據無限任用' plan'
        Will prioritize scenarios matching this requirement
        Scenario generation stages:
        1. Grouping elements by page/component (Page Object Model)
        2. Mapping user journeys (multi-step flows)
        3. Generating functional scenarios (LLM + patterns)
           • Prioritizing scenarios matching: 'Test purchase flow for '5G寬頻數據無限任用' plan'
        ...

[USER INSTRUCTION MATCH] Found 2 scenario(s) matching: 'Test purchase flow for '5G寬頻數據無限任用' plan'
    [1] Purchase 5G寬頻數據無限任用 plan - Complete flow (Priority: critical)
        Tagged with: user-requirement
    [2] Subscribe to 5G寬頻數據無限任用 48個月 plan (Priority: high)
```

## Verification

The test will:
- ✅ Show matching scenarios in the output
- ✅ Verify matching scenarios have high/critical priority
- ✅ Show tags including "user-requirement"
- ✅ Log the user instruction in RequirementsAgent logs

## Troubleshooting

**If no matching scenarios are found:**
- The instruction might not match available UI elements
- Try using more specific keywords from the page
- Check the generated scenarios to see what was actually created
- The LLM might need more context - ensure ObservationAgent found relevant elements

**If scenarios don't have high priority:**
- Check RequirementsAgent logs for LLM response
- Verify the LLM prompt includes the user instruction
- Check that `use_llm=True` in RequirementsAgent config

## Without User Instruction

If you don't set `USER_INSTRUCTION`, RequirementsAgent will:
- Generate generic scenarios from UI elements
- Use standard priority distribution
- Not prioritize any specific flow

This is the default behavior and still works perfectly for general test coverage.

