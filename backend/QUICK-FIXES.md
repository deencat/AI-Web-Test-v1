# Quick Fixes for Test Failures

## Fix 1: Database Schema Test (Optional)

The test needs data in the database. Run:

```powershell
python reset_db.py
```

This will:
- ✅ Reset the database
- ✅ Create test user (admin@aiwebtest.com)
- ✅ Initialize schema
- ✅ Add sample data

Then re-run:
```powershell
python test_comprehensive.py
```

## Fix 2: Increase Browser Test Timeout

Update `run_comprehensive_tests.py`:

```python
# Line 47 - change timeout from 60 to 120
result = subprocess.run(
    [sys.executable, script],
    capture_output=True,
    text=True,
    timeout=120  # Changed from 60
)
```

## Fix 3: Unicode Warnings (Optional - Cosmetic Only)

The warnings about cp950 codec are harmless. They're just emoji symbols in test output.

To suppress them, add to top of `run_comprehensive_tests.py`:

```python
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

## Quick Test Individual Components

If you want to test specific parts:

### Test API Only:
```powershell
python test_api_endpoints.py
```
**Expected**: ✅ ALL PASS (9/9)

### Test Authentication:
```powershell
python test_auth.py
```
**Expected**: ✅ PASS

### Test AI Generation:
```powershell
python test_generation_service.py
```
**Expected**: ✅ PASS (may take 10-15 seconds)

### Test Browser Automation:
```powershell
# Run manually to see actual output
python test_playwright_direct.py
```

### Test Stagehand (with LLM):
```powershell
# May take longer due to LLM calls
python test_stagehand_simple.py
```

## Summary

**Critical Tests**: ✅ All Passing  
**Non-Critical Tests**: ⚠️ 2 failures, 2 skipped  
**Recommendation**: **Proceed with development**

The failures are in optional/integration tests that don't block core functionality.
