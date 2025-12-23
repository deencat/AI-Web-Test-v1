# Frontend Development - Component 1: TestStepEditor

**Component:** TestStepEditor.tsx  
**Priority:** #1 (Core functionality)  
**Estimated Time:** 4-6 hours  
**Location:** `frontend/src/components/TestStepEditor.tsx`

---

## Component Purpose

Allow users to edit test steps with:
- Auto-save functionality (debounced)
- Version tracking
- Visual feedback (saving indicators)
- Current version display

---

## Component Structure

```typescript
// frontend/src/components/TestStepEditor.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash'; // Install if needed: npm install lodash

interface TestStepEditorProps {
  testId: number;
  initialSteps: string;
  initialVersion?: number;
  onVersionCreated?: (newVersion: number) => void;
}

export const TestStepEditor: React.FC<TestStepEditorProps> = ({
  testId,
  initialSteps,
  initialVersion = 1,
  onVersionCreated
}) => {
  const [steps, setSteps] = useState(initialSteps);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [currentVersion, setCurrentVersion] = useState(initialVersion);
  const [error, setError] = useState<string | null>(null);

  // Auto-save function (debounced)
  const autoSave = useCallback(
    debounce(async (content: string) => {
      try {
        setIsSaving(true);
        setError(null);
        
        const response = await fetch(`/api/v1/tests/${testId}/steps`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            steps: content,
            change_reason: 'Auto-save edit'
          })
        });

        if (!response.ok) {
          throw new Error('Failed to save');
        }

        const data = await response.json();
        setLastSaved(new Date());
        setCurrentVersion(data.version_number || currentVersion + 1);
        
        if (onVersionCreated) {
          onVersionCreated(data.version_number);
        }
      } catch (err) {
        setError('Failed to save changes');
        console.error('Save error:', err);
      } finally {
        setIsSaving(false);
      }
    }, 2000), // 2 second debounce
    [testId, currentVersion]
  );

  // Handle text change
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setSteps(newValue);
    autoSave(newValue);
  };

  // Manual save
  const handleManualSave = async () => {
    autoSave.cancel(); // Cancel any pending auto-save
    await autoSave(steps);
  };

  // Format last saved time
  const getLastSavedText = () => {
    if (!lastSaved) return 'Not saved yet';
    
    const seconds = Math.floor((Date.now() - lastSaved.getTime()) / 1000);
    
    if (seconds < 60) return `Saved ${seconds} seconds ago`;
    if (seconds < 3600) return `Saved ${Math.floor(seconds / 60)} minutes ago`;
    return `Saved ${Math.floor(seconds / 3600)} hours ago`;
  };

  return (
    <div className="test-step-editor">
      {/* Header */}
      <div className="editor-header flex justify-between items-center mb-4">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold">Test Steps</h3>
          <span className="text-sm text-gray-500">Version {currentVersion}</span>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Saving indicator */}
          {isSaving && (
            <span className="text-sm text-blue-600 flex items-center gap-2">
              <span className="animate-spin">⏳</span> Saving...
            </span>
          )}
          
          {/* Last saved */}
          {!isSaving && lastSaved && (
            <span className="text-sm text-green-600">
              ✓ {getLastSavedText()}
            </span>
          )}
          
          {/* Error */}
          {error && (
            <span className="text-sm text-red-600">
              ❌ {error}
            </span>
          )}
          
          {/* Manual save button */}
          <button
            onClick={handleManualSave}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Save Now
          </button>
        </div>
      </div>

      {/* Editor */}
      <textarea
        value={steps}
        onChange={handleChange}
        className="w-full h-64 p-4 border border-gray-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Enter test steps here...
        
Example:
1. Navigate to https://example.com
2. Click on 'Login' button
3. Enter username and password
4. Click 'Submit'
5. Verify dashboard loads"
      />

      {/* Info */}
      <div className="mt-2 text-sm text-gray-500">
        ℹ️ Changes are auto-saved 2 seconds after you stop typing.
        Each save creates a new version.
      </div>
    </div>
  );
};

export default TestStepEditor;
```

---

## Installation Steps

### 1. Install Dependencies (if needed)

```powershell
cd frontend
npm install lodash
npm install @types/lodash --save-dev
```

### 2. Create the Component File

```powershell
# Create file at: frontend/src/components/TestStepEditor.tsx
# Copy the code above
```

### 3. Update TestDetailPage to Use Component

```typescript
// frontend/src/pages/TestDetailPage.tsx

import TestStepEditor from '../components/TestStepEditor';

// Inside your component:
const [testData, setTestData] = useState<any>(null);

// Render:
<TestStepEditor
  testId={testData.id}
  initialSteps={testData.steps || ''}
  initialVersion={testData.current_version || 1}
  onVersionCreated={(newVersion) => {
    console.log('New version created:', newVersion);
    // Optionally refresh version history
  }}
/>
```

---

## Testing Checklist

### Basic Functionality
- [ ] Component renders without errors
- [ ] Initial steps display correctly
- [ ] Can type in textarea
- [ ] Auto-save triggers after 2 seconds
- [ ] Manual save button works
- [ ] Version number increments after save

### Visual Feedback
- [ ] "Saving..." appears while saving
- [ ] "Saved X ago" appears after save
- [ ] Error message shows on failure
- [ ] Version number updates after save

### Edge Cases
- [ ] Empty steps (should still save)
- [ ] Very long content (10,000+ characters)
- [ ] Rapid typing (debounce working)
- [ ] Network error handling
- [ ] Disabled state while saving

---

## API Integration

### Endpoint: PUT /api/v1/tests/{id}/steps

**Request:**
```json
{
  "steps": "1. Navigate to...\n2. Click...",
  "change_reason": "Auto-save edit"
}
```

**Response:**
```json
{
  "id": 123,
  "version_number": 5,
  "message": "Test steps updated and version created"
}
```

**Error Response:**
```json
{
  "detail": "Test not found"
}
```

---

## Styling Notes

### Tailwind Classes Used
- `flex`, `justify-between`, `items-center` - Flexbox layout
- `gap-4` - Spacing between elements
- `text-lg`, `text-sm` - Font sizes
- `text-gray-500`, `text-blue-600` - Colors
- `p-4`, `mb-4` - Padding, margin
- `border`, `rounded-lg` - Borders, rounded corners
- `hover:bg-blue-700` - Hover effects
- `disabled:opacity-50` - Disabled state
- `animate-spin` - Spinning animation

### Custom Styling (if needed)
```css
/* Add to your global CSS if needed */
.test-step-editor textarea {
  resize: vertical;
  min-height: 200px;
}

.test-step-editor textarea:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}
```

---

## Next Steps After This Component

Once TestStepEditor is complete and tested:

1. **Component 2:** VersionHistoryPanel
   - Displays list of versions
   - Triggers comparison and rollback

2. **Integration:**
   - Wire TestStepEditor into TestDetailPage
   - Test end-to-end flow

3. **Polish:**
   - Add loading states
   - Improve error handling
   - Add tooltips

---

## Development Commands

### Start Frontend Dev Server
```powershell
cd frontend
npm run dev
# Open http://localhost:3000
```

### Start Backend Server (in separate terminal)
```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload
# Open http://localhost:8000/docs
```

### Test API Endpoints
```powershell
# Open Swagger UI
http://localhost:8000/docs

# Test PUT /tests/{id}/steps
# Use test ID from your database
```

---

## Troubleshooting

### Issue: "Cannot find module 'lodash'"
**Solution:**
```powershell
npm install lodash @types/lodash
```

### Issue: "Auto-save not working"
**Check:**
1. Debounce delay (should be 2 seconds)
2. Network tab in browser DevTools
3. Backend logs for errors
4. Token in localStorage

### Issue: "Version number not updating"
**Check:**
1. API response includes `version_number`
2. State update in `setCurrentVersion`
3. Backend creating new versions correctly

---

## Time Breakdown

| Task | Time |
|------|------|
| Setup component file | 15 min |
| Implement basic structure | 30 min |
| Add auto-save logic | 1 hour |
| Add manual save | 30 min |
| Add visual feedback | 45 min |
| Styling | 45 min |
| Integration with page | 30 min |
| Testing | 1 hour |
| Bug fixes | 30 min |
| **Total** | **4-6 hours** |

---

## Success Criteria

**MVP (Must Have):**
- ✅ Can edit test steps
- ✅ Auto-save works (2-second debounce)
- ✅ Manual save button works
- ✅ Version number displays and updates
- ✅ Basic error handling

**Nice to Have (If Time):**
- ⭐ Rich text formatting
- ⭐ Syntax highlighting
- ⭐ Undo/redo functionality
- ⭐ Keyboard shortcuts (Ctrl+S to save)
- ⭐ Character count

---

**Ready to start? Let's build this component!** 🚀

Create the file and start coding. Test frequently using the dev server!
