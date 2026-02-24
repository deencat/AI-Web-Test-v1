/**
 * Agent Workflow Service — Mock Stub
 *
 * Sprint 10 Phase 1 — API Contract Definition (Developer B)
 *
 * All methods return mock data while Developer A implements the real backend.
 * When the backend is ready, replace mock blocks with real axios calls.
 *
 * API v2 endpoints (to be implemented by Developer A):
 *   POST   /api/v2/generate-tests
 *   GET    /api/v2/workflows/{id}
 *   GET    /api/v2/workflows/{id}/results
 *   DELETE /api/v2/workflows/{id}
 */
import api, { apiHelpers } from './api';
import type {
  AgentStage,
  GenerateTestsRequest,
  WorkflowCreateResponse,
  WorkflowStatusResponse,
  WorkflowResultsResponse,
} from '../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Internal Mock Helpers
// ---------------------------------------------------------------------------

function mockWorkflowId(): string {
  return `wf-mock-${Math.random().toString(36).slice(2, 10)}`;
}

function mockIso(offsetMs = 0): string {
  return new Date(Date.now() + offsetMs).toISOString();
}

// ---------------------------------------------------------------------------
// Mock progress simulation (keyed by workflow_id → start timestamp)
// ---------------------------------------------------------------------------

const mockStartTimes = new Map<string, number>();

/**
 * Returns a mock WorkflowStatusResponse that progresses over ~10 seconds:
 *   0-1s  → pending
 *   1-3s  → initialising  (20%)
 *   3-5s  → analysing     (40%)
 *   5-7s  → generating    (60%)
 *   7-9s  → validating    (80%)
 *   9s+   → completed     (100%)
 */
function mockProgressStatus(workflowId: string): WorkflowStatusResponse {
  const start = mockStartTimes.get(workflowId) ?? Date.now();
  const elapsed = (Date.now() - start) / 1000; // seconds

  const stages: Array<{ minT: number; stage: AgentStage; percentage: number; message: string; current_step: number }> = [
    { minT: 0, stage: 'initializing', percentage: 10, message: 'Setting up agents…',               current_step: 1 },
    { minT: 1, stage: 'initializing', percentage: 20, message: 'Agents ready, launching browser…', current_step: 1 },
    { minT: 3, stage: 'analyzing',    percentage: 40, message: 'Observing page & UI elements…',    current_step: 2 },
    { minT: 5, stage: 'generating',   percentage: 60, message: 'Generating test scenarios…',       current_step: 3 },
    { minT: 7, stage: 'validating',   percentage: 80, message: 'Reviewing & scoring tests…',       current_step: 4 },
  ];

  if (elapsed >= 9) {
    return {
      workflow_id: workflowId,
      status: 'completed',
      progress: { stage: 'complete', percentage: 100, message: 'Tests ready!', current_step: 5, total_steps: 5 },
      created_at: mockIso(-10_000),
      updated_at: mockIso(),
    };
  }

  const current = [...stages].reverse().find(s => elapsed >= s.minT) ?? stages[0];
  const { minT: _omit, ...progressFields } = current;
  return {
    workflow_id: workflowId,
    status: 'running',
    progress: { ...progressFields, total_steps: 5 },
    created_at: mockIso(-elapsed * 1_000),
    updated_at: mockIso(),
  };
}

// ---------------------------------------------------------------------------
// AgentWorkflowService
// ---------------------------------------------------------------------------

class AgentWorkflowService {
  private readonly baseUrl = '/api/v2';

  /**
   * Trigger AI test generation for a given URL.
   * POST /api/v2/generate-tests
   *
   * @returns WorkflowCreateResponse with a workflow_id for polling / SSE
   */
  async generateTests(request: GenerateTestsRequest): Promise<WorkflowCreateResponse> {
    if (apiHelpers.useMockData()) {
      const id = mockWorkflowId();
      mockStartTimes.set(id, Date.now());
      return {
        workflow_id: id,
        status: 'pending',
        message: 'Workflow queued — AI analysis will begin shortly.',
        estimated_duration_seconds: 10,
      };
    }

    try {
      const response = await api.post<WorkflowCreateResponse>(
        `${this.baseUrl}/generate-tests`,
        request
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Poll the current status of a workflow.
   * GET /api/v2/workflows/{workflow_id}
   */
  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatusResponse> {
    if (apiHelpers.useMockData()) {
      return mockProgressStatus(workflowId);
    }

    try {
      const response = await api.get<WorkflowStatusResponse>(
        `${this.baseUrl}/workflows/${workflowId}`
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Retrieve the generated test cases for a completed workflow.
   * GET /api/v2/workflows/{workflow_id}/results
   */
  async getWorkflowResults(workflowId: string): Promise<WorkflowResultsResponse> {
    if (apiHelpers.useMockData()) {
      return {
        workflow_id: workflowId,
        status: 'completed',
        test_cases: [
          {
            id: 'tc-mock-001',
            title: 'User can navigate to homepage',
            description: 'Verify the homepage loads successfully',
            test_type: 'smoke',
            steps: [
              {
                step_number: 1,
                action: 'navigate',
                target: 'https://example.com',
                value: '',
                description: 'Open the target URL',
              },
            ],
            assertions: [
              {
                assertion_type: 'visible',
                target: 'body',
                expected_value: '',
                description: 'Page body should be visible',
              },
            ],
            estimated_duration_seconds: 10,
            confidence_score: 0.95,
            tags: ['smoke', 'homepage'],
          },
          {
            id: 'tc-mock-002',
            title: 'User can interact with primary CTA',
            description: 'Verify the primary call-to-action button is clickable',
            test_type: 'regression',
            steps: [
              {
                step_number: 1,
                action: 'navigate',
                target: 'https://example.com',
                value: '',
              },
              {
                step_number: 2,
                action: 'click',
                target: 'button[data-testid="cta-primary"]',
                value: '',
                description: 'Click the primary CTA button',
              },
            ],
            assertions: [
              {
                assertion_type: 'url_contains',
                target: '',
                expected_value: '/signup',
                description: 'Should redirect to signup page',
              },
            ],
            estimated_duration_seconds: 15,
            confidence_score: 0.88,
            tags: ['regression', 'cta'],
          },
        ],
        summary: {
          total_tests: 2,
          test_types: { smoke: 1, regression: 1 },
          avg_confidence_score: 0.915,
          total_steps: 3,
        },
        generated_at: mockIso(),
      };
    }

    try {
      const response = await api.get<WorkflowResultsResponse>(
        `${this.baseUrl}/workflows/${workflowId}/results`
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Cancel a running workflow.
   * DELETE /api/v2/workflows/{workflow_id}
   */
  async cancelWorkflow(workflowId: string): Promise<{ success: boolean; message: string }> {
    if (apiHelpers.useMockData()) {
      return {
        success: true,
        message: `Workflow ${workflowId} has been cancelled.`,
      };
    }

    try {
      const response = await api.delete<{ success: boolean; message: string }>(
        `${this.baseUrl}/workflows/${workflowId}`
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new AgentWorkflowService();
