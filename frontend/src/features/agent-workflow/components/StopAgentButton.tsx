/**
 * StopAgentButton — Sprint 10 (10B.12)
 *
 * Renders a "⏹ Stop Agent" button that calls DELETE /workflows/{id}
 * via the `onStop` callback.  The button is disabled when the workflow is
 * in a terminal state (completed / failed / cancelled) or when status is null.
 *
 * After clicking, an inline "Stopping workflow…" confirmation is shown.
 */
import React, { useState } from 'react';
import type { WorkflowStatus } from '../../../types/agentWorkflow.types';

const TERMINAL_STATUSES: WorkflowStatus[] = ['completed', 'failed', 'cancelled'];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface StopAgentButtonProps {
  /** Current workflow lifecycle status; null means no active workflow */
  workflowStatus: WorkflowStatus | null;
  /** Called when the user requests a stop (calls DELETE /workflows/{id}) */
  onStop: () => void;
  /** Extra disabled guard — e.g. while a status request is in-flight */
  isLoading?: boolean;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const StopAgentButton: React.FC<StopAgentButtonProps> = ({
  workflowStatus,
  onStop,
  isLoading = false,
  className = '',
}) => {
  const [showConfirmation, setShowConfirmation] = useState(false);

  const isDisabled =
    isLoading ||
    workflowStatus === null ||
    TERMINAL_STATUSES.includes(workflowStatus as WorkflowStatus);

  const handleClick = () => {
    if (isDisabled) return;
    setShowConfirmation(true);
    onStop();
  };

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <button
        type="button"
        data-testid="stop-agent-button"
        onClick={handleClick}
        disabled={isDisabled}
        aria-label="Stop agent workflow"
        className={[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
          'transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1',
          isDisabled
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed focus:ring-gray-200'
            : 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 hover:border-red-300 focus:ring-red-300',
        ].join(' ')}
      >
        <span aria-hidden="true">⏹</span>
        Stop Agent
      </button>

      {showConfirmation && (
        <span
          data-testid="stop-confirmation"
          className="text-xs text-orange-600 font-medium"
          role="status"
          aria-live="polite"
        >
          Stopping workflow…
        </span>
      )}
    </div>
  );
};
