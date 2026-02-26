/**
 * AgentStatusMonitor — Sprint 10 (10B.11)
 *
 * Displays structured agent execution progress derived from SSE events:
 *   • Agent timeline (4 stages) with live status indicators
 *   • Per-agent key metrics: elements_found, scenarios_generated, tests_generated, confidence
 *   • Overall progress bar
 *   • Expandable "View Logs" section with agent messages
 *   • Error display and loading indicator
 *
 * Props come from the parent (fed by useWorkflowProgress) — avoids double SSE connections.
 */
import React, { useState } from 'react';
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
  const [logsExpanded, setLogsExpanded] = useState(false);

  const progressPct = Math.round(Math.min(totalProgress, 1) * 100);

  // Derive log entries from agent messages — ordered by execution sequence
  const logEntries = AGENT_ORDER.flatMap((agent) => {
    const prog = agentProgress[agent];
    if (!prog?.message) return [];
    return [{ agent, message: prog.message, status: prog.status }];
  });

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}
      data-testid="agent-status-monitor"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-base font-semibold text-gray-900">Agent Status</h3>
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

      {/* Overall progress bar */}
      <div className="mb-5">
        <div className="flex justify-between items-center text-xs text-gray-500 mb-1">
          <span>Overall Progress</span>
          <span data-testid="overall-progress-pct">{progressPct}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2" role="progressbar" aria-valuenow={progressPct} aria-valuemin={0} aria-valuemax={100}>
          <div
            className={[
              'h-2 rounded-full transition-all duration-500',
              workflowStatus === 'failed'    ? 'bg-red-500'   :
              workflowStatus === 'completed' ? 'bg-green-500' :
              'bg-blue-600',
            ].join(' ')}
            style={{ width: `${progressPct}%` }}
            data-testid="overall-progress-bar"
          />
        </div>
      </div>

      {/* Agent timeline */}
      <ol className="space-y-2" aria-label="Agent execution timeline">
        {AGENT_ORDER.map((agent) => {
          const status = getStageStatus(agent, currentAgent, workflowStatus, agentProgress);
          const prog   = agentProgress[agent];

          return (
            <li
              key={agent}
              data-testid={`agent-stage-${agent}`}
              data-status={status}
              className={[
                'flex items-start gap-3 p-3 rounded-lg border transition-colors',
                status === 'running'   ? 'border-blue-200 bg-blue-50'   :
                status === 'completed' ? 'border-green-200 bg-green-50' :
                status === 'failed'    ? 'border-red-200 bg-red-50'     :
                'border-gray-100 bg-gray-50',
              ].join(' ')}
            >
              <StatusDot status={status} />

              <div className="flex-1 min-w-0">
                {/* Agent name + duration */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800">
                    {AGENT_LABELS[agent]}
                  </span>
                  {prog?.duration_seconds != null && (
                    <span className="text-xs text-gray-400 ml-2 tabular-nums">
                      {formatDuration(prog.duration_seconds)}
                    </span>
                  )}
                </div>

                {/* Description */}
                <p className="text-xs text-gray-500 mt-0.5">{AGENT_DESCRIPTIONS[agent]}</p>

                {/* Status message */}
                {prog?.message && (
                  <p className="text-xs text-gray-600 mt-1 italic truncate">{prog.message}</p>
                )}

                {/* Key metrics */}
                <div className="flex flex-wrap gap-3 mt-1 text-xs text-gray-500">
                  {prog?.elements_found != null && (
                    <span data-testid={`metric-elements-${agent}`}>
                      {prog.elements_found} elements
                    </span>
                  )}
                  {prog?.scenarios_generated != null && (
                    <span data-testid={`metric-scenarios-${agent}`}>
                      {prog.scenarios_generated} scenarios
                    </span>
                  )}
                  {prog?.tests_generated != null && (
                    <span data-testid={`metric-tests-${agent}`}>
                      {prog.tests_generated} tests
                    </span>
                  )}
                  {prog?.confidence != null && (
                    <span data-testid={`metric-confidence-${agent}`}>
                      {(prog.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>

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

      {/* Logs toggle + viewer */}
      <div className="mt-4 border-t border-gray-100 pt-3">
        <button
          type="button"
          data-testid="toggle-logs-button"
          onClick={() => setLogsExpanded((prev) => !prev)}
          className="text-xs text-blue-600 hover:text-blue-700 underline focus:outline-none focus:ring-1 focus:ring-blue-400 rounded"
          aria-expanded={logsExpanded}
          aria-controls="agent-log-viewer"
        >
          {logsExpanded ? 'Hide Logs ▲' : 'View Logs ▼'}
        </button>

        {logsExpanded && (
          <div
            id="agent-log-viewer"
            data-testid="log-viewer"
            className="mt-2 p-3 bg-gray-900 rounded-lg text-xs text-green-400 font-mono max-h-48 overflow-y-auto space-y-1"
            aria-label="Agent activity logs"
            role="log"
            aria-live="polite"
          >
            {logEntries.length === 0 ? (
              <p className="text-gray-500">No log entries yet.</p>
            ) : (
              logEntries.map((entry, i) => (
                <div key={i} data-testid={`log-entry-${entry.agent}`}>
                  <span className="text-gray-400 uppercase mr-1">[{entry.agent}]</span>
                  <span className={entry.status === 'failed' ? 'text-red-400' : ''}>
                    {entry.message}
                  </span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
