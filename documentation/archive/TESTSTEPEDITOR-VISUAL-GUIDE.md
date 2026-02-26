# TestStepEditor Component - Visual Guide

## 📸 Component Overview

The TestStepEditor component replaces the old step editing UI with a version-controlled, auto-saving editor.

---

## 🎨 Visual Design

```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v2)                      [Add Step]  [Save Now]    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 1 │  │ Navigate to https://example.com          │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
│                                                                 │
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 2 │  │ Click on 'Login' button                  │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
│                                                                 │
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 3 │  │ Enter username: admin                    │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
│                                                                 │
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 4 │  │ Enter password: ****                     │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│ ⓘ Changes auto-saved 2 seconds after editing                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 📱 States & Visual Feedback

### 1. Initial State (No Changes)
```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v2)                      [Add Step]  [Save Now]    │
├────────────────────────────────────────────────────────────────┤
│ [Steps listed here...]                                         │
├────────────────────────────────────────────────────────────────┤
│ ⓘ Changes auto-saved 2 seconds after editing                  │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- Gray info icon (ⓘ) with hint text
- "Save Now" button disabled (gray)
- Version number visible: "(v2)"

---

### 2. Typing State (User Editing)
```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v2)                      [Add Step]  [Save Now]    │
├────────────────────────────────────────────────────────────────┤
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 1 │  │ Navigate to https://example.com█         │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
├────────────────────────────────────────────────────────────────┤
│ ⓘ Changes auto-saved 2 seconds after editing                  │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- Cursor blinking in input
- "Save Now" button enabled (blue)
- 2-second timer started (not visible)

---

### 3. Saving State (API Call in Progress)
```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v2)                      [Add Step]  [Saving...]   │
├────────────────────────────────────────────────────────────────┤
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 1 │  │ Navigate to https://example.com          │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
├────────────────────────────────────────────────────────────────┤
│ 💾 Saving...                                                   │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- Blue "💾 Saving..." text
- "Saving..." button (disabled, gray)
- Version still showing v2

---

### 4. Saved State (Success)
```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v3)                      [Add Step]  [Save Now]    │
├────────────────────────────────────────────────────────────────┤
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 1 │  │ Navigate to https://example.com          │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
├────────────────────────────────────────────────────────────────┤
│ ✓ Saved 3 seconds ago                                         │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- Green "✓ Saved X ago" text
- Version incremented: "(v3)"
- "Save Now" button disabled again (no changes)
- Timestamp updates every 10 seconds

---

### 5. Error State (Save Failed)
```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v2)                      [Add Step]  [Save Now]    │
├────────────────────────────────────────────────────────────────┤
│  ╭───╮  ┌──────────────────────────────────────────┐  ↑  🗑️  │
│  │ 1 │  │ Navigate to https://example.com          │  ↓       │
│  ╰───╯  └──────────────────────────────────────────┘           │
├────────────────────────────────────────────────────────────────┤
│ ⚠️ Error: Network error                                        │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- Red "⚠️ Error: [message]" text
- Version unchanged (save failed)
- "Save Now" button enabled (can retry)

---

### 6. Empty State (No Steps)
```
┌────────────────────────────────────────────────────────────────┐
│ Test Steps (v1)                      [Add Step]  [Save Now]    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│          No steps yet. Click "Add Step" to create one.         │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│ ⓘ Changes auto-saved 2 seconds after editing                  │
└────────────────────────────────────────────────────────────────┘
```

**Elements:**
- Dashed border box with centered text
- Gray informational text
- "Add Step" button ready to use

---

## 🎯 Interactive Elements

### 1. Step Number Badge
```
╭───╮
│ 1 │  ← Blue circle with white text
╰───╯    Auto-increments (1, 2, 3...)
```

**Style:**
- Background: `bg-blue-700` (#1d4ed8)
- Text: White, bold
- Shape: Rounded circle
- Size: 32px × 32px

---

### 2. Input Field
```
┌──────────────────────────────────────────┐
│ Navigate to https://example.com          │  ← Step text input
└──────────────────────────────────────────┘
```

**States:**
- **Default:** Gray border (`border-gray-300`)
- **Focus:** Blue ring (`ring-2 ring-blue-700`)
- **Typing:** Blue border (`border-blue-700`)

---

### 3. Move Buttons (Up/Down)
```
↑  ← Move step up (disabled if first step)
↓  ← Move step down (disabled if last step)
```

**States:**
- **Enabled:** Gray, turns blue on hover
- **Disabled:** Light gray, 30% opacity, cursor-not-allowed

---

### 4. Delete Button
```
🗑️  ← Trash icon (lucide-react Trash2)
```

**Style:**
- Color: Red (`text-red-600`)
- Hover: Red background (`hover:bg-red-50`)
- Size: 16px × 16px

---

### 5. Add Step Button
```
[+ Add Step]  ← Button with Plus icon
```

**Style:**
- Color: Blue text (`text-blue-700`)
- Hover: Light blue background (`hover:bg-blue-50`)
- Icon: Plus from lucide-react

---

### 6. Save Now Button
```
[Save Now]  or  [Saving...]
```

**States:**
- **Enabled:** Blue background (`bg-blue-600`), white text
- **Hover:** Darker blue (`hover:bg-blue-700`)
- **Disabled:** Gray (`bg-gray-400`), cursor-not-allowed
- **Saving:** Shows "Saving..." text

---

## 🎨 Color Palette

```css
/* Primary Colors */
Blue:    #1d4ed8  (bg-blue-700)   - Step numbers, buttons
Light Blue: #2563eb (bg-blue-600)  - Save button

/* Status Colors */
Green:   #059669  (text-green-600) - Success ("✓ Saved")
Red:     #dc2626  (text-red-600)   - Errors ("⚠️ Error")
Blue:    #2563eb  (text-blue-600)  - Info ("💾 Saving...")
Gray:    #6b7280  (text-gray-500)  - Hints ("ⓘ Changes...")

/* Border Colors */
Default: #d1d5db  (border-gray-300)
Focus:   #1d4ed8  (ring-blue-700)
Dashed:  #d1d5db  (border-gray-300)

/* Background Colors */
White:   #ffffff  (bg-white)       - Input backgrounds
Light:   #f9fafb  (bg-gray-50)     - Hover states
Blue:    #eff6ff  (bg-blue-50)     - Hover on blue elements
Red:     #fef2f2  (bg-red-50)      - Hover on delete
```

---

## 📐 Spacing & Sizing

```css
/* Component Spacing */
Gap between steps:    8px  (space-y-2)
Padding in inputs:    16px (px-4 py-2)
Header spacing:       8px  (mb-2)
Footer spacing:       8px  (mt-2)

/* Element Sizes */
Step number circle:   32px × 32px  (w-8 h-8)
Icons:                16px × 16px  (w-4 h-4)
Input height:         40px         (py-2)
Button height:        32px         (py-1)

/* Border Radius */
Inputs:               8px   (rounded-lg)
Buttons:              6px   (rounded-lg)
Step circle:          50%   (rounded-full)
```

---

## 🔤 Typography

```css
/* Text Sizes */
Label:          14px  (text-sm)  - "Test Steps"
Version:        12px  (text-xs)  - "(v3)"
Input text:     16px  (text-base)
Status text:    12px  (text-xs)  - Footer messages
Button text:    14px  (text-sm)

/* Font Weights */
Label:          600   (font-semibold)
Version:        400   (font-normal)
Step number:    600   (font-semibold)
Input:          400   (font-normal)
```

---

## 🎬 Animations

### 1. Auto-Save Debounce
```
User types → Wait 2 seconds → API call starts
    ↓
If user types again → Reset timer → Wait 2 seconds again
```

### 2. Status Transitions
```
Initial → Typing → Saving → Saved
   ↓         ↓        ↓        ↓
  ⓘ      (unchanged)  💾       ✓
```

### 3. Time Updates
```
Saved → Update every 10 seconds
  ↓
"3 seconds ago" → "13 seconds ago" → "23 seconds ago" → ...
  ↓
"1 minute ago" → "2 minutes ago" → ...
```

---

## 💻 Code Structure

```typescript
TestStepEditor
├── Props
│   ├── testId: number
│   ├── initialSteps: string[]
│   ├── initialVersion?: number
│   ├── onChange?: (steps) => void
│   └── onSave?: (versionNumber, steps) => void
│
├── State
│   ├── steps: string[]
│   ├── currentVersion: number
│   ├── isSaving: boolean
│   ├── lastSaved: Date | null
│   └── error: string | null
│
├── Functions
│   ├── autoSave (debounced 2s)
│   ├── handleStepChange
│   ├── handleAddStep
│   ├── handleDeleteStep
│   ├── handleMoveStepUp
│   ├── handleMoveStepDown
│   ├── handleManualSave
│   └── getTimeSince
│
└── Render
    ├── Header (label + buttons)
    ├── Steps List (or empty state)
    └── Status Footer (saving/saved/error)
```

---

## 🔗 Integration Points

### Parent Component: TestsPage.tsx

```typescript
<TestStepEditor
  testId={Number(editingTest.id)}
  initialSteps={editForm.steps}
  initialVersion={(editingTest as any).current_version || 1}
  onChange={(newSteps) => {
    // Update parent state
    setEditForm({ ...editForm, steps: newSteps });
  }}
  onSave={(versionNumber, steps) => {
    // Handle successful save
    console.log('Version saved:', versionNumber);
    setEditForm({ ...editForm, steps });
  }}
/>
```

---

## 📱 Responsive Design

### Desktop (≥1024px)
- Full width steps
- All buttons visible
- Comfortable spacing

### Tablet (768px-1023px)
- Slightly narrower inputs
- Icons still visible
- Touch-friendly buttons

### Mobile (<768px)
- Stack elements vertically
- Larger touch targets
- Simplified layout

---

## ♿ Accessibility

### Keyboard Navigation
- **Tab:** Navigate between inputs
- **Enter:** Submit/save (in button)
- **Escape:** Cancel edit (if implemented)

### Screen Readers
- Labels associated with inputs
- Button titles for icon-only buttons
- Status messages announced

### Visual Indicators
- Focus rings on all interactive elements
- Clear disabled states
- High contrast colors

---

## 🎯 User Flows

### Flow 1: Add New Step
```
1. Click "Add Step" button
2. Empty input appears at bottom
3. Type step description
4. Wait 2 seconds
5. Auto-save triggers
6. "Saving..." appears
7. "Saved X ago" appears
8. Version increments
```

### Flow 2: Edit Existing Step
```
1. Click in step input
2. Modify text
3. Wait 2 seconds
4. Auto-save triggers
5. Version increments
```

### Flow 3: Reorder Steps
```
1. Click up/down arrow
2. Steps swap positions
3. Auto-save triggers immediately
4. New order saved
```

### Flow 4: Manual Save
```
1. Make changes
2. Click "Save Now"
3. Saves immediately (no 2s wait)
4. Useful for quick saves
```

---

## 📊 Performance

### Metrics:
- **Auto-save delay:** 2 seconds
- **API call time:** ~100-500ms
- **Render time:** <50ms
- **Memory usage:** Minimal (small state)

### Optimizations:
- Debounced auto-save prevents spam
- Only saves if content changed
- Efficient React re-renders
- No unnecessary API calls

---

**Visual Guide Complete!** 🎨

This component provides a professional, user-friendly interface for editing test steps with automatic version control.
