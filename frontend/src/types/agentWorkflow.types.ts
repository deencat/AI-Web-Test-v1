/**
 * Agent Workflow API Contract Types
 *
 * Sprint 10 Phase 1 — API Contract Definition (Developer B)
 * These TypeScript types mirror the Pydantic schemas defined by Developer A:
 *   - GenerateTestsRequest
 *   - WorkflowStatusResponse
 *   - AgentProgressEvent
 *   - WorkflowResultsResponse
 *
 * ⚠️  CONTRACT LOCKED — Do not modify without coordinating with Developer A.
 *     Any schema changes must be agreed before implementation resumes.
 */

// ---------------------------------------------------------------------------
// Primitive / Utility Types
// ---------------------------------------------------------------------------

/** Unique identifier for a workflow run */
export type WorkflowId = string;

/** Lifecycle status of a workflow */
export type WorkflowStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/** Processing stage within a running workflow */
export type AgentStage =
  | 'initializing'
  | 'analyzing'
  | 'generating'
  | 'validating'
  | 'complete';

// ---------------------------------------------------------------------------
// Progress Tracking
// ---------------------------------------------------------------------------

/** Current progress detail for a running workflow.
 *  Maps to Pydantic AgentProgressDetail.
 */
export interface AgentProgress {
  /** Current processing stage */
  stage: AgentStage;
  /** Overall completion percentage (0–100) */
  percentage: number;
  /** Human-readable status message */
  message: string;
  /** Index of the current processing step (1-based, optional) */
  current_step?: number;
  /** Total number of steps in this stage (optional) */
  total_steps?: number;
}

// ---------------------------------------------------------------------------
// Request Types (Frontend → Backend)
// ---------------------------------------------------------------------------

/** Request body for POST /api/v2/generate-tests.
 *  Mirrors Pydantic GenerateTestsRequest.
 */
export interface GenerateTestsRequest {
  /** Target URL to analyse and generate tests for */
  url: string;
  /** Subset of test types to generate (e.g. 'smoke', 'regression') */
  test_types?: string[];
  /** Maximum number of test cases to generate */
  max_tests?: number;
  /** Browser to use during page analysis */
  browser?: 'chromium' | 'firefox' | 'webkit';
  /** Whether to include assertion steps in generated tests */
  include_assertions?: boolean;
  /** Optional freeform context description to guide generation */
  context?: string;
}

// ---------------------------------------------------------------------------
// Response Types (Backend → Frontend)
// ---------------------------------------------------------------------------

/** Response body for POST /api/v2/generate-tests.
 *  Mirrors Pydantic WorkflowCreateResponse.
 */
export interface WorkflowCreateResponse {
  workflow_id: WorkflowId;
  status: Extract<WorkflowStatus, 'pending'>;
  message: string;
  estimated_duration_seconds: number;
}

/** Response body for GET /api/v2/workflows/{workflow_id}.
 *  Mirrors Pydantic WorkflowStatusResponse.
 */
export interface WorkflowStatusResponse {
  workflow_id: WorkflowId;
  status: WorkflowStatus;
  progress: AgentProgress;
  created_at: string;   // ISO 8601
  updated_at: string;   // ISO 8601
  /** Present only when status is 'failed' */
  error?: string;
}

// ---------------------------------------------------------------------------
// SSE Event Types (Server-Sent Events payload)
// ---------------------------------------------------------------------------

/** Payload delivered over the SSE stream for a running workflow.
 *  Mirrors Pydantic AgentProgressEvent.
 */
export interface AgentProgressEvent {
  workflow_id: WorkflowId;
  /** Discriminator for the event kind */
  event_type: 'progress' | 'completed' | 'failed' | 'cancelled';
  progress: AgentProgress;
  timestamp: string;    // ISO 8601
  /** Present only when event_type is 'completed' */
  result_summary?: {
    total_tests: number;
    duration_seconds: number;
  };
  /** Present only when event_type is 'failed' */
  error?: string;
}

// ---------------------------------------------------------------------------
// Results Types
// ---------------------------------------------------------------------------

/** A single test step within a generated test case */
export interface TestStep {
  step_number: number;
  action: string;
  target: string;
  value: string;
  description?: string;
}

/** A single assertion within a generated test case */
export interface TestAssertion {
  assertion_type: string;
  target: string;
  expected_value: string;
  description?: string;
}

/** A single AI-generated test case.
 *  Mirrors Pydantic GeneratedTestCase.
 */
export interface GeneratedTestCase {
  id: string;
  title: string;
  description: string;
  test_type: string;
  steps: TestStep[];
  assertions: TestAssertion[];
  estimated_duration_seconds: number;
  /** AI confidence in the quality of this test case (0.0–1.0) */
  confidence_score: number;
  tags?: string[];
}

/** Summary statistics for a completed workflow */
export interface WorkflowResultsSummary {
  total_tests: number;
  /** Map of test_type → count */
  test_types: Record<string, number>;
  avg_confidence_score: number;
  total_steps: number;
}

/** Full results payload for a completed workflow.
 *  Mirrors Pydantic WorkflowResultsResponse.
 */
export interface WorkflowResultsResponse {
  workflow_id: WorkflowId;
  status: Extract<WorkflowStatus, 'completed'>;
  test_cases: GeneratedTestCase[];
  summary: WorkflowResultsSummary;
  generated_at: string;  // ISO 8601
}

// ---------------------------------------------------------------------------
// Callback Type
// ---------------------------------------------------------------------------

/** Callback signature for SSE event subscribers */
export type WorkflowEventCallback = (event: AgentProgressEvent) => void;
