/**
 * Tests for agentWorkflowService.ts (mock stub)
 * Verifies the API client stub returns correctly shaped mock data
 * before the real backend (Developer A) is available.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import agentWorkflowService from '../../services/agentWorkflowService';
import type {
  GenerateTestsRequest,
  WorkflowStatusResponse,
  WorkflowResultsResponse,
} from '../../types/agentWorkflow.types';

// Mock the api module so tests never make real HTTP calls
vi.mock('../../services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  },
  apiHelpers: {
    useMockData: vi.fn().mockReturnValue(true),
    getErrorMessage: vi.fn((e: unknown) => String(e)),
  },
}));

describe('agentWorkflowService - Mock Stub', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // generateTests
  // ---------------------------------------------------------------------------
  describe('generateTests()', () => {
    it('should return a workflow_id string when mock data is enabled', async () => {
      const request: GenerateTestsRequest = { url: 'https://example.com' };
      const result = await agentWorkflowService.generateTests(request);

      expect(result).toHaveProperty('workflow_id');
      expect(typeof result.workflow_id).toBe('string');
      expect(result.workflow_id.length).toBeGreaterThan(0);
    });

    it('should return status pending for a new workflow', async () => {
      const request: GenerateTestsRequest = { url: 'https://example.com' };
      const result = await agentWorkflowService.generateTests(request);

      expect(result.status).toBe('pending');
    });

    it('should include message and estimated_duration_seconds in mock response', async () => {
      const request: GenerateTestsRequest = { url: 'https://example.com' };
      const result = await agentWorkflowService.generateTests(request);

      expect(result).toHaveProperty('message');
      expect(result).toHaveProperty('estimated_duration_seconds');
    });
  });

  // ---------------------------------------------------------------------------
  // getWorkflowStatus
  // ---------------------------------------------------------------------------
  describe('getWorkflowStatus()', () => {
    it('should return a WorkflowStatusResponse for a given workflow id', async () => {
      const response: WorkflowStatusResponse =
        await agentWorkflowService.getWorkflowStatus('wf-mock-001');

      expect(response).toHaveProperty('workflow_id');
      expect(response).toHaveProperty('status');
      expect(response).toHaveProperty('progress');
      expect(response).toHaveProperty('created_at');
      expect(response).toHaveProperty('updated_at');
    });

    it('should echo back the provided workflow id', async () => {
      const id = 'wf-mock-007';
      const response = await agentWorkflowService.getWorkflowStatus(id);
      expect(response.workflow_id).toBe(id);
    });

    it('should return a valid WorkflowStatus value', async () => {
      const response = await agentWorkflowService.getWorkflowStatus('wf-mock-001');
      const validStatuses = ['pending', 'running', 'completed', 'failed', 'cancelled'];
      expect(validStatuses).toContain(response.status);
    });

    it('should include progress with stage, percentage and message', async () => {
      const response = await agentWorkflowService.getWorkflowStatus('wf-mock-001');
      expect(response.progress).toHaveProperty('stage');
      expect(response.progress).toHaveProperty('percentage');
      expect(response.progress).toHaveProperty('message');
      expect(response.progress.percentage).toBeGreaterThanOrEqual(0);
      expect(response.progress.percentage).toBeLessThanOrEqual(100);
    });
  });

  // ---------------------------------------------------------------------------
  // getWorkflowResults
  // ---------------------------------------------------------------------------
  describe('getWorkflowResults()', () => {
    it('should return a WorkflowResultsResponse for a given workflow id', async () => {
      const response: WorkflowResultsResponse =
        await agentWorkflowService.getWorkflowResults('wf-mock-001');

      expect(response).toHaveProperty('workflow_id');
      expect(response).toHaveProperty('status');
      expect(response).toHaveProperty('test_cases');
      expect(response).toHaveProperty('summary');
      expect(response).toHaveProperty('generated_at');
    });

    it('should echo back the provided workflow id', async () => {
      const id = 'wf-mock-007';
      const response = await agentWorkflowService.getWorkflowResults(id);
      expect(response.workflow_id).toBe(id);
    });

    it('should return an array of test cases', async () => {
      const response = await agentWorkflowService.getWorkflowResults('wf-mock-001');
      expect(Array.isArray(response.test_cases)).toBe(true);
    });

    it('should include valid summary fields', async () => {
      const response = await agentWorkflowService.getWorkflowResults('wf-mock-001');
      expect(response.summary).toHaveProperty('total_tests');
      expect(response.summary).toHaveProperty('test_types');
      expect(response.summary).toHaveProperty('avg_confidence_score');
      expect(response.summary).toHaveProperty('total_steps');
      expect(response.summary.total_tests).toBeGreaterThanOrEqual(0);
    });
  });

  // ---------------------------------------------------------------------------
  // cancelWorkflow
  // ---------------------------------------------------------------------------
  describe('cancelWorkflow()', () => {
    it('should return success true for a mock cancellation', async () => {
      const result = await agentWorkflowService.cancelWorkflow('wf-mock-001');
      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
    });

    it('should return a message confirming cancellation', async () => {
      const result = await agentWorkflowService.cancelWorkflow('wf-mock-001');
      expect(typeof result.message).toBe('string');
    });
  });
});
