/**
 * Test Execution Types
 * Sprint 3 - Matches backend schemas from app/schemas/test_execution.py
 */

// ============================================================================
// Enums
// ============================================================================

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type ExecutionResult = 'pass' | 'fail' | 'error' | 'skip';
export type BrowserType = 'chromium' | 'firefox' | 'webkit';
export type EnvironmentType = 'dev' | 'staging' | 'production';
export type TriggerType = 'manual' | 'scheduled' | 'ci_cd' | 'webhook';

// ============================================================================
// Execution Step Types
// ============================================================================

export interface TestExecutionStep {
  id: number;
  execution_id: number;
  step_number: number;
  step_description: string;
  expected_result?: string;
  is_critical: boolean;
  result: ExecutionResult;
  actual_result?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  screenshot_path?: string;
  screenshot_before?: string;
  screenshot_after?: string;
  retry_count: number;
  created_at: string;
}

// ============================================================================
// Test Execution Types
// ============================================================================

export interface TestExecutionBase {
  test_case_id: number;
  browser?: string;
  environment?: string;
  base_url?: string;
}

export interface TestExecution extends TestExecutionBase {
  id: number;
  status: ExecutionStatus;
  result?: ExecutionResult;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  skipped_steps: number;
  console_log?: string;
  error_message?: string;
  screenshot_path?: string;
  video_path?: string;
  triggered_by?: string;
  trigger_details?: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  // Queue fields (Sprint 3 Day 2)
  queued_at?: string;
  priority?: number;
  queue_position?: number;
}

export interface TestExecutionDetail extends TestExecution {
  steps: TestExecutionStep[];
}

export interface TestExecutionListItem {
  id: number;
  test_case_id: number;
  status: ExecutionStatus;
  result?: ExecutionResult;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  skipped_steps: number;
  browser?: string;
  environment?: string;
  triggered_by?: string;
  created_at: string;
}

export interface TestExecutionListResponse {
  items: TestExecutionListItem[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// Statistics Types
// ============================================================================

export interface ExecutionStatistics {
  total_executions: number;
  by_status: Record<ExecutionStatus, number>;
  by_result: Record<ExecutionResult, number>;
  by_browser: Record<string, number>;
  by_environment: Record<string, number>;
  pass_rate: number;
  average_duration_seconds?: number;
  total_duration_hours: number;
  executions_last_24h: number;
  executions_last_7d: number;
  executions_last_30d: number;
  most_executed_tests?: Array<{
    test_case_id: number;
    test_case_title: string;
    execution_count: number;
  }>;
}

// ============================================================================
// Request/Response Types
// ============================================================================

export interface ExecutionStartRequest {
  browser?: BrowserType;
  environment?: EnvironmentType;
  base_url?: string;
  triggered_by?: TriggerType;
  browser_profile_id?: number;
  browser_profile_data?: {
    cookies: Array<{
      name: string;
      value: string;
      domain: string;
      path: string;
      expires?: number;
      httpOnly?: boolean;
      secure?: boolean;
      sameSite?: 'Strict' | 'Lax' | 'None';
    }>;
    localStorage: Record<string, string>;
    sessionStorage: Record<string, string>;
  };
  http_credentials?: {
    username: string;
    password: string;
  };
}

export interface ExecutionStartResponse {
  id: number;
  test_case_id: number;
  status: ExecutionStatus;
  message: string;
  priority?: number;
  queued_at?: string;
  queue_position?: number;
}

// ============================================================================
// Queue Types (Sprint 3 Day 2)
// ============================================================================

export interface QueueStatus {
  status: 'operational' | 'stopped';
  total_queued: number;
  total_running: number;
  total_completed: number;
  max_concurrent: number;
  is_under_limit: boolean;
}

export interface QueueStatistics {
  queued_count: number;
  running_count: number;
  completed_count: number;
  failed_count: number;
  cancelled_count: number;
  average_queue_time_seconds?: number;
  average_execution_time_seconds?: number;
}

export interface ActiveExecution {
  id: number;
  test_case_id: number;
  status: ExecutionStatus;
  started_at?: string;
  duration_seconds?: number;
  progress_percentage?: number;
}

// ============================================================================
// Execution Feedback Types (Sprint 4)
// ============================================================================

export type FailureType = 
  | 'selector_not_found'
  | 'timeout'
  | 'assertion_failed'
  | 'network_error'
  | 'permission_error'
  | 'navigation_error'
  | 'unknown_error';

export type CorrectionSource = 'human' | 'ai_suggestion' | 'auto_applied';
export type SelectorType = 'css' | 'xpath' | 'text' | 'aria';
export type AnomalyType = 'performance' | 'flaky' | 'environment' | 'intermittent_failure';

export interface ExecutionFeedbackBase {
  execution_id: number;
  step_index?: number; // null for execution-level feedback
  failure_type?: FailureType;
  error_message?: string;
  screenshot_url?: string;
  page_url?: string;
  browser_type?: string;
  failed_selector?: string;
  selector_type?: SelectorType;
  notes?: string;
  tags?: string[];
}

export interface ExecutionFeedback extends ExecutionFeedbackBase {
  id: number;
  page_html_snapshot?: string;
  viewport_width?: number;
  viewport_height?: number;
  corrected_step?: Record<string, any>;
  correction_source?: CorrectionSource;
  correction_confidence?: number;
  correction_applied_at?: string;
  corrected_by_user_id?: number;
  step_duration_ms?: number;
  memory_usage_mb?: number;
  network_requests?: number;
  is_anomaly: boolean;
  anomaly_score?: number;
  anomaly_type?: AnomalyType;
  created_at: string;
  updated_at: string;
}

export interface ExecutionFeedbackListItem {
  id: number;
  execution_id: number;
  step_index?: number;
  failure_type?: FailureType;
  error_message?: string;
  screenshot_url?: string;
  page_url?: string;
  browser_type?: string;
  failed_selector?: string;
  selector_type?: SelectorType;
  correction_source?: CorrectionSource;
  correction_confidence?: number;
  is_anomaly: boolean;
  anomaly_score?: number;
  created_at: string;
}

export interface ExecutionFeedbackListResponse {
  items: ExecutionFeedbackListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface CorrectionSubmit {
  corrected_step: Record<string, any>;
  correction_source: CorrectionSource;
  correction_confidence?: number;
  notes?: string;
}

export interface ExecutionFeedbackStats {
  total_feedback: number;
  total_failures: number;
  total_corrected: number;
  total_anomalies: number;
  correction_rate: number; // Percentage
  top_failure_types: Array<{
    type: string;
    count: number;
  }>;
  top_failed_selectors: Array<{
    selector: string;
    count: number;
  }>;
}

export interface ExecutionFeedbackCreate extends ExecutionFeedbackBase {
  page_html_snapshot?: string;
  viewport_width?: number;
  viewport_height?: number;
  step_duration_ms?: number;
  memory_usage_mb?: number;
  network_requests?: number;
}

export interface ExecutionFeedbackUpdate {
  failure_type?: FailureType;
  error_message?: string;
  notes?: string;
  tags?: string[];
  is_anomaly?: boolean;
  anomaly_score?: number;
  anomaly_type?: AnomalyType;
}
