import { Test } from '../types/api';

export const mockTests: Test[] = [
  {
    id: 'TEST-001',
    name: 'Login Flow Test',
    description: 'Test the Three Hong Kong customer login flow',
    status: 'passed',
    priority: 'high',
    agent: 'Explorer Agent',
    created_at: '2025-11-01T10:00:00Z',
    updated_at: '2025-11-01T10:45:00Z',
    last_run: '2025-11-01T10:45:00Z',
    execution_time: 45.2,
  },
  {
    id: 'TEST-002',
    name: 'API Health Check',
    description: 'Verify API endpoints are responding correctly',
    status: 'passed',
    priority: 'medium',
    agent: 'Developer Agent',
    created_at: '2025-11-01T11:00:00Z',
    updated_at: '2025-11-01T11:32:00Z',
    last_run: '2025-11-01T11:32:00Z',
    execution_time: 32.1,
  },
  {
    id: 'TEST-003',
    name: 'Payment Gateway Test',
    description: 'Test payment processing functionality',
    status: 'failed',
    priority: 'high',
    agent: 'Explorer Agent',
    created_at: '2025-11-01T12:00:00Z',
    updated_at: '2025-11-01T12:28:00Z',
    last_run: '2025-11-01T12:28:00Z',
    execution_time: 28.5,
  },
];

export const mockDashboardStats = {
  total_tests: 156,
  passed: 142,
  failed: 8,
  running: 6,
  active_agents: 4,
  pass_rate: 91.0,
  last_run: '2025-11-01T13:30:00Z',
};

export const mockAgentActivity = [
  {
    id: '1',
    agent: 'Explorer Agent',
    status: 'active',
    current_task: 'Generating test cases for checkout flow',
    last_activity: '2025-11-10T10:30:00Z',
  },
  {
    id: '2',
    agent: 'Developer Agent',
    status: 'active',
    current_task: 'Executing API health checks',
    last_activity: '2025-11-10T10:28:00Z',
  },
  {
    id: '3',
    agent: 'Evolution Agent',
    status: 'idle',
    current_task: 'Monitoring for test failures',
    last_activity: '2025-11-10T10:15:00Z',
  },
];

// Test trend data for charts (last 7 days)
export const mockTestTrends = [
  { date: '2025-11-13', passed: 18, failed: 2, total: 20 },
  { date: '2025-11-14', passed: 22, failed: 1, total: 23 },
  { date: '2025-11-15', passed: 19, failed: 3, total: 22 },
  { date: '2025-11-16', passed: 24, failed: 1, total: 25 },
  { date: '2025-11-17', passed: 21, failed: 2, total: 23 },
  { date: '2025-11-18', passed: 26, failed: 1, total: 27 },
  { date: '2025-11-19', passed: 28, failed: 2, total: 30 },
];
