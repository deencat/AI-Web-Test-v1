# Quick Guide: Testing Sprint 4 Feedback System

## Option 1: Create Test with Intentional Failures

```bash
cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend
python create_test_with_failures.py
```

This will:
1. Create a test case with invalid selectors
2. Optionally execute it
3. Automatically capture feedback when steps fail
4. Show you the feedback in the UI

## Option 2: Report False Positives (Stagehand Issue)

When a test **passes** but shouldn't have (wrong button clicked, etc.):

### Interactive Mode
```bash
cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend
python report_false_positive.py
```

Follow the prompts to report the issue.

### Quick Mode
```bash
python report_false_positive.py 123 5 "Clicked Cancel instead of Submit"
```
- `123` = execution ID
- `5` = step number
- Description = what went wrong

## Option 3: Manual API Call

```bash
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": 123,
    "step_index": 5,
    "failure_type": "other",
    "error_message": "FALSE POSITIVE: Clicked wrong button",
    "notes": "Test passed but clicked Cancel instead of Submit",
    "tags": ["false-positive", "stagehand-issue"]
  }'
```

## Viewing Feedback

### In UI
1. Navigate to: `http://localhost:3000/executions/{execution_id}`
2. Scroll to "Execution Feedback & Learning" section
3. Click "Correct This" to submit corrections

### Via API
```bash
# Get feedback for execution
curl "http://localhost:8000/api/v1/executions/123/feedback" \
  -H "Authorization: Bearer $TOKEN"

# Get statistics
curl "http://localhost:8000/api/v1/feedback/stats/summary" \
  -H "Authorization: Bearer $TOKEN"
```

## Recommended Workflow for False Positives

1. **Run Test** → Test passes but you suspect false positive
2. **Review** → Check screenshots/video, confirm wrong action occurred
3. **Report** → Use `report_false_positive.py` to create feedback entry
4. **Correct** → Submit corrected selector via UI or API
5. **Update Test** → Modify test case with better selector
6. **Re-run** → Verify the fix works

## Best Practices

✅ **Always add verification steps** after critical actions
✅ **Use specific selectors** instead of generic ones
✅ **Review Stagehand results** manually for critical tests
✅ **Tag tests** with `stagehand`, `needs-verification`, etc.
✅ **Document corrections** with detailed notes

## Tools Available

| Tool | Purpose |
|------|---------|
| `create_test_with_failures.py` | Create tests that will fail |
| `report_false_positive.py` | Report false positives manually |
| `test_sprint4_simplified.py` | Test the feedback API |
| UI Feedback Section | View/correct feedback in browser |

## See Also

- `HANDLING-FALSE-POSITIVES.md` - Detailed guide on false positives
- `SPRINT-4-COMPLETION.md` - Complete Sprint 4 documentation
- Frontend: `ExecutionProgressPage` - UI for viewing/correcting feedback
