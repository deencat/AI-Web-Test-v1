# AI Web Test — Frontend

React 18 + TypeScript + Vite SPA for the AI Web Test platform.

**Last Updated:** 2026-06-30  
**Backend:** FastAPI at `http://127.0.0.1:8000`  
**Codemap:** [`docs/CODEMAPS/frontend.md`](../docs/CODEMAPS/frontend.md)  
**Execution UI context:** [`documentation/ADR-002-test-execution-engine.md`](../documentation/ADR-002-test-execution-engine.md)

## Quick Start

### Prerequisites
- Node.js 18+ installed
- npm or yarn package manager
- Backend server running (for real API mode)

### Installation & Setup

```bash
# 1. Install dependencies
npm install

# 2. Create .env file from example
cp .env.example .env

# 3. Configure your .env file (see Configuration section below)

# 4. Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Application will be available at:** http://localhost:5173/

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `frontend/` directory (copy from `.env.example`):

```env
# Backend API URL
VITE_API_URL=http://127.0.0.1:8000/api/v1

# Use mock data (true) or real API (false)
VITE_USE_MOCK=false
```

### Configuration Modes

**Option 1: Connect to Real Backend (Recommended)**
```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_USE_MOCK=false
```
- Requires backend server running on port 8000
- Uses real authentication and data
- **Default credentials:** username: `admin`, password: `admin123`
- **AI test generation requires:** OpenRouter API key configured in backend

**Option 2: Use Mock Data (Frontend-only Development)**
```env
VITE_USE_MOCK=true
```
- No backend required
- Accepts any username/password
- Uses static mock data for testing UI
- AI test generation returns mock tests (no real AI)

### Starting the Backend Server

If using real API mode, start the backend first:

```bash
# In a separate terminal
cd ../backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be available at: http://127.0.0.1:8000  
API Documentation: http://127.0.0.1:8000/api/v1/docs

**Important:** For AI test generation features to work, the backend needs an OpenRouter API key configured in `backend/.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_MODEL=mistralai/mixtral-8x7b-instruct
```
Get your free API key from: https://openrouter.ai/keys

---

## 🎯 Features Implemented

### ✅ Completed (Sprint 1 - Day 1)

**Authentication:**
- [x] Professional login page
- [x] Mock authentication (accepts any username/password)
- [x] JWT token storage (localStorage)
- [x] Protected routes with authentication check
- [x] Logout functionality

**Dashboard:**
- [x] Test statistics (Total, Passed, Failed, Pass Rate)
- [x] Recent tests list with status indicators
- [x] Responsive card layout
- [x] Real-time status animations (pulsing for running tests)

**Tests Page:**
- [x] Test list with status badges
- [x] Test details display
- [x] Create new test button (UI only)
- [x] Responsive design

**Knowledge Base:**
- [x] Category display with color badges
- [x] Document upload UI
- [x] Document list with metadata
- [x] Search functionality (UI only)
- [x] Referenced count by agents

**Settings:**
- [x] Profile information form
- [x] Password change form
- [x] Preferences toggles
- [x] Save/Cancel actions (UI only)

**Layout & Navigation:**
- [x] Fixed header with logo and user menu
- [x] Sidebar navigation with icons
- [x] Active link highlighting
- [x] Responsive layout (mobile/tablet/desktop)

---

## Project Structure (current)

```
frontend/src/
├── App.tsx                 # Routes (see codemap for full list)
├── pages/                  # Login, Dashboard, Tests, Executions, Settings, …
├── components/             # RunTestButton, ExecutionSettings, XPathCache, …
├── features/
│   ├── agent-workflow/     # Multi-agent pipeline UI (SSE progress)
│   └── settings/           # Email OTP credentials
├── services/               # API clients → /api/v1 and /api/v2
├── context/                # EphemeralCredentialContext (UAT creds)
└── types/                  # TypeScript definitions
```

Full route and service map: [`docs/CODEMAPS/frontend.md`](../docs/CODEMAPS/frontend.md).

## Key Features

- **Test management** — CRUD, versioning, step editor, step library modules
- **Three-tier execution** — Run tests with configurable fallback (Settings → Execution)
- **Execution progress** — Live step status, screenshots, tier analytics, RCA panel
- **Agent workflow** — Trigger crawl-and-save and multi-agent pipelines (API v2)
- **ReqIQ proxy** — Requirements/readiness via `requirementsService`
- **Debug mode** — Interactive step-range debugging

---

## 📁 Project Structure (Sprint 1 snapshot — legacy)

## 🎨 Design System

### Color Palette

```typescript
{
  primary: '#2E86AB',    // Main actions, branding
  success: '#28A745',    // Passed tests, positive states
  warning: '#FFC107',    // Warnings, running tests
  danger: '#DC3545',     // Failed tests, errors
  info: '#17A2B8',       // Information messages
}
```

### Components

**Button Component:**
- Variants: `primary`, `secondary`, `danger`
- Sizes: `sm`, `md`, `lg`
- States: default, hover, loading, disabled

**Input Component:**
- Label support
- Error message display
- Helper text
- Validation states

**Card Component:**
- White background with shadow
- Rounded corners
- Optional padding
- Border styling

---

## 🔐 Authentication Flow

### With Real Backend (VITE_USE_MOCK=false)

```
Login Page
    ↓
Enter credentials (admin / admin123)
    ↓
POST /api/v1/auth/login
    ↓
Receive JWT access token
    ↓
GET /api/v1/auth/me (fetch user data)
    ↓
Store token + user in localStorage
    ↓
Redirect to Dashboard
    ↓
Protected routes check for token
    ↓
Logout → DELETE token → Redirect to Login
```

**Default Credentials:**
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** admin

### With Mock Data (VITE_USE_MOCK=true)

```
Login Page
    ↓
Enter any username/password
    ↓
Mock authentication (always succeeds)
    ↓
Store mock JWT token in localStorage
    ↓
Redirect to Dashboard
    ↓
Protected routes check for token
    ↓
Logout clears token → Redirect to Login
```

**Demo Credentials (Mock Mode):**
- Any username works (e.g., `admin`, `qa_engineer`)
- Any password works (e.g., `password`)

---

## 📊 Mock Data

### Dashboard Stats
```typescript
{
  total_tests: 156,
  passed: 142,
  failed: 8,
  running: 6,
  pass_rate: 91.0
}
```

### Test Data
- 4 sample tests with different statuses
- Includes: pass, fail, running states
- Execution times and timestamps

### Knowledge Base
- 4 predefined categories (CRM, Billing, Products, Customer Service)
- 2 sample documents with metadata
- Agent reference counts

---

## 🛠️ Technology Stack

**Core:**
- ⚛️ React 18.3.1 - UI library
- 📘 TypeScript 5.6.2 - Type safety
- ⚡ Vite 6.0.1 - Build tool

**Styling:**
- 🎨 TailwindCSS 3.4.17 - Utility-first CSS
- 🎯 PostCSS - CSS processing

**Routing:**
- 🧭 React Router DOM 7.1.1 - Client-side routing

**UI Icons:**
- 🎭 Lucide React 0.468.0 - Icon library

**Utilities:**
- 🎪 clsx 2.1.1 - Conditional className utility

---

## 📱 Responsive Design

### Breakpoints
- **Mobile:** < 768px (stacked layout)
- **Tablet:** 768px - 1024px (adjusted layout)
- **Desktop:** > 1024px (full layout with sidebar)

### Responsive Features
- Collapsible sidebar on mobile
- Grid layouts adapt to screen size
- Touch-friendly button sizes (44px minimum)
- Readable text at all sizes

---

## 🎯 Design Mode Compliance

This project follows the **Design Mode** requirements from `Design Mode.md`:

✅ **Frontend only** - No backend connections  
✅ **Dummy JSON data** - All data is mocked  
✅ **Component navigation** - All routes linked  
✅ **Responsive buttons** - Interactive UI elements  
✅ **No backend logic** - Pure frontend prototype  
✅ **PM document aligned** - Follows Sprint 1 Plan  

---

## 🔄 Available Scripts

```bash
# Development
npm run dev          # Start dev server (http://localhost:5173)

# Build
npm run build        # Production build (outputs to dist/)

# Preview
npm run preview      # Preview production build locally

# Linting
npm run lint         # Run ESLint on source files
```

---

## 📝 Next Steps (Sprint 1 - Day 2)

### Planned Enhancements:
1. **Add More Mock Data:**
   - More test cases
   - More KB documents
   - More categories

2. **UI Polish:**
   - Loading skeletons
   - Empty states
   - Better animations
   - Toast notifications

3. **Additional Pages:**
   - Test details page
   - Test creation wizard
   - KB document viewer

4. **Responsive Improvements:**
   - Mobile menu toggle
   - Better tablet layout
   - Touch gestures

5. **Accessibility:**
   - ARIA labels
   - Keyboard navigation
   - Screen reader support

---

## 🐛 Known Issues

None currently - all components working as expected! ✅

---

## 📚 Resources

- **React Docs:** https://react.dev/
- **TypeScript Handbook:** https://www.typescriptlang.org/docs/
- **TailwindCSS Docs:** https://tailwindcss.com/docs
- **React Router Docs:** https://reactrouter.com/
- **Vite Guide:** https://vite.dev/guide/
- **Lucide Icons:** https://lucide.dev/icons/

---

## 👨‍💻 Development Notes

### State Management
- Currently using `localStorage` for authentication state
- No global state management (Redux/Context) yet
- Each page manages its own local state

### Data Flow
```
Mock Data (src/mock/) 
    ↓
Pages load mock data
    ↓
Display in UI components
```

### Future Backend Integration
When backend is ready:
1. Replace mock data imports with API calls
2. Add API client with axios/fetch
3. Add loading and error states
4. Implement real authentication
5. Add form submissions

---

## 🎨 UI Screenshots

### Login Page
- Clean, centered design
- Gradient background
- Professional card layout

### Dashboard
- 4 stat cards (Total, Passed, Failed, Pass Rate)
- Recent tests list with status indicators
- Responsive grid layout

### Tests Page
- Comprehensive test list
- Status badges
- Action buttons

### Knowledge Base
- Category cards with counts
- Document list with metadata
- Search functionality

### Settings
- Profile information form
- Password change
- Preferences toggles

---

## ✅ Sprint 1 - Day 1 Completion Checklist

- [x] React + TypeScript project initialized
- [x] TailwindCSS configured
- [x] Project structure created
- [x] Common components (Button, Input, Card)
- [x] Layout components (Header, Sidebar, Layout)
- [x] Login page with mock authentication
- [x] Dashboard page with stats and recent tests
- [x] Tests page with test list
- [x] Knowledge Base page with categories
- [x] Settings page with forms
- [x] Routing with protected routes
- [x] Mock data for all pages
- [x] TypeScript types defined
- [x] Responsive design
- [x] Professional UI design
- [x] No linting errors
 
**Status:** ✅ **COMPLETE - Ready for Day 2!**

---

## 📞 Support

For questions or issues, refer to:
- `frontend-setup-guide.md` - Detailed setup instructions
- Sprint 1 Plan - Project management document
- Design Mode.md - Design requirements

---

**Built with ❤️ for AI Web Test v1.0**  
**Mode:** Prototyping | **Framework:** React + TypeScript + Vite  
**Status:** Sprint 1 Day 1 ✅ Complete

