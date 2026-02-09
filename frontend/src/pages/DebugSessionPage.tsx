/**
 * Debug Session Page
 * 
 * Wrapper page component for the Interactive Debug Panel.
 * Handles routing parameters and provides navigation context.
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { InteractiveDebugPanel } from '../components/InteractiveDebugPanel';
import { Layout } from '../components/layout/Layout';

export const DebugSessionPage: React.FC = () => {
  const { executionId, targetStep, endStep, mode } = useParams<{
    executionId: string;
    targetStep: string;
    endStep?: string;
    mode: string;
  }>();
  const navigate = useNavigate();

  // Validate parameters
  if (!executionId || !targetStep || !mode) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <p className="text-red-600 font-semibold mb-2">Invalid Parameters</p>
            <p className="text-gray-600 text-sm mb-4">
              Missing required parameters: executionId, targetStep, or mode
            </p>
            <button
              onClick={() => navigate('/executions')}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm"
            >
              Go to Executions
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const executionIdNum = parseInt(executionId, 10);
  const targetStepNum = parseInt(targetStep, 10);
  const endStepNum = endStep ? parseInt(endStep, 10) : undefined;
  const debugMode = mode as 'auto' | 'manual';

  // Validate mode
  if (debugMode !== 'auto' && debugMode !== 'manual') {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <p className="text-red-600 font-semibold mb-2">Invalid Debug Mode</p>
            <p className="text-gray-600 text-sm mb-4">
              Mode must be 'auto' or 'manual', got: {mode}
            </p>
            <button
              onClick={() => navigate('/executions')}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm"
            >
              Go to Executions
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const handleClose = () => {
    navigate(`/executions/${executionId}`);
  };

  return (
    <Layout>
      {/* Breadcrumb Navigation */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/executions/${executionId}`)}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Execution #{executionId}
        </button>
      </div>

      {/* Debug Panel */}
      <InteractiveDebugPanel
        executionId={executionIdNum}
        targetStepNumber={targetStepNum}
        endStepNumber={endStepNum}
        mode={debugMode}
        onClose={handleClose}
      />
    </Layout>
  );
};

export default DebugSessionPage;
