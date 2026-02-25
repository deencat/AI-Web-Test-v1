/**
 * Tests for agentWorkflowService — Real API integration (Sprint 10)
 *
 * No mock data path.  All methods make real HTTP calls via axios (mocked here).
 * Tests verify correct endpoint, request shape, response mapping, and error handling.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AxiosResponse } from 'axios';
import agentWorkflowService from '../../services/agentWorkflowService';
import type {
  GenerateTestsRequest,
  WorkflowStatusResponse,
  WorkflowResultsResponse,
} from '../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Mock axios so no real HTTP is made
// ---------------------------------------------------------------------------

const mockPost = vi.fn();
const mockGet = vi.fn();
const mockDelete = vi.fn();

vi.mock('../../services/api', () => ({
  default: {
    post:   (...args: unknown[]) => mockPost(...args),
    get:    (...args: unknown[]) => mockGet(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
  // Named export used by agentWorkflowService
  apiV2: {
    post:   (...args: unknown[]) => mockPost(...args),
    get:    (...args: unknown[]) => mockGet(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
  apiHelpers: {
    useMockData:    vi.fn().mockReturnValue(false), // ← REAL API
    getErrorMessage: vi.fn((e: unknown) => (e instanceof Error ? e.message : String(e))),
  },
}));

// ---------------------------------------------------------------------------
// Fixtures — shapes that match the real backend schemas
// ---------------------------------------------------------------------------

const WORKFLOW_ID = 'wf-real-001';

const REAL_STATUS_RESPONSE: WorkflowStatusResponse = {
  workflow_id: WORKFLOW_ID,
  status: 'pending',
  current_agent: null,
  progress: {},
  total_progress: 0.0,
  started_at: new Date().toISOString(),
  estimated_completion: null,
  error: null,
};

const RUNNING_STATUS: WorkflowStatusResponse = {
  workflow_id: WORKFLOW_ID,
  status: 'running',
  current_agent: 'observation',
  progress: {
    observation: {
      agent: 'observation',
      status: 'running',
      progress: 0.5,
      message: 'Extracting UI elements…',
    },
  },
  total_progress: 0.125,
  started_at: new Date().toISOString(),
  estimated_completion: null,
  error: null,
};

const REAL_RESULTS_RESPONSE: WorkflowResultsResponse = {
  workflow_id: WORKFLOW_ID,
  status: 'completed',
  test_case_ids: [101, 102, 103],
  test_count: 3,
  observation_result: { ui_elements: [], page_context: { url: 'https://example.com' } },
  requirements_result: { scenarios: [] },
  analysis_result: { risk_scores: [] },
  evolution_result: { test_count: 3, test_case_ids: [101, 102, 103] },
  completed_at: new Date().toISOString(),
  total_duration_seconds: 42.5,
};

function axiosRes<T>(data: T): AxiosResponse<T> {
  return { data, status: 200, statusText: 'OK', headers: {}, config: {} } as AxiosResponse<T>;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('agentWorkflowService — Real API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // generateTests
  // ---------------------------------------------------------------------------
  describe('generateTests()', () => {
    it('calls POST /api/v2/generate-tests with correct payload', async () => {
      mockPost.mockResolvedValue(axiosRes(REAL_STATUS_RESPONSE));

      const request: GenerateTestsRequest = {
        url: 'https://example.com',
        user_instruction: 'Test login flow',
        depth: 1,
      };
      await agentWorkflowService.generateTests(request);

      expect(mockPost).toHaveBeenCalledWith(
        '/api/v2/generate-tests',
        expect.objectContaining({ url: 'https://example.com', user_instruction: 'Test login flow', depth: 1 })
      );
    });

    it('returns a WorkflowStatusResponse with workflow_id and status pending', async () => {
      mockPost.mockResolvedValue(axiosRes(REAL_STATUS_RESPONSE));

      const result = await agentWorkflowService.generateTests({ url: 'https://example.com' });

      expect(result.workflow_id).toBe(WORKFLOW_ID);
      expect(result.status).toBe('pending');
      expect(result).toHaveProperty('total_progress');
      expect(result).toHaveProperty('started_at');
    });

    it('throws an error when the API call fails', async () => {
      mockPost.mockRejectedValue(new Error('Network error'));

      await expect(
        agentWorkflowService.generateTests({ url: 'https://example.com' })
      ).rejects.toThrow('Network error');
    });
  });

  // ---------------------------------------------------------------------------
  // getWorkflowStatus
  // ---------------------------------------------------------------------------
  describe('getWorkflowStatus()', () => {
    it('calls GET /api/v2/workflows/{id}', async () => {
      mockGet.mockResolvedValue(axiosRes(RUNNING_STATUS));

      await agentWorkflowService.getWorkflowStatus(WORKFLOW_ID);

      expect(mockGet).toHaveBeenCalledWith(`/api/v2/workflows/${WORKFLOW_ID}`);
    });

    it('returns a WorkflowStatusResponse with real-API shape', async () => {
      mockGet.mockResolvedValue(axiosRes(RUNNING_STATUS));

      const result: WorkflowStatusResponse = await agentWorkflowService.getWorkflowStatus(WORKFLOW_ID);

      expect(result.workflow_id).toBe(WORKFLOW_ID);
      expect(result.status).toBe('running');
      expect(result.current_agent).toBe('observation');
      expect(typeof result.total_progress).toBe('number');
      expect(result.progress).toHaveProperty('observation');
      expect(result.progress.observation.progress).toBe(0.5);
    });

    it('throws an error when the API call fails', async () => {
      mockGet.mockRejectedValue(new Error('Timeout'));

      await expect(agentWorkflowService.getWorkflowStatus(WORKFLOW_ID)).rejects.toThrow('Timeout');
    });
  });

  // ---------------------------------------------------------------------------
  // getWorkflowResults
  // ---------------------------------------------------------------------------
  describe('getWorkflowResults()', () => {
    it('calls GET /api/v2/workflows/{id}/results', async () => {
      mockGet.mockResolvedValue(axiosRes(REAL_RESULTS_RESPONSE));

      await agentWorkflowService.getWorkflowResults(WORKFLOW_ID);

      expect(mockGet).toHaveBeenCalledWith(`/api/v2/workflows/${WORKFLOW_ID}/results`);
    });

    it('returns a WorkflowResultsResponse with real-API shape', async () => {
      mockGet.mockResolvedValue(axiosRes(REAL_RESULTS_RESPONSE));

      const result: WorkflowResultsResponse = await agentWorkflowService.getWorkflowResults(WORKFLOW_ID);

      expect(result.workflow_id).toBe(WORKFLOW_ID);
      expect(result.status).toBe('completed');
      expect(Array.isArray(result.test_case_ids)).toBe(true);
      expect(result.test_case_ids).toEqual([101, 102, 103]);
      expect(result.test_count).toBe(3);
      expect(result).toHaveProperty('completed_at');
      expect(result).toHaveProperty('total_duration_seconds');
      expect(result.evolution_result).toBeTruthy();
    });

    it('throws when API call fails', async () => {
      mockGet.mockRejectedValue(new Error('Not found'));

      await expect(agentWorkflowService.getWorkflowResults(WORKFLOW_ID)).rejects.toThrow('Not found');
    });
  });

  // ---------------------------------------------------------------------------
  // cancelWorkflow
  // ---------------------------------------------------------------------------
  describe('cancelWorkflow()', () => {
    it('calls DELETE /api/v2/workflows/{id}', async () => {
      mockDelete.mockResolvedValue({ data: null, status: 204 });

      await agentWorkflowService.cancelWorkflow(WORKFLOW_ID);

      expect(mockDelete).toHaveBeenCalledWith(`/api/v2/workflows/${WORKFLOW_ID}`);
    });

    it('resolves without throwing on 204 response', async () => {
      mockDelete.mockResolvedValue({ data: null, status: 204 });

      await expect(agentWorkflowService.cancelWorkflow(WORKFLOW_ID)).resolves.not.toThrow();
    });

    it('throws when API call fails', async () => {
      mockDelete.mockRejectedValue(new Error('Server error'));

      await expect(agentWorkflowService.cancelWorkflow(WORKFLOW_ID)).rejects.toThrow('Server error');
    });
  });
});
