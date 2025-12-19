# Frontend Setup Guide - Design Mode
## AI Web Test v1.0 Prototype

**Mode:** Prototyping (Frontend Only, No Backend)  
**Duration:** Sprint 1 - Days 1-2  
**Goal:** Create professional UI with dummy data  

---

## 📁 Project Structure to Create

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── common/           # Generic components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── Badge.tsx
│   │   ├── layout/           # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Layout.tsx
│   │   └── auth/             # Auth-specific components
│   │       └── LoginForm.tsx
│   ├── pages/                # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── TestsPage.tsx
│   │   ├── KnowledgeBasePage.tsx
│   │   └── SettingsPage.tsx
│   ├── mock/                 # Mock data (Design Mode)
│   │   ├── users.ts
│   │   ├── tests.ts
│   │   ├── knowledgeBase.ts
│   │   └── dashboard.ts
│   ├── types/                # TypeScript types
│   │   ├── user.ts
│   │   ├── test.ts
│   │   └── knowledgeBase.ts
│   ├── hooks/                # Custom React hooks
│   │   └── useAuth.ts
│   ├── utils/                # Utility functions
│   │   └── helpers.ts
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Entry point
│   └── index.css             # Global styles
├── public/
│   └── vite.svg
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 🎨 Step-by-Step Setup

### Step 1: Create Base Components (90 minutes)

Create the following files:

#### `src/components/common/Button.tsx`
```typescript
import React from 'react';
import { clsx } from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseStyles = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-primary text-white hover:bg-blue-700 focus:ring-primary',
    secondary: 'bg-gray-200 text-gray-700 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-danger text-white hover:bg-red-700 focus:ring-danger',
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  return (
    <button
      className={clsx(
        baseStyles,
        variants[variant],
        sizes[size],
        (disabled || loading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading...
        </span>
      ) : (
        children
      )}
    </button>
  );
};
```

#### `src/components/common/Input.tsx`
```typescript
import React from 'react';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className,
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        className={clsx(
          'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-colors',
          error ? 'border-danger focus:ring-danger' : 'border-gray-300',
          className
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-danger">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};
```

#### `src/components/common/Card.tsx`
```typescript
import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className,
  padding = true 
}) => {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-md border border-gray-200',
        padding && 'p-6',
        className
      )}
    >
      {children}
    </div>
  );
};
```

---

### Step 2: Create Mock Data (30 minutes)

#### `src/mock/users.ts`
```typescript
export const mockUsers = [
  {
    id: '1',
    email: 'admin@aiwebtest.com',
    username: 'admin',
    full_name: 'Admin User',
    is_active: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    email: 'qa@aiwebtest.com',
    username: 'qa_engineer',
    full_name: 'QA Engineer',
    is_active: true,
    created_at: '2025-01-02T00:00:00Z',
  },
];

// Mock login function
export const mockLogin = (username: string, password: string) => {
  // Accept any username/password for prototyping
  const user = mockUsers.find(u => u.username === username) || mockUsers[0];
  return {
    success: true,
    user,
    token: 'mock-jwt-token-' + Date.now(),
  };
};
```

#### `src/mock/tests.ts`
```typescript
export const mockTests = [
  {
    id: 'TEST-001',
    name: 'Login Flow Test',
    description: 'Test the Three Hong Kong customer login flow',
    status: 'pass',
    created_at: '2025-11-01T10:00:00Z',
    execution_time: 45.2,
  },
  {
    id: 'TEST-002',
    name: 'Account Dashboard Test',
    description: 'Verify account dashboard loads correctly',
    status: 'pass',
    created_at: '2025-11-01T11:00:00Z',
    execution_time: 32.1,
  },
  {
    id: 'TEST-003',
    name: 'Billing Page Test',
    description: 'Test billing information display',
    status: 'fail',
    created_at: '2025-11-01T12:00:00Z',
    execution_time: 28.5,
  },
  {
    id: 'TEST-004',
    name: 'Service Activation Test',
    description: 'Test new service activation flow',
    status: 'running',
    created_at: '2025-11-01T13:00:00Z',
    execution_time: 0,
  },
];

export const mockDashboardStats = {
  total_tests: 156,
  passed: 142,
  failed: 8,
  running: 6,
  pass_rate: 91.0,
  last_run: '2025-11-01T13:30:00Z',
};
```

#### `src/mock/knowledgeBase.ts`
```typescript
export const mockKBCategories = [
  { id: 'cat-001', name: 'CRM', color: '#3498db', count: 5 },
  { id: 'cat-002', name: 'Billing', color: '#2ecc71', count: 8 },
  { id: 'cat-003', name: 'Products & Services', color: '#16a085', count: 12 },
  { id: 'cat-004', name: 'Customer Service', color: '#c0392b', count: 6 },
];

export const mockKBDocuments = [
  {
    id: 'doc-001',
    category_id: 'cat-001',
    file_name: 'CRM_User_Guide.pdf',
    file_size: 2.1,
    uploaded_at: '2025-10-15T00:00:00Z',
    referenced_count: 47,
  },
  {
    id: 'doc-002',
    category_id: 'cat-003',
    file_name: '5G_Product_Catalog.pdf',
    file_size: 2.4,
    uploaded_at: '2025-10-20T00:00:00Z',
    referenced_count: 18,
  },
];
```

---

### Step 3: Create Type Definitions (15 minutes)

#### `src/types/user.ts`
```typescript
export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  user: User;
  token: string;
}
```

---

### Step 4: Create Login Page (1 hour)

#### `src/pages/LoginPage.tsx`
```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { mockLogin } from '../mock/users';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Simulate API delay
    setTimeout(() => {
      const result = mockLogin(username, password);
      
      if (result.success) {
        // Store token in localStorage
        localStorage.setItem('token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Navigate to dashboard
        navigate('/dashboard');
      } else {
        setError('Invalid credentials');
      }
      
      setLoading(false);
    }, 500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🤖 AI Web Test
          </h1>
          <p className="text-gray-600">Intelligent Test Automation Platform</p>
        </div>

        <Card>
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Sign In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full"
            >
              Sign In
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>Demo credentials: any username/password</p>
          </div>
        </Card>
      </div>
    </div>
  );
};
```

---

### Step 5: Create Dashboard Page (1 hour)

#### `src/pages/DashboardPage.tsx`
```typescript
import React, { useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { mockDashboardStats, mockTests } from '../mock/tests';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState(mockDashboardStats);
  const [recentTests, setRecentTests] = useState(mockTests.slice(0, 5));

  useEffect(() => {
    // Simulate loading data
    setStats(mockDashboardStats);
    setRecentTests(mockTests.slice(0, 5));
  }, []);

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here's your test overview.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Tests</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total_tests}</p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Passed</p>
                <p className="text-3xl font-bold text-success">{stats.passed}</p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-3xl font-bold text-danger">{stats.failed}</p>
              </div>
              <div className="text-4xl">❌</div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pass Rate</p>
                <p className="text-3xl font-bold text-primary">{stats.pass_rate}%</p>
              </div>
              <div className="text-4xl">📈</div>
            </div>
          </Card>
        </div>

        {/* Recent Tests */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Tests</h2>
          <div className="space-y-3">
            {recentTests.map((test) => (
              <div
                key={test.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    test.status === 'pass' ? 'bg-success' :
                    test.status === 'fail' ? 'bg-danger' :
                    'bg-warning animate-pulse'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900">{test.name}</p>
                    <p className="text-sm text-gray-600">{test.id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {test.status === 'running' ? 'Running...' : `${test.execution_time}s`}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(test.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Layout>
  );
};
```

---

### Step 6: Create Layout Components (1 hour)

#### `src/components/layout/Layout.tsx`
```typescript
import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 ml-64">
          {children}
        </main>
      </div>
    </div>
  );
};
```

#### `src/components/layout/Header.tsx`
```typescript
import React from 'react';
import { useNavigate } from 'react-router-dom';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8">
      <div className="flex items-center gap-3">
        <span className="text-2xl">🤖</span>
        <span className="text-xl font-bold text-gray-900">AI Web Test</span>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{user.full_name || 'User'}</span>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Logout
        </button>
      </div>
    </header>
  );
};
```

#### `src/components/layout/Sidebar.tsx`
```typescript
import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, FileText, Database, Settings } from 'lucide-react';

const navItems = [
  { path: '/dashboard', icon: Home, label: 'Dashboard' },
  { path: '/tests', icon: FileText, label: 'Tests' },
  { path: '/knowledge-base', icon: Database, label: 'Knowledge Base' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 fixed h-[calc(100vh-4rem)] mt-16">
      <nav className="p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};
```

---

### Step 7: Setup Routing (30 minutes)

#### Update `src/App.tsx`
```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import './index.css';

function App() {
  const isAuthenticated = !!localStorage.getItem('token');

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={isAuthenticated ? <DashboardPage /> : <Navigate to="/login" />}
        />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## ✅ Verification Checklist

After completing these steps, verify:

- [ ] React app runs at `http://localhost:5173/`
- [ ] Login page looks professional
- [ ] Can login with any username/password
- [ ] Dashboard displays after login
- [ ] Stats cards show mock data
- [ ] Recent tests list displays
- [ ] Sidebar navigation shows
- [ ] Logout button works
- [ ] Responsive design works on mobile/tablet/desktop

---

## 🎯 Next Steps (Tomorrow - Day 2)

1. Create Tests Page component
2. Create Knowledge Base Page component
3. Create Settings Page component
4. Add more mock data
5. Polish UI/UX
6. Add loading states
7. Add empty states
8. Test responsive design

---

## 📚 Resources

- **TailwindCSS Docs:** https://tailwindcss.com/docs
- **React Router Docs:** https://reactrouter.com/
- **Lucide Icons:** https://lucide.dev/icons/
- **TypeScript Handbook:** https://www.typescriptlang.org/docs/

---

## 🐛 Common Issues

**Issue:** Vite not found
**Solution:** `npm install -g vite`

**Issue:** TypeScript errors
**Solution:** Check `tsconfig.json` configuration

**Issue:** Tailwind not working
**Solution:** Verify `tailwind.config.js` and `index.css` are configured

---

**Happy Coding! 🚀**

