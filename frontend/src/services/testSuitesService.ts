import api from './api';

export interface TestSuiteItem {
  id: number;
  test_case_id: number;
  execution_order: number;
  test_case?: {
    id: number;
    title: string;
    description?: string;
  };
}

export interface TestSuite {
  id: number;
  name: string;
  description?: string;
  tags?: string[];
  user_id: number;
  created_at: string;
  updated_at: string;
  items: TestSuiteItem[];
}

export interface CreateTestSuiteRequest {
  name: string;
  description?: string;
  tags?: string[];
  test_case_ids: number[];
}

export interface UpdateTestSuiteRequest {
  name?: string;
  description?: string;
  tags?: string[];
  test_case_ids?: number[];
}

export interface RunSuiteRequest {
  browser?: string;
  environment?: string;
  stop_on_failure?: boolean;
  parallel?: boolean;
}

export interface SuiteExecutionResponse {
  suite_execution_id: number;
  queued_executions: number[];
  message: string;
}

const testSuitesService = {
  // Get all test suites
  getAllSuites: async (tags?: string[]): Promise<TestSuite[]> => {
    const params = tags && tags.length > 0 ? { tags: tags.join(',') } : {};
    const response = await api.get('/suites', { params });
    return response.data;
  },

  // Get a single test suite by ID
  getSuite: async (id: number): Promise<TestSuite> => {
    const response = await api.get(`/suites/${id}`);
    return response.data;
  },

  // Create a new test suite
  createSuite: async (data: CreateTestSuiteRequest): Promise<TestSuite> => {
    const response = await api.post('/suites', data);
    return response.data;
  },

  // Update an existing test suite
  updateSuite: async (id: number, data: UpdateTestSuiteRequest): Promise<TestSuite> => {
    const response = await api.put(`/suites/${id}`, data);
    return response.data;
  },

  // Delete a test suite
  deleteSuite: async (id: number): Promise<void> => {
    await api.delete(`/suites/${id}`);
  },

  // Run a test suite
  runSuite: async (id: number, config: RunSuiteRequest): Promise<SuiteExecutionResponse> => {
    const response = await api.post(`/suites/${id}/run`, config);
    return response.data;
  },

  // Get suite execution history
  getSuiteExecutions: async (suiteId: number): Promise<any[]> => {
    const response = await api.get(`/suites/${suiteId}/executions`);
    return response.data;
  }
};

export default testSuitesService;
