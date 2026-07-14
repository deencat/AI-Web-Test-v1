/**
 * StopExecutionButton — cooperative cancel control for test executions.
 *
 * Mirrors StopAgentButton UX: red outline button, inline "Stopping execution…"
 * confirmation, disabled for terminal statuses.
 */
import React, { useState } from 'react';
import type { ExecutionStatus } from '../../types/execution';

const TERMINAL_STATUSES: ExecutionStatus[] = ['completed', 'failed', 'cancelled'];

export interface StopExecutionButtonProps {
  executionStatus: ExecutionStatus | null;
  onStop: () => void;
  isLoading?: boolean;
  className?: string;
}

export const StopExecutionButton: React.FC<StopExecutionButtonProps> = ({
  executionStatus,
  onStop,
  isLoading = false,
  className = '',
}) => {
  const [showConfirmation, setShowConfirmation] = useState(false);

  const isDisabled =
    isLoading ||
    executionStatus === null ||
    TERMINAL_STATUSES.includes(executionStatus as ExecutionStatus);

  const handleClick = () => {
    if (isDisabled) return;
    setShowConfirmation(true);
    onStop();
  };

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <button
        type="button"
        data-testid="stop-execution-button"
        onClick={handleClick}
        disabled={isDisabled}
        aria-label="Stop test execution"
        className={[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
          'transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1',
          isDisabled
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed focus:ring-gray-200'
            : 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 hover:border-red-300 focus:ring-red-300',
        ].join(' ')}
      >
        <span aria-hidden="true">⏹</span>
        Stop Execution
      </button>

      {showConfirmation && (
        <span
          data-testid="stop-execution-confirmation"
          className="text-xs text-orange-600 font-medium"
          role="status"
          aria-live="polite"
        >
          Stopping execution…
        </span>
      )}
    </div>
  );
};
