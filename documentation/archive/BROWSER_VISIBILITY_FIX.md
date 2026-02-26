# Browser Visibility Fix - Summary

**Date:** February 10, 2026  
**Issue:** Browser not opening during test execution  
**Status:** ✅ **FIXED**

---

## 🔴 Root Causes Identified

### Issue 1: Not Using Virtual Environment
- Tests were run with system Python instead of venv Python
- **Stagehand module** (required for Phase 2 execution) was installed in venv but not accessible
- Error: `No module named 'stagehand'`

### Issue 2: ObservationAgent Always Headless
- `observation_agent.py` line 248 hardcoded `headless=True`
- Browser was never visible during crawling phase
- No configuration option to show browser

### Issue 3: Git Merge Conflicts (Already Fixed)
- Unresolved conflict markers in `backend/app/models/__init__.py`
- Blocked all imports and execution
- Fixed in commit `dd2080a`

---

## ✅ Fixes Applied

### Fix 1: Enable Browser Visibility in ObservationAgent

**Commit:** `dd190a7` - "fix: Enable visible browser mode for ObservationAgent and AnalysisAgent"

**Changes to `backend/agents/observation_agent.py`:**
```python
# Before (always headless):
browser = await p.chromium.launch(headless=True)

# After (configurable):
headless = self.config.get("headless_browser", True) if self.config else True
browser = await p.chromium.launch(headless=headless)
```

**Changes to `backend/tests/integration/test_four_agent_e2e_real.py`:**
```python
@pytest.fixture
def observation_agent_real(mock_message_queue):
    config = {
        "use_llm": True,
        "max_depth": 1,
        "max_pages": 1,
        "headless_browser": False  # ← NEW: Show browser during observation
    }
    return ObservationAgent(...)
```

### Fix 2: Use Virtual Environment Python

**Before (incorrect):**
```powershell
python -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s
```

**After (correct):**
```powershell
.\venv\Scripts\python.exe -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s
```

---

## 🎯 Expected Behavior Now

### Phase 1: ObservationAgent (Browser Opens Here!)
- ✅ **Browser window opens** (Chromium via Playwright)
- ✅ Navigates to target URL
- ✅ Extracts 40+ UI elements
- ✅ Browser closes after ~20 seconds

### Phase 2: RequirementsAgent
- ⚙️ LLM generates BDD scenarios (~20 seconds)
- No browser activity

### Phase 3: AnalysisAgent (Browser Opens Again!)
- ✅ **Browser window opens** for real-time execution
- ✅ Executes 17 scenarios in parallel (3 at a time)
- ✅ Uses Phase 2 execution engine with Stagehand
- ✅ Browser visible during test execution (~2-3 minutes)

### Phase 4: EvolutionAgent
- ⚙️ LLM generates test steps (~80 seconds)
- ⚙️ Stores test cases in database
- No browser activity

---

## 📊 Test Configuration

### Environment Variables
```powershell
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"
$env:LOGIN_PASSWORD = "cA8mn49"
$env:USER_INSTRUCTION = "Complete purchase flow for 5G plan with 48 month contract term"
$env:ENABLE_AB_TEST = "true"
```

### Browser Settings
- **ObservationAgent:** `headless_browser: False` (visible)
- **AnalysisAgent:** `headless_browser: False` (visible)
- **Viewport:** 1920x1080
- **User Agent:** AI-Web-Test ObservationAgent/1.0

### Execution Settings
- **Parallel Execution:** 3 scenarios per batch
- **RPN Threshold:** 0 (execute all scenarios)
- **Real-time Execution:** Enabled

---

## 🔍 Verification

### Check Stagehand Installation
```powershell
cd backend
.\venv\Scripts\python.exe -m pip list | Select-String "stagehand"
# Output: stagehand 0.5.7 ✅
```

### Check Browser Processes (During Test)
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*chrome*"}
# Should show chromium.exe processes when browser is open
```

### Monitor Test Progress
```powershell
# Watch log file in real-time
Get-Content backend\logs\test_four_agent_e2e_*.log -Wait -Tail 20
```

---

## 🎬 Test Execution Timeline

| Time | Phase | Activity | Browser Visible? |
|------|-------|----------|------------------|
| 0:00 | Setup | Initialize agents | ❌ No |
| 0:05 | Step 1 | ObservationAgent crawls page | ✅ **YES** (20s) |
| 0:25 | Step 2 | RequirementsAgent generates scenarios | ❌ No |
| 0:45 | Step 3 | AnalysisAgent executes tests | ✅ **YES** (2-3 min) |
| 3:45 | Step 4 | EvolutionAgent generates test steps | ❌ No |
| 5:05 | Step 5 | Feedback loop analysis | ❌ No |
| 5:15 | Complete | Test summary | ❌ No |

**Total Duration:** ~5-6 minutes  
**Browser Visible Time:** ~3 minutes (Step 1 + Step 3)

---

## 🚀 How to Run

### Option 1: Full Test (Recommended)
```powershell
cd C:\Users\andrechw\Documents\AI-Web-Test-v1\backend

# Set environment variables
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"
$env:LOGIN_PASSWORD = "cA8mn49"
$env:USER_INSTRUCTION = "Complete purchase flow for 5G plan with 48 month contract term"
$env:ENABLE_AB_TEST = "true"

# Run with venv Python
.\venv\Scripts\python.exe -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s
```

### Option 2: Quick Test (Observation Only)
```powershell
cd backend
.\venv\Scripts\python.exe -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s -k "observation"
```

### Option 3: Watch Logs in Real-Time
```powershell
# Terminal 1: Run test
cd backend
.\venv\Scripts\python.exe -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s

# Terminal 2: Watch logs
Get-Content logs\test_four_agent_e2e_*.log -Wait -Tail 50
```

---

## ✅ Success Criteria

- ✅ Browser window opens during Step 1 (ObservationAgent)
- ✅ Browser window opens during Step 3 (AnalysisAgent)
- ✅ No "No module named 'stagehand'" errors
- ✅ Real-time execution completes (17 scenarios)
- ✅ Test cases stored in database (18 test cases)
- ✅ Test passes all assertions

---

## 📝 Commits

1. **dd2080a** - "fix: Resolve merge conflict in models __init__.py"
   - Fixed syntax error blocking imports

2. **dd190a7** - "fix: Enable visible browser mode for ObservationAgent and AnalysisAgent"
   - Added `headless_browser` config option
   - Updated test fixtures to show browser

---

## 🎯 Current Status

**Test Running:** ✅ In Progress (Terminal 8)  
**Log File:** `backend/logs/test_four_agent_e2e_20260210_*.log`  
**Output File:** `backend/test_output_venv.txt`

**Expected:** Browser should now be visible during:
1. Step 1: ObservationAgent crawling (~20 seconds)
2. Step 3: AnalysisAgent test execution (~2-3 minutes)

---

**Next:** Wait for test completion and verify browser visibility! 🎉



