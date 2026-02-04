# Sprint 5.5 Enhancement 5: Frontend Testing Guide
**Browser Profile Session Persistence - Frontend UI Implementation**

**Date:** February 3, 2026  
**Status:** Ready for Testing  
**Phase:** Phase 2 - Frontend UI Complete

---

## Overview

This guide provides step-by-step instructions to test the newly implemented Browser Profile Session Persistence frontend UI.

### What's New
- **Browser Profiles Page**: Full CRUD UI for managing profile metadata
- **One-Click Browser Session**: Start browser directly from UI (no API knowledge needed!)
- **Profile Export Wizard**: Download session data (cookies, localStorage, sessionStorage) as ZIP
- **Profile Upload Integration**: Upload profiles during test execution
- **Navigation**: New "Browser Profiles" menu item in sidebar
- **Swagger UI Alternative**: Advanced option for power users

---

## Prerequisites

### Backend Requirements
✅ Backend server running on `http://localhost:8000`  
✅ Database migration executed (`python migrations/add_browser_profiles_table.py`)  
✅ User account created (login credentials)  
✅ All 20 backend tests passing

### Frontend Requirements
✅ Frontend dev server running (`npm run dev`)  
✅ TypeScript types created (`src/types/browserProfile.ts`)  
✅ Service layer implemented (`src/services/browserProfileService.ts`)  
✅ BrowserProfilesPage component created  
✅ Routing and navigation configured

---

## Testing Workflow

### **Phase 1: Profile Management (CRUD Operations)**

#### **Step 1.1: Navigate to Browser Profiles**
1. Login to the application
2. Click "Browser Profiles" in the sidebar (between Knowledge Base and Settings)
3. **Expected**: Browser Profiles page loads with empty state message

#### **Step 1.2: Create Profile**
1. Click "Create Profile" button
2. Fill in the form:
   - **Profile Name**: `Windows 11 - Admin Session`
   - **Operating System**: `🪟 Windows`
   - **Browser Type**: `🌐 Chromium`
   - **Description**: `Admin user logged into production environment`
3. Click "Create Profile"
4. **Expected**: 
   - Modal closes
   - Profile appears in the list with OS/browser icons
   - Shows creation date and "Last Sync: Never"

#### **Step 1.3: Create Multiple Profiles**
Create 2 more profiles:
- **Profile 2**: `Linux - Dev Environment` (🐧 Linux, 🦊 Firefox)
- **Profile 3**: `macOS - QA User` (🍎 macOS, 🧭 Webkit)

**Expected**: All 3 profiles displayed in grid layout

#### **Step 1.4: Edit Profile**
1. Click "Edit" button on first profile
2. Change description to: `Admin user with elevated permissions`
3. Click "Update Profile"
4. **Expected**: Profile card updates with new description

#### **Step 1.5: Delete Profile**
1. Click trash icon on third profile (`macOS - QA User`)
2. Confirm deletion in dialog
3. **Expected**: Profile removed from list, count updates to 2

---

### **Phase 2: Profile Export (Session Capture)**

#### **Step 2.1: Start Export Workflow**
1. Back in the UI, click "Export" button on `Windows 11 - Admin Session` profile
2. **Export Modal opens** with two options:
   - **🚀 Quick Start (Recommended)**: One-click browser session
   - **📋 Alternative: Use Swagger UI**: For advanced users

#### **Step 2.2: Start Browser Session (Recommended Method)**
1. Click the green **"Start Browser Session"** button
2. **Expected**:
   - Button shows "Starting Browser..."
   - A browser window opens automatically
   - Alert displays: "✅ Browser started successfully!"
   - Session ID auto-fills in the green box (e.g., `standalone_abc123def456`)

#### **Step 2.3: Manual Login**
1. In the opened browser window:
   - Navigate to your target website (e.g., `https://web.three.com.hk`)
   - **Manually log in** with your credentials
   - Browse a few pages to generate session data
   - **⚠️ KEEP THE BROWSER WINDOW OPEN!** (do NOT close it)

#### **Step 2.4: Export Profile**
1. Back in the Export Modal (browser profile page)
2. **Verify Session ID is filled** (should be auto-filled from Step 2.2)
   - ⚠️ If session ID is empty, go back to Step 2.2 and click "Start Browser Session" first
   - Session ID format: `standalone_abc123def456`
3. Click **"Export & Download"** button
4. **Expected**:
   - Loading indicator shows "Exporting..."
   - ZIP file downloads: `windows_11_admin_session_2026-02-03.zip`
   - Profile's "Last Sync" timestamp updates
   - Modal closes automatically

#### **Step 2.5: Verify ZIP Contents**
1. Extract the downloaded ZIP file
2. **Expected structure**:
   ```
   profile_data.json
     {
       "cookies": [...],
       "localStorage": {...},
       "sessionStorage": {...}
     }
   ```
3. Verify cookies array contains authentication tokens
4. Verify localStorage/sessionStorage contain session data

---

### **Phase 3: Profile Upload (Test Execution Integration)**

#### **Step 3.1: Navigate to Tests Page**
1. Click "Tests" in the sidebar
2. Select any test case from the list
3. Click the "Run Test" button

#### **Step 3.2: Upload Profile During Execution**
1. **Profile Upload Dialog** opens (new feature!)
2. You'll see two options:
   - **Run with Profile**: Upload ZIP and include session data
   - **Run without Profile**: Standard execution (no pre-auth)
3. Click "Browse Files" or drag & drop the ZIP from Phase 2
4. **Expected**: File name and size display (e.g., `windows_11_admin_session_2026-02-03.zip - 3.45 KB`)
5. (Optional) Enable **HTTP Basic Auth**:
   - Check **"Use HTTP Basic Auth"**
   - Enter username and password
   - Use this when the environment prompts for Basic Auth before the login page

#### **Step 3.3: Execute Test with Profile**
1. Click "Run with Profile" button
2. **Expected**:
   - Button shows "Uploading Profile..."
   - Then "Queuing..."
   - Dialog closes
   - Test execution starts
   - Console logs show: `"Test will run with browser profile session data"`

#### **Step 3.4: Verify Session Persistence**
1. Navigate to "Executions" page
2. Find the execution you just started
3. Click to view execution details
4. **Expected behavior**:
   - Test should **skip login steps** (already authenticated via profile)
   - Session cookies/localStorage from profile are active
   - Test continues from authenticated state

---

### **Phase 4: Profile Upload Modal (Alternative Workflow)**

#### **Step 4.1: Upload Profile Without Execution**
1. Go to Browser Profiles page
2. Click "Upload Profile" button
3. Select the exported ZIP file
4. Click "Upload Profile"
5. **Expected**:
   - Alert shows: `Profile uploaded successfully! X cookies, Y localStorage items.`
   - Modal closes
   - Profile data is now available for use (though not saved as a profile record)

---

## Test Scenarios

### **Scenario 1: Multi-Platform Testing**
**Purpose**: Verify platform-specific profiles work correctly

1. Create profiles for all 3 OS types:
   - 🪟 Windows + 🌐 Chromium
   - 🐧 Linux + 🦊 Firefox  
   - 🍎 macOS + 🧭 Webkit
2. Export session data from each platform
3. Upload during test execution on corresponding platform
4. **Expected**: Session data matches platform requirements

### **Scenario 2: Large Profile Data**
**Purpose**: Test performance with large session data

1. Log into a complex application with:
   - 50+ cookies
   - Large localStorage objects (>100 keys)
   - Multiple domains
2. Export profile
3. Verify ZIP file size (should be <1MB compressed)
4. Upload and execute test
5. **Expected**: No performance degradation

### **Scenario 3: Profile Expiration**
**Purpose**: Verify expired sessions are handled

1. Export a profile
2. Wait for cookies to expire (or manually expire them)
3. Upload expired profile during execution
4. **Expected**: Test should detect expired session and handle gracefully

### **Scenario 4: Concurrent Execution with Profiles**
**Purpose**: Test multiple simultaneous executions with different profiles

1. Create 3 different profiles (different users/roles)
2. Queue 3 test executions simultaneously, each with a different profile
3. **Expected**: All tests run in isolation with correct session data

---

## UI/UX Validation

### **NEW: One-Click Export Feature** ⭐
The Export Modal now features:
- ✅ **Green "Start Browser Session" button** - Primary action, no API knowledge needed
- ✅ **Auto-fill session ID** - Session ID automatically populated after browser starts
- ✅ **Visual session indicator** - Green box displays active session ID
- ✅ **Loading states** - Clear "Starting Browser..." and "Exporting..." indicators
- ✅ **Smart browser launch** - Chromium opens automatically with persistent session
- ✅ **Collapsible Swagger UI instructions** - Alternative method for advanced users

### **Visual Checks**
- ✅ Profile cards display OS/browser icons correctly
- ✅ Modals are properly centered and responsive
- ✅ Loading states show appropriate spinners/indicators
- ✅ Dark mode support works for all components
- ✅ Drag & drop zone highlights on hover
- ✅ File upload shows filename and size

### **Interaction Checks**
- ✅ All buttons respond to clicks
- ✅ Forms validate required fields
- ✅ Error messages display clearly
- ✅ Success messages appear and dismiss
- ✅ Modals close on Cancel/ESC
- ✅ Refresh button reloads profile list

### **Data Consistency**
- ✅ Profile list updates after CRUD operations
- ✅ Last Sync timestamp updates after export
- ✅ Profile count matches displayed profiles
- ✅ Search/filter works (if implemented)

---

## Error Handling Tests

### **Test 1: Network Errors**
1. Stop the backend server
2. Try to create a profile
3. **Expected**: Clear error message: "Failed to create profile: Network Error"

### **Test 2: Invalid File Upload**
1. Try uploading a non-ZIP file
2. **Expected**: File input should reject (accept=".zip")

### **Test 3: Missing Session ID**
1. Try to export profile without entering session ID
2. **Expected**: Form validation prevents submission

### **Test 4: Invalid Session ID**
1. Enter a non-existent session ID for export
2. **Expected**: Error message: "Failed to export profile: Session not found"

### **Test 5: Unauthorized Access**
1. Logout
2. Try to access `/browser-profiles` directly
3. **Expected**: Redirect to login page

---

## API Integration Verification

### **Check Browser Network Tab**

#### **Create Profile**
```
Request: POST /api/v1/browser-profiles
Response: 201 Created
Body: { "id": 1, "profile_name": "Windows 11 - Admin Session", ... }
```

#### **List Profiles**
```
Request: GET /api/v1/browser-profiles
Response: 200 OK
Body: { "profiles": [...], "total": 3 }
```

#### **Export Profile**
```
Request: POST /api/v1/browser-profiles/1/export
Body: { "session_id": "standalone_abc123" }
Response: 200 OK (application/zip)
Headers: Content-Disposition: attachment; filename="windows_11_admin_session_2026-02-03.zip"
```

#### **Start Standalone Browser** ⭐ NEW!
```
Request: POST /api/v1/debug/standalone-browser?browser=chromium&headless=false
Response: 201 Created
Body: {
  "session_id": "standalone_abc123def456",
  "mode": "manual",
  "status": "ready",
  "message": "Standalone browser session started! Navigate to your website and log in manually..."
}
```

#### **Upload Profile**
```
Request: POST /api/v1/browser-profiles/upload
Body: FormData with file
Response: 200 OK
Body: { "profile_data": { "cookies": [...], ... } }
```

#### **Execute with Profile**
```
Request: POST /api/v1/executions/tests/123/run
Body: {
  "browser": "chromium",
  "environment": "dev",
  "browser_profile_data": { "cookies": [...], ... }
}
Response: 201 Created
Body: { "id": 456, "status": "pending", ... }
```

---

## Performance Metrics

### **Target Metrics**
- ✅ Profile list loads in <500ms
- ✅ Create/edit profile completes in <300ms
- ✅ Export profile (small data) completes in <2s
- ✅ Upload profile (1MB ZIP) completes in <3s
- ✅ Page renders without layout shifts
- ✅ Modal animations are smooth (60fps)

### **Measurement Tools**
- Use Chrome DevTools → Network tab
- Use Chrome DevTools → Performance tab
- Monitor backend logs for API response times

---

## Known Limitations & Future Enhancements

### **Current Limitations**
1. **No bulk operations**: Can't delete multiple profiles at once
2. **No search/filter**: Profile list is unfiltered (will add in future sprint)
3. **No profile preview**: Can't view profile contents before upload
4. **No profile versioning**: Can't store multiple versions of same profile

### **Planned Enhancements**
1. **Profile Templates**: Pre-configured profiles for common scenarios
2. **Profile Sharing**: Export/import profiles between team members
3. **Profile Diff**: Compare two profiles side-by-side
4. **Auto-Sync**: Periodic background sync of active sessions
5. **Profile Analytics**: Track usage statistics per profile
6. **Browser Selection UI**: Choose browser type (chromium/firefox/webkit) in UI instead of default

---

## Troubleshooting

### **Issue: Profile list is empty after creation**
**Solution**: Check browser console for API errors. Verify backend is running and accessible.

### **Issue: Export button does nothing**
**Solution**: 
1. Try using the "Start Browser Session" button instead
2. If browser doesn't open, check backend is running
3. Verify session_id appears in the green box after clicking
4. Check browser console for JavaScript errors
5. Check backend logs for endpoint errors

### **Issue: "Start Browser Session" button fails**
**Solution**:
1. Verify backend is running on http://localhost:8000
2. Check authentication token is valid (not expired)
3. Look for errors in browser console (F12 → Console)
4. Check backend logs for `/debug/standalone-browser` errors
5. Try refreshing the page and logging in again

### **Issue: Session ID is not filled after login**
**Solution**: 
⚠️ **Important**: Session ID auto-fills IMMEDIATELY after clicking "Start Browser Session" button, NOT after performing login.

**Correct workflow:**
1. Click "Start Browser Session" button → Session ID auto-fills instantly
2. Use the opened browser window to log in → Session ID remains filled
3. Click "Export & Download" → Uses the auto-filled session ID

**If session ID is missing:**
1. Check if you clicked "Start Browser Session" button first (green button)
2. Session ID should appear in green box below the button within 2-3 seconds
3. If browser opened but no session ID shown, check browser console for errors
4. Try closing browser and clicking "Start Browser Session" again

### **Issue: Upload fails with "Invalid ZIP"**
**Solution**: 
1. Re-export profile (may be corrupted)
2. Verify ZIP contains `profile_data.json`
3. Check file size (should be <10MB)

### **Issue: Test still prompts for login despite profile**
**Solution**: 
1. Verify cookies domain matches test URL
2. Check cookie expiration dates
3. Ensure localStorage keys are correct
4. Re-export profile with fresh login

---

## Success Criteria

### **Phase 2 Frontend Implementation Complete When:**
- ✅ All UI components render without errors
- ✅ All CRUD operations work end-to-end
- ✅ Profile export downloads valid ZIP files
- ✅ Profile upload integrates with test execution
- ✅ Navigation works across all pages
- ✅ Error handling covers all edge cases
- ✅ UI/UX follows existing design patterns
- ✅ No console errors or warnings
- ✅ All TypeScript types are correct
- ✅ Dark mode works throughout

### **Enhancement 5 Fully Complete When:**
- ✅ Backend API: 7 endpoints functional (✅ Done)
- ✅ Backend Tests: 20/20 passing (✅ Done)
- ✅ Frontend UI: All components working (🔄 Ready for Testing)
- ✅ End-to-End: Full workflow verified (⏳ Next Step)
- ✅ Documentation: Complete user guide (✅ This document)

---

## Next Steps

1. **Start Frontend Dev Server**:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Execute Testing Workflow**: Follow all phases above

3. **Report Issues**: Document any bugs or unexpected behavior

4. **Iterate**: Fix issues and re-test until all criteria met

5. **Final Commit**: Once testing passes, commit all frontend changes

6. **Sprint Complete**: Mark Sprint 5.5 Enhancement 5 as DONE

---

## Resources

### **Documentation**
- Backend Implementation: `SPRINT-5.5-ENHANCEMENT-5-COMPLETE.md`
- API Testing Guide: `BROWSER-PROFILES-SWAGGER-TESTING-GUIDE.md`
- Frontend Types: `frontend/src/types/browserProfile.ts`
- Service Layer: `frontend/src/services/browserProfileService.ts`

### **Code Files**
- Main UI: `frontend/src/pages/BrowserProfilesPage.tsx` (620 lines)
- Run Button: `frontend/src/components/RunTestButton.tsx` (updated)
- Routing: `frontend/src/App.tsx` (route added)
- Navigation: `frontend/src/components/layout/Sidebar.tsx` (menu item added)

### **API Endpoints**
- Base URL: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- Test Script: `test_browser_profiles_api.py`

---

**Happy Testing! 🚀**

*If you encounter any issues, refer to the Troubleshooting section or check backend logs.*
