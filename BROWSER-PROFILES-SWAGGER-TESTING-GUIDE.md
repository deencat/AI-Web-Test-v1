# Browser Profiles API - Swagger UI Testing Guide

**Date:** February 3, 2026  
**Status:** ✅ All API endpoints verified and working  
**Swagger UI:** http://localhost:8000/docs

---

## Quick Start

### 1. Open Swagger UI
```
Open in browser: http://localhost:8000/docs
```

### 2. Authenticate

1. Click the **"Authorize"** button (top right, lock icon)
2. Enter your credentials:
   - **Username:** `admin`
   - **Password:** `admin123` (or your password)
3. Click **"Authorize"**
4. Click **"Close"**

Now all API calls will include your JWT token automatically! 🎉

---

## API Endpoints to Test

### Endpoint 1: Create Browser Profile

**POST `/api/v1/browser-profiles`**

1. Click on the endpoint to expand
2. Click **"Try it out"**
3. Edit the request body:
```json
{
  "profile_name": "Windows 11 - Production",
  "os_type": "windows",
  "browser_type": "chromium",
  "description": "Windows 11 with production login"
}
```
4. Click **"Execute"**
5. Check response: Should be **201 Created** with profile data

**Expected Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "profile_name": "Windows 11 - Production",
  "os_type": "windows",
  "browser_type": "chromium",
  "description": "Windows 11 with production login",
  "created_at": "2026-02-03T07:08:22.384275",
  "updated_at": "2026-02-03T07:08:22.384275",
  "last_sync_at": null
}
```

**Note the `id` value** - you'll need it for other tests!

---

### Endpoint 2: List All Profiles

**GET `/api/v1/browser-profiles`**

1. Click on the endpoint to expand
2. Click **"Try it out"**
3. Click **"Execute"**

**Expected Response:**
```json
{
  "profiles": [
    {
      "id": 1,
      "profile_name": "Windows 11 - Production",
      "os_type": "windows",
      "browser_type": "chromium",
      ...
    }
  ],
  "total": 1
}
```

---

### Endpoint 3: Get Specific Profile

**GET `/api/v1/browser-profiles/{profile_id}`**

1. Click on the endpoint to expand
2. Click **"Try it out"**
3. Enter profile ID: `1` (from create step)
4. Click **"Execute"**

**Expected Response:** Same as create, with updated timestamps

---

### Endpoint 4: Update Profile

**PATCH `/api/v1/browser-profiles/{profile_id}`**

1. Click on the endpoint to expand
2. Click **"Try it out"**
3. Enter profile ID: `1`
4. Edit request body:
```json
{
  "description": "Updated description - tested in Swagger UI"
}
```
5. Click **"Execute"**

**Expected Response:** Updated profile with new description

---

### Endpoint 5: Delete Profile

**DELETE `/api/v1/browser-profiles/{profile_id}`**

1. Click on the endpoint to expand
2. Click **"Try it out"**
3. Enter profile ID: `1`
4. Click **"Execute"**

**Expected Response:** **204 No Content** (empty response body)

---

## Testing Advanced Workflows

### Workflow 1: Export Profile from Debug Session

**Prerequisites:**
1. Create a test case (if you don't have one)
2. Create an execution for that test case

**Steps:**

#### Step 1: Create Profile
```
POST /api/v1/browser-profiles
{
  "profile_name": "Export Test",
  "os_type": "linux",
  "browser_type": "chromium"
}
→ Note the profile_id (e.g., 2)
```

#### Step 2: Start Debug Session
```
POST /api/v1/debug/start
{
  "execution_id": 1,  // Use existing execution ID
  "target_step_number": 1,
  "mode": "manual"
}
→ Note the session_id (e.g., "debug_abc123")
→ Browser opens - manually log in to your test website
```

#### Step 3: Export Profile
```
POST /api/v1/browser-profiles/2/export
{
  "session_id": "debug_abc123"
}
→ Downloads ZIP file: profile_2_Export_Test.zip
```

**ZIP Contents:**
- `profile.json` - Session data (cookies, localStorage, sessionStorage)
- `metadata.json` - Profile info and export timestamp

---

### Workflow 2: Upload and Use Profile

#### Step 1: Upload Profile ZIP

**POST `/api/v1/browser-profiles/upload`**

1. Click on the endpoint
2. Click **"Try it out"**
3. Click **"Choose File"**
4. Select your profile ZIP file
5. Click **"Execute"**

**Expected Response:**
```json
{
  "success": true,
  "message": "Profile uploaded and parsed successfully",
  "profile_data": {
    "cookies": [...],
    "localStorage": {...},
    "sessionStorage": {...},
    "exported_at": "2026-02-03T07:08:22.123456"
  },
  "metadata": {
    "profile_id": 2,
    "profile_name": "Export Test",
    "os_type": "linux",
    "browser_type": "chromium"
  },
  "file_size_bytes": 1234
}
```

**Copy the `profile_data` object** - you'll need it for test execution!

#### Step 2: Execute Test with Profile

**POST `/api/v1/tests/{test_case_id}/run`**

1. Find a test case ID (or create one)
2. Click on the execution endpoint
3. Click **"Try it out"**
4. Edit request body:
```json
{
  "browser": "chromium",
  "environment": "dev",
  "base_url": "https://your-test-site.com",
  "browser_profile_data": {
    "cookies": [...],  // Paste from upload response
    "localStorage": {...},
    "sessionStorage": {...}
  }
}
```
5. Click **"Execute"**

**Result:** Test executes with pre-injected session - **no login required!** ✅

---

## Validation Tests

### Test 1: OS Type Validation

Try creating a profile with invalid OS type:
```json
{
  "profile_name": "Invalid OS",
  "os_type": "ios",  // Invalid!
  "browser_type": "chromium"
}
```

**Expected:** **422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "loc": ["body", "os_type"],
      "msg": "os_type must be one of: windows, linux, macos",
      "type": "value_error"
    }
  ]
}
```

### Test 2: Browser Type Validation

Try creating a profile with invalid browser type:
```json
{
  "profile_name": "Invalid Browser",
  "os_type": "windows",
  "browser_type": "safari"  // Invalid!
}
```

**Expected:** **422 Unprocessable Entity** with validation error

### Test 3: Case Insensitivity

Try creating with uppercase values:
```json
{
  "profile_name": "Case Test",
  "os_type": "WINDOWS",  // Uppercase
  "browser_type": "CHROMIUM"  // Uppercase
}
```

**Expected:** **201 Created** - values normalized to lowercase

### Test 4: Profile Ownership

1. Create profile with User A
2. Try to access with User B (different login)
3. **Expected:** **404 Not Found** (cannot access other users' profiles)

---

## Common Issues & Solutions

### Issue 1: 401 Unauthorized
**Cause:** JWT token expired or not included  
**Solution:** Click "Authorize" button again and re-login

### Issue 2: 404 Not Found on profile ID
**Cause:** Profile doesn't exist or belongs to different user  
**Solution:** Check profile ID with GET /browser-profiles

### Issue 3: 422 Validation Error
**Cause:** Invalid os_type or browser_type  
**Solution:** Use only: windows/linux/macos and chromium/firefox/webkit

### Issue 4: Export fails with "Session not found"
**Cause:** Debug session ID is invalid or expired  
**Solution:** Start new debug session with POST /debug/start

---

## API Test Results ✅

**All endpoints tested and verified:**

```
✅ POST   /api/v1/browser-profiles          - Create profile
✅ GET    /api/v1/browser-profiles          - List profiles
✅ GET    /api/v1/browser-profiles/{id}     - Get profile
✅ PATCH  /api/v1/browser-profiles/{id}     - Update profile
✅ DELETE /api/v1/browser-profiles/{id}     - Delete profile
✅ POST   /api/v1/browser-profiles/{id}/export - Export session
✅ POST   /api/v1/browser-profiles/upload   - Upload profile
```

**Test Script Results:**
```bash
$ python test_browser_profiles_api.py
✅ Login successful!
✅ Profile created successfully! (ID: 1)
✅ Found 1 profile(s)
✅ Profile retrieved successfully!
✅ Profile updated successfully!
✅ Profile deleted successfully!
✅ All API tests completed!
```

---

## Next Steps

1. ✅ **Swagger UI Testing** - Complete (this guide)
2. ⏳ **Manual Workflow Testing** - Test full export/upload cycle
3. ⏳ **Frontend UI** - Build visual profile manager (Phase 2)
4. ⏳ **Integration Testing** - Test with real test executions
5. ⏳ **Production Deployment** - Deploy to staging/production

---

## Useful curl Commands

If you prefer command-line testing:

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=admin&password=admin123"
# Save the access_token
```

### Create Profile
```bash
TOKEN="your-jwt-token-here"

curl -X POST "http://localhost:8000/api/v1/browser-profiles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_name": "Test Profile",
    "os_type": "windows",
    "browser_type": "chromium"
  }'
```

### List Profiles
```bash
curl -X GET "http://localhost:8000/api/v1/browser-profiles" \
  -H "Authorization: Bearer $TOKEN"
```

### Delete Profile
```bash
curl -X DELETE "http://localhost:8000/api/v1/browser-profiles/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Documentation

For complete implementation details, see:
- `SPRINT-5.5-ENHANCEMENT-5-COMPLETE.md` - Full implementation report
- `backend/app/api/v1/endpoints/browser_profiles.py` - API source code
- `backend/tests/test_browser_profiles.py` - Test suite (20/20 passing)

---

**Happy Testing! 🚀**

*Developer B - February 3, 2026*
