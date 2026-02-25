/**
 * Agent Workflow API Contract Types — Sprint 10 (Real API Integration)
 *
 * These TypeScript types mirror the Pydantic schemas in
 * backend/app/schemas/workflow.py and the API spec in
 * backend/app/api/v2/API_SPECIFICATION.md.
 *
 * ⚠️  REAL API — No more mock data. VITE_USE_MOCK=false.
 */

// ---------------------------------------------------------------------------
// Primitive / Utility Types
// ---------------------------------------------------------------------------

/** Unique identifier for a workflow run */
export type WorkflowId = string;

/** Lifecycle status of a workflow */
export type WorkflowStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

// ---------------------------------------------------------------------------
// Per-Agent Progress (matches backend AgentProgress Pydantic model)
// ---------------------------------------------------------------------------

/**
 * Progress detail for a single agent.
 * Returned inside WorkflowStatusResponse.progress (a Record<agentName, AgentProgress>).
 */
export interface AgentProgress {
  /** Agent name: observation | requirements | analysis | evolution */
  agent: string;
  /** Status: pending | running | completed | failed */
  status: string;
  /** Completion fraction 0.0–1.0 */
  progress: number;
  /** Human-readable status message */
  message?: string | null;
  /** ISO 8601 timestamp when agent started */
  started_at?: string | null;
  /** ISO 8601 timestamp when agent completed */
  completed_at?: string | null;
  /** Duration in seconds */
  duration_seconds?: number | null;
  /** AI confidence score (ObservationAgent) */
  confidence?: number | null;
  /** Number of UI elements found (ObservationAgent) */
  elements_found?: number | null;
  /** Number of scenarios generated (RequirementsAgent) */
  scenarios_generated?: number | null;
  /** Number of tests generated (EvolutionAgent) */
  tests_generated?: number | null;
}

// ---------------------------------------------------------------------------
// Request Types (Frontend → Backend)
// ---------------------------------------------------------------------------

/**
 * Request body for POST /api/v2/generate-tests.
 * Mirrors Pydantic GenerateTestsRequest.
 */
export interface GenerateTestsRequest {
  /** Target URL to analyse and generate tests for */
  url: string;
  /** Optional instruction (e.g. "Test purchase flow for 5G plan") */
  user_instruction?: string;
  /** Crawl depth: 1 = current page, 2 = include links, 3 = deep crawl. Default: 1 */
  depth?: number;
  /** Optional login credentials */
  login_credentials?: { username?: string; email?: string; password: string };
  /** Optional Gmail credentials for OTP */
  gmail_credentials?: { email: string; password: string };
}

// ---------------------------------------------------------------------------
// Response Types (Backend → Frontend) — matches real API spec
// ---------------------------------------------------------------------------

/**
 * Response body for POST /api/v2/generate-tests (202 Accepted).
 * All POST entry points return WorkflowStatusResponse.
 * Mirrors Pydantic WorkflowStatusResponse.
 */
export interface WorkflowStatusResponse {
  workflow_id: WorkflowId;
  /** Overall lifecycle status */
  status: WorkflowStatus;
  /** Name of the currently executing agent, or null */
  current_agent: string | null;
  /** Per-agent progress map */
  progress: Record<string, AgentProgress>;
  /** Overall progress fraction 0.0–1.0 */
  total_progress: number;
  /** ISO 8601 start time */
  started_at: string;
  /** Estimated completion time (ISO 8601); null if unknown */
  estimated_completion?: string | null;
  /** Error message when status === 'failed' */
  error?: string | null;
}

/**
 * Full results payload for a completed workflow.
 * Mirrors Pydantic WorkflowResultsResponse.
 * GET /api/v2/workflows/{id}/results
 */
export interface WorkflowResultsResponse {
  workflow_id: WorkflowId;
  status: WorkflowStatus;
  /** Database IDs of generated test cases */
  test_case_ids: number[];
  /** Count of generated tests */
  test_count: number;
  /** ObservationAgent result payload */
  observation_result?: Record<string, unknown> | null;
  /** RequirementsAgent result payload */
  requirements_result?: Record<string, unknown> | null;
  /** AnalysisAgent result payload */
  analysis_result?: Record<string, unknown> | null;
  /** EvolutionAgent result payload */
  evolution_result?: Record<string, unknown> | null;
  /** ISO 8601 completion timestamp */
  completed_at: string;
  /** Total duration in seconds */
  total_duration_seconds: number;
}

/**
 * Error response for 4xx / 5xx status codes.
 * Mirrors Pydantic WorkflowErrorResponse.
 */
export interface WorkflowErrorResponse {
  error: string;
  code: string;
  workflow_id?: string | null;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// SSE Event Types — matches real backend event format
// ---------------------------------------------------------------------------

export type SseEventType =
  | 'agent_started'
  | 'agent_progress'
  | 'agent_completed'
  | 'workflow_completed'
  | 'workflow_failed';

/**
 * SSE event payload received from GET /api/v2/workflows/{id}/stream.
 *
 * The backend sends named SSE events.  Each message data JSON has this shape.
 * Event names: agent_started | agent_progress | agent_completed |
 *              workflow_completed | workflow_failed
 */
export interface AgentProgressEvent {
  /** Event name (same as SSE `event:` field) */
  event: SseEventType;
  /** Event-specific data payload */
  data: Record<string, unknown>;
  /** ISO 8601 timestamp */
  timestamp: string;
}

/** Callback signature for SSE event subscribers */
export type WorkflowEventCallback = (event: AgentProgressEvent) => void;

// ---------------------------------------------------------------------------
// Display Types — used by UI components, derived from real API responses
// ---------------------------------------------------------------------------

/**
 * Stage identifier for the pipeline visualisation.
 * Maps from the four real agents + idle/complete states.
 */
export type AgentStage =
  | 'idle'
  | 'observation'
  | 'requirements'
  | 'analysis'
  | 'evolution'
  | 'complete';

/**
 * Simplified progress model used by AgentProgressPipeline.
 * Derived from WorkflowStatusResponse by the hook/service layer.
 */
export interface DisplayProgress {
  /** Active agent name (maps to AgentStage) */
  currentAgent: AgentStage;
  /** Overall percentage 0–100 */
  percentage: number;
  /** Human-readable status message */
  message: string;
  /** Per-agent progress map (pass-through from API) */
  agentProgress: Record<string, AgentProgress>;
}
