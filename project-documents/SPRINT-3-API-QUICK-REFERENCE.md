# Sprint 3 - API Quick Reference Card
## Test Execution Endpoints

**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Auth:** `Authorization: Bearer <token>`  
**Docs:** `http://127.0.0.1:8000/docs`

---

## Authentication

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@aiwebtest.com&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Use in requests:**
```http
Authorization: Bearer <access_token>
```

---

## Test Execution

### Execute Test
```http
POST /tests/{test_id}/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "priority": 5  // 1=high, 5=medium, 10=low (optional)
}
```

**Response:**
```json
{
  "id": 123,
  "status": "pending",
  "test_case_id": 5,
  "queued_at": "2025-11-25T10:30:00",
  "priority": 5,
  "queue_position": 2
}
```

---

### Get Execution Details
```http
GET /executions/{execution_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 123,
  "test_case_id": 5,
  "status": "running",  // pending | running | completed | failed
  "result": null,       // passed | failed | error | null
  "started_at": "2025-11-25T10:30:05",
  "completed_at": null,
  "duration": null,
  "steps_total": 4,
  "steps_passed": 2,
  "steps_failed": 0,
  "error_message": null,
  "test_case": {
    "name": "Login Flow Test",
    "description": "Test user login functionality"
  },
  "steps": [
    {
      "id": 456,
      "step_order": 0,
      "action": "Navigate to homepage",
      "expected_result": "Homepage loads successfully",
      "actual_result": "Page loaded in 2.3s",
      "status": "passed",
      "screenshot_path": "/artifacts/screenshots/exec_123_step_0_pass.png",
      "error_message": null
    },
    {
      "id": 457,
      "step_order": 1,
      "action": "Click login button",
      "expected_result": "Login form appears",
      "actual_result": "Form displayed",
      "status": "passed",
      "screenshot_path": "/artifacts/screenshots/exec_123_step_1_pass.png",
      "error_message": null
    },
    {
      "id": 458,
      "step_order": 2,
      "action": "Enter credentials",
      "expected_result": "Credentials accepted",
      "actual_result": null,  // Still running
      "status": "running",
      "screenshot_path": null,
      "error_message": null
    },
    {
      "id": 459,
      "step_order": 3,
      "action": "Verify dashboard",
      "expected_result": "Dashboard loads",
      "actual_result": null,  // Not started yet
      "status": "pending",
      "screenshot_path": null,
      "error_message": null
    }
  ]
}
```

**Poll this endpoint every 2 seconds while `status` is "pending" or "running"**

---

### List Executions
```http
GET /executions?skip=0&limit=20&status=completed&result=passed
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (number): Pagination offset (default: 0)
- `limit` (number): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (pending | running | completed | failed)
- `result` (string): Filter by result (passed | failed | error)

**Response:**
```json
{
  "items": [
    {
      "id": 123,
      "test_case_id": 5,
      "test_case_name": "Login Flow Test",
      "status": "completed",
      "result": "passed",
      "started_at": "2025-11-25T10:30:00",
      "duration": 12.5,
      "steps_passed": 4,
      "steps_total": 4
    },
    // ... more executions
  ],
  "total": 45,
  "skip": 0,
  "limit": 20
}
```

---

### Delete Execution
```http
DELETE /executions/{execution_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Execution deleted successfully"
}
```

---

## Queue Management

### Get Queue Status
```http
GET /executions/queue/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "operational",  // operational | stopped
  "active_count": 3,        // Currently running
  "pending_count": 2,       // Waiting in queue
  "max_concurrent": 5,      // Max simultaneous executions
  "queue_size": 5,          // Total queued + active
  "is_under_limit": false   // Can accept more?
}
```

**Poll every 2 seconds to update UI**

---

### Get Queue Statistics
```http
GET /executions/queue/statistics
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_processed": 128,
  "total_successful": 115,
  "total_failed": 13,
  "success_rate": 89.84,
  "average_duration": 12.3
}
```

---

### Get Active Executions
```http
GET /executions/queue/active
Authorization: Bearer <token>
```

**Response:**
```json
{
  "active_executions": [
    {
      "id": 123,
      "test_case_id": 5,
      "test_case_name": "Login Test",
      "started_at": "2025-11-25T10:30:00",
      "priority": 5
    },
    // ... up to 5 active executions
  ],
  "count": 3
}
```

---

### Clear Queue (Admin Only)
```http
POST /executions/queue/clear
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Queue cleared",
  "cleared_count": 7
}
```

---

## Execution Statistics

### Get Execution Stats
```http
GET /executions/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_count": 45,
  "completed_count": 42,
  "passed_count": 38,
  "failed_count": 4,
  "error_count": 3,
  "pass_rate": 90.5,
  "average_duration": 12.3
}
```

---

## Screenshots

### Get Screenshot
```http
GET /artifacts/screenshots/{filename}
```

**Filename Format:**
- `exec_{execution_id}_step_{step_order}_pass.png`
- `exec_{execution_id}_step_{step_order}_fail.png`

**Example:**
```
http://127.0.0.1:8000/artifacts/screenshots/exec_123_step_0_pass.png
```

**No authentication required for screenshots**

---

## Status & Result Values

### Execution Status
- `pending` - Queued, not started yet
- `running` - Currently executing
- `completed` - Finished successfully (check `result`)
- `failed` - Execution failed (system error)

### Execution Result
- `passed` - All steps passed ✅
- `failed` - One or more steps failed ❌
- `error` - System error occurred 🔧
- `null` - Not completed yet

### Step Status
- `pending` - Not started yet ⏳
- `running` - Currently executing ▶️
- `passed` - Step succeeded ✅
- `failed` - Step failed ❌

---

## Priority Levels

- `1` - **High Priority** (executes first)
- `5` - **Medium Priority** (default)
- `10` - **Low Priority** (executes last)

---

## Polling Strategy

### Execution Detail Page
```typescript
// Poll every 2 seconds while running
const { data } = useQuery({
  queryKey: ['execution', id],
  queryFn: () => fetch(`/executions/${id}`),
  refetchInterval: (data) => {
    return data?.status === 'pending' || data?.status === 'running' 
      ? 2000  // 2 seconds
      : false; // Stop when completed
  },
});
```

### Queue Status Widget
```typescript
// Poll every 2 seconds continuously
const { data } = useQuery({
  queryKey: ['queue-status'],
  queryFn: () => fetch('/executions/queue/status'),
  refetchInterval: 2000, // Always refresh
});
```

### Execution Statistics
```typescript
// Poll every 10 seconds
const { data } = useQuery({
  queryKey: ['execution-stats'],
  queryFn: () => fetch('/executions/stats'),
  refetchInterval: 10000, // 10 seconds
});
```

---

## Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created (execution queued)
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (execution doesn't exist)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "detail": "Error message here"
}
```

### Example Error Handling
```typescript
try {
  const response = await fetch(url, options);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
} catch (error) {
  console.error('API Error:', error);
  toast.error(error.message);
}
```

---

## Quick Test Script

### Test All Endpoints
```typescript
// 1. Login
const loginResponse = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=admin@aiwebtest.com&password=admin123'
});
const { access_token } = await loginResponse.json();

// 2. Execute test
const runResponse = await fetch('http://127.0.0.1:8000/api/v1/tests/1/run', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ priority: 5 })
});
const { id: executionId } = await runResponse.json();
console.log('Execution ID:', executionId);

// 3. Poll execution status
const checkStatus = async () => {
  const response = await fetch(
    `http://127.0.0.1:8000/api/v1/executions/${executionId}`,
    {
      headers: { 'Authorization': `Bearer ${access_token}` }
    }
  );
  const execution = await response.json();
  console.log('Status:', execution.status, 'Result:', execution.result);
  
  if (execution.status === 'completed') {
    console.log('✅ Test finished!');
    console.log('Steps passed:', execution.steps_passed, '/', execution.steps_total);
    execution.steps.forEach(step => {
      console.log(`Step ${step.step_order}:`, step.status, step.screenshot_path);
    });
  } else {
    setTimeout(checkStatus, 2000); // Poll again in 2 seconds
  }
};

checkStatus();
```

---

## TypeScript Interfaces

```typescript
interface ExecutionResponse {
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
  queued_at?: string;
  priority?: number;
  queue_position?: number;
}

interface ExecutionDetailResponse extends ExecutionResponse {
  test_case: {
    name: string;
    description: string;
  };
  steps: Array<{
    id: number;
    execution_id: number;
    step_order: number;
    action: string;
    expected_result: string;
    actual_result: string | null;
    status: 'pending' | 'running' | 'passed' | 'failed';
    screenshot_path: string | null;
    error_message: string | null;
  }>;
}

interface QueueStatusResponse {
  status: 'operational' | 'stopped';
  active_count: number;
  pending_count: number;
  max_concurrent: number;
  queue_size: number;
  is_under_limit: boolean;
}

interface ExecutionStatistics {
  total_count: number;
  completed_count: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  pass_rate: number;
  average_duration: number;
}
```

---

## Common Use Cases

### Run a Test and Navigate to Progress Page
```typescript
const handleRunTest = async (testId: number) => {
  try {
    const response = await fetch(`/api/v1/tests/${testId}/run`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ priority: 5 })
    });
    
    const execution = await response.json();
    
    toast.success(`Test queued! Position #${execution.queue_position}`);
    router.push(`/executions/${execution.id}`);
  } catch (error) {
    toast.error('Failed to start test');
  }
};
```

### Display Real-Time Progress
```typescript
const ExecutionProgress = ({ executionId }: { executionId: number }) => {
  const { data: execution } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: () => fetchExecution(executionId),
    refetchInterval: (data) => 
      data?.status === 'running' || data?.status === 'pending' ? 2000 : false,
  });

  return (
    <div>
      <h2>Status: {execution?.status}</h2>
      <ProgressBar 
        value={execution?.steps_passed} 
        max={execution?.steps_total} 
      />
      <StepsList steps={execution?.steps || []} />
    </div>
  );
};
```

### Show Queue Status
```typescript
const QueueStatus = () => {
  const { data: queue } = useQuery({
    queryKey: ['queue'],
    queryFn: fetchQueueStatus,
    refetchInterval: 2000,
  });

  return (
    <div>
      <p>Active: {queue?.active_count} / {queue?.max_concurrent}</p>
      <p>Pending: {queue?.pending_count}</p>
      <p>Status: {queue?.is_under_limit ? '✅ Available' : '⚠️ At capacity'}</p>
    </div>
  );
};
```

---

## Need Help?

### Interactive Testing
Use Swagger UI: `http://127.0.0.1:8000/docs`
- Test all endpoints interactively
- See request/response examples
- Get auth token easily

### Sample Data
Run backend verification script:
```bash
cd backend
python test_final_verification.py
```

This creates 5 sample executions with screenshots.

### Questions?
Contact backend developer for:
- API clarifications
- Data format questions
- New endpoint requests
- Backend feature requests

---

**Quick Reference Version:** 1.0  
**Last Updated:** November 25, 2025  
**Backend Version:** Sprint 3 Day 2 Complete

