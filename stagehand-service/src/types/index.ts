/**
 * Type definitions for Stagehand Service
 */

export interface TestStep {
  action: string;
  selector?: string;
  value?: string;
  timeout?: number;
  expected?: string;
}

export interface TestCase {
  id: number;
  title: string;
  description?: string;
  steps: TestStep[];
  url?: string;
}

export interface SessionConfig {
  browser?: 'chromium' | 'firefox' | 'webkit';
  headless?: boolean;
  screenshot_dir?: string;
  video_dir?: string;
  user_config?: {
    provider?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    api_key?: string;
  };
}

export interface ExecutionResult {
  success: boolean;
  message?: string;
  screenshot?: string;
  error?: string;
  duration_ms?: number;
}

export interface SessionInfo {
  session_id: string;
  test_id: number;
  user_id: number;
  created_at: string;
  last_activity: string;
  status: 'active' | 'idle' | 'closed';
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime_seconds: number;
  active_sessions: number;
  memory_usage_mb: number;
  version: string;
}
