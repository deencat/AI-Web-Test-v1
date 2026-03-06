/**
 * AgentProgressPipeline — Sprint 10 Real API integration (Developer B)
 *
 * Visualises the four real agent stages using DisplayProgress from
 * useWorkflowProgress.  Stage IDs map to the real agent names.
 */
import React from 'react';
import type { DisplayProgress, WorkflowStatus } from '../../../types/agentWorkflow.types';
import { StopAgentButton } from './StopAgentButton';

// ---------------------------------------------------------------------------
// Stage Configuration — maps to real agent names
// ---------------------------------------------------------------------------

interface StageConfig {
  id: string;
  label: string;
  description: string;
}

const STAGES: StageConfig[] = [
  { id: 'observation',  label: 'Observation',  description: 'Crawl page & extract UI elements' },
  { id: 'requirements', label: 'Requirements', description: 'Generate BDD scenarios' },
  { id: 'analysis',     label: 'Analysis',     description: 'Risk scoring & prioritisation' },
  { id: 'evolution',    label: 'Evolution',    description: 'Generate executable test code' },
  { id: 'complete',     label: 'Complete',     description: 'Tests ready' },
];

type StageVisualState = 'completed' | 'active' | 'pending' | 'failed';

const STAGE_ORDER = ['observation', 'requirements', 'analysis', 'evolution', 'complete'];

function getVisualState(
  stageId: string,
  currentAgent: string | null,
  workflowStatus: WorkflowStatus | null
): StageVisualState {
  const stageIdx   = STAGE_ORDER.indexOf(stageId);
  const currentIdx = currentAgent ? STAGE_ORDER.indexOf(currentAgent) : -1;

  if (workflowStatus === 'completed') return stageIdx <= STAGE_ORDER.indexOf('evolution') ? 'completed' : 'completed';
  if (workflowStatus === 'failed')    return stageIdx <= currentIdx ? 'failed' : 'pending';
  if (stageIdx < currentIdx)  return 'completed';
  if (stageIdx === currentIdx) return 'active';
  return 'pending';
}

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

const StageIcon: React.FC<{ state: StageVisualState; stepNumber: number }> = ({ state, stepNumber }) => {
  const base = 'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors';
  if (state === 'completed') return (
    <div className={`${base} bg-green-100 text-green-700 border-2 border-green-400`}>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
      </svg>
    </div>
  );
  if (state === 'active') return (
    <div className={`${base} bg-blue-600 text-white border-2 border-blue-600 shadow-sm`}>
      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  );
  if (state === 'failed') return (
    <div className={`${base} bg-red-100 text-red-600 border-2 border-red-400`}>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
      </svg>
    </div>
  );
  return (
    <div className={`${base} bg-gray-100 text-gray-400 border-2 border-gray-200`}>{stepNumber}</div>
  );
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AgentProgressPipelineProps {
  workflowStatus: WorkflowStatus | null;
  /** DisplayProgress derived from useWorkflowProgress; null while loading */
  progress: DisplayProgress | null;
  error?: string | null;
  /** If provided, renders a ⏹ Stop Agent button in the header (10B.12) */
  onStop?: () => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const AgentProgressPipeline: React.FC<AgentProgressPipelineProps> = ({
  workflowStatus,
  progress,
  error,
  onStop,
  className = '',
}) => {
  const currentAgent = progress?.currentAgent ?? null;
  const percentage   = progress?.percentage ?? 0;
  const message      = progress?.message ?? '';

  const barColor =
    workflowStatus === 'failed'    ? 'bg-red-500'
    : workflowStatus === 'completed' ? 'bg-green-500'
    : 'bg-blue-600';

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}
      data-testid="agent-progress-pipeline"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-900">Workflow Progress</h3>
        <div className="flex items-center gap-2">
          {onStop && (
            <StopAgentButton
              workflowStatus={workflowStatus}
              onStop={onStop}
            />
          )}
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
              ${workflowStatus === 'running'    ? 'bg-blue-100 text-blue-700'
              : workflowStatus === 'completed'  ? 'bg-green-100 text-green-700'
              : workflowStatus === 'failed'     ? 'bg-red-100 text-red-600'
              : workflowStatus === 'pending'    ? 'bg-yellow-100 text-yellow-700'
              : 'bg-gray-100 text-gray-500'}`}
            data-testid="workflow-status-badge"
          >
            {workflowStatus ?? 'idle'}
          </span>
        </div>
      </div>

      {/* Global progress bar */}
      <div className="mb-5">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-500 truncate">{message || 'Waiting…'}</span>
          <span className="text-xs font-semibold text-gray-700 ml-2 flex-shrink-0" data-testid="progress-percentage">
            {percentage}%
          </span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {/* Stage list */}
      <ol className="space-y-3">
        {STAGES.map((stage, idx) => {
          const visualState = getVisualState(stage.id, currentAgent, workflowStatus);
          const isActive = visualState === 'active';
          const agentProg = progress?.agentProgress?.[stage.id];

          return (
            <li
              key={stage.id}
              data-testid={`stage-${stage.id}`}
              aria-current={isActive ? 'step' : undefined}
              className={`flex items-start gap-3 rounded-lg p-2 transition-colors
                ${isActive ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
            >
              <StageIcon state={visualState} stepNumber={idx + 1} />
              <div className="flex-1 min-w-0 pt-1">
                <p className={`text-sm font-medium ${isActive ? 'text-blue-700' : 'text-gray-700'}`}>
                  {stage.label}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {isActive && agentProg?.message
                    ? agentProg.message
                    : stage.description}
                </p>
                {/* Per-agent detail badges */}
                {agentProg?.elements_found != null && (
                  <span className="inline-block mt-1 text-xs text-gray-500">{agentProg.elements_found} elements</span>
                )}
                {agentProg?.scenarios_generated != null && (
                  <span className="inline-block mt-1 text-xs text-gray-500">{agentProg.scenarios_generated} scenarios</span>
                )}
                {agentProg?.tests_generated != null && (
                  <span className="inline-block mt-1 text-xs text-gray-500">{agentProg.tests_generated} tests</span>
                )}
              </div>
            </li>
          );
        })}
      </ol>

      {/* Error panel */}
      {error && (
        <div data-testid="workflow-error" className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
};
