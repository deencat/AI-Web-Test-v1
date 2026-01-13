# Feedback Data Sync - End-to-End Testing Guide

**Date**: 2 January 2026  
**Feature**: Team Collaboration via Feedback Import/Export  
**Sprint**: Sprint 4 - Execution Feedback System

---

## Prerequisites

✅ Backend server running on `http://localhost:8000`  
✅ Frontend dev server running  
✅ User logged in with valid JWT token  
✅ Database has some feedback entries (or can create test data)

---

## Testing Checklist

### Part 1: Export Functionality ✓

#### Test 1.1: Basic Export
- [ ] Navigate to Settings page (`/settings`)
- [ ] Scroll to "Team Collaboration" section
- [ ] Verify FeedbackDataSync component is visible
- [ ] Click "Export to JSON" button
- [ ] Verify loading state shows "Exporting..."
- [ ] Verify file downloads automatically
- [ ] Verify filename format: `feedback-export-YYYY-MM-DD.json`
- [ ] Verify success message appears: "Export successful! File downloaded."
- [ ] Verify success message auto-hides after 5 seconds

**Expected Result**: JSON file downloads with feedback data

#### Test 1.2: Verify Export Content
- [ ] Open downloaded JSON file in text editor
- [ ] Verify structure:
  ```json
  {
    "export_date": "...",
    "exported_by": "user@example.com",
    "feedback_count": N,
    "feedback": [...]
  }
  ```
- [ ] Verify each feedback item has:
  - `failure_type`
  - `failed_selector`
  - `page_url` (without query parameters - security check)
  - `created_at`
  - `submitted_by` (email, not user ID)
  - `execution_metadata` (test_case_id, test_title)
- [ ] Verify HTML snapshots are **NOT** present (`html_snapshot: null`)
- [ ] Verify no foreign key fields (`execution_id`, `user_id` removed)

**Expected Result**: Clean, sanitized JSON data

#### Test 1.3: Export Error Handling
- [ ] Stop the backend server
- [ ] Click "Export to JSON" button
- [ ] Verify error message appears in red alert
- [ ] Restart backend server

**Expected Result**: Proper error display

---

### Part 2: Import Functionality ✓

#### Test 2.1: File Selection
- [ ] Click "Select JSON File" button
- [ ] Verify file picker opens
- [ ] Select a non-JSON file (e.g., .txt, .pdf)
- [ ] Verify error message: "Please select a JSON file"
- [ ] Click "Select JSON File" again
- [ ] Select a valid JSON export file
- [ ] Verify import preview dialog opens

**Expected Result**: Only JSON files accepted

#### Test 2.2: Import Preview Dialog
- [ ] Verify dialog shows:
  - File name
  - File size in KB
  - Merge strategy options (3 radio buttons)
- [ ] Verify "Skip Duplicates (Recommended)" is selected by default
- [ ] Click each radio button and verify selection changes:
  - Skip Duplicates
  - Update Existing
  - Create All (Allow Duplicates)
- [ ] Verify Cancel button is enabled
- [ ] Verify Import button is enabled

**Expected Result**: Dialog shows file info and merge options

#### Test 2.3: Import with Skip Duplicates Strategy
- [ ] Select "Skip Duplicates (Recommended)"
- [ ] Click "Import" button
- [ ] Verify loading state shows "Importing..."
- [ ] Wait for completion
- [ ] Verify dialog closes
- [ ] Verify success message appears in green
- [ ] Verify result statistics show:
  - Total processed: X
  - Newly imported: Y (green)
  - Duplicates skipped: Z (blue)
  - Updated: 0 (yellow)
  - Failed: 0 (or if any, shown in red)

**Expected Result**: Import succeeds with duplicate detection

#### Test 2.4: Re-import Same File
- [ ] Click "Select JSON File" again
- [ ] Select the same file used in Test 2.3
- [ ] Select "Skip Duplicates"
- [ ] Click "Import"
- [ ] Verify result shows:
  - Newly imported: 0
  - Duplicates skipped: X (should be 100% of file)
  - Failed: 0

**Expected Result**: All entries skipped as duplicates

#### Test 2.5: Import with Update Existing Strategy
- [ ] Export feedback again (to get latest data)
- [ ] Manually edit the JSON file (change some `correction_notes` values)
- [ ] Click "Select JSON File"
- [ ] Select the edited file
- [ ] Choose "Update Existing"
- [ ] Click "Import"
- [ ] Verify result shows:
  - Updated: X (number of edited entries)

**Expected Result**: Existing entries updated

#### Test 2.6: Import with Create All Strategy
- [ ] Click "Select JSON File"
- [ ] Select a previously imported file
- [ ] Choose "Create All (Allow Duplicates)"
- [ ] Click "Import"
- [ ] Verify result shows:
  - Newly imported: X (all entries, even duplicates)
  - Duplicates skipped: 0

**Expected Result**: Duplicates are created

#### Test 2.7: Invalid JSON File
- [ ] Create a text file with invalid JSON content:
  ```
  { "invalid": json content here }
  ```
- [ ] Rename it to `.json` extension
- [ ] Click "Select JSON File"
- [ ] Select the invalid JSON file
- [ ] Click "Import"
- [ ] Verify error message appears with details

**Expected Result**: JSON validation error displayed

#### Test 2.8: Wrong JSON Structure
- [ ] Create a JSON file with wrong structure:
  ```json
  {
    "some_field": "value",
    "wrong_structure": true
  }
  ```
- [ ] Click "Select JSON File"
- [ ] Select the file
- [ ] Click "Import"
- [ ] Verify error message about invalid format

**Expected Result**: Format validation error displayed

#### Test 2.9: Cancel Import
- [ ] Click "Select JSON File"
- [ ] Select a valid file
- [ ] In the preview dialog, click "Cancel"
- [ ] Verify dialog closes
- [ ] Verify no import occurs
- [ ] Verify file input is reset

**Expected Result**: Import cancelled successfully

---

### Part 3: Security Verification ✓

#### Test 3.1: URL Sanitization
- [ ] Export feedback
- [ ] Open JSON file
- [ ] Check all `page_url` values
- [ ] Verify no query parameters present (e.g., no `?token=abc` or `&id=123`)

**Expected Result**: URLs are clean without query params

#### Test 3.2: HTML Exclusion
- [ ] Export feedback
- [ ] Open JSON file
- [ ] Search for `html_snapshot` field
- [ ] Verify all values are `null`

**Expected Result**: No HTML content in export

#### Test 3.3: User ID Mapping
- [ ] Export feedback
- [ ] Open JSON file
- [ ] Check `submitted_by` field
- [ ] Verify it contains email addresses, not numeric IDs

**Expected Result**: Email addresses instead of user IDs

#### Test 3.4: Foreign Key Removal
- [ ] Export feedback
- [ ] Open JSON file
- [ ] Search for `execution_id` and `user_id` fields
- [ ] Verify these fields are not present

**Expected Result**: No foreign key references

---

### Part 4: UI/UX Testing ✓

#### Test 4.1: Visual Design
- [ ] Verify Security Notice card displays all 7 security features
- [ ] Verify blue info icon appears in security notice
- [ ] Verify Export section has proper layout
- [ ] Verify Import section has proper layout
- [ ] Verify buttons have correct colors and hover states
- [ ] Verify cards have proper spacing and shadows

**Expected Result**: Professional, consistent design

#### Test 4.2: Responsive Behavior
- [ ] Resize browser window to different widths
- [ ] Verify layout adjusts appropriately
- [ ] Verify dialog is centered on all screen sizes
- [ ] Verify buttons remain clickable

**Expected Result**: Responsive design works

#### Test 4.3: Loading States
- [ ] During export, verify button shows loading spinner
- [ ] During import, verify button shows loading spinner
- [ ] Verify buttons are disabled during operations
- [ ] Verify loading text appears

**Expected Result**: Clear loading indicators

#### Test 4.4: Success/Error Messages
- [ ] Verify success messages use green background
- [ ] Verify error messages use red background
- [ ] Verify icons appear in messages
- [ ] Verify messages are readable and clear

**Expected Result**: Clear feedback to user

---

### Part 5: Integration Testing ✓

#### Test 5.1: Multi-User Workflow
**Setup**: Two developers (A and B) with separate databases

- [ ] Developer A adds feedback entries
- [ ] Developer A exports to JSON
- [ ] Developer A shares file with Developer B
- [ ] Developer B imports file with "Skip Duplicates"
- [ ] Verify Developer B can see feedback from Developer A
- [ ] Verify no duplicates created

**Expected Result**: Successful cross-database sync

#### Test 5.2: Bidirectional Sync
- [ ] Developer A adds feedback 1-3
- [ ] Developer B adds feedback 4-6
- [ ] Developer A exports and sends to B
- [ ] Developer B imports A's data
- [ ] Developer B exports all (1-6) and sends to A
- [ ] Developer A imports B's data
- [ ] Verify both have feedback 1-6

**Expected Result**: Both databases in sync

#### Test 5.3: Large Dataset
- [ ] Create 100+ feedback entries (use script if needed)
- [ ] Export all feedback
- [ ] Verify export completes successfully
- [ ] Import the file
- [ ] Verify import completes successfully
- [ ] Check performance (should be < 10 seconds)

**Expected Result**: Handles large datasets

---

### Part 6: Error Recovery ✓

#### Test 6.1: Network Failure During Export
- [ ] Disconnect network
- [ ] Click "Export to JSON"
- [ ] Verify error message appears
- [ ] Reconnect network
- [ ] Retry export
- [ ] Verify succeeds

**Expected Result**: Graceful error handling

#### Test 6.2: Network Failure During Import
- [ ] Start import
- [ ] Disconnect network mid-import
- [ ] Verify error message appears
- [ ] Verify partial import doesn't corrupt database
- [ ] Reconnect and retry

**Expected Result**: Safe failure handling

#### Test 6.3: Browser Refresh During Import
- [ ] Start import
- [ ] Immediately refresh browser
- [ ] Verify no data corruption
- [ ] Retry import

**Expected Result**: No data corruption

---

## Test Data Setup

### Creating Test Feedback Data

If you need test data, run this in the backend terminal:

```bash
cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend
source venv/bin/activate
python create_test_with_failures.py
```

Or use the existing test script:

```bash
python test_feedback_export_import.py
```

This will create sample feedback entries for testing.

---

## Known Issues / Limitations

1. **File Size**: Large exports (>10MB) may take time
2. **Browser Compatibility**: File download uses Blob API (modern browsers)
3. **Memory**: Large JSON files loaded into memory during import

---

## Success Criteria

- ✅ Export downloads valid JSON file
- ✅ Import accepts valid files and rejects invalid ones
- ✅ Duplicate detection works (100% skip on re-import)
- ✅ All merge strategies function correctly
- ✅ Security features confirmed (URL sanitization, HTML exclusion, etc.)
- ✅ Error handling works for all failure scenarios
- ✅ UI provides clear feedback for all actions
- ✅ Multi-user sync workflow successful
- ✅ No data corruption under any scenario

---

## Reporting Issues

If you encounter any issues during testing:

1. **Note the test number** (e.g., Test 2.3)
2. **Describe the issue** clearly
3. **Include error messages** (from console and UI)
4. **Note the data** (how many feedback entries, file size, etc.)
5. **Browser/OS info** if relevant

---

## Next Steps After Testing

Once all tests pass:

1. ✅ Update project README with feature description
2. ✅ Create user guide for team members
3. ✅ Clean up test files and debug scripts
4. ✅ Commit changes to git
5. ✅ Mark Sprint 4 feature as complete

---

## Quick Test Script

For rapid testing, you can use this sequence:

```bash
# 1. Export test
curl -X GET "http://localhost:8000/api/v1/feedback/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o test-export.json

# 2. Import test
curl -X POST "http://localhost:8000/api/v1/feedback/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test-export.json" \
  -F "merge_strategy=skip_duplicates"
```

---

**Testing Status**: Ready to begin  
**Estimated Time**: 30-45 minutes for complete test suite
