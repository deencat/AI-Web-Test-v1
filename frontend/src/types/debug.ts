/**
 * Debug Mode Types
 * Matches backend schemas from app/schemas/debug_session.py
 */

// ============================================================================
// Enums
// ============================================================================

export type DebugMode = 'auto' | 'manual';

export type DebugSessionStatus =
  | 'initializing'
  | 'setup_in_progress'
  | 'ready'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type DebugStepResult = 'pass' | 'fail' | 'error' | 'skip';

// ============================================================================
// Debug Session Types
// ============================================================================

export interface DebugSessionStartRequest {
  execution_id: number;
  mode: DebugMode;
  target_step_number: number;
  end_step_number?: number | null;
  skip_prerequisites?: boolean;
}

export interface ManualSetupInstruction {
  step_number: number;
  description: string;
  action: string;
  expected_state: string;
}

export interface DebugSessionStartResponse {
  session_id: string;
  mode: DebugMode;
  status: DebugSessionStatus;
  message: string;
  browser_url?: string;
  manual_setup_instructions?: ManualSetupInstruction[];
  estimated_setup_cost?: number;
  execution_cost?: number;
}

export interface DebugStepExecuteRequest {
  session_id: string;
  iteration_note?: string;
}

export interface DebugStepExecuteResponse {
  session_id: string;
  iteration_number: number;
  result: DebugStepResult;
  actual_result?: string;
  error_message?: string;
  screenshot_path?: string;
  duration_seconds: number;
  message: string;
}

export interface DebugNextStepResponse {
  session_id: string;
  step_number: number;
  step_description: string;
  success: boolean;
  error_message?: string;
  screenshot_path?: string;
  duration_seconds: number;
  tokens_used: number;
  has_more_steps: boolean;
  next_step_preview?: string;
  total_steps: number;
  end_step_number?: number | null;
  range_complete?: boolean;
}

export interface DebugSessionStatusResponse {
  session_id: string;
  mode: DebugMode;
  status: DebugSessionStatus;
  target_step_number: number;
  prerequisite_steps_count: number;
  current_step?: number;
  setup_completed: boolean;
  tokens_used: number;
  iterations_count: number;
  started_at: string;
  setup_completed_at?: string;
  last_activity_at: string;
  ended_at?: string;
  error_message?: string;
  devtools_url?: string;
  browser_pid?: number;
}

export interface DebugSessionStopResponse {
  session_id: string;
  message: string;
  final_status: DebugSessionStatus;
  total_iterations: number;
  total_tokens_used: number;
}

export interface DebugSessionManualInstructionsResponse {
  session_id: string;
  instructions: ManualSetupInstruction[];
  estimated_time_minutes: number;
  message: string;
}

export interface DebugSessionConfirmSetupResponse {
  session_id: string;
  status: DebugSessionStatus;
  message: string;
}

export interface DebugSessionListItem {
  session_id: string;
  mode: DebugMode;
  status: DebugSessionStatus;
  execution_id: number;
  target_step_number: number;
  current_iteration: number;
  total_tokens_used: number;
  started_at: string;
  last_activity_at: string;
}

export interface DebugSessionListResponse {
  sessions: DebugSessionListItem[];
  total: number;
  active_sessions: number;
}
