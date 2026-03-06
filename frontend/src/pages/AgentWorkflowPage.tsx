/**
 * Agent Workflow Page
 *
 * Sprint 10 — Developer B
 *
 * Orchestrates the full agent workflow UI:
 *   1. Trigger  — user submits a URL to start a workflow
 *   2. Progress — live SSE/polling updates while the workflow runs
 *   3. Results  — rendered test cases when the workflow completes
 */

import { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import {
  AgentWorkflowTrigger,
  AgentProgressPipeline,
  AgentStatusMonitor,
  WorkflowResults,
  useWorkflowProgress,
} from '../features/agent-workflow';

export function AgentWorkflowPage() {
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  const {
    status,
    progress,
    error,
    agentProgress,
    currentAgent,
    totalProgress,
    isLoading,
    cancel,
  } = useWorkflowProgress(workflowId);

  const handleReset = () => {
    setWorkflowId(null);
  };

  const isComplete = status === 'completed';

  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Workflow</h1>
          <p className="mt-1 text-sm text-gray-500">
            Generate test cases automatically using the multi-agent pipeline.
          </p>
        </div>

        {/* Step 1 — Trigger (always visible so user can start a new run) */}
        {!workflowId && (
          <AgentWorkflowTrigger onWorkflowStarted={setWorkflowId} />
        )}

        {/* Step 2 — Progress (visible while a workflow is running or has just finished/failed) */}
        {workflowId && !isComplete && (
          <div className="space-y-4">
            <AgentProgressPipeline
              workflowStatus={status}
              progress={progress}
              error={error}
              onStop={cancel}
            />

            <AgentStatusMonitor
              workflowStatus={status}
              agentProgress={agentProgress}
              currentAgent={currentAgent}
              totalProgress={totalProgress}
              isLoading={isLoading}
              error={error}
            />
          </div>
        )}

        {/* Step 3 — Results (visible once the workflow completes successfully) */}
        {isComplete && workflowId && (
          <WorkflowResults workflowId={workflowId} onReset={handleReset} />
        )}

        {/* Allow starting over after failure/cancel */}
        {workflowId && (status === 'failed' || status === 'cancelled') && (
          <div className="flex justify-end">
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Start New Workflow
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}

export default AgentWorkflowPage;
