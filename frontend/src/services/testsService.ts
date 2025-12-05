import api, { apiHelpers } from './api';
import {
  Test,
  CreateTestRequest,
  UpdateTestRequest,
  RunTestRequest,
  RunTestResponse,
  PaginatedResponse,
  GenerateTestsRequest,
  GenerateTestsResponse,
} from '../types/api';
import { mockTests } from '../mock/tests';

/**
 * Tests Service
 * Handles all test-related API operations
 */

class TestsService {
  /**
   * Get all tests
   */
  async getAllTests(params?: {
    status?: string;
    priority?: string;
    agent?: string;
    page?: number;
    per_page?: number;
  }): Promise<Test[]> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      let filtered = [...mockTests];

      // Apply filters
      if (params?.status) {
        filtered = filtered.filter((test) => test.status === params.status);
      }
      if (params?.priority) {
        filtered = filtered.filter((test) => test.priority === params.priority);
      }
      if (params?.agent) {
        filtered = filtered.filter((test) => test.agent === params.agent);
      }

      return filtered;
    }

    // Real API call
    try {
      const response = await api.get<any>('/tests', { params });
      // Backend returns { items, total, skip, limit }
      // We need to extract items array
      return response.data.items || response.data.data || [];
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get test by ID
   */
  async getTestById(id: string): Promise<Test> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const test = mockTests.find((t) => t.id === id);
      if (!test) {
        throw new Error('Test not found');
      }
      return test;
    }

    // Real API call
    try {
      const response = await api.get<Test>(`/tests/${id}`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Create new test
   */
  async createTest(data: CreateTestRequest): Promise<Test> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const newTest: Test = {
        id: `T-${Date.now()}`,
        name: data.title,  // Use title instead of name
        description: data.description,
        status: data.status || 'pending',
        priority: data.priority || 'medium',
        agent: 'Orchestrator',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockTests.push(newTest);
      return newTest;
    }

    // Real API call
    try {
      const response = await api.post<Test>('/tests', data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Update test
   */
  async updateTest(id: string, data: UpdateTestRequest): Promise<Test> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const testIndex = mockTests.findIndex((t) => t.id === id);
      if (testIndex === -1) {
        throw new Error('Test not found');
      }

      mockTests[testIndex] = {
        ...mockTests[testIndex],
        ...data,
        updated_at: new Date().toISOString(),
      };

      return mockTests[testIndex];
    }

    // Real API call
    try {
      const response = await api.put<Test>(`/tests/${id}`, data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete test
   */
  async deleteTest(id: string): Promise<void> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const testIndex = mockTests.findIndex((t) => t.id === id);
      if (testIndex === -1) {
        throw new Error('Test not found');
      }
      mockTests.splice(testIndex, 1);
      return;
    }

    // Real API call
    try {
      await api.delete(`/tests/${id}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Run test
   */
  async runTest(testId: string): Promise<RunTestResponse> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      // Simulate running test
      const testIndex = mockTests.findIndex((t) => t.id === testId);
      if (testIndex === -1) {
        throw new Error('Test not found');
      }

      // Update test status to running
      mockTests[testIndex].status = 'running';

      // Simulate completion after 2 seconds
      setTimeout(() => {
        mockTests[testIndex].status = Math.random() > 0.3 ? 'passed' : 'failed';
        mockTests[testIndex].last_run = new Date().toISOString();
        mockTests[testIndex].execution_time = Math.floor(Math.random() * 5000) + 1000;
      }, 2000);

      return {
        test_run_id: `run-${Date.now()}`,
        status: 'running',
        message: 'Test execution started',
      };
    }

    // Real API call
    try {
      const response = await api.post<RunTestResponse>('/tests/run', {
        test_id: testId,
      } as RunTestRequest);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get test statistics
   */
  async getTestStats(): Promise<{
    total: number;
    passed: number;
    failed: number;
    pending: number;
    pass_rate: number;
  }> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const total = mockTests.length;
      const passed = mockTests.filter((t) => t.status === 'passed').length;
      const failed = mockTests.filter((t) => t.status === 'failed').length;
      const pending = mockTests.filter((t) => t.status === 'pending').length;
      const pass_rate = total > 0 ? (passed / total) * 100 : 0;

      return { total, passed, failed, pending, pass_rate };
    }

    // Real API call
    try {
      const response = await api.get('/tests/stats');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Generate test cases from natural language prompt
   */
  async generateTests(data: GenerateTestsRequest): Promise<GenerateTestsResponse> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Generate mock test cases
      const count = data.num_tests || 5;
      const test_cases = Array.from({ length: count }, (_, i) => ({
        id: `GENERATED-${Date.now()}-${i + 1}`,
        title: `Test Case ${i + 1}: ${data.requirement.substring(0, 50)}`,
        description: `Verify that ${data.requirement.toLowerCase()} works correctly as expected`,
        steps: [
          'Navigate to the application homepage',
          'Locate and click on the target element',
          'Verify the element state changes',
          'Confirm the expected behavior',
          'Validate success message appears',
        ],
        expected_result: 'The test should pass with all steps completing successfully',
        priority: (i === 0 ? 'high' : i < 3 ? 'medium' : 'low') as 'high' | 'medium' | 'low',
      }));

      return {
        test_cases,
        prompt: data.requirement,
        generated_at: new Date().toISOString(),
      };
    }

    // Real API call
    try {
      const response = await api.post<GenerateTestsResponse>('/tests/generate', data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new TestsService();

