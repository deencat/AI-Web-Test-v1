/**
 * WorkflowResults — Sprint 10 Real API integration (Developer B)
 *
 * Displays the result of a completed workflow using WorkflowResultsResponse.
 * The real API returns test_case_ids (DB IDs) + agent result payloads.
 * Shows a summary panel, per-agent details, and the list of generated test IDs.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Button } from '../../../components/common/Button';
import agentWorkflowService from '../../../services/agentWorkflowService';
import type { WorkflowResultsResponse } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface SummaryCardProps {
  label: string;
  value: string | number;
}
const SummaryCard: React.FC<SummaryCardProps> = ({ label, value }) => (
  <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
    <span className="text-2xl font-bold text-gray-900">{value}</span>
    <span className="text-xs text-gray-500 mt-0.5 text-center">{label}</span>
  </div>
);

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface WorkflowResultsProps {
  workflowId: string;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const WorkflowResults: React.FC<WorkflowResultsProps> = ({
  workflowId,
  className = '',
}) => {
  const [results, setResults] = useState<WorkflowResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await agentWorkflowService.getWorkflowResults(workflowId);
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results.');
    } finally {
      setIsLoading(false);
    }
  }, [workflowId]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  // ---- Loading ----
  if (isLoading) {
    return (
      <div data-testid="results-loading" className={`flex items-center justify-center p-12 ${className}`}>
        <svg className="w-6 h-6 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="ml-3 text-sm text-gray-500">Loading results…</span>
      </div>
    );
  }

  // ---- Error ----
  if (error || !results) {
    return (
      <div data-testid="results-error" className={`p-6 bg-red-50 rounded-xl border border-red-200 ${className}`}>
        <p className="text-sm font-medium text-red-700 mb-1">Failed to load results</p>
        <p className="text-sm text-red-600">{error ?? 'Unknown error'}</p>
        <Button onClick={fetchResults} className="mt-3">Retry</Button>
      </div>
    );
  }

  const durationSecs = Math.round(results.total_duration_seconds);
  const obsElements  = (results.observation_result?.ui_elements as unknown[])?.length ?? 0;
  const reqScenarios = (results.requirements_result?.scenarios as unknown[])?.length ?? 0;

  return (
    <div data-testid="workflow-results" className={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900">Generated Tests</h3>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
            Completed
          </span>
        </div>
        <p className="text-xs text-gray-400 mt-0.5">
          Workflow {workflowId.slice(0, 8)}… · finished {new Date(results.completed_at).toLocaleTimeString()}
        </p>
      </div>

      {/* Summary stats */}
      <div
        data-testid="results-summary"
        className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-6 border-b border-gray-100"
      >
        <SummaryCard label="Tests generated" value={results.test_count} />
        <SummaryCard label="Duration (s)"    value={durationSecs} />
        <SummaryCard label="UI elements"     value={obsElements} />
        <SummaryCard label="BDD scenarios"   value={reqScenarios} />
      </div>

      {/* Test case IDs */}
      {results.test_case_ids.length > 0 && (
        <div className="p-6 border-b border-gray-100">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Test Case IDs ({results.test_case_ids.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {results.test_case_ids.map((id) => (
              <span
                key={id}
                className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono border border-blue-200"
              >
                #{id}
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Open the Test Cases page to view, edit, and run these tests.
          </p>
        </div>
      )}

      {/* Agent result overview */}
      <div className="p-6 space-y-3">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Agent Outputs</h4>
        {[
          { label: 'ObservationAgent',  key: 'observation_result',  present: !!results.observation_result },
          { label: 'RequirementsAgent', key: 'requirements_result', present: !!results.requirements_result },
          { label: 'AnalysisAgent',     key: 'analysis_result',     present: !!results.analysis_result },
          { label: 'EvolutionAgent',    key: 'evolution_result',    present: !!results.evolution_result },
        ].map(({ label, present }) => (
          <div key={label} className="flex items-center gap-2 text-sm text-gray-700">
            <span className={present ? 'text-green-500' : 'text-gray-300'} aria-hidden="true">
              {present ? '✓' : '○'}
            </span>
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};
