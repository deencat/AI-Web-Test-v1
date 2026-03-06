/**
 * AgentStatusMonitor — Sprint 10 (10B.11)
 *
 * Lightweight stage-details panel (not a second progress pipeline):
 *   • Current/most-relevant stage details
 *   • Mid-stage progress (when backend provides agent progress)
 *   • Key metrics for the focused stage
 *   • Completed-stage chips for quick scan
 *   • Error/loading states
 */
import React from 'react';
import type { AgentProgress, WorkflowStatus } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AGENT_ORDER = ['observation', 'requirements', 'analysis', 'evolution'] as const;
type AgentName = (typeof AGENT_ORDER)[number];

const AGENT_LABELS: Record<AgentName, string> = {
  observation:  'Observation',
  requirements: 'Requirements',
  analysis:     'Analysis',
  evolution:    'Evolution',
};

const AGENT_DESCRIPTIONS: Record<AgentName, string> = {
  observation:  'Crawl page & extract UI elements',
  requirements: 'Generate BDD scenarios',
  analysis:     'Risk scoring & prioritisation',
  evolution:    'Generate executable test code',
};

type StageStatus = 'completed' | 'running' | 'pending' | 'failed';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStageStatus(
  agent: AgentName,
  currentAgent: string | null,
  workflowStatus: WorkflowStatus | null,
  agentProgress: Record<string, AgentProgress>
): StageStatus {
  const prog = agentProgress[agent];

  if (prog?.status === 'failed')    return 'failed';
  if (prog?.status === 'completed') return 'completed';

  // If whole workflow is done, mark all remaining as completed
  if (workflowStatus === 'completed') return 'completed';

  if (currentAgent === agent)       return 'running';
  if (prog?.status === 'running')   return 'running';
  return 'pending';
}

function getFocusedAgent(
  currentAgent: string | null,
  workflowStatus: WorkflowStatus | null,
  agentProgress: Record<string, AgentProgress>
): AgentName {
  if (currentAgent && AGENT_ORDER.includes(currentAgent as AgentName)) {
    return currentAgent as AgentName;
  }

  const running = AGENT_ORDER.find((agent) => agentProgress[agent]?.status === 'running');
  if (running) return running;

  const lastCompleted = [...AGENT_ORDER].reverse().find((agent) => agentProgress[agent]?.status === 'completed');
  if (lastCompleted) return lastCompleted;

  if (workflowStatus === 'completed') return 'evolution';
  return 'observation';
}

function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '';
  return seconds >= 60
    ? `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
    : `${Math.round(seconds)}s`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const StatusDot: React.FC<{ status: StageStatus }> = ({ status }) => (
  <span
    className={[
      'mt-1 flex-shrink-0 w-2.5 h-2.5 rounded-full',
      status === 'running'   ? 'bg-blue-500 animate-pulse'  : '',
      status === 'completed' ? 'bg-green-500'                : '',
      status === 'failed'    ? 'bg-red-500'                  : '',
      status === 'pending'   ? 'bg-gray-300'                 : '',
    ].filter(Boolean).join(' ')}
    aria-hidden="true"
  />
);

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AgentStatusMonitorProps {
  workflowStatus: WorkflowStatus | null;
  /** Per-agent progress map from useWorkflowProgress */
  agentProgress: Record<string, AgentProgress>;
  currentAgent: string | null;
  /** Overall progress fraction 0.0–1.0 */
  totalProgress: number;
  /** True while polling/initial load is in-flight */
  isLoading?: boolean;
  /** Error message when workflowStatus === 'failed' */
  error?: string | null;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const AgentStatusMonitor: React.FC<AgentStatusMonitorProps> = ({
  workflowStatus,
  agentProgress,
  currentAgent,
  totalProgress,
  isLoading = false,
  error,
  className = '',
}) => {
  const focusedAgent = getFocusedAgent(currentAgent, workflowStatus, agentProgress);
  const focusedProgress = agentProgress[focusedAgent];
  const focusedStatus = getStageStatus(focusedAgent, currentAgent, workflowStatus, agentProgress);
  const focusedPct = Math.round((focusedProgress?.progress ?? 0) * 100);

  const completedAgents = AGENT_ORDER.filter((agent) =>
    getStageStatus(agent, currentAgent, workflowStatus, agentProgress) === 'completed'
  );

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}
      data-testid="agent-status-monitor"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-base font-semibold text-gray-900">Stage Details</h3>
        {isLoading && (
          <span
            data-testid="status-loading"
            className="text-xs text-blue-500"
            role="status"
            aria-live="polite"
          >
            Loading…
          </span>
        )}
      </div>

      {/* Focused stage card */}
      <div
        data-testid="current-stage-card"
        className={[
          'p-4 rounded-lg border',
          focusedStatus === 'running' ? 'border-blue-200 bg-blue-50' :
          focusedStatus === 'completed' ? 'border-green-200 bg-green-50' :
          focusedStatus === 'failed' ? 'border-red-200 bg-red-50' :
          'border-gray-100 bg-gray-50',
        ].join(' ')}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <StatusDot status={focusedStatus} />
            <span className="text-sm font-medium text-gray-800" data-testid="current-stage-name">
              {AGENT_LABELS[focusedAgent]}
            </span>
            <span
              data-testid="current-stage-status"
              className={[
                'text-xs px-2 py-0.5 rounded-full capitalize',
                focusedStatus === 'running' ? 'bg-blue-100 text-blue-700' :
                focusedStatus === 'completed' ? 'bg-green-100 text-green-700' :
                focusedStatus === 'failed' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-600',
              ].join(' ')}
            >
              {focusedStatus}
            </span>
          </div>
          {focusedProgress?.duration_seconds != null && (
            <span className="text-xs text-gray-500 tabular-nums" data-testid="current-stage-duration">
              {formatDuration(focusedProgress.duration_seconds)}
            </span>
          )}
        </div>

        <p className="text-xs text-gray-500 mt-1">{AGENT_DESCRIPTIONS[focusedAgent]}</p>

        {focusedProgress?.message && (
          <p className="text-sm text-gray-700 mt-2" data-testid="current-stage-message">
            {focusedProgress.message}
          </p>
        )}

        {/* Mid-stage progress (shown only when available and meaningful) */}
        {focusedPct > 0 && focusedPct < 100 && focusedStatus === 'running' && (
          <div className="mt-3" data-testid="current-stage-progress">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>In-stage progress</span>
              <span data-testid="current-stage-progress-pct">{focusedPct}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all duration-500"
                style={{ width: `${focusedPct}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-3 mt-3 text-xs text-gray-600">
          {focusedProgress?.elements_found != null && (
            <span data-testid="metric-elements-current">{focusedProgress.elements_found} elements</span>
          )}
          {focusedProgress?.scenarios_generated != null && (
            <span data-testid="metric-scenarios-current">{focusedProgress.scenarios_generated} scenarios</span>
          )}
          {focusedProgress?.tests_generated != null && (
            <span data-testid="metric-tests-current">{focusedProgress.tests_generated} tests</span>
          )}
          {focusedProgress?.confidence != null && (
            <span data-testid="metric-confidence-current">{(focusedProgress.confidence * 100).toFixed(0)}% confidence</span>
          )}
        </div>
      </div>

      {/* Completed stage chips (compact context, avoids duplicating full pipeline) */}
      <div className="mt-4" data-testid="completed-stages">
        <p className="text-xs text-gray-500 mb-2">Completed stages</p>
        <div className="flex flex-wrap gap-2">
          {completedAgents.length === 0 ? (
            <span className="text-xs text-gray-400" data-testid="no-completed-stages">None yet</span>
          ) : completedAgents.map((agent) => (
            <span
              key={agent}
              data-testid={`completed-${agent}`}
              className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700"
            >
              ✓ {AGENT_LABELS[agent]}
            </span>
          ))}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div
          className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
          data-testid="status-error"
          role="alert"
        >
          {error}
        </div>
      )}
    </div>
  );
};
