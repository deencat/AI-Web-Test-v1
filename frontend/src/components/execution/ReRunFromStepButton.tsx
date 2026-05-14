/**
 * ReRunFromStepButton — Sprint 10.12 Feature B
 *
 * A secondary button that appears on each failed/error step row in
 * ExecutionProgressPage. Clicking it opens a confirmation dialog that
 * shows the source execution and step details, then calls
 * executionService.startExecution with resume params on confirm.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import executionService from '../../services/executionService';
import type { ExecutionResult } from '../../types/execution';

export interface ReRunFromStepButtonProps {
  /** Test case to re-run */
  testCaseId: number;
  /** Execution whose snapshot will be used as source */
  executionId: number;
  /** 1-based step number to resume from */
  stepNumber: number;
  /** Result of this step — button only renders on fail/error */
  stepResult: ExecutionResult;
  /** Execution config to pass through */
  baseUrl: string;
  browser?: string;
  environment?: string;
}

export function ReRunFromStepButton({
  testCaseId,
  executionId,
  stepNumber,
  stepResult,
  baseUrl,
  browser = 'chromium',
  environment = 'dev',
}: ReRunFromStepButtonProps) {
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Only show for failed/error steps
  if (stepResult !== 'fail' && stepResult !== 'error') {
    return null;
  }

  const handleConfirm = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await executionService.startExecution(testCaseId, {
        base_url: baseUrl,
        browser: browser as 'chromium' | 'firefox' | 'webkit',
        environment: environment as 'dev' | 'staging' | 'production',
        triggered_by: 'manual',
        resume_from_execution_id: executionId,
        start_from_step: stepNumber,
      });
      setDialogOpen(false);
      navigate(`/executions/${response.id}`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to start re-run');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setErrorMsg(null);
          setDialogOpen(true);
        }}
        className="mt-2 px-3 py-1 text-xs font-medium text-orange-700 bg-orange-50 border border-orange-200 rounded hover:bg-orange-100 focus:outline-none focus:ring-2 focus:ring-orange-400"
      >
        ↩ Re-run from here
      </button>

      {dialogOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Re-run from failed step"
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        >
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-3">Re-run from Failed Step</h2>

            <p className="text-sm text-gray-700 mb-4">
              This will create a new execution that restores the browser state recorded after{' '}
              <span className="font-semibold">
                step {stepNumber - 1}
              </span>{' '}
              of{' '}
              <span className="font-semibold">execution {executionId}</span> and then resumes
              running from{' '}
              <span className="font-semibold">step {stepNumber}</span>.
            </p>

            {errorMsg && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                {errorMsg}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                type="button"
                disabled={isLoading}
                onClick={() => setDialogOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isLoading}
                onClick={handleConfirm}
                className="px-4 py-2 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isLoading && (
                  <span className="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full" />
                )}
                Confirm re-run
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
