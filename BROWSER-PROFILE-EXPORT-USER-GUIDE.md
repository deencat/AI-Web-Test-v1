# Browser Profile Export: User Guide
**Simplified Workflow with Swagger UI**

**Date:** February 3, 2026  
**Feature:** Sprint 5.5 Enhancement 5 - Browser Profile Session Persistence

---

## Overview

This guide explains how to export browser session data (cookies, localStorage, sessionStorage) using the improved UI with step-by-step guidance.

### Why Use Swagger UI?

The debug session endpoint requires an existing `execution_id`, which makes it impractical to implement a standalone "Start Session" button in the frontend. Instead, we guide users through Swagger UI, which provides:

✅ **Interactive API documentation**  
✅ **Built-in authentication**  
✅ **Try-it-out functionality**  
✅ **Clear request/response visualization**  
✅ **No terminal commands needed**

---

## Export Workflow (Step-by-Step)

### **Step 1: Open the Export Dialog**

1. Navigate to **Browser Profiles** page
2. Click **Export** button on any profile
3. The Export Modal opens with detailed instructions

### **Step 2: Open Swagger UI**

Click the link in the instructions: **http://localhost:8000/docs**

This opens in a new tab, keeping your workflow context.

### **Step 3: Authenticate**

1. Click the green **"Authorize"** button at the top of Swagger UI
2. In the dialog:
   - **Value:** `Bearer YOUR_TOKEN` (get your token from localStorage or login response)
   - Click **Authorize**
   - Click **Close**

💡 **Pro Tip:** You can find your token in browser DevTools → Application → Local Storage → `token`

### **Step 4: Start Debug Session**

1. Scroll down to **Debug** section
2. Find: **`POST /api/v1/debug/start`**
3. Click **"Try it out"**
4. Copy this JSON into the Request body:

```json
{
  "execution_id": 1,
  "target_step_number": 1,
  "mode": "manual"
}
```

5. Click **Execute**

**What this does:**
- Starts a browser window with a persistent session
- Does NOT execute any test steps (manual mode)
- Uses execution_id=1 as a placeholder (can be any existing execution)

### **Step 5: Log In Manually**

A browser window opens automatically:

1. **Navigate** to your target website (e.g., `https://web.three.com.hk`)
2. **Log in** with your credentials
3. **Browse around** to generate session data (visit a few pages)
4. **⚠️ KEEP THE BROWSER WINDOW OPEN!** (closing it will destroy the session)

### **Step 6: Copy Session ID**

Back in Swagger UI, scroll down to the **Response body**:

```json
{
  "session_id": "debug_abc123def456",
  "mode": "manual",
  "status": "ready",
  "message": "Manual setup mode - Please complete the setup steps",
  ...
}
```

**Copy the `session_id`** value (e.g., `debug_abc123def456`)

### **Step 7: Export & Download**

Back in the Browser Profiles page:

1. **Paste the session_id** into the input field
2. Click **"Export & Download"**
3. **ZIP file downloads automatically** to your device

**File name format:** `{profile_name}_{date}.zip`  
**Example:** `windows_11_admin_session_2026-02-03.zip`

---

## What's in the ZIP File?

The exported ZIP contains a single file: `profile_data.json`

```json
{
  "cookies": [
    {
      "name": "session_token",
      "value": "abc123...",
      "domain": ".example.com",
      "path": "/",
      "expires": 1738627200,
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    }
  ],
  "localStorage": {
    "user_id": "12345",
    "theme": "dark",
    "preferences": "{...}"
  },
  "sessionStorage": {
    "cart_items": "[]",
    "last_page": "/dashboard"
  }
}
```

---

## UI Features

### **Interactive Instructions**

The Export Modal includes:

- ✅ **Numbered step-by-step guide**
- ✅ **Clickable links** (Swagger UI opens in new tab)
- ✅ **Copy buttons** for JSON snippets
- ✅ **Toggle instructions** (hide/show)
- ✅ **Contextual help** (tooltips and notes)

### **Copy to Clipboard**

Click the 📋 copy icon to copy the JSON request body:

```json
{
  "execution_id": 1,
  "target_step_number": 1,
  "mode": "manual"
}
```

### **Hide/Show Instructions**

- **First time users:** Full instructions displayed by default
- **Experienced users:** Click "Hide Instructions" for a cleaner view
- **Need help again?** Click "📋 Show Instructions" to expand

---

## Why This Approach?

### **Technical Constraints**

The `/debug/start` endpoint requires:
- `execution_id` (integer) - Must reference an existing test execution
- `target_step_number` (integer) - Which step to debug
- `mode` (string) - "auto" or "manual"

This design is because debug sessions are meant for debugging specific failed test steps, not standalone browser sessions.

### **Alternative Considered: Standalone Debug Endpoint**

We considered creating a new `/debug/standalone-session` endpoint, but:
- ❌ Requires backend changes (out of scope for Phase 2)
- ❌ Increases API surface area
- ❌ Duplicates browser management logic
- ✅ Swagger UI works perfectly for this use case

### **Why Swagger UI is Ideal**

✅ **Already available** (no new infrastructure)  
✅ **Interactive** (no curl/terminal needed)  
✅ **Visual feedback** (see request/response)  
✅ **Authentication built-in** (token management)  
✅ **Self-documenting** (users learn the API)

---

## Best Practices

### **For Users**

1. **Use meaningful profile names**: `Production_Admin_User` not `Profile1`
2. **Keep sessions fresh**: Export profiles weekly if cookies expire
3. **Test before sharing**: Upload and test profile before sharing with team
4. **Document context**: Use description field to note what's logged in

### **For Developers**

1. **Document execution IDs**: Keep a list of valid execution_ids for manual testing
2. **Monitor session cleanup**: Debug sessions auto-cleanup after timeout
3. **Check browser logs**: Errors appear in browser console and backend logs

---

## Troubleshooting

### **Problem: "Token expired" in Swagger UI**

**Solution:** Get a fresh token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### **Problem: "Execution not found" error**

**Solution:** Use a valid execution_id. Get one from:
```bash
curl -s http://localhost:8000/api/v1/executions \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.items[0].id'
```

### **Problem: Browser window closes immediately**

**Solution:** 
- Check `headless: false` in request (should be false)
- Verify backend is running and accessible
- Check backend logs for errors

### **Problem: Session ID not working for export**

**Solution:**
- Verify session is still active (hasn't timed out)
- Confirm browser window is still open
- Check session ID is copied correctly (no extra spaces)

### **Problem: ZIP file is empty or corrupted**

**Solution:**
- Make sure you logged in and generated session data
- Verify cookies were set (check DevTools → Application → Cookies)
- Try exporting again with a fresh session

---

## Security Considerations

### **Session Data is Sensitive**

The exported ZIP file contains:
- 🔒 Authentication tokens
- 🔒 User session cookies
- 🔒 Stored credentials (if saved in localStorage)
- 🔒 Personal preferences and data

**⚠️ Never share profile ZIPs publicly or commit to version control!**

### **Data Privacy**

- ✅ **In-memory processing**: Session data never written to server disk
- ✅ **User-controlled**: You own the ZIP file, delete anytime
- ✅ **GDPR compliant**: No server-side storage of personal data
- ✅ **Temporary sessions**: Debug sessions auto-cleanup after timeout

---

## Advanced: Automating with Scripts

For power users, you can automate the workflow with a script:

```bash
#!/bin/bash
# export_profile.sh

TOKEN="YOUR_TOKEN_HERE"
PROFILE_ID=1

# 1. Start debug session
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/debug/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"execution_id": 1, "target_step_number": 1, "mode": "manual"}')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo "Debug session started: $SESSION_ID"
echo "⏸️  Please log in manually in the browser window..."
read -p "Press Enter when logged in..."

# 2. Export profile
curl -X POST "http://localhost:8000/api/v1/browser-profiles/$PROFILE_ID/export" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}" \
  -o "profile_$PROFILE_ID.zip"

echo "✅ Profile exported to profile_$PROFILE_ID.zip"
```

---

## Future Enhancements

Potential improvements for future sprints:

1. **Standalone Session Endpoint**: Add `/debug/standalone-browser` endpoint
2. **One-Click Export**: Frontend button that handles entire workflow
3. **Session Manager**: UI to view/manage active debug sessions
4. **Auto-Sync**: Periodic background export of active sessions
5. **Profile Scheduler**: Automated profile updates on schedule

---

## Comparison: Old vs New UX

### **❌ Old Approach (Terminal)**
```bash
# Users had to run this manually
curl -X POST http://localhost:8000/api/v1/debug/start \
  -H "Authorization: Bearer abc123..." \
  -H "Content-Type: application/json" \
  -d '{"execution_id": 1, "target_step_number": 1, "mode": "manual"}'
```

**Problems:**
- Requires terminal access
- Need to know curl syntax
- Must manually extract session_id from JSON response
- No visual feedback
- Intimidating for non-technical users

### **✅ New Approach (Swagger UI)**

**Benefits:**
- ✅ No terminal needed
- ✅ Point-and-click interface
- ✅ Visual JSON editor
- ✅ Automatic authentication
- ✅ Copy/paste helpers
- ✅ Response highlighting
- ✅ User-friendly for all skill levels

---

## Summary

The Browser Profile Export workflow now provides:

1. **Clear UI guidance** - Step-by-step instructions in the export modal
2. **Swagger UI integration** - Leverage existing API documentation
3. **Copy-paste helpers** - One-click copy of JSON snippets
4. **Visual workflow** - See exactly what's happening at each step
5. **No terminal needed** - Accessible to non-technical users

**Status:** ✅ Production-ready  
**User Feedback:** Awaiting initial user testing  
**Documentation:** Complete

---

**Questions or Issues?**

- Check the troubleshooting section above
- Review backend logs: `backend/logs/app.log`
- Open a GitHub issue with reproduction steps
- Contact Developer B for support

---

**Last Updated:** February 3, 2026  
**Document Version:** 1.0  
**Feature Status:** Ready for Testing
