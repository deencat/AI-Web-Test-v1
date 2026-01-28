# Debug Range Selection - User Guide

## Two Navigation Modes Explained

### 🤖 Auto Navigate Mode (Recommended for Most Cases)

**What it does:**
- AI automatically executes prerequisite steps (e.g., steps 1-20 if you want to debug 21-25)
- Sets up the browser to the exact state needed
- Ready to debug immediately after setup completes

**When to use:**
- First time debugging a test
- When you don't have a browser already set up
- When you want convenience over speed

**Cost:**
- Token usage: ~100 tokens per prerequisite step
- Time: ~6 seconds per prerequisite step

**Example:**
```
Want to debug: Steps 21-22
Auto Navigate will:
1. Execute steps 1-20 automatically (~2000 tokens, ~120 seconds)
2. Browser reaches step 20 state
3. You debug steps 21-22 manually with Play/Pause/Next controls
```

---

### 🧭 Manual Navigate Mode (Advanced - Skip Prerequisites)

**What it does:**
- **Assumes you've already navigated the browser manually** to the starting state
- Skips all prerequisite steps
- Uses your existing browser state immediately

**When to use:**
- You've already manually navigated to the desired state
- You want to save tokens and time
- You're debugging repeatedly and already at the right page

**Cost:**
- Token usage: 0 tokens for setup (huge savings!)
- Time: Instant (no setup wait)

**⚠️ CRITICAL: Manual Navigation Requirements**

You MUST manually navigate your browser to the correct state BEFORE starting debug mode:

1. **Open the target website** in your regular browser
2. **Complete all prerequisite actions** manually:
   - Log in if needed
   - Navigate to the correct page
   - Fill in any required fields
   - Reach the exact state where step 21 would start
3. **Keep the browser open**
4. **Then** start Manual Navigate mode in the debug interface

**Example:**
```
Want to debug: Steps 21-22 (upload HKID)

Before starting debug mode, manually:
1. Open https://www.three.com.hk in Chrome
2. Log in with test credentials
3. Navigate through pages until you reach the HKID upload page
4. Make sure you're at the exact state before step 21

Then:
1. In AI Web Test, click Debug on execution
2. Set Start: 21, End: 22
3. Choose "Manual Navigation" mode
4. Click "Start Debugging"
5. System uses YOUR browser state (0 tokens, instant)
6. Debug steps 21-22 with the debug panel controls
```

---

## How to Use Debug Range Selection

### Step 1: Access Debug Dialog

1. Go to **Executions** page
2. Find your test execution (e.g., #298)
3. Click the **🐛 Debug** button
4. Dialog opens with range selection

### Step 2: Configure Range

**Start Step** (required)
- Enter the first step you want to debug
- Example: `21` (if you want to debug from step 21)

**End Step** (optional)
- Enter the last step you want to debug
- Example: `22` (if you only want to debug steps 21-22)
- Leave empty to debug until the end of the test

### Step 3: Choose Navigation Mode

**Option A: Auto Navigate** (Recommended)
- ✅ Select this if you haven't navigated manually
- System executes steps 1-20 automatically
- Shows: "⚡ Uses ~2000 tokens • 120s setup time"

**Option B: Manual Navigation** (Advanced)
- ✅ Select this ONLY if you've already navigated your browser manually
- ⚠️ You MUST be at the correct state before clicking Start
- Shows: "⚡ Uses 0 tokens • Instant start"

### Step 4: Review Preview

The dialog shows what will happen:
```
Auto Navigate Example:
1. AI will execute steps 1-20 (setup)
2. Debug steps 21-22
3. Est. time: 130 seconds

Manual Navigate Example:
1. Manual navigation (skip prerequisites)
2. Debug steps 21-22 immediately  
3. Est. time: 5 seconds
```

### Step 5: Start Debugging

1. Click **"▶️ Start Debugging"** button
2. System creates debug session
3. Browser launches (or uses existing for manual mode)
4. Debug panel shows your steps 21-22
5. Use controls: **Play** (auto-execute), **Pause**, **⏭️ Next Step** (one at a time), **Stop**

---

## Troubleshooting

### Issue: Two Browser Windows Open

**Cause:** You selected Manual Navigate but the system still opened a browser

**Solution:**
Manual Navigate mode currently shares the same browser initialization as Auto mode. The difference is:
- Auto mode: Browser + AI executes prerequisites
- Manual mode: Browser opens + waits for you (skip_prerequisites=true)

**Workaround:**
Use Auto Navigate mode with skip_prerequisites for best results, or manually navigate in the opened browser.

### Issue: Shows "Test Steps (1/0)"

**Cause:** Frontend wasn't fetching actual test steps

**Fixed in this update:**
- Now fetches real steps from execution API
- Displays actual step descriptions
- Filters to your selected range

### Issue: "Please complete 0 setup steps manually"

**Cause:** Manual mode with skip_prerequisites shows confusing message

**Fixed in this update:**
- Message now says: "Using current browser state. Ready to debug step X to Y."

---

## Best Practices

### For First-Time Debugging
✅ Use **Auto Navigate** mode
- Let AI handle setup
- Focus on debugging the failing steps
- Accept the token cost for convenience

### For Repeated Debugging
✅ Use **Manual Navigate** after initial setup
1. Run once with Auto Navigate
2. Browser reaches desired state
3. For next iteration, use Manual Navigate to skip setup
4. Save 2000+ tokens per debug session

### For Long Tests (50+ steps)
✅ Use **Range Selection** to focus
- Don't debug all 50 steps
- Identify failing range (e.g., steps 35-40)
- Debug only that range
- Massive time savings

---

## Common Scenarios

### Scenario 1: Debug Specific Failing Steps

**Goal:** Steps 21-22 are failing in a 37-step test

**Steps:**
1. Debug button → Range Dialog
2. Start: `21`, End: `22`
3. Mode: **Auto Navigate**
4. Start Debugging
5. AI executes steps 1-20 (setup)
6. You debug steps 21-22 with controls

**Result:** Focused debugging, ~20 minutes saved

---

### Scenario 2: Quick Re-Debug After Fix

**Goal:** You fixed step 21, want to verify immediately

**Steps:**
1. Keep browser open from previous debug session
2. Debug button → Range Dialog  
3. Start: `21`, End: `22`
4. Mode: **Manual Navigation** ⚠️
5. Ensure browser is still at step 20 state
6. Start Debugging
7. Debug step 21 immediately (0 tokens, instant)

**Result:** Instant verification, 0 tokens used

---

### Scenario 3: Debug Until End of Test

**Goal:** Debug from step 21 to the end (step 37)

**Steps:**
1. Debug button → Range Dialog
2. Start: `21`
3. End: **(leave empty)**
4. Mode: **Auto Navigate**
5. Start Debugging

**Result:** Debugs steps 21-37

---

## Quick Reference

| Mode | Prerequisites | Tokens | Time | Use When |
|------|--------------|--------|------|----------|
| **Auto Navigate** | AI executes | ~100/step | ~6s/step | First time, convenience |
| **Manual Navigate** | You execute | 0 | Instant | Already navigated, save tokens |

| Range | Example | Result |
|-------|---------|--------|
| **Start only** | Start: 21, End: (empty) | Debug 21 to end |
| **Start + End** | Start: 21, End: 22 | Debug exactly 21-22 |
| **Single step** | Start: 21, End: 21 | Debug only step 21 |

---

## Summary

**Debug Range Selection** gives you:
- ✅ Focus on specific failing steps
- ✅ Choose between AI automation (auto) or manual navigation (save tokens)
- ✅ Clear preview of cost and time
- ✅ Flexible range specification

**Remember:**
- **Auto Navigate** = Convenience (AI does setup)
- **Manual Navigate** = Speed + Savings (you do setup)

Choose based on your needs!
