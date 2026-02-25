/**
 * AgentWorkflowTrigger — Sprint 10 Real API integration (Developer B)
 *
 * Form that triggers the 4-agent AI test generation workflow.
 * Calls agentWorkflowService.generateTests() which hits POST /api/v2/generate-tests
 * and returns a WorkflowStatusResponse (202 Accepted) with a workflow_id.
 */
import React, { useState } from 'react';
import { Button } from '../../../components/common/Button';
import agentWorkflowService from '../../../services/agentWorkflowService';
import type { GenerateTestsRequest } from '../../../types/agentWorkflow.types';

export interface AgentWorkflowTriggerProps {
  /** Invoked with the new workflow_id once the workflow is accepted by the backend */
  onWorkflowStarted: (workflowId: string) => void;
  className?: string;
}

export const AgentWorkflowTrigger: React.FC<AgentWorkflowTriggerProps> = ({
  onWorkflowStarted,
  className = '',
}) => {
  const [url, setUrl] = useState('');
  const [userInstruction, setUserInstruction] = useState('');
  const [depth, setDepth] = useState<1 | 2 | 3>(1);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

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
      depth,
      ...(userInstruction.trim() && { user_instruction: userInstruction.trim() }),
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

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>
      <h2 className="text-xl font-semibold text-gray-900 mb-1">AI Test Generation</h2>
      <p className="text-sm text-gray-500 mb-5">
        Provide a URL and the 4-agent workflow will analyse the page and generate test cases automatically.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4" data-testid="agent-workflow-form">
        {/* URL */}
        <div>
          <label htmlFor="workflow-url" className="block text-sm font-medium text-gray-700 mb-1">
            Target URL <span className="text-red-500">*</span>
          </label>
          <input
            id="workflow-url"
            data-testid="url-input"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/login"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          />
        </div>

        {/* User instruction */}
        <div>
          <label htmlFor="workflow-instruction" className="block text-sm font-medium text-gray-700 mb-1">
            Instructions <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            id="workflow-instruction"
            data-testid="instruction-input"
            type="text"
            value={userInstruction}
            onChange={(e) => setUserInstruction(e.target.value)}
            placeholder="e.g. Test login flow with invalid credentials"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          />
        </div>

        {/* Crawl depth */}
        <div>
          <label htmlFor="workflow-depth" className="block text-sm font-medium text-gray-700 mb-1">
            Crawl depth
          </label>
          <select
            id="workflow-depth"
            data-testid="depth-select"
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value) as 1 | 2 | 3)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          >
            <option value={1}>1 — Current page only</option>
            <option value={2}>2 — Include linked pages</option>
            <option value={3}>3 — Deep crawl</option>
          </select>
        </div>

        {/* Error */}
        {submitError && (
          <p data-testid="submit-error" className="text-sm text-red-600">
            {submitError}
          </p>
        )}

        {/* Submit */}
        <Button
          type="submit"
          data-testid="generate-button"
          disabled={isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Starting…' : 'Generate Tests'}
        </Button>
      </form>
    </div>
  );
};
