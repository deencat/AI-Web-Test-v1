# Handling False Positives in Stagehand Executions

## Problem Statement

Stagehand AI-powered actions sometimes produce **false positives**:
- Clicks wrong button but reports success
- Doesn't perform action but reports success
- Performs partial action but reports complete success

This is dangerous because:
1. Tests pass when they should fail
2. Bugs go undetected
3. False confidence in test coverage

## Solution: Manual Feedback Annotation

### Workflow for False Positives

#### 1. **Identify False Positive**
When you review an execution and notice a false positive:
- Test passed but shouldn't have
- Wrong element was interacted with
- Action didn't actually complete

#### 2. **Create Manual Feedback Entry**

Even though the step "passed", you can manually create feedback:

```python
import requests

def report_false_positive(execution_id: int, step_index: int, token: str):
    """Create feedback for a false positive (test passed but shouldn't have)."""
    
    feedback_data = {
        "execution_id": execution_id,
        "step_index": step_index,
        "failure_type": "other",  # False positive is a special case
        "error_message": "FALSE POSITIVE: Step reported success but actual action was incorrect",
        "notes": """
        Manual review revealed:
        - Expected action: Click 'Submit' button
        - Actual action: Clicked 'Cancel' button instead
        - Test incorrectly passed due to Stagehand selector ambiguity
        
        This is a false positive that needs correction.
        """,
        "failed_selector": "button",  # The ambiguous selector that caused the issue
        "selector_type": "text",
        "page_url": "https://example.com/form",
        "browser_type": "chromium",
        "tags": ["false-positive", "manual-review", "stagehand-issue"]
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json=feedback_data
    )
    
    return response.json()
```

#### 3. **Submit Correction**

After creating the feedback, submit the correct selector:

```python
def submit_correction_for_false_positive(feedback_id: int, token: str):
    """Submit correction with more specific selector."""
    
    correction_data = {
        "corrected_step": {
            "action": "click",
            "selector": "button[type='submit'][class*='primary']",  # More specific
            "value": "",
            "description": "Click Submit button (not Cancel)"
        },
        "correction_source": "human",
        "correction_confidence": 0.95,
        "notes": """
        Correction: Use more specific selector to avoid ambiguity.
        Original selector 'button' was too generic and Stagehand clicked wrong button.
        New selector ensures we click the correct Submit button.
        """
    }
    
    response = requests.post(
        f"http://localhost:8000/api/v1/feedback/{feedback_id}/correction",
        headers={"Authorization": f"Bearer {token}"},
        json=correction_data
    )
    
    return response.json()
```

## Enhanced Assertions (Recommended)

### Add Verification Steps

Instead of trusting Stagehand's success report, add verification steps:

```json
{
  "steps": [
    {
      "step_number": 1,
      "action": "click",
      "selector": "button",
      "description": "Click Submit button"
    },
    {
      "step_number": 2,
      "action": "wait",
      "selector": ".success-message",
      "description": "Verify success message appears",
      "expected_result": "Success message is visible"
    },
    {
      "step_number": 3,
      "action": "assert",
      "selector": "h1",
      "value": "Thank You",
      "description": "Verify page title changed",
      "expected_result": "Page shows 'Thank You'"
    }
  ]
}
```

**Benefits**:
- Catches false positives automatically
- Forces verification of actual results
- Provides better failure context

## UI Enhancement for Reporting False Positives

### Add "Report Issue" Button

In the ExecutionProgressPage, add a button for **passed** steps:

```typescript
// For steps that passed but user suspects false positive
<button
  onClick={() => handleReportFalsePositive(step)}
  className="text-orange-600 hover:text-orange-800"
>
  ⚠️ Report False Positive
</button>
```

This opens a modal to create feedback even for "passed" steps.

## Pattern Recognition (Sprint 5)

Once you have several false positive corrections:

1. **Pattern Analysis** will identify:
   - Common ambiguous selectors (e.g., generic "button")
   - Pages prone to false positives
   - Stagehand behavior patterns

2. **Auto-Correction** will suggest:
   - More specific selectors
   - Additional verification steps
   - Assertion improvements

3. **Confidence Scoring** will:
   - Flag risky steps before execution
   - Warn about ambiguous selectors
   - Recommend human review for low-confidence actions

## Immediate Actions

### 1. Review Recent Executions

```bash
# Find executions with suspicious pass rates
curl -X GET "http://localhost:8000/api/v1/executions?status=completed&result=pass" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Add Verification Steps

For critical actions, always add verification:
- Form submission → Check for success message
- Navigation → Verify URL or page title
- Data entry → Read back the value

### 3. Tag Suspicious Tests

```python
# Tag tests that need review
{
  "tags": ["needs-verification", "stagehand", "high-risk"]
}
```

## Best Practices

### DO:
✅ Add verification steps after critical actions
✅ Use specific selectors (IDs, unique classes)
✅ Manually review Stagehand test results
✅ Report false positives via feedback system
✅ Include screenshots in feedback for proof

### DON'T:
❌ Trust Stagehand success without verification
❌ Use generic selectors (button, div, span)
❌ Skip manual review of critical tests
❌ Ignore suspicious pass rates
❌ Let false positives accumulate

## Monitoring Dashboard (Future Enhancement)

Consider building a dashboard to track:
- False positive rate per test
- Stagehand vs. Playwright reliability
- Common failure patterns
- Correction success rate

This will help identify problematic tests and improve overall quality.

## Example: Complete False Positive Workflow

```python
# 1. Execution completed with suspicious "pass"
execution_id = 123
step_index = 5

# 2. Manual review reveals false positive
# (User watches video/screenshots and sees wrong button was clicked)

# 3. Create feedback
feedback = report_false_positive(execution_id, step_index, token)

# 4. Submit correction with better selector
correction = submit_correction_for_false_positive(feedback["id"], token)

# 5. Update test case with corrected selector
update_test_case(test_case_id, {
  "steps": [...with corrected selector...]
})

# 6. Re-run test to verify fix
new_execution = execute_test(test_case_id)

# 7. If still fails, add verification step
add_verification_step(test_case_id, step_index + 1)
```

## Summary

The Execution Feedback System is **perfect** for handling false positives because:

1. **Captures the problem** - Even for "passed" steps
2. **Documents the correction** - Builds knowledge base
3. **Enables learning** - Sprint 5 will auto-detect similar issues
4. **Improves tests** - Forces better selectors and verification

**Start by creating feedback entries for known false positives, and the system will learn to prevent them in the future!**
