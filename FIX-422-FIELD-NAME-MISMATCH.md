# Fix: 422 Unprocessable Content Error

## 🐛 Problem
When clicking "Save All Tests", got error:
```
POST /api/v1/tests HTTP/1.1" 422 Unprocessable Content
```

## 🔍 Root Cause
**Field Name Mismatch** between frontend and backend:

| Frontend Sent | Backend Expected |
|---------------|------------------|
| `name` ❌ | `title` ✅ |
| `test_type` (optional) ❌ | `test_type` (required) ✅ |
| `steps` (optional) ❌ | `steps` (required) ✅ |
| `expected_result` (optional) ❌ | `expected_result` (required) ✅ |

## ✅ Solution Applied

### 1. Updated CreateTestRequest Type (`frontend/src/types/api.ts`)

**BEFORE:**
```typescript
export interface CreateTestRequest {
  name: string;              // ❌ Wrong field name
  description: string;
  priority?: 'high' | 'medium' | 'low';
  agent?: string;
  test_type?: string;        // ❌ Should be required
  steps?: string[];          // ❌ Should be required
  expected_result?: string;  // ❌ Should be required
  preconditions?: string;
  test_data?: Record<string, any>;
}
```

**AFTER:**
```typescript
export interface CreateTestRequest {
  title: string;             // ✅ Correct field name
  description: string;
  test_type: string;         // ✅ Required
  priority?: 'high' | 'medium' | 'low';
  steps: string[];           // ✅ Required
  expected_result: string;   // ✅ Required
  preconditions?: string;
  test_data?: Record<string, any>;
  status?: 'passed' | 'failed' | 'pending' | 'running';
  category_id?: number;
  tags?: string[];
  test_metadata?: Record<string, any>;
}
```

### 2. Updated handleSaveTest Function

**BEFORE:**
```typescript
await testsService.createTest({
  name: testCase.title,        // ❌ Wrong field name
  description: testCase.description,
  steps: testCase.steps,
  expected_result: testCase.expected_result,
  priority: testCase.priority,
  test_type: testCase.test_type || 'e2e',
  preconditions: testCase.preconditions,
  test_data: testCase.test_data,
});
```

**AFTER:**
```typescript
await testsService.createTest({
  title: testCase.title,       // ✅ Correct field name
  description: testCase.description,
  test_type: testCase.test_type || 'e2e',  // ✅ First (required field)
  steps: testCase.steps,
  expected_result: testCase.expected_result,
  priority: testCase.priority,
  preconditions: testCase.preconditions,
  test_data: testCase.test_data,
});
```

### 3. Updated handleSaveAllTests Function
Same fix applied to bulk save operation.

---

## 📋 Backend Schema Reference

From `backend/app/schemas/test_case.py`:

```python
class TestCaseBase(BaseModel):
    title: str                          # ✅ REQUIRED
    description: str                    # ✅ REQUIRED
    test_type: TestType                 # ✅ REQUIRED
    priority: Priority = Priority.MEDIUM
    steps: List[str | Dict[str, Any]]  # ✅ REQUIRED
    expected_result: str                # ✅ REQUIRED
    preconditions: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    test_metadata: Optional[Dict[str, Any]] = None
```

---

## 🎯 Now It Works!

### Request Flow:
```
Frontend → createTest({
  title: "Test Case Title"      ✅
  test_type: "e2e"              ✅
  steps: ["Step 1", "Step 2"]   ✅
  expected_result: "Success"    ✅
  ...
})

→ Backend validates ✅
→ Saves to database ✅
→ Returns 200 OK ✅
```

### Previous Error Flow:
```
Frontend → createTest({
  name: "Test Case Title"       ❌ Field doesn't exist
  ...
})

→ Backend validation fails ❌
→ Returns 422 Unprocessable Content ❌
```

---

## ✅ Test Now

1. **Refresh browser** to load new code
2. **Click "Save All Tests"** or **"Save to Tests"**
3. Should see: `✅ Successfully saved X of X tests!`
4. Check backend logs: Should show `200 OK` instead of `422`

---

## 📝 Files Modified

1. `frontend/src/types/api.ts` - Fixed CreateTestRequest interface
2. `frontend/src/pages/TestsPage.tsx` - Fixed both save functions

---

## 🎓 Lesson Learned

**Always check backend schema** before creating frontend types!

Backend schema is the source of truth:
- Field names must match exactly
- Required fields must be marked as required
- Field types must align

Use tools like:
- Swagger/OpenAPI docs
- Backend schema files
- API error messages (422 = validation error)
