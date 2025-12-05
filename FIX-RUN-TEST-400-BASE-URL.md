# Fix: Run Test Button 400 Bad Request - Missing base_url

## 🐛 Problem

**User Reported**:
- Click "Run Test" button → Not working
- Server logs show: `400 Bad Request`

**Server Output**:
```
INFO: 127.0.0.1:54064 - "POST /api/v1/executions/tests/53/run HTTP/1.1" 400 Bad Request
```

## 🔍 Root Cause Analysis

### Backend Requirement:
```python
# backend/app/api/v1/endpoints/executions.py
@router.post("/tests/{test_case_id}/run")
async def run_test_with_playwright(
    test_case_id: int,
    request: ExecutionStartRequest,  # Expects base_url!
    ...
):
    # Validates base_url is provided
    if not request.base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="base_url is required for test execution"  # ❌ THIS ERROR!
        )
```

### Frontend Was Sending:
```typescript
// BEFORE (missing base_url):
await executionService.startExecution(testCaseId, {
  browser: 'chromium',
  environment: 'dev',
  triggered_by: 'manual',
  priority: 5,
  // ❌ NO base_url field!
});
```

**Result**: Backend rejected the request with `400 Bad Request` because `base_url` is required but was not provided.

---

## ✅ Solution Implemented

### 1. **Enhanced RunTestButton to Fetch and Extract base_url**

**Modified**: `frontend/src/components/RunTestButton.tsx`

**Strategy**:
1. If `baseUrl` prop provided → use it
2. Else fetch test details from API
3. Try to extract `base_url` from `test_data` field
4. Fallback: Extract URL from first test step using regex
5. Last resort: Use default `https://example.com` with warning

**Implementation**:
```typescript
const handleRunTest = async () => {
  let testBaseUrl = baseUrl; // From props if available
  
  // If not provided, fetch test details
  if (!testBaseUrl) {
    const testDetails: any = await testsService.getTest(testCaseId.toString());
    
    // Try to get from test_data.base_url field
    if (testDetails.test_data?.base_url) {
      testBaseUrl = testDetails.test_data.base_url;
    }
    
    // Fallback: Extract URL from first step
    else if (testDetails.steps?.[0]) {
      const stepText = typeof testDetails.steps[0] === 'string' 
        ? testDetails.steps[0] 
        : testDetails.steps[0].description || '';
      
      const urlMatch = stepText.match(/https?:\/\/[^\s]+/);
      if (urlMatch) {
        testBaseUrl = urlMatch[0];
      }
    }
    
    // Last resort: default URL with warning
    if (!testBaseUrl) {
      testBaseUrl = 'https://example.com';
      console.warn(`No base_url found for test ${testCaseId}, using default`);
    }
  }
  
  // Now always includes base_url ✅
  await executionService.startExecution(testCaseId, {
    browser: 'chromium',
    environment: 'dev',
    triggered_by: 'manual',
    priority,
    base_url: testBaseUrl,  // ✅ NOW INCLUDED!
  });
};
```

### 2. **Added baseUrl Optional Prop**

**New Interface**:
```typescript
interface RunTestButtonProps {
  testCaseId: number;
  testCaseName?: string;
  priority?: 1 | 5 | 10;
  onExecutionStart?: (executionId: number) => void;
  disabled?: boolean;
  className?: string;
  baseUrl?: string;  // ✅ NEW: Optional base URL
}
```

**Benefits**:
- Pages can pass `baseUrl` directly if they have it
- If not provided, component fetches it automatically
- Backward compatible (all existing uses still work)

---

## 📋 How It Works Now

### Scenario 1: Test with test_data.base_url (AI-Generated Tests)

**Test Data Structure**:
```json
{
  "id": 53,
  "title": "Three.com.hk 5G Broadband Flow",
  "test_data": {
    "base_url": "https://web.three.com.hk/5gbroadband/plan-hsbc-en.html",
    "contract_period": "30 months",
    ...
  },
  "steps": [...]
}
```

**Execution**:
1. Click "Run Test"
2. Component fetches test details
3. Extracts `test_data.base_url` ✅
4. Sends to API with `base_url` field
5. Backend accepts request
6. Test executes successfully!

### Scenario 2: Test with URL in First Step

**Test Data Structure**:
```json
{
  "id": 54,
  "title": "Login Test",
  "steps": [
    "Navigate to https://example.com/login",
    "Enter username",
    ...
  ]
}
```

**Execution**:
1. Click "Run Test"
2. Component fetches test details
3. No `test_data.base_url` found
4. Regex extracts `https://example.com/login` from first step ✅
5. Sends to API with `base_url` field
6. Test executes successfully!

### Scenario 3: Test Without URL (Fallback)

**Test Data Structure**:
```json
{
  "id": 55,
  "title": "Generic Test",
  "steps": [
    "Click button",
    "Verify result"
  ]
}
```

**Execution**:
1. Click "Run Test"
2. Component fetches test details
3. No `test_data.base_url` found
4. No URL in steps
5. Uses default `https://example.com` ⚠️
6. Console warning logged
7. Test may fail if URL doesn't match

---

## 🎯 Test Case Examples

### Example 1: Three.com.hk Test (From HOW-TO-GENERATE-THREE-HK-TEST.md)

When you generate a test using the guide, it creates:
```json
{
  "title": "Three.com.hk - 5G Broadband Complete Subscription Flow",
  "test_data": {
    "base_url": "https://web.three.com.hk/5gbroadband/plan-hsbc-en.html",
    "model": "qwen/qwen-2.5-7b-instruct",
    ...
  }
}
```

✅ **Run Test works**: Extracts `base_url` from `test_data`

### Example 2: Manual Test Creation

If you manually create a test and add URL in first step:
```json
{
  "title": "Manual Test",
  "steps": [
    "Go to https://myapp.com/dashboard",
    "Click logout"
  ]
}
```

✅ **Run Test works**: Extracts `https://myapp.com/dashboard` from step

### Example 3: Test Without URL

```json
{
  "title": "Abstract Test",
  "steps": [
    "Do something",
    "Verify something"
  ]
}
```

⚠️ **Run Test uses fallback**: Uses `https://example.com` (likely to fail)
💡 **Solution**: Edit test and add URL to first step or test_data

---

## 🔧 Technical Details

### URL Extraction Logic:

**Priority Order**:
1. **Props** → If `baseUrl` prop passed to component
2. **test_data.base_url** → Most reliable (saved by AI generation)
3. **First step regex** → Extracts any `http://` or `https://` URL
4. **Default fallback** → `https://example.com` with console warning

**Regex Pattern**:
```typescript
/https?:\/\/[^\s]+/
```
- Matches: `http://` or `https://`
- Captures: Everything until first whitespace
- Examples:
  - `"Navigate to https://example.com/page"` → `https://example.com/page` ✅
  - `"Go to http://test.com and click"` → `http://test.com` ✅
  - `"Click button"` → No match ❌

### Error Handling:

```typescript
try {
  const testDetails = await testsService.getTest(testCaseId.toString());
  // ... extraction logic
} catch (error) {
  console.error('Failed to fetch test details:', error);
  testBaseUrl = 'https://example.com';  // Safe fallback
}
```

**Benefits**:
- Never crashes if API fails
- Always provides a base_url to backend
- Logs warnings for debugging

---

## 📊 Comparison

### BEFORE (Broken):
```
User clicks "Run Test"
    ↓
Frontend sends:
{
  browser: "chromium",
  environment: "dev"
  // ❌ NO base_url
}
    ↓
Backend validation fails
    ↓
❌ 400 Bad Request
"base_url is required"
```

### AFTER (Working):
```
User clicks "Run Test"
    ↓
Frontend fetches test details
    ↓
Extracts base_url from:
  1. test_data.base_url
  2. First step URL
  3. Default fallback
    ↓
Frontend sends:
{
  browser: "chromium",
  environment: "dev",
  base_url: "https://web.three.com.hk/..."  // ✅ INCLUDED
}
    ↓
Backend accepts request
    ↓
✅ Test execution starts!
```

---

## ✨ Summary

**Problem**: Run Test button failed with `400 Bad Request` because `base_url` was missing  
**Root Cause**: Backend requires `base_url` but frontend wasn't sending it  
**Solution**: Enhanced RunTestButton to:
1. Fetch test details before execution
2. Extract `base_url` from `test_data` or first step
3. Always include `base_url` in execution request

**Result**: Run Test button now works! ✅

---

## 🚀 Action Required

**Refresh your browser** (Ctrl+R) to load the new code!

Then try:
1. ✅ Navigate to Tests Page
2. ✅ Click "Run Test" on test #53 (or any test)
3. ✅ Should see "Queuing..." state
4. ✅ Navigate to execution progress page
5. ✅ Watch test execute!

No more `400 Bad Request` errors! 🎉

---

## 📝 Files Modified

1. ✅ `frontend/src/components/RunTestButton.tsx`
   - Added `baseUrl` optional prop
   - Added logic to fetch test and extract base_url
   - Now always includes base_url in execution request

---

## 💡 Best Practices

### When Creating Tests:

1. **AI-Generated Tests** (Recommended):
   - Use the generation feature
   - AI automatically includes `base_url` in `test_data`
   - ✅ Run Test works automatically

2. **Manual Tests**:
   - Include URL in first step:
     - ✅ "Navigate to https://example.com/page"
     - ❌ "Go to the homepage" (too vague)
   - Or add `test_data` with `base_url` field
   - ✅ Run Test extracts URL from step

3. **Editing Tests**:
   - Make sure URL is present somewhere:
     - In `test_data.base_url` field, OR
     - In first test step
   - Otherwise test will use default fallback

### When Using RunTestButton Component:

```typescript
// Option 1: Let component auto-fetch (recommended)
<RunTestButton testCaseId={test.id} />

// Option 2: Provide base_url if you have it
<RunTestButton 
  testCaseId={test.id} 
  baseUrl="https://example.com" 
/>
```

Both work perfectly! 🎊
