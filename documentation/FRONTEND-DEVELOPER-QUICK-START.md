# Frontend Developer Quick Start
## For Your Friend (VS Code + Copilot)

**Your Focus:** React + TypeScript frontend development  
**Working Directory:** `frontend/`  
**IDE:** VS Code with GitHub Copilot

---

## ⚡ 5-Minute Setup

```bash
# 1. Clone and navigate
git clone <repo-url>
cd AI-Web-Test-v1/frontend

# 2. Install dependencies
npm install

# 3. Create .env file
echo "VITE_USE_MOCK=false" > .env
echo "VITE_API_URL=http://localhost:8000/api" >> .env

# 4. Start dev server
npm run dev
```

**Frontend:** http://localhost:5173  
**Login:** admin / admin123

---

## 🎯 Your Sprint 2 Tasks

### **Week 3: Test Generation UI**
1. **Test Generation Form** (2 days)
   - Natural language input textarea
   - Generate button
   - Loading state
   - Error handling

2. **Test Case Display** (2 days)
   - Test case list component
   - Test case card component
   - Filter/search functionality
   - Detail view modal

3. **Integration** (1 day)
   - Connect to `/api/v1/tests/generate` endpoint
   - Handle API responses
   - Update types in `src/types/api.ts`

### **Week 4: Knowledge Base & Polish**
1. **KB Upload UI** (2 days)
   - File upload component (drag & drop)
   - Document list view
   - Category selector

2. **Dashboard Charts** (2 days)
   - Install Recharts: `npm install recharts`
   - Add line chart for test trends
   - Add pie chart for test status

3. **Testing** (1 day)
   - Update Playwright tests
   - Fix any failing tests

---

## 📁 Key Files You'll Work With

```
frontend/src/
├── pages/
│   ├── TestsPage.tsx          ← Add test generation UI here
│   ├── KnowledgeBasePage.tsx  ← Add KB upload here
│   └── DashboardPage.tsx      ← Add charts here
├── components/
│   └── ui/                    ← Reusable components
├── services/
│   ├── testService.ts         ← Add test generation API calls
│   └── kbService.ts           ← Add KB API calls
└── types/
    └── api.ts                 ← Update types when backend changes
```

---

## 🔧 Daily Commands

```bash
# Start development
npm run dev

# Run tests (backend must be running!)
npm test

# Run tests in UI mode
npm run test:ui

# Check TypeScript errors
npm run type-check

# Build for production
npm run build
```

---

## 🎨 Component Patterns to Follow

### **1. Use Existing UI Components**

```typescript
// Good: Use existing components
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

function MyComponent() {
  return (
    <Card>
      <Input placeholder="Enter text" />
      <Button>Submit</Button>
    </Card>
  );
}
```

### **2. API Service Pattern**

```typescript
// In src/services/testService.ts
import api from './api';
import { GenerateTestRequest, GenerateTestResponse } from '@/types/api';

class TestService {
  async generateTests(prompt: string): Promise<GenerateTestResponse> {
    const response = await api.post<GenerateTestResponse>(
      '/tests/generate',
      { prompt }
    );
    return response.data;
  }
}

export default new TestService();
```

### **3. Page Component Pattern**

```typescript
// In src/pages/TestGenerationPage.tsx
import { useState } from 'react';
import testService from '@/services/testService';

export default function TestGenerationPage() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [tests, setTests] = useState([]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await testService.generateTests(prompt);
      setTests(result.test_cases);
    } catch (error) {
      console.error('Failed to generate tests:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea 
        value={prompt} 
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Tests'}
      </button>
      {/* Display tests */}
    </div>
  );
}
```

---

## 🔄 When Backend Adds New Endpoint

**Backend will notify you:**
```
New endpoint: POST /api/v1/tests/generate
Request: { prompt: string }
Response: { test_cases: TestCase[] }
```

**Your steps:**

1. **Update types** (`src/types/api.ts`):
```typescript
export interface TestCase {
  id: number;
  title: string;
  description: string;
  steps: string[];
  expected_result: string;
}

export interface GenerateTestRequest {
  prompt: string;
}

export interface GenerateTestResponse {
  test_cases: TestCase[];
}
```

2. **Add service method** (`src/services/testService.ts`):
```typescript
async generateTests(prompt: string): Promise<GenerateTestResponse> {
  const response = await api.post<GenerateTestResponse>(
    '/tests/generate',
    { prompt }
  );
  return response.data;
}
```

3. **Use in component**:
```typescript
import testService from '@/services/testService';

const result = await testService.generateTests('Test login flow');
```

---

## 🐛 Common Issues & Solutions

### **Issue: Backend not responding**

```bash
# Check if backend is running
# Ask backend developer to start it
# Or use mock mode:
# In .env: VITE_USE_MOCK=true
```

### **Issue: TypeScript errors**

```bash
# Check types match backend response
# Ask backend developer for schema
# Update src/types/api.ts
```

### **Issue: Tests failing**

```bash
# Make sure backend is running
npm test

# Or run with UI to debug
npm run test:ui
```

### **Issue: CORS errors**

```
# Ask backend developer to add your origin to CORS settings
# Should be in backend/.env:
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

---

## 📞 Communication with Backend Developer

### **When you need a new endpoint:**

```
Hey! I need an endpoint to:
- Get all test cases for a user
- Filter by status
- Paginate results

Suggested:
GET /api/v1/tests?status=pending&page=1&limit=10

Response:
{
  tests: TestCase[],
  total: number,
  page: number,
  pages: number
}

Can you implement this?
```

### **When you find a bug:**

```
Bug in POST /api/v1/tests/generate:
- Sending: { prompt: "test login" }
- Expected: { test_cases: [...] }
- Got: 500 Internal Server Error
- Error: "KeyError: 'user_id'"

Can you check the endpoint?
```

### **Daily sync:**

```
Yesterday: Completed test generation form UI
Today: Working on test case display component
Blocked: Need test case schema from backend
```

---

## 📚 Resources

**Documentation:**
- `TEAM-SPLIT-HANDOFF-GUIDE.md` - Full guide
- `docs/API-REQUIREMENTS.md` - API contracts
- `frontend/README.md` - Frontend docs

**Code Examples:**
- `src/pages/LoginPage.tsx` - Form handling
- `src/pages/DashboardPage.tsx` - Data display
- `src/services/authService.ts` - API service pattern

**Testing:**
- `tests/e2e/01-auth.spec.ts` - Auth tests
- `tests/e2e/02-dashboard.spec.ts` - Dashboard tests

---

## ✅ Setup Checklist

- [ ] Cloned repo
- [ ] `npm install` completed
- [ ] `.env` file created
- [ ] Frontend runs on http://localhost:5173
- [ ] Can login with admin/admin123
- [ ] Tests passing (`npm test`)
- [ ] VS Code with Copilot installed
- [ ] Read Sprint 2 tasks
- [ ] Created your git branch
- [ ] Contacted backend developer

---

## 🎯 Your Goal This Week

**Build the Test Generation UI that allows users to:**
1. Enter a natural language prompt
2. Click "Generate Tests"
3. See generated test cases
4. View test case details

**Keep it simple, make it work, then make it pretty!** ✨

---

**Need Help?**
1. Check `TEAM-SPLIT-HANDOFF-GUIDE.md`
2. Ask backend developer
3. Review existing code patterns
4. Use Copilot for suggestions

**Good luck! 🚀**

