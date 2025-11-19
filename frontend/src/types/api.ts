/**
 * API Response Types
 * Based on docs/API-REQUIREMENTS.md
 */

// Generic API Response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

// Paginated response
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Error response
export interface ApiError {
  message: string;
  details?: string;
  field?: string;
  code?: string;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

// Test types
export interface Test {
  id: string;
  name: string;
  description: string;
  status: 'passed' | 'failed' | 'pending' | 'running';
  priority: 'high' | 'medium' | 'low';
  agent: string;
  created_at: string;
  updated_at: string;
  last_run?: string;
  execution_time?: number;
  steps?: TestStep[];
}

export interface TestStep {
  id: string;
  order: number;
  description: string;
  status: 'passed' | 'failed' | 'skipped';
  screenshot_url?: string;
  error_message?: string;
}

export interface CreateTestRequest {
  name: string;
  description: string;
  priority?: 'high' | 'medium' | 'low';
  agent?: string;
}

export interface UpdateTestRequest {
  name?: string;
  description?: string;
  status?: 'passed' | 'failed' | 'pending' | 'running';
  priority?: 'high' | 'medium' | 'low';
}

export interface RunTestRequest {
  test_id: string;
}

export interface RunTestResponse {
  test_run_id: string;
  status: string;
  message: string;
}

// Knowledge Base types
export interface KBDocument {
  id: string;
  name: string;
  description: string;
  category: string;
  document_type: 'system_guide' | 'product' | 'process' | 'reference';
  file_size: string;
  file_url?: string;
  uploaded_by: string;
  uploaded_at: string;
  tags: string[];
  referenced_count: number;
  version?: number;
}

export interface KBCategory {
  id: string;
  name: string;
  count: number;
  color?: string;
  description?: string;
}

export interface UploadDocumentRequest {
  file: File;
  name: string;
  description: string;
  category_id: string;
  document_type: 'system_guide' | 'product' | 'process' | 'reference';
  tags?: string[];
}

export interface CreateCategoryRequest {
  name: string;
  description?: string;
  color?: string;
}

export interface SearchDocumentsRequest {
  query: string;
  category_id?: string;
  document_type?: string;
  tags?: string[];
  page?: number;
  per_page?: number;
}

// Settings types
export interface Settings {
  // General
  project_name: string;
  default_timeout: number;

  // Notifications
  email_notifications: boolean;
  slack_notifications: boolean;
  test_failure_alerts: boolean;

  // Agent Configuration
  ai_model: string;
  temperature: number;
  max_tokens: number;

  // Test Execution
  parallel_runs?: number;
  retry_count?: number;
  timeout_multiplier?: number;

  // Integration
  github_webhook_url?: string;
  slack_channel?: string;

  // API Endpoints (read-only)
  backend_api_url?: string;
  openrouter_api_key?: string;
}

export interface UpdateSettingsRequest {
  project_name?: string;
  default_timeout?: number;
  email_notifications?: boolean;
  slack_notifications?: boolean;
  test_failure_alerts?: boolean;
  ai_model?: string;
  temperature?: number;
  max_tokens?: number;
  parallel_runs?: number;
  retry_count?: number;
  timeout_multiplier?: number;
  github_webhook_url?: string;
  slack_channel?: string;
}

// Agent Activity types
export interface AgentActivity {
  id: string;
  agent: string;
  action: string;
  timestamp: string;
  details?: string;
}

// Dashboard Stats types
export interface DashboardStats {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  pending_tests: number;
  active_agents: number;
  pass_rate?: number;
}

// Test trend data
export interface TestTrendData {
  date: string;
  passed: number;
  failed: number;
  total: number;
}

