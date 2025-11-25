# Sprint 3 Frontend Development Guide
## Test Execution UI & Real-Time Monitoring

**Version:** 1.0  
**Date:** November 25, 2025  
**Backend Status:** ✅ Complete and Deployed  
**Frontend Status:** 🎯 Ready to Start  
**Estimated Duration:** 4 days

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Getting Started](#getting-started)
4. [Day 1-2: Test Execution UI](#day-1-2-test-execution-ui)
5. [Day 3-4: Execution Results & History](#day-3-4-execution-results--history)
6. [API Reference](#api-reference)
7. [Component Architecture](#component-architecture)
8. [Testing Guide](#testing-guide)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What You're Building

A **real-time test execution monitoring system** that allows users to:
1. ✅ Click "Run Test" to execute tests against real websites
2. ✅ See their position in the execution queue
3. ✅ Watch tests execute step-by-step in real-time
4. ✅ View screenshots from each test step
5. ✅ Browse execution history with filters
6. ✅ See statistics and analytics

### Backend Features Available

The backend team has completed:
- ✅ **Stagehand + Playwright Integration** - Tests execute in real Chrome browser
- ✅ **Queue System** - Max 5 concurrent executions, priority-based queuing
- ✅ **Screenshot Capture** - Every step saves a screenshot
- ✅ **Database Tracking** - Complete execution lifecycle recorded
- ✅ **RESTful API** - 10+ endpoints fully documented
- ✅ **100% Test Coverage** - All features verified working

### What Success Looks Like

By the end of Sprint 3, users will be able to:
```
1. Navigate to a test case
2. Click "Run Test" button
3. See "Test queued - Position #2 in queue"
4. Navigate to execution page
5. Watch in real-time as:
   - Step 1: Navigate to homepage ✅ (2.3s)
   - Step 2: Click login button ▶️ (running...)
   - Step 3: Enter credentials ⏳ (pending)
6. View screenshot thumbnails for each step
7. See final result: "Test Passed ✅ (12.5s)"
8. Browse all past executions
9. View statistics dashboard
```

---

## Prerequisites

### 1. Repository Access
```bash
# Clone the repository
git clone https://github.com/deencat/AI-Web-Test-v1.git
cd AI-Web-Test-v1

# Ensure you're on main branch (backend features are deployed here)
git checkout main
git pull origin main
```

### 2. Backend Server Running

**Start the backend:**
```bash
cd backend
.\venv\Scripts\activate
python start_server.py
```

**Verify it's running:**
- Open: `http://127.0.0.1:8000/docs`
- You should see Swagger UI with all API endpoints

### 3. Test Account

**Default admin account:**
- Email: `admin@aiwebtest.com`
- Password: `admin123`

**Get your auth token:**
```bash
# Login via API
POST http://127.0.0.1:8000/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@aiwebtest.com&password=admin123

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}

# Use in subsequent requests:
Authorization: Bearer <access_token>
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Tech Stack Assumption:**
- React 18+ or Next.js
- TypeScript
- TailwindCSS or Material-UI
- React Query or SWR (for API calls)
- React Router (for navigation)

---

## Getting Started

### Step 1: Explore the API

**Open Swagger UI:**
```
http://127.0.0.1:8000/docs
```

**Try these endpoints:**

1. **Login** (to get token)
   - POST `/api/v1/auth/login`
   - Body: `username=admin@aiwebtest.com&password=admin123`

2. **List Test Cases**
   - GET `/api/v1/tests`
   - Note the test IDs

3. **Run a Test**
   - POST `/api/v1/tests/{test_id}/run`
   - Body: `{ "priority": 5 }`
   - Note the execution ID in response

4. **Watch Execution**
   - GET `/api/v1/executions/{execution_id}`
   - Call this multiple times (every 2 seconds)
   - Watch status change: pending → running → completed

5. **View Queue Status**
   - GET `/api/v1/executions/queue/status`
   - See how many executions are active

### Step 2: Test Backend Manually

**Run a complete test flow:**

```bash
cd backend
.\venv\Scripts\activate
python test_final_verification.py
```

This will:
1. Login
2. Create/get a test case
3. Queue 5 executions
4. Wait for them to complete
5. Display results

**Expected output:**
```
[OK] Login successful
[OK] Queue status: operational
[OK] Queued 5 executions
[OK] Completed: 5/5
[OK] Passed: 5/5
[OK] FINAL VERIFICATION: PASSED
```

### Step 3: View Sample Data

**Check screenshots directory:**
```bash
cd backend/artifacts/screenshots
ls -la
```

You'll see files like:
- `exec_53_step_0_pass.png` - Execution #53, Step 0, Passed
- `exec_53_step_1_pass.png` - Execution #53, Step 1, Passed
- `exec_54_step_0_pass.png` - Execution #54, Step 0, Passed

These are actual screenshots from test executions!

**View in browser:**
```
http://127.0.0.1:8000/artifacts/screenshots/exec_53_step_0_pass.png
```

---

## Day 1-2: Test Execution UI

### Goal
Users can run tests and see real-time progress

### Task 1.1: "Run Test" Button Component

**Location:** Test detail page (e.g., `/tests/{id}`)

**Component:** `RunTestButton.tsx`

```typescript
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

interface RunTestButtonProps {
  testId: number;
  onExecutionStarted?: (executionId: number) => void;
}

export const RunTestButton: React.FC<RunTestButtonProps> = ({ 
  testId, 
  onExecutionStarted 
}) => {
  const [isRunning, setIsRunning] = useState(false);

  const runTestMutation = useMutation({
    mutationFn: async (priority: number = 5) => {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/tests/${testId}/run`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ priority }),
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to start test execution');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      // data contains: { id, status, test_case_id, queued_at, priority }
      console.log('Test queued:', data);
      onExecutionStarted?.(data.id);
      
      // Show success notification
      toast.success(`Test queued! Execution ID: ${data.id}`);
      
      // Navigate to execution page
      router.push(`/executions/${data.id}`);
    },
    onError: (error) => {
      toast.error('Failed to run test: ' + error.message);
    },
  });

  return (
    <button
      onClick={() => runTestMutation.mutate(5)}
      disabled={runTestMutation.isPending}
      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
    >
      {runTestMutation.isPending ? (
        <>
          <Spinner className="inline mr-2" />
          Queueing...
        </>
      ) : (
        <>
          <PlayIcon className="inline mr-2" />
          Run Test
        </>
      )}
    </button>
  );
};
```

**API Endpoint:**
```
POST /api/v1/tests/{test_id}/run
Request: { priority?: 1 | 5 | 10 }  // Optional, default: 5
Response: {
  id: number,                  // Execution ID
  status: "pending",
  test_case_id: number,
  queued_at: "2025-11-25T10:30:00",
  priority: 5,
  queue_position: 2
}
```

**Where to Add:**
- Test detail page header
- Test list (as an action button per row)
- Test case card (as a card action)

---

### Task 1.2: Queue Status Indicator

**Component:** `QueueStatusWidget.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';

interface QueueStatus {
  status: 'operational' | 'stopped';
  active_count: number;
  pending_count: number;
  max_concurrent: number;
  queue_size: number;
  is_under_limit: boolean;
}

export const QueueStatusWidget: React.FC = () => {
  const { data: queueStatus, isLoading } = useQuery({
    queryKey: ['queue-status'],
    queryFn: async () => {
      const response = await fetch(
        'http://127.0.0.1:8000/api/v1/executions/queue/status',
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      return response.json() as Promise<QueueStatus>;
    },
    refetchInterval: 2000, // Refresh every 2 seconds
  });

  if (isLoading || !queueStatus) {
    return <div>Loading...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-2">Queue Status</h3>
      
      <div className="space-y-2">
        {/* Status Indicator */}
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full mr-2 ${
            queueStatus.status === 'operational' ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="capitalize">{queueStatus.status}</span>
        </div>

        {/* Active Executions */}
        <div className="flex justify-between">
          <span className="text-gray-600">Active:</span>
          <span className="font-semibold">
            {queueStatus.active_count} / {queueStatus.max_concurrent}
          </span>
        </div>

        {/* Pending in Queue */}
        <div className="flex justify-between">
          <span className="text-gray-600">Pending:</span>
          <span className="font-semibold">{queueStatus.pending_count}</span>
        </div>

        {/* Total Queue Size */}
        <div className="flex justify-between">
          <span className="text-gray-600">Total:</span>
          <span className="font-semibold">{queueStatus.queue_size}</span>
        </div>

        {/* Progress Bar */}
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ 
                width: `${(queueStatus.active_count / queueStatus.max_concurrent) * 100}%` 
              }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {queueStatus.is_under_limit 
              ? '✅ Queue has capacity' 
              : '⚠️ Queue at max capacity'
            }
          </p>
        </div>
      </div>
    </div>
  );
};
```

**API Endpoint:**
```
GET /api/v1/executions/queue/status
Response: {
  status: "operational",
  active_count: 3,
  pending_count: 2,
  max_concurrent: 5,
  queue_size: 5,
  is_under_limit: false
}
```

**Where to Display:**
- Dashboard sidebar
- Executions list page header
- Global status bar

---

### Task 1.3: Execution Progress Page

**Route:** `/executions/{execution_id}`

**Component:** `ExecutionProgressPage.tsx`

```typescript
import { useParams } from 'react-router-dom';
import { useQuery } from '@tantml:react-query';

interface ExecutionDetail {
  id: number;
  test_case_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result: 'passed' | 'failed' | 'error' | null;
  started_at: string;
  completed_at: string | null;
  duration: number | null;
  steps_total: number;
  steps_passed: number;
  steps_failed: number;
  error_message: string | null;
  test_case: {
    name: string;
    description: string;
  };
  steps: Array<{
    id: number;
    step_order: number;
    action: string;
    expected_result: string;
    actual_result: string | null;
    status: 'pending' | 'running' | 'passed' | 'failed';
    screenshot_path: string | null;
    error_message: string | null;
  }>;
}

export const ExecutionProgressPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();

  const { data: execution, isLoading } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: async () => {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/executions/${executionId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      return response.json() as Promise<ExecutionDetail>;
    },
    refetchInterval: (data) => {
      // Only refresh if still running
      return data?.status === 'pending' || data?.status === 'running' 
        ? 2000  // 2 seconds
        : false; // Stop refreshing when completed
    },
  });

  if (isLoading || !execution) {
    return <LoadingSpinner />;
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold mb-2">
              {execution.test_case.name}
            </h1>
            <p className="text-gray-600">{execution.test_case.description}</p>
          </div>
          <ExecutionStatusBadge status={execution.status} result={execution.result} />
        </div>

        {/* Execution Info */}
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div>
            <span className="text-gray-600 text-sm">Execution ID</span>
            <p className="font-semibold">#{execution.id}</p>
          </div>
          <div>
            <span className="text-gray-600 text-sm">Started</span>
            <p className="font-semibold">
              {new Date(execution.started_at).toLocaleTimeString()}
            </p>
          </div>
          <div>
            <span className="text-gray-600 text-sm">Duration</span>
            <p className="font-semibold">
              {execution.duration ? `${execution.duration}s` : 'In progress...'}
            </p>
          </div>
          <div>
            <span className="text-gray-600 text-sm">Progress</span>
            <p className="font-semibold">
              {execution.steps_passed + execution.steps_failed} / {execution.steps_total}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all ${
                execution.result === 'passed' ? 'bg-green-500' :
                execution.result === 'failed' ? 'bg-red-500' :
                'bg-blue-500'
              }`}
              style={{ 
                width: `${((execution.steps_passed + execution.steps_failed) / execution.steps_total) * 100}%` 
              }}
            />
          </div>
        </div>
      </div>

      {/* Steps List */}
      <StepProgressList steps={execution.steps} />

      {/* Error Message */}
      {execution.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
          <h3 className="text-red-800 font-semibold mb-2">Error</h3>
          <p className="text-red-700">{execution.error_message}</p>
        </div>
      )}
    </div>
  );
};
```

**API Endpoint:**
```
GET /api/v1/executions/{execution_id}
Response: ExecutionDetail (see TypeScript interface above)
```

---

### Task 1.4: Step-by-Step Progress Display

**Component:** `StepProgressList.tsx`

```typescript
interface Step {
  id: number;
  step_order: number;
  action: string;
  expected_result: string;
  actual_result: string | null;
  status: 'pending' | 'running' | 'passed' | 'failed';
  screenshot_path: string | null;
  error_message: string | null;
}

interface StepProgressListProps {
  steps: Step[];
}

export const StepProgressList: React.FC<StepProgressListProps> = ({ steps }) => {
  return (
    <div className="space-y-4">
      {steps.map((step) => (
        <StepCard key={step.id} step={step} />
      ))}
    </div>
  );
};

const StepCard: React.FC<{ step: Step }> = ({ step }) => {
  const getStatusIcon = () => {
    switch (step.status) {
      case 'pending':
        return <span className="text-gray-400">⏳</span>;
      case 'running':
        return <span className="text-blue-500 animate-spin">▶️</span>;
      case 'passed':
        return <span className="text-green-500">✅</span>;
      case 'failed':
        return <span className="text-red-500">❌</span>;
    }
  };

  const getStatusColor = () => {
    switch (step.status) {
      case 'pending': return 'border-gray-300 bg-gray-50';
      case 'running': return 'border-blue-500 bg-blue-50';
      case 'passed': return 'border-green-500 bg-green-50';
      case 'failed': return 'border-red-500 bg-red-50';
    }
  };

  return (
    <div className={`border-l-4 rounded-lg p-4 ${getStatusColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start flex-1">
          <span className="text-2xl mr-3">{getStatusIcon()}</span>
          <div className="flex-1">
            <h3 className="font-semibold text-lg">
              Step {step.step_order + 1}: {step.action}
            </h3>
            <p className="text-gray-600 mt-1">
              <span className="font-medium">Expected:</span> {step.expected_result}
            </p>
            {step.actual_result && (
              <p className="text-gray-600 mt-1">
                <span className="font-medium">Actual:</span> {step.actual_result}
              </p>
            )}
            {step.error_message && (
              <p className="text-red-600 mt-2">
                <span className="font-medium">Error:</span> {step.error_message}
              </p>
            )}
          </div>
        </div>

        {/* Screenshot Thumbnail */}
        {step.screenshot_path && (
          <div className="ml-4">
            <img
              src={`http://127.0.0.1:8000${step.screenshot_path}`}
              alt={`Step ${step.step_order} screenshot`}
              className="w-32 h-24 object-cover rounded cursor-pointer hover:opacity-80"
              onClick={() => {
                // Open full-size modal
                openScreenshotModal(step.screenshot_path);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};
```

---

### Day 1-2 Deliverables

✅ **Checklist:**
- [ ] Run Test button functional
- [ ] Test queues successfully
- [ ] Queue status widget displays real-time data
- [ ] Execution progress page created
- [ ] Auto-refresh working (2-second intervals)
- [ ] Steps display with correct status icons
- [ ] Status colors match step status
- [ ] Screenshot thumbnails display
- [ ] Progress bar animates correctly
- [ ] Error messages display properly

---

## Day 3-4: Execution Results & History

### Task 2.1: Execution History List

**Route:** `/executions`

**Component:** `ExecutionHistoryPage.tsx`

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface ExecutionListItem {
  id: number;
  test_case_id: number;
  test_case_name: string;
  status: string;
  result: string | null;
  started_at: string;
  duration: number | null;
  steps_passed: number;
  steps_total: number;
}

export const ExecutionHistoryPage: React.FC = () => {
  const [filters, setFilters] = useState({
    status: '',
    result: '',
    skip: 0,
    limit: 20,
  });

  const { data: executions, isLoading } = useQuery({
    queryKey: ['executions', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.result) params.append('result', filters.result);
      params.append('skip', filters.skip.toString());
      params.append('limit', filters.limit.toString());

      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/executions?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      return response.json();
    },
  });

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Execution History</h1>

      {/* Filters */}
      <ExecutionFilters filters={filters} onChange={setFilters} />

      {/* Table */}
      <ExecutionTable 
        executions={executions?.items || []} 
        isLoading={isLoading}
      />

      {/* Pagination */}
      <Pagination 
        total={executions?.total || 0}
        skip={filters.skip}
        limit={filters.limit}
        onChange={(skip) => setFilters({ ...filters, skip })}
      />
    </div>
  );
};
```

**API Endpoint:**
```
GET /api/v1/executions?skip=0&limit=20&status=completed&result=passed
Response: {
  items: ExecutionListItem[],
  total: number,
  skip: number,
  limit: number
}
```

---

### Task 2.2: Screenshot Gallery

**Component:** `ScreenshotGallery.tsx`

```typescript
interface ScreenshotGalleryProps {
  steps: Step[];
}

export const ScreenshotGallery: React.FC<ScreenshotGalleryProps> = ({ steps }) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const screenshots = steps
    .filter(step => step.screenshot_path)
    .map((step, index) => ({
      path: step.screenshot_path!,
      action: step.action,
      expected: step.expected_result,
      order: step.step_order,
      status: step.status,
    }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Screenshots</h2>

      {/* Thumbnail Grid */}
      <div className="grid grid-cols-4 gap-4">
        {screenshots.map((screenshot, index) => (
          <div
            key={index}
            className="cursor-pointer hover:opacity-80 transition"
            onClick={() => setSelectedIndex(index)}
          >
            <img
              src={`http://127.0.0.1:8000${screenshot.path}`}
              alt={`Step ${screenshot.order}`}
              className="w-full h-32 object-cover rounded"
            />
            <p className="text-sm text-center mt-2">
              Step {screenshot.order + 1}
            </p>
          </div>
        ))}
      </div>

      {/* Full-Size Modal */}
      {selectedIndex !== null && (
        <ScreenshotModal
          screenshots={screenshots}
          currentIndex={selectedIndex}
          onClose={() => setSelectedIndex(null)}
          onNavigate={setSelectedIndex}
        />
      )}
    </div>
  );
};
```

---

### Task 2.3: Execution Statistics Dashboard

**Component:** `ExecutionStatsWidget.tsx`

```typescript
interface ExecutionStats {
  total_count: number;
  completed_count: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  pass_rate: number;
  average_duration: number;
}

export const ExecutionStatsWidget: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['execution-stats'],
    queryFn: async () => {
      const response = await fetch(
        'http://127.0.0.1:8000/api/v1/executions/stats',
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      return response.json() as Promise<ExecutionStats>;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading || !stats) {
    return <LoadingSpinner />;
  }

  return (
    <div className="grid grid-cols-4 gap-4">
      {/* Total Executions */}
      <StatCard
        title="Total Executions"
        value={stats.total_count}
        icon="📊"
        color="blue"
      />

      {/* Pass Rate */}
      <StatCard
        title="Pass Rate"
        value={`${stats.pass_rate.toFixed(1)}%`}
        icon="✅"
        color="green"
      />

      {/* Failed Tests */}
      <StatCard
        title="Failed"
        value={stats.failed_count}
        icon="❌"
        color="red"
      />

      {/* Avg Duration */}
      <StatCard
        title="Avg Duration"
        value={`${stats.average_duration.toFixed(1)}s`}
        icon="⏱️"
        color="purple"
      />
    </div>
  );
};
```

**API Endpoint:**
```
GET /api/v1/executions/stats
Response: {
  total_count: 45,
  completed_count: 42,
  passed_count: 38,
  failed_count: 4,
  error_count: 3,
  pass_rate: 90.5,
  average_duration: 12.3
}
```

---

### Day 3-4 Deliverables

✅ **Checklist:**
- [ ] Execution history list displays
- [ ] Filters work (status, result)
- [ ] Pagination functional
- [ ] Click row navigates to detail page
- [ ] Screenshot gallery displays thumbnails
- [ ] Click thumbnail opens full-size modal
- [ ] Modal has prev/next navigation
- [ ] Statistics dashboard shows key metrics
- [ ] Charts display (pie, line, bar)
- [ ] Delete execution button works
- [ ] Confirm dialog before delete

---

## API Reference

### Base Configuration

```typescript
// api/config.ts
export const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
});
```

### All Execution Endpoints

```typescript
// api/executions.ts

// Execute a test
export async function executeTest(testId: number, priority: number = 5) {
  const response = await fetch(`${API_BASE_URL}/tests/${testId}/run`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ priority }),
  });
  return response.json();
}

// Get execution details
export async function getExecution(executionId: number) {
  const response = await fetch(`${API_BASE_URL}/executions/${executionId}`, {
    headers: getAuthHeaders(),
  });
  return response.json();
}

// List executions
export async function listExecutions(params: {
  skip?: number;
  limit?: number;
  status?: string;
  result?: string;
}) {
  const queryParams = new URLSearchParams(params as any);
  const response = await fetch(
    `${API_BASE_URL}/executions?${queryParams}`,
    { headers: getAuthHeaders() }
  );
  return response.json();
}

// Get queue status
export async function getQueueStatus() {
  const response = await fetch(`${API_BASE_URL}/executions/queue/status`, {
    headers: getAuthHeaders(),
  });
  return response.json();
}

// Get execution statistics
export async function getExecutionStats() {
  const response = await fetch(`${API_BASE_URL}/executions/stats`, {
    headers: getAuthHeaders(),
  });
  return response.json();
}

// Delete execution
export async function deleteExecution(executionId: number) {
  const response = await fetch(`${API_BASE_URL}/executions/${executionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return response.json();
}
```

---

## Component Architecture

### Recommended Structure

```
frontend/src/
├── pages/
│   ├── executions/
│   │   ├── [id].tsx                 # Execution detail page
│   │   └── index.tsx                # Execution history list
│   └── tests/
│       └── [id].tsx                 # Test detail (add Run button here)
├── components/
│   ├── executions/
│   │   ├── RunTestButton.tsx        # Button to execute test
│   │   ├── QueueStatusWidget.tsx    # Queue status display
│   │   ├── ExecutionStatusBadge.tsx # Status badge component
│   │   ├── ExecutionProgressPage.tsx
│   │   ├── StepProgressList.tsx     # List of steps
│   │   ├── StepCard.tsx             # Individual step
│   │   ├── ExecutionTable.tsx       # Table view
│   │   ├── ExecutionFilters.tsx     # Filter controls
│   │   ├── ScreenshotGallery.tsx    # Screenshot gallery
│   │   ├── ScreenshotModal.tsx      # Full-size viewer
│   │   ├── ExecutionStatsWidget.tsx # Statistics widget
│   │   └── DeleteExecutionButton.tsx
│   └── shared/
│       ├── LoadingSpinner.tsx
│       ├── Pagination.tsx
│       └── StatusBadge.tsx
├── api/
│   ├── config.ts                    # API configuration
│   ├── auth.ts                      # Auth functions
│   └── executions.ts                # Execution API functions
└── types/
    └── execution.ts                 # TypeScript interfaces
```

---

## Testing Guide

### Manual Testing Checklist

**Day 1-2 Testing:**
1. [ ] Navigate to a test case
2. [ ] Click "Run Test" button
3. [ ] Verify test queues (check API response)
4. [ ] Navigate to execution page
5. [ ] Verify page auto-refreshes every 2 seconds
6. [ ] Watch steps change status in real-time
7. [ ] Verify screenshots display
8. [ ] Click screenshot thumbnail to enlarge
9. [ ] Verify queue status widget updates
10. [ ] Wait for test completion
11. [ ] Verify final status and result display

**Day 3-4 Testing:**
1. [ ] Navigate to executions list
2. [ ] Verify executions display
3. [ ] Test filter by status
4. [ ] Test filter by result
5. [ ] Test pagination
6. [ ] Click execution row → navigate to detail
7. [ ] View screenshot gallery
8. [ ] Navigate through screenshots in modal
9. [ ] Download screenshot
10. [ ] View statistics dashboard
11. [ ] Verify charts display correctly
12. [ ] Delete an execution
13. [ ] Confirm it's removed from list

### Automated Testing

```typescript
// Test: Run Test Button
describe('RunTestButton', () => {
  it('should execute test when clicked', async () => {
    render(<RunTestButton testId={1} />);
    
    const button = screen.getByText('Run Test');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(button).toHaveTextContent('Queueing...');
    });
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/executions/123');
    });
  });
});

// Test: Execution Progress Page
describe('ExecutionProgressPage', () => {
  it('should display execution details', async () => {
    render(<ExecutionProgressPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Name')).toBeInTheDocument();
      expect(screen.getByText('Step 1:')).toBeInTheDocument();
    });
  });

  it('should auto-refresh while running', async () => {
    jest.useFakeTimers();
    render(<ExecutionProgressPage />);
    
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
});
```

---

## Troubleshooting

### Common Issues

**1. CORS Errors**

**Problem:** Browser blocks API requests

**Solution:** Backend already has CORS configured, but verify:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Authentication Fails**

**Problem:** 401 Unauthorized errors

**Solution:** Check token is stored and sent correctly:
```typescript
// Verify token exists
console.log('Token:', localStorage.getItem('token'));

// Check request headers
console.log('Headers:', {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
});
```

**3. Images Don't Load**

**Problem:** Screenshot images return 404

**Solution:** Verify correct path:
```typescript
// Correct format
const imagePath = `http://127.0.0.1:8000${screenshot_path}`;
// screenshot_path from API: "/artifacts/screenshots/exec_53_step_0_pass.png"
```

**4. Auto-Refresh Not Working**

**Problem:** Execution status doesn't update

**Solution:** Check refetch interval:
```typescript
const { data } = useQuery({
  queryKey: ['execution', id],
  queryFn: fetchExecution,
  refetchInterval: (data) => {
    // Only refresh if still running
    return data?.status === 'running' ? 2000 : false;
  },
});
```

**5. Backend Not Running**

**Problem:** Connection refused errors

**Solution:** Start backend server:
```bash
cd backend
.\venv\Scripts\activate
python start_server.py
```

Verify: `http://127.0.0.1:8000/docs`

---

## Next Steps

### After Sprint 3

**Sprint 4 Preview:**
- WebSocket integration for real-time updates (no polling)
- Advanced analytics and reporting
- Test comparison (compare executions)
- Execution scheduling
- Email notifications

**Frontend Improvements:**
- Dark mode
- Mobile responsive design
- Keyboard shortcuts
- Export results to PDF
- Share execution links

---

## Resources

### Documentation
- **API Docs:** `http://127.0.0.1:8000/docs`
- **UI Design:** `project-documents/ai-web-test-ui-design-document.md`
- **Backend PRD:** `project-documents/AI-Web-Test-v1-PRD.md`
- **SRS:** `project-documents/AI-Web-Test-v1-SRS.md`

### Backend Developer Contact
- For API questions or issues
- For backend feature requests
- For data format clarifications

### Example Data
- Test executions in database
- Screenshots in `backend/artifacts/screenshots/`
- Run `backend/test_final_verification.py` for sample data

---

## Questions?

**Common Questions:**

**Q: How often should I poll the API?**  
A: Every 2 seconds while execution is running. Stop when completed.

**Q: What's the max concurrent executions?**  
A: 5 simultaneous executions. Queue handles overflow.

**Q: How long do tests take to complete?**  
A: Average 12 seconds. Simple tests: 5-8s. Complex: 20-30s.

**Q: Can I cancel a running execution?**  
A: Not in Sprint 3. This is a Sprint 4 feature.

**Q: Where are screenshots stored?**  
A: `backend/artifacts/screenshots/` - accessible via HTTP.

**Q: What if execution fails?**  
A: Status becomes "failed", error_message explains why.

**Q: Can I re-run a failed test?**  
A: Yes, click "Run Test" again. New execution is created.

---

**Ready to start building? Good luck with Sprint 3! 🚀**

---

**Document Version:** 1.0  
**Last Updated:** November 25, 2025  
**Next Review:** After Sprint 3 completion

