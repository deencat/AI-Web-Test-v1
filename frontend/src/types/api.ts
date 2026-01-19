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
  title: string;
  description: string;
  test_type: 'e2e' | 'unit' | 'integration' | 'api';
  priority?: 'high' | 'medium' | 'low';
  status?: 'pending' | 'passed' | 'failed' | 'running';
  steps: string[];
  expected_result: string;
  preconditions?: string;
  test_data?: Record<string, any>;
  category_id?: number;
  tags?: string[];
  test_metadata?: Record<string, any>;
}

export interface UpdateTestRequest {
  title?: string;
  name?: string;  // Keep for backward compatibility
  description?: string;
  test_type?: 'e2e' | 'unit' | 'integration' | 'api';
  status?: 'passed' | 'failed' | 'pending' | 'running';
  priority?: 'high' | 'medium' | 'low';
  steps?: string[];
  expected_result?: string;
  preconditions?: string;
  test_data?: Record<string, any>;
  category_id?: number;
  tags?: string[];
  test_metadata?: Record<string, any>;
}

export interface RunTestRequest {
  test_id: string;
}

export interface RunTestResponse {
  test_run_id: string;
  status: string;
  message: string;
}

// Test Generation types
export interface GenerateTestsRequest {
  requirement: string;  // Changed from 'prompt' to match backend
  test_type?: 'e2e' | 'unit' | 'integration' | 'api';
  num_tests?: number;  // Changed from 'count' to match backend
  model?: string;
  // KB Integration (Sprint 2 Day 11)
  category_id?: number;      // KB category ID for context
  use_kb_context?: boolean;  // Whether to use KB context (default: true)
  max_kb_docs?: number;      // Max KB documents to include (default: 10)
}

export interface GeneratedTestCase {
  id?: string;
  title: string;
  description: string;
  steps: string[];
  expected_result: string;
  priority: 'high' | 'medium' | 'low';
}

export interface GenerateTestsResponse {
  test_cases: GeneratedTestCase[];
  prompt: string;
  generated_at: string;
}

// Knowledge Base types
export interface KBDocument {
  id: number;
  title: string;
  description: string | null;
  filename: string;
  file_path: string;
  file_type: 'pdf' | 'docx' | 'txt' | 'md';
  file_size: number;
  referenced_count: number;
  content: string | null;
  created_at: string;
  updated_at: string;
  category: KBCategory;
}

export interface KBCategory {
  id: number;
  name: string;
  description: string | null;
  color: string;
  icon: string | null;
}

export interface KBDocumentListResponse {
  items: KBDocument[];
  total: number;
  skip: number;
  limit: number;
}

export interface KBStatistics {
  total_documents: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_category: Record<string, number>;
  by_file_type: Record<string, number>;
  most_referenced?: Array<{
    id: number;
    title: string;
    referenced_count: number;
  }>;
}

export interface UploadDocumentRequest {
  file: File;
  name: string;
  description: string;
  category_id: string;
  document_type: 'system_guide' | 'product' | 'process' | 'reference';
  tags?: string[];
}export interface CreateCategoryRequest {
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

// AI Provider Settings Types (Sprint 3 - Settings Page Dynamic Configuration)
export interface AvailableProvider {
  name: string;
  display_name: string;
  is_configured: boolean;
  models: string[];
  recommended_model: string | null;
}

export interface AvailableProvidersResponse {
  providers: AvailableProvider[];
  default_generation_provider: string;
  default_generation_model: string;
  default_execution_provider: string;
  default_execution_model: string;
}

export interface UserSettings {
  id: number;
  user_id: number;
  generation_provider: string;
  generation_model: string;
  generation_temperature: number;
  generation_max_tokens: number;
  execution_provider: string;
  execution_model: string;
  execution_temperature: number;
  execution_max_tokens: number;
  created_at: string;
  updated_at: string | null;
}

export interface UpdateUserSettingsRequest {
  generation_provider?: string;
  generation_model?: string;
  generation_temperature?: number;
  generation_max_tokens?: number;
  execution_provider?: string;
  execution_model?: string;
  execution_temperature?: number;
  execution_max_tokens?: number;
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

// Sprint 5: Stagehand Provider types
export interface StagehandProviderResponse {
  provider: 'python' | 'typescript';
  available_providers: string[];
}

export interface StagehandProviderUpdate {
  provider: 'python' | 'typescript';
}

export interface StagehandProviderHealth {
  provider: 'python' | 'typescript';
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency_ms?: number;
  error?: string;
}

// Sprint 5.5: 3-Tier Execution Engine types
export type FallbackStrategy = 'option_a' | 'option_b' | 'option_c';

export interface ExecutionSettings {
  id: number;
  user_id: number;
  fallback_strategy: FallbackStrategy;
  timeout_per_tier_seconds: number;
  max_retry_per_tier: number;
  track_token_usage: boolean;
  track_execution_time: boolean;
  track_success_rate: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExecutionSettingsUpdate {
  fallback_strategy?: FallbackStrategy;
  timeout_per_tier_seconds?: number;
  max_retry_per_tier?: number;
  track_token_usage?: boolean;
  track_execution_time?: boolean;
  track_success_rate?: boolean;
}

export interface StrategyInfo {
  name: FallbackStrategy;
  display_name: string;
  description: string;
  cost_level: 'low' | 'medium' | 'high';
  performance_level: 'high' | 'medium' | 'low';
  fallback_chain: string[];
  recommended_for: string;
  pros: string[];
  cons: string[];
}

export interface TierDistributionStats {
  user_id: number;
  total_executions: number;
  tier1_executions: number;
  tier2_executions: number;
  tier3_executions: number;
  tier1_percentage: number;
  tier2_percentage: number;
  tier3_percentage: number;
  tier1_success_rate: number;
  tier2_success_rate: number;
  tier3_success_rate: number;
  tier1_avg_time_ms: number;
  tier2_avg_time_ms: number;
  tier3_avg_time_ms: number;
}

export interface StrategyEffectivenessStats {
  strategy: FallbackStrategy;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  avg_execution_time_ms: number;
  tier1_final_count: number;
  tier2_final_count: number;
  tier3_final_count: number;
  tier1_percentage: number;
  tier2_percentage: number;
  tier3_percentage: number;
  estimated_cost: 'low' | 'medium' | 'high';
}

