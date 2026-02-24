/**
 * AgentProgressPipeline — Sprint 10 Phase 2 (Developer B)
 *
 * Visualises the five pipeline stages of the agent workflow with
 * individual per-stage progress bars and a global progress indicator.
 *
 * Receives live data from useWorkflowProgress via props.
 */
import React from 'react';
import type { AgentProgress, AgentStage, WorkflowStatus } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Stage Configuration
// ---------------------------------------------------------------------------

interface StageConfig {
  id: AgentStage;
  label: string;
  description: string;
}

const STAGES: StageConfig[] = [
  { id: 'initializing', label: 'Initialising', description: 'Setting up agents' },
  { id: 'analyzing',   label: 'Analysing',    description: 'Observing page & UI elements' },
  { id: 'generating',  label: 'Generating',   description: 'Creating test scenarios' },
  { id: 'validating',  label: 'Validating',   description: 'Reviewing & scoring tests' },
  { id: 'complete',    label: 'Complete',     description: 'Tests ready' },
];

/** Determine the visual state of a pipeline stage */
type StageVisualState = 'completed' | 'active' | 'pending' | 'failed';

function getStageVisualState(
  stageId: AgentStage,
  currentStage: AgentStage | null,
  workflowStatus: WorkflowStatus | null
): StageVisualState {
  const stageOrder: AgentStage[] = ['initializing', 'analyzing', 'generating', 'validating', 'complete'];
  const stageIndex = stageOrder.indexOf(stageId);
  const currentIndex = currentStage ? stageOrder.indexOf(currentStage) : -1;

  if (workflowStatus === 'failed') return stageIndex <= currentIndex ? 'failed' : 'pending';
  if (stageIndex < currentIndex) return 'completed';
  if (stageIndex === currentIndex) return 'active';
  return 'pending';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface StageIconProps {
  state: StageVisualState;
  stepNumber: number;
}

const StageIcon: React.FC<StageIconProps> = ({ state, stepNumber }) => {
  const base = 'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors';

  if (state === 'completed') {
    return (
      <div className={`${base} bg-green-100 text-green-700 border-2 border-green-400`}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  if (state === 'active') {
    return (
      <div className={`${base} bg-blue-600 text-white border-2 border-blue-600 shadow-sm`}>
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }
  if (state === 'failed') {
    return (
      <div className={`${base} bg-red-100 text-red-600 border-2 border-red-400`}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }
  return (
    <div className={`${base} bg-gray-100 text-gray-400 border-2 border-gray-200`}>
      {stepNumber}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AgentProgressPipelineProps {
  /** Current workflow status; null before first data arrives */
  workflowStatus: WorkflowStatus | null;
  /** Granular progress object from the hook; null while loading */
  progress: AgentProgress | null;
  /** Error message when workflowStatus === 'failed' */
  error?: string | null;
  /** Optional class overrides */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const AgentProgressPipeline: React.FC<AgentProgressPipelineProps> = ({
  workflowStatus,
  progress,
  error,
  className = '',
}) => {
  const currentStage: AgentStage | null = progress?.stage ?? null;
  const percentage = progress?.percentage ?? 0;
  const message = progress?.message ?? '';

  // ---- Global progress bar color ----
  const progressBarColor =
    workflowStatus === 'failed'    ? 'bg-red-500'
    : workflowStatus === 'completed' ? 'bg-green-500'
    : 'bg-blue-600';

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}
      data-testid="agent-progress-pipeline"
    >
      {/* ---- Header ---- */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-900">Workflow Progress</h3>
        <span
          className={`
            px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
            ${workflowStatus === 'running'   ? 'bg-blue-100 text-blue-700'
              : workflowStatus === 'completed' ? 'bg-green-100 text-green-700'
              : workflowStatus === 'failed'    ? 'bg-red-100 text-red-600'
              : workflowStatus === 'pending'   ? 'bg-yellow-100 text-yellow-700'
              : 'bg-gray-100 text-gray-500'}
          `}
          data-testid="workflow-status-badge"
        >
          {workflowStatus ?? 'idle'}
        </span>
      </div>

      {/* ---- Global progress bar ---- */}
      <div className="mb-5">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{message || 'Waiting for updates…'}</span>
          <span data-testid="progress-percentage">{percentage}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${progressBarColor}`}
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        {(progress?.current_step != null && progress?.total_steps != null) && (
          <p className="text-xs text-gray-400 mt-1">
            Step {progress.current_step} of {progress.total_steps}
          </p>
        )}
      </div>

      {/* ---- Pipeline stages ---- */}
      <ol className="space-y-3" aria-label="Workflow stages">
        {STAGES.map((stage, idx) => {
          const visualState = getStageVisualState(stage.id, currentStage, workflowStatus);
          const isActive = visualState === 'active';

          return (
            <li
              key={stage.id}
              className={`
                flex items-center gap-3 p-3 rounded-lg transition-colors
                ${isActive ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'}
              `}
              data-testid={`stage-${stage.id}`}
              aria-current={isActive ? 'step' : undefined}
            >
              <StageIcon state={visualState} stepNumber={idx + 1} />
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${isActive ? 'text-blue-700' : visualState === 'completed' ? 'text-green-700' : 'text-gray-600'}`}>
                  {stage.label}
                </p>
                <p className="text-xs text-gray-400 truncate">{stage.description}</p>
              </div>
            </li>
          );
        })}
      </ol>

      {/* ---- Error message ---- */}
      {error && (
        <div
          className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
          data-testid="pipeline-error"
          role="alert"
        >
          <strong className="font-medium">Workflow failed: </strong>{error}
        </div>
      )}
    </div>
  );
};

export default AgentProgressPipeline;
