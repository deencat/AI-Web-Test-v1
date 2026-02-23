/**
 * WorkflowResults — Sprint 10 Phase 2 (Developer B)
 *
 * Displays the generated test cases once a workflow has completed.
 * Fetches results from agentWorkflowService.getWorkflowResults() and
 * renders an expandable list with summary statistics.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { Button } from '../../../components/common/Button';
import agentWorkflowService from '../../../services/agentWorkflowService';
import type { GeneratedTestCase, WorkflowResultsResponse } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface ConfidenceBadgeProps {
  score: number;
}

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ score }) => {
  const pct = Math.round(score * 100);
  const color =
    pct >= 85 ? 'bg-green-100 text-green-700'
    : pct >= 60 ? 'bg-yellow-100 text-yellow-700'
    : 'bg-red-100 text-red-600';
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {pct}% confidence
    </span>
  );
};

interface TestCaseCardProps {
  testCase: GeneratedTestCase;
  defaultExpanded?: boolean;
}

const TestCaseCard: React.FC<TestCaseCardProps> = ({ testCase, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div
      className="border border-gray-200 rounded-lg overflow-hidden"
      data-testid={`test-case-${testCase.id}`}
    >
      {/* Card header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-start justify-between gap-3 px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        aria-expanded={expanded}
      >
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{testCase.title}</p>
          <p className="text-xs text-gray-500 mt-0.5 truncate">{testCase.description}</p>
        </div>
        <div className="flex-shrink-0 flex items-center gap-2 mt-0.5">
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 capitalize">
            {testCase.test_type}
          </span>
          <ConfidenceBadge score={testCase.confidence_score} />
          <span
            className={`text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            aria-hidden="true"
          >
            ▾
          </span>
        </div>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="px-4 py-3 bg-white space-y-4">
          {/* Steps */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              Steps ({testCase.steps.length})
            </h4>
            <ol className="space-y-1.5">
              {testCase.steps.map((step) => (
                <li key={step.step_number} className="flex gap-2 text-sm text-gray-700">
                  <span className="flex-shrink-0 w-5 h-5 bg-gray-100 rounded text-xs font-medium text-gray-500 flex items-center justify-center">
                    {step.step_number}
                  </span>
                  <span>
                    <span className="font-medium capitalize">{step.action}</span>
                    {step.target && (
                      <code className="ml-1 px-1 py-0.5 bg-gray-100 rounded text-xs">{step.target}</code>
                    )}
                    {step.value && <span className="ml-1 text-gray-500">→ "{step.value}"</span>}
                    {step.description && <span className="ml-1 text-gray-400">({step.description})</span>}
                  </span>
                </li>
              ))}
            </ol>
          </div>

          {/* Assertions */}
          {testCase.assertions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Assertions ({testCase.assertions.length})
              </h4>
              <ul className="space-y-1.5">
                {testCase.assertions.map((assertion, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-green-500 flex-shrink-0" aria-hidden="true">✓</span>
                    <span>
                      <span className="font-medium capitalize">{assertion.assertion_type.replace('_', ' ')}</span>
                      {assertion.target && (
                        <code className="ml-1 px-1 py-0.5 bg-gray-100 rounded text-xs">{assertion.target}</code>
                      )}
                      {assertion.expected_value && (
                        <span className="ml-1 text-gray-500">= "{assertion.expected_value}"</span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Meta */}
          <div className="flex flex-wrap gap-2 pt-1 border-t border-gray-100">
            <span className="text-xs text-gray-400">
              ~{testCase.estimated_duration_seconds}s
            </span>
            {testCase.tags?.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface WorkflowResultsProps {
  /** The completed workflow to fetch results for */
  workflowId: string;
  /** Called when the user wants to start a new workflow */
  onReset?: () => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const WorkflowResults: React.FC<WorkflowResultsProps> = ({
  workflowId,
  onReset,
  className = '',
}) => {
  const [results, setResults] = useState<WorkflowResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const data = await agentWorkflowService.getWorkflowResults(workflowId);
      setResults(data);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : 'Failed to fetch results.');
    } finally {
      setIsLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // -------------------------------------------------------------------------
  // Render — loading
  // -------------------------------------------------------------------------

  if (isLoading) {
    return (
      <div
        className={`bg-white rounded-xl shadow-sm border border-gray-200 p-8 flex items-center justify-center ${className}`}
        data-testid="results-loading"
      >
        <svg className="animate-spin h-6 w-6 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-gray-500 text-sm">Loading results…</span>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render — error
  // -------------------------------------------------------------------------

  if (fetchError || !results) {
    return (
      <div
        className={`bg-white rounded-xl shadow-sm border border-red-200 p-6 ${className}`}
        data-testid="results-error"
      >
        <p className="text-red-600 text-sm mb-4">
          {fetchError ?? 'No results available.'}
        </p>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={fetchResults}>Retry</Button>
          {onReset && <Button variant="secondary" size="sm" onClick={onReset}>Start over</Button>}
        </div>
      </div>
    );
  }

  const { test_cases, summary } = results;

  // -------------------------------------------------------------------------
  // Render — results
  // -------------------------------------------------------------------------

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}
      data-testid="workflow-results"
    >
      {/* ---- Header ---- */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Generated Tests
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">Workflow {workflowId}</p>
        </div>
        {onReset && (
          <Button variant="secondary" size="sm" onClick={onReset} data-testid="reset-button">
            New workflow
          </Button>
        )}
      </div>

      {/* ---- Summary bar ---- */}
      <div
        className="grid grid-cols-2 sm:grid-cols-4 gap-4 px-6 py-4 bg-gray-50 border-b border-gray-100"
        data-testid="results-summary"
      >
        <div>
          <p className="text-xs text-gray-500">Test cases</p>
          <p className="text-xl font-bold text-gray-900">{summary.total_tests}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Total steps</p>
          <p className="text-xl font-bold text-gray-900">{summary.total_steps}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Avg confidence</p>
          <p className="text-xl font-bold text-gray-900">
            {Math.round(summary.avg_confidence_score * 100)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Test types</p>
          <p className="text-sm font-medium text-gray-700">
            {Object.entries(summary.test_types)
              .map(([type, count]) => `${type} (${count})`)
              .join(', ')}
          </p>
        </div>
      </div>

      {/* ---- Test case list ---- */}
      <div className="px-6 py-4 space-y-3" data-testid="test-case-list">
        {test_cases.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-6">No test cases were generated.</p>
        ) : (
          test_cases.map((tc: GeneratedTestCase) => (
            <TestCaseCard key={tc.id} testCase={tc} />
          ))
        )}
      </div>
    </div>
  );
};

export default WorkflowResults;
