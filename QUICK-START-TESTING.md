# Quick Start - Testing Feedback Data Sync Feature

## 🚀 You Are Here
Both servers are running:
- ✅ Backend: http://localhost:8000
- ✅ Frontend: http://localhost:3000 (or your dev server port)

## 🎯 Quick Test (2 Minutes)

### Step 1: Navigate to Settings
```
1. Open browser: http://localhost:3000
2. Login if needed (admin / admin123)
3. Click "Settings" in navigation
4. Scroll to "Team Collaboration" section
```

### Step 2: Test Export
```
1. Click "Export to JSON" button
2. Wait for file to download
3. Check your Downloads folder for: feedback-export-YYYY-MM-DD.json
4. Verify green success message appears
```

### Step 3: Test Import
```
1. Click "Select JSON File" button
2. Choose the file you just downloaded
3. Dialog opens showing file info
4. Keep "Skip Duplicates (Recommended)" selected
5. Click "Import" button
6. Wait for completion
7. See results:
   - Total processed: X
   - Newly imported: 0 (all are duplicates)
   - Duplicates skipped: X (should be 100%)
```

✅ **If you see "Duplicates skipped: X" - IT WORKS!**

## 📋 What to Look For

### Export Success Indicators
- ✅ Green success message: "Export successful! File downloaded."
- ✅ File appears in Downloads folder
- ✅ File name format: `feedback-export-2026-01-02.json`
- ✅ Success message auto-hides after 5 seconds

### Import Success Indicators
- ✅ Preview dialog shows file name and size
- ✅ Can select different merge strategies
- ✅ Green success section appears with statistics
- ✅ Duplicates are correctly detected (100% on re-import)
- ✅ No error messages

## 🔍 Verify Security Features

Open the exported JSON file in a text editor and check:

```json
{
  "export_date": "2026-01-02T...",
  "exported_by": "admin@example.com",  // ✅ Email, not user ID
  "feedback_count": 30,
  "feedback": [
    {
      "failure_type": "selector_not_found",
      "page_url": "https://example.com/page",  // ✅ No query params
      "html_snapshot": null,  // ✅ No HTML content
      "submitted_by": "admin@example.com",  // ✅ Email
      // ❌ No execution_id or user_id fields (removed for portability)
      "execution_metadata": {  // ✅ Metadata preserved
        "test_case_id": 1,
        "test_title": "Login Test"
      }
    }
  ]
}
```

## 🧪 Advanced Testing (Optional)

### Test Different Merge Strategies
1. Export feedback
2. Manually edit JSON file (change some notes)
3. Import with "Update Existing" strategy
4. Verify "Updated: X" count shows changed entries

### Test Error Handling
1. Create invalid JSON file
2. Try to import
3. Verify error message appears
4. Error should be clear and helpful

## 📊 Expected Results Summary

| Test | Expected Result |
|------|----------------|
| First export | Downloads JSON file |
| Re-import same file | 100% duplicates skipped |
| Invalid file | Clear error message |
| Wrong format | Validation error shown |
| Cancel import | Dialog closes, no import |

## 🎉 Success Criteria

You know it's working when:
- ✅ Export downloads file successfully
- ✅ Import preview dialog works
- ✅ Duplicate detection shows 100% on re-import
- ✅ Results display with correct counts
- ✅ No console errors
- ✅ URLs are sanitized (no query params in JSON)
- ✅ HTML snapshots are null

## 🐛 If Something Goes Wrong

### Export button does nothing
- Check browser console for errors (F12)
- Verify backend is running: `curl http://localhost:8000/api/v1/health`
- Check if you're logged in

### Import shows errors
- Verify file is valid JSON
- Check file has correct structure
- Try exporting a new file and importing that

### Duplicate detection not working
- Make sure you're using "Skip Duplicates" strategy
- Verify you're importing the same file
- Check console for errors

## 📱 Next Steps After Testing

1. ✅ If everything works → Mark feature as complete
2. ✅ Test with a colleague (multi-user workflow)
3. ✅ Create user documentation
4. ✅ Update project README
5. ✅ Commit changes to git

## 📚 Need More Info?

- **Detailed Testing Guide**: `frontend/FEEDBACK-SYNC-TESTING-GUIDE.md`
- **Implementation Details**: `FEEDBACK-SYNC-INTEGRATION-COMPLETE.md`
- **Backend Test Script**: `backend/test_feedback_export_import.py`

---

**Ready? Let's test!** 🚀
Open http://localhost:3000/settings and look for "Team Collaboration" section!
