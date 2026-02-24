/**
 * AgentWorkflowTrigger — Sprint 10 Phase 2 (Developer B)
 *
 * Form component that lets a user supply a URL and optional settings to
 * start the 4-agent AI test generation workflow.
 *
 * Calls agentWorkflowService.generateTests() and passes the resulting
 * workflow_id up via the onWorkflowStarted callback.
 */
import React, { useState } from 'react';
import { Button } from '../../../components/common/Button';
import agentWorkflowService from '../../../services/agentWorkflowService';
import type { GenerateTestsRequest } from '../../../types/agentWorkflow.types';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AgentWorkflowTriggerProps {
  /** Invoked with the new workflow_id once the workflow is queued */
  onWorkflowStarted: (workflowId: string) => void;
  /** Optional class overrides for the root element */
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const AgentWorkflowTrigger: React.FC<AgentWorkflowTriggerProps> = ({
  onWorkflowStarted,
  className = '',
}) => {
  // Form state
  const [url, setUrl] = useState('');
  const [maxTests, setMaxTests] = useState<number>(10);
  const [includeAssertions, setIncludeAssertions] = useState(true);
  const [context, setContext] = useState('');

  // Async state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setSubmitError('Please enter a valid URL.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    const request: GenerateTestsRequest = {
      url: url.trim(),
      max_tests: maxTests,
      include_assertions: includeAssertions,
      context: context.trim() || undefined,
    };

    try {
      const response = await agentWorkflowService.generateTests(request);
      onWorkflowStarted(response.workflow_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to start workflow.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>
      <h2 className="text-xl font-semibold text-gray-900 mb-1">
        AI Test Generation
      </h2>
      <p className="text-sm text-gray-500 mb-5">
        Provide a URL and the 4-agent workflow will analyse the page and generate test cases automatically.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4" data-testid="agent-workflow-form">
        {/* ---- URL ---- */}
        <div>
          <label htmlFor="workflow-url" className="block text-sm font-medium text-gray-700 mb-1">
            Target URL <span className="text-red-500">*</span>
          </label>
          <input
            id="workflow-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/login"
            required
            className="
              w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              disabled:bg-gray-50 disabled:cursor-not-allowed
            "
            disabled={isSubmitting}
            data-testid="url-input"
          />
        </div>

        {/* ---- Max tests ---- */}
        <div>
          <label htmlFor="workflow-max-tests" className="block text-sm font-medium text-gray-700 mb-1">
            Max tests to generate
          </label>
          <input
            id="workflow-max-tests"
            type="number"
            min={1}
            max={50}
            value={maxTests}
            onChange={(e) => setMaxTests(Number(e.target.value))}
            className="
              w-28 rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              disabled:bg-gray-50 disabled:cursor-not-allowed
            "
            disabled={isSubmitting}
            data-testid="max-tests-input"
          />
        </div>

        {/* ---- Include assertions ---- */}
        <div className="flex items-center gap-2">
          <input
            id="workflow-assertions"
            type="checkbox"
            checked={includeAssertions}
            onChange={(e) => setIncludeAssertions(e.target.checked)}
            disabled={isSubmitting}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            data-testid="assertions-checkbox"
          />
          <label htmlFor="workflow-assertions" className="text-sm text-gray-700">
            Include assertion steps
          </label>
        </div>

        {/* ---- Context ---- */}
        <div>
          <label htmlFor="workflow-context" className="block text-sm font-medium text-gray-700 mb-1">
            Context / instructions <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            id="workflow-context"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="e.g. Focus on the checkout flow, ignore the blog section."
            rows={2}
            className="
              w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              disabled:bg-gray-50 disabled:cursor-not-allowed resize-none
            "
            disabled={isSubmitting}
            data-testid="context-textarea"
          />
        </div>

        {/* ---- Error ---- */}
        {submitError && (
          <p
            className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 border border-red-200"
            data-testid="submit-error"
          >
            {submitError}
          </p>
        )}

        {/* ---- Submit ---- */}
        <Button
          type="submit"
          variant="primary"
          loading={isSubmitting}
          disabled={isSubmitting}
          className="w-full"
          data-testid="generate-button"
        >
          Generate Tests
        </Button>
      </form>
    </div>
  );
};

export default AgentWorkflowTrigger;
