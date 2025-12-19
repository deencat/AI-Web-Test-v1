# Tests Page - Saving Generated Tests Guide

## 🎯 How Test Saving Works

### Generated Tests (Temporary)
- When you click "Generate Test Cases", the AI creates test cases
- These are stored **temporarily in your browser** (localStorage)
- ⚠️ **NOT YET SAVED TO DATABASE**
- Will persist across page refreshes
- Will be lost if you clear browser data

### Saved Tests (Permanent)
- Tests saved to the database
- Accessible from "Saved Tests" section
- Can be run, edited, deleted
- Persist permanently

---

## 💾 How to Save Tests

### Option 1: Save Individual Test
1. Generate test cases
2. Review each generated test
3. Click **"Save to Tests"** button on the test you want
4. Test is saved to database
5. Test is removed from "Generated" list

### Option 2: Save All Tests
1. Generate test cases
2. Review all tests
3. Click **"Save All Tests"** button at the bottom
4. All tests are saved to database at once
5. You're redirected to "Saved Tests" view

---

## 🔄 Workflow Example

```
Step 1: Generate Tests
┌─────────────────────────────────────┐
│ Describe test you want to create:  │
│ ┌─────────────────────────────────┐ │
│ │ Test Three.com.hk 5G Broadband │ │
│ │ subscription flow...            │ │
│ └─────────────────────────────────┘ │
│ [ ✨ Generate Test Cases ]          │
└─────────────────────────────────────┘
                ↓
Step 2: Review Generated Tests (Temporary - in browser)
┌─────────────────────────────────────────────────────┐
│ ℹ️ Generated tests are temporarily saved           │
│    Click "Save to Tests" to save permanently        │
├─────────────────────────────────────────────────────┤
│ Generated Test Cases (5)                            │
│                                                     │
│ 📋 Test Case 1: Login Flow                         │
│ [ Edit ] [ Save to Tests ] [ Delete ]              │
│                                                     │
│ 📋 Test Case 2: Plan Selection                     │
│ [ Edit ] [ Save to Tests ] [ Delete ]              │
│                                                     │
│ ... (3 more tests)                                 │
│                                                     │
│ [ Save All Tests ] [ Generate More Tests ]         │
└─────────────────────────────────────────────────────┘
                ↓ (Click "Save All Tests")
Step 3: Tests Saved to Database
┌─────────────────────────────────────────────────────┐
│ ✅ Successfully saved 5 of 5 tests!                 │
│                                                     │
│ Saved Tests                                         │
│ Filters: [ All ] [ Passed ] [ Failed ] [ Pending ] │
│                                                     │
│ 📋 Test Case 1: Login Flow                         │
│ Status: Pending | Priority: High                   │
│ [ Run Test ] [ Edit ] [ Delete ]                   │
│                                                     │
│ 📋 Test Case 2: Plan Selection                     │
│ Status: Pending | Priority: Medium                 │
│ [ Run Test ] [ Edit ] [ Delete ]                   │
│                                                     │
│ ... (3 more saved tests)                           │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 What Happens When You Refresh?

### Before Saving to Database:
```
Page Refresh → Generated tests STILL THERE ✅
(Stored in browser localStorage)

BUT:
Clear Browser Data → Generated tests LOST ❌
Close Browser → Generated tests STILL THERE ✅
Switch Computer → Generated tests LOST ❌
```

### After Saving to Database:
```
Page Refresh → Saved tests STILL THERE ✅
Clear Browser Data → Saved tests STILL THERE ✅
Close Browser → Saved tests STILL THERE ✅
Switch Computer → Saved tests STILL THERE ✅
(Stored in database permanently)
```

---

## 📝 Quick Reference

| Action | Location | Persistence | Lost On |
|--------|----------|-------------|---------|
| Generate Tests | Tests Page → Generate | Browser localStorage | Clear browser data |
| Save to Tests (Individual) | Click button on test card | Database (permanent) | Never |
| Save All Tests | Click button at bottom | Database (permanent) | Never |
| Run Test | Saved Tests section | Results in database | Never |

---

## ⚠️ Important Notes

### 1. Generated Tests Are Not Saved Automatically
- You MUST click "Save to Tests" or "Save All Tests"
- Until saved, tests only exist in your browser
- An info banner reminds you to save

### 2. Editing Generated Tests
- You can edit generated tests before saving
- Click "Edit" on any test card
- Changes are saved to localStorage temporarily
- Click "Save to Tests" to make them permanent

### 3. Refreshing the Page
- Generated tests persist across refresh (thanks to localStorage)
- You'll see them again when you return to the page
- But still need to save them to database for permanent storage

### 4. Running Tests
- You can only run tests that are saved to the database
- Generated tests must be saved first
- "Run Test" button appears on saved tests

---

## 🎯 Best Practices

### ✅ DO:
1. **Review before saving** - Edit tests if needed
2. **Save promptly** - Don't rely on localStorage long-term
3. **Use "Save All"** - Faster for multiple tests
4. **Check Saved Tests** - Verify tests are in database

### ❌ DON'T:
1. **Don't clear browser data** - Without saving first
2. **Don't leave tests unsaved** - For extended periods
3. **Don't assume they're saved** - Always click Save button
4. **Don't skip review** - AI might need corrections

---

## 🚀 Example Workflow

### Scenario: Generate and Save Three.com.hk Test

1. **Open Tests Page**
   ```
   http://localhost:5173/tests
   ```

2. **Paste Requirement**
   ```
   Test the Three.com.hk 5G Broadband subscription flow...
   (See HOW-TO-GENERATE-THREE-HK-TEST.md for full text)
   ```

3. **Click "Generate Test Cases"**
   - Wait 3-5 seconds
   - AI generates 5 test cases

4. **Review Generated Tests**
   - Check test titles
   - Review steps
   - Edit if needed

5. **Save All Tests**
   - Click "Save All Tests" button
   - See success message: "✅ Successfully saved 5 of 5 tests!"
   - Redirected to Saved Tests view

6. **Run Your Test**
   - Find test in Saved Tests list
   - Click "Run Test"
   - Navigate to Executions to see results

---

## 🐛 Troubleshooting

### Problem: Generated tests disappeared after refresh
**Solution**: They should still be there (localStorage). If not:
- Check if you cleared browser data
- Check browser console for errors
- Try generating again

### Problem: "Save to Tests" button not working
**Solution**: 
- Check backend is running (http://localhost:8000)
- Check browser console for errors
- Verify you're logged in

### Problem: Tests saved but not appearing in Saved Tests
**Solution**:
- Refresh the page
- Check filter (All/Passed/Failed/Pending)
- Check backend logs for errors

### Problem: Want to discard generated tests
**Solution**:
- Click "Delete" on each test, OR
- Click "Generate New Tests" to clear all, OR
- Refresh page and click "Generate New Tests"

---

## 📊 Feature Summary

| Feature | Status | Location |
|---------|--------|----------|
| Generate Tests | ✅ Working | Tests Page → Generate section |
| localStorage Persistence | ✅ Working | Automatic |
| Save Individual Test | ✅ Working | Test card → "Save to Tests" |
| Save All Tests | ✅ Working | Bottom button |
| Edit Before Save | ✅ Working | Test card → "Edit" |
| Info Banner | ✅ Working | Above generated tests |
| Refresh Persistence | ✅ Working | Automatic |
| Database Storage | ✅ Working | After "Save" clicked |

---

## 🎓 Key Takeaways

1. **Generated ≠ Saved**
   - Generated tests are temporary (browser)
   - Saved tests are permanent (database)

2. **Always Click Save**
   - "Save to Tests" for individual
   - "Save All Tests" for bulk

3. **LocalStorage = Safety Net**
   - Survives page refresh
   - Doesn't replace database save

4. **Review Before Save**
   - AI is smart but not perfect
   - Edit if needed

5. **Saved Tests = Runnable**
   - Only saved tests can be executed
   - Check "Saved Tests" section

---

Need help? Check:
- `HOW-TO-GENERATE-THREE-HK-TEST.md` - Example test generation
- `TESTS-PAGE-UI-TESTING-GUIDE.md` - Detailed UI testing guide
- `AI-TEST-GENERATION-PIPELINE.md` - Technical documentation
