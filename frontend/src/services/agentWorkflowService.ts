/**
 * Agent Workflow Service — Real API integration (Sprint 10)
 *
 * All methods make real HTTP calls to the backend /api/v2 endpoints.
 * Mock data has been removed. VITE_USE_MOCK must be false.
 *
 * API v2 endpoints:
 *   POST   /api/v2/generate-tests
 *   GET    /api/v2/workflows/{id}
 *   GET    /api/v2/workflows/{id}/results
 *   DELETE /api/v2/workflows/{id}
 */
import { apiV2 as api, apiHelpers } from './api';
import type {
  GenerateTestsRequest,
  WorkflowStatusResponse,
  WorkflowResultsResponse,
} from '../types/agentWorkflow.types';

const BASE = '/api/v2';

class AgentWorkflowService {
  /**
   * Trigger AI test generation for a given URL.
   * POST /api/v2/generate-tests
   *
   * Returns WorkflowStatusResponse (202 Accepted) with workflow_id for polling / SSE.
   */
  async generateTests(request: GenerateTestsRequest): Promise<WorkflowStatusResponse> {
    try {
      const response = await api.post<WorkflowStatusResponse>(
        `${BASE}/generate-tests`,
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
    try {
      const response = await api.get<WorkflowStatusResponse>(
        `${BASE}/workflows/${workflowId}`
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
    try {
      const response = await api.get<WorkflowResultsResponse>(
        `${BASE}/workflows/${workflowId}/results`
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Cancel a running workflow.
   * DELETE /api/v2/workflows/{workflow_id}
   * Returns 204 No Content on success.
   */
  async cancelWorkflow(workflowId: string): Promise<void> {
    try {
      await api.delete(`${BASE}/workflows/${workflowId}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new AgentWorkflowService();
