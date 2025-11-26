import api, { apiHelpers } from './api';
import {
  TestExecutionDetail,
  TestExecutionListResponse,
  ExecutionStartRequest,
  ExecutionStartResponse,
  ExecutionStatistics,
  QueueStatus,
  QueueStatistics,
  ActiveExecution,
} from '../types/execution';

/**
 * Execution Service
 * Handles test execution, queue management, and execution history
 */

class ExecutionService {
  /**
   * Start a test execution (queues the test)
   */
  async startExecution(
    testCaseId: number,
    request: ExecutionStartRequest = {}
  ): Promise<ExecutionStartResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        id: Date.now(),
        test_case_id: testCaseId,
        status: 'pending',
        message: 'Test queued for execution',
        priority: request.priority || 5,
        queued_at: new Date().toISOString(),
        queue_position: Math.floor(Math.random() * 5) + 1,
      };
    }

    // Real API call
    try {
      const response = await api.post<ExecutionStartResponse>(
        `/tests/${testCaseId}/run`,
        request
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get execution details with steps
   */
  async getExecutionDetail(executionId: number): Promise<TestExecutionDetail> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        id: executionId,
        test_case_id: 1,
        status: 'completed',
        result: 'pass',
        started_at: new Date(Date.now() - 300000).toISOString(),
        completed_at: new Date().toISOString(),
        duration_seconds: 45.2,
        total_steps: 5,
        passed_steps: 5,
        failed_steps: 0,
        skipped_steps: 0,
        browser: 'chromium',
        environment: 'dev',
        triggered_by: 'manual',
        user_id: 1,
        created_at: new Date(Date.now() - 300000).toISOString(),
        updated_at: new Date().toISOString(),
        steps: [
          {
            id: 1,
            execution_id: executionId,
            step_number: 1,
            step_description: 'Navigate to homepage',
            is_critical: true,
            result: 'pass',
            actual_result: 'Successfully navigated',
            started_at: new Date(Date.now() - 300000).toISOString(),
            completed_at: new Date(Date.now() - 290000).toISOString(),
            duration_seconds: 2.1,
            retry_count: 0,
            created_at: new Date(Date.now() - 300000).toISOString(),
          },
          {
            id: 2,
            execution_id: executionId,
            step_number: 2,
            step_description: 'Click login button',
            is_critical: true,
            result: 'pass',
            actual_result: 'Button clicked successfully',
            started_at: new Date(Date.now() - 290000).toISOString(),
            completed_at: new Date(Date.now() - 280000).toISOString(),
            duration_seconds: 1.5,
            retry_count: 0,
            created_at: new Date(Date.now() - 290000).toISOString(),
          },
        ],
      };
    }

    // Real API call
    try {
      const response = await api.get<TestExecutionDetail>(`/executions/${executionId}`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get list of executions with pagination and filtering
   */
  async getExecutions(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    result?: string;
    test_case_id?: number;
  }): Promise<TestExecutionListResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation - Generate diverse test data
      const allMockItems = Array.from({ length: 20 }, (_, i) => ({
        id: i + 1,
        test_case_id: Math.floor(Math.random() * 10) + 1,
        status: (['pending', 'running', 'completed', 'failed', 'cancelled'] as const)[Math.floor(Math.random() * 5)],
        result: (['pass', 'fail', 'error', 'skip'] as const)[Math.floor(Math.random() * 4)],
        started_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
        completed_at: new Date().toISOString(),
        duration_seconds: Math.random() * 100,
        total_steps: 5,
        passed_steps: Math.floor(Math.random() * 5),
        failed_steps: Math.floor(Math.random() * 2),
        skipped_steps: 0,
        browser: 'chromium',
        environment: 'dev',
        triggered_by: 'manual',
        created_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
      }));

      // Apply filters
      let filteredItems = allMockItems;
      
      if (params?.status) {
        filteredItems = filteredItems.filter(item => item.status === params.status);
      }
      
      if (params?.result) {
        filteredItems = filteredItems.filter(item => item.result === params.result);
      }
      
      if (params?.test_case_id) {
        filteredItems = filteredItems.filter(item => item.test_case_id === params.test_case_id);
      }

      // Apply pagination
      const skip = params?.skip || 0;
      const limit = params?.limit || 20;
      const paginatedItems = filteredItems.slice(skip, skip + limit);

      return {
        items: paginatedItems,
        total: filteredItems.length,
        skip,
        limit,
      };
    }

    // Real API call
    try {
      const response = await api.get<TestExecutionListResponse>('/executions', { params });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get execution statistics
   */
  async getStatistics(): Promise<ExecutionStatistics> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        total_executions: 150,
        by_status: {
          pending: 5,
          running: 2,
          completed: 120,
          failed: 20,
          cancelled: 3,
        },
        by_result: {
          pass: 100,
          fail: 20,
          error: 5,
          skip: 25,
        },
        by_browser: {
          chromium: 100,
          firefox: 30,
          webkit: 20,
        },
        by_environment: {
          dev: 50,
          staging: 60,
          production: 40,
        },
        pass_rate: 66.7,
        average_duration_seconds: 45.5,
        total_duration_hours: 1.9,
        executions_last_24h: 25,
        executions_last_7d: 75,
        executions_last_30d: 150,
        most_executed_tests: [
          { test_case_id: 1, test_case_title: 'Login Test', execution_count: 50 },
          { test_case_id: 2, test_case_title: 'Checkout Test', execution_count: 30 },
        ],
      };
    }

    // Real API call
    try {
      const response = await api.get<ExecutionStatistics>('/executions/stats');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete an execution
   */
  async deleteExecution(executionId: number): Promise<void> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return Promise.resolve();
    }

    // Real API call
    try {
      await api.delete(`/executions/${executionId}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get queue status
   */
  async getQueueStatus(): Promise<QueueStatus> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        status: 'operational',
        total_queued: 3,
        total_running: 2,
        total_completed: 45,
        max_concurrent: 5,
        is_under_limit: true,
      };
    }

    // Real API call
    try {
      const response = await api.get<QueueStatus>('/executions/queue/status');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get queue statistics
   */
  async getQueueStatistics(): Promise<QueueStatistics> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        queued_count: 3,
        running_count: 2,
        completed_count: 45,
        failed_count: 5,
        cancelled_count: 1,
        average_queue_time_seconds: 12.5,
        average_execution_time_seconds: 45.3,
      };
    }

    // Real API call
    try {
      const response = await api.get<QueueStatistics>('/executions/queue/statistics');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get active executions
   */
  async getActiveExecutions(): Promise<ActiveExecution[]> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return [
        {
          id: 1,
          test_case_id: 5,
          status: 'running',
          started_at: new Date(Date.now() - 30000).toISOString(),
          duration_seconds: 30,
          progress_percentage: 60,
        },
        {
          id: 2,
          test_case_id: 8,
          status: 'running',
          started_at: new Date(Date.now() - 15000).toISOString(),
          duration_seconds: 15,
          progress_percentage: 30,
        },
      ];
    }

    // Real API call
    try {
      const response = await api.get<ActiveExecution[]>('/executions/queue/active');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Clear the execution queue (admin only)
   */
  async clearQueue(): Promise<void> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return Promise.resolve();
    }

    // Real API call
    try {
      await api.post('/executions/queue/clear');
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get screenshot URL
   */
  getScreenshotUrl(screenshotPath: string): string {
    if (!screenshotPath) return '';
    
    // If screenshot path is relative, prepend the API base URL
    if (screenshotPath.startsWith('/')) {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      return `${baseUrl}${screenshotPath}`;
    }
    
    return screenshotPath;
  }
}

export default new ExecutionService();
