import { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { ManualInstructionsView } from './ManualInstructionsView';
import debugService from '../../services/debugService';
import type {
  DebugSessionStatusResponse,
  DebugSessionStatus,
} from '../../types/debug';

interface DebugSessionViewProps {
  sessionId: string;
  onClose: () => void;
}

interface ExecutionHistory {
  iteration: number;
  result: string;
  actual_result?: string;
  error_message?: string;
  screenshot_path?: string;
  duration_seconds: number;
  timestamp: string;
  note?: string;
}

export function DebugSessionView({ sessionId, onClose }: DebugSessionViewProps) {
  const [session, setSession] = useState<DebugSessionStatusResponse | null>(null);
  const [executionHistory, setExecutionHistory] = useState<ExecutionHistory[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [iterationNote, setIterationNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(false);
  const [manualInstructions, setManualInstructions] = useState<any[]>([]);

  // Fetch session status
  const fetchStatus = async () => {
    try {
      const data = await debugService.getSessionStatus(sessionId);
      setSession(data);
      setError(null);

      // Auto-fetch manual instructions if in manual mode and waiting for confirmation
      // Only show instructions during setup_in_progress, hide them once ready
      if (data.mode === 'manual' && data.status === 'setup_in_progress' && !showInstructions) {
        fetchManualInstructions();
      } else if (data.mode === 'manual' && data.status === 'ready' && showInstructions) {
        // Hide instructions once session is ready
        setShowInstructions(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch session status');
    }
  };

  // Fetch manual instructions
  const fetchManualInstructions = async () => {
    try {
      const data = await debugService.getManualInstructions(sessionId);
      setManualInstructions(data.instructions);
      setShowInstructions(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch instructions');
    }
  };

  // Confirm manual setup complete
  const handleConfirmSetup = async () => {
    setIsConfirming(true);
    try {
      await debugService.confirmSetupComplete(sessionId);
      await fetchStatus();
      setShowInstructions(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to confirm setup');
    } finally {
      setIsConfirming(false);
    }
  };

  // Execute target step
  const handleExecuteStep = async () => {
    setIsExecuting(true);
    setError(null);

    try {
      const result = await debugService.executeStep({
        session_id: sessionId,
        iteration_note: iterationNote || undefined,
      });

      // Add to history
      const historyItem: ExecutionHistory = {
        iteration: result.iteration_number,
        result: result.result,
        actual_result: result.actual_result,
        error_message: result.error_message,
        screenshot_path: result.screenshot_path,
        duration_seconds: result.duration_seconds,
        timestamp: new Date().toISOString(),
        note: iterationNote || undefined,
      };
      setExecutionHistory((prev) => [historyItem, ...prev]);

      // Clear note and refresh status
      setIterationNote('');
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute step');
    } finally {
      setIsExecuting(false);
    }
  };

  // Stop session
  const handleStop = async () => {
    if (!confirm('Are you sure you want to stop this debug session?')) {
      return;
    }

    setIsStopping(true);
    try {
      await debugService.stopSession(sessionId);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop session');
      setIsStopping(false);
    }
  };

  // Poll status every 5 seconds
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!session) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center gap-3">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
          <span className="text-lg text-gray-600">Loading debug session...</span>
        </div>
      </Card>
    );
  }

  const isReady = session.status === 'ready' || session.status === 'executing';
  const isSetupInProgress = session.status === 'setup_in_progress';
  // For manual mode: allow execution once browser is opened (status = ready)
  // For auto mode: allow execution once status = ready
  // Max iterations default to 50 (reasonable limit for debugging)
  const maxIterations = 50;
  const canExecute = isReady && !isExecuting && session.iterations_count < maxIterations;

  // Debug logging
  console.log('Debug Session State:', {
    status: session.status,
    isReady,
    isExecuting,
    iterations_count: session.iterations_count,
    max_iterations: maxIterations,
    iterationCheck: session.iterations_count < maxIterations,
    canExecute,
  });

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                🐛 Debug Session
                <StatusBadge status={session.status} />
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Session ID: {session.session_id.slice(0, 8)}...
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleStop}
              disabled={isStopping}
            >
              {isStopping ? 'Stopping...' : 'Stop Session'}
            </Button>
          </div>

          {/* Session Info Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-600">Mode</div>
              <div className="text-lg font-semibold text-gray-900 capitalize">
                {session.mode === 'auto' ? '🤖 Auto' : '👤 Manual'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Target Step</div>
              <div className="text-lg font-semibold text-gray-900">
                Step {session.target_step_number}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Iterations</div>
              <div className="text-lg font-semibold text-gray-900">
                {session.iterations_count} / {maxIterations}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Tokens Used</div>
              <div className="text-lg font-semibold text-gray-900">
                {session.tokens_used}
              </div>
            </div>
          </div>

          {/* Token Breakdown */}
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-700 space-y-1">
              <div className="flex justify-between">
                <span>Total iterations:</span>
                <span className="font-medium">{session.iterations_count}</span>
              </div>
              <div className="flex justify-between">
                <span>Setup completed:</span>
                <span className="font-medium">{session.setup_completed ? '✅ Yes' : '❌ No'}</span>
              </div>
              <div className="flex justify-between border-t border-gray-300 pt-1 mt-1">
                <span className="font-semibold">Total tokens:</span>
                <span className="font-semibold">{session.tokens_used}</span>
              </div>
            </div>
          </div>

          {/* Browser URL */}
          {session.devtools_url && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-sm">
                <span className="font-medium text-blue-900">Browser DevTools:</span>
                <a
                  href={session.devtools_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-blue-600 hover:text-blue-700 underline"
                >
                  {session.devtools_url}
                </a>
              </div>
            </div>
          )}

          {/* Session State Info (for debugging) */}
          <div className="mt-4 p-3 bg-gray-100 border border-gray-300 rounded-lg">
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex justify-between">
                <span>Session Status:</span>
                <span className="font-medium">{session.status}</span>
              </div>
              <div className="flex justify-between">
                <span>Is Ready:</span>
                <span className="font-medium">{isReady ? '✅ Yes' : '❌ No'}</span>
              </div>
              <div className="flex justify-between">
                <span>Is Executing:</span>
                <span className="font-medium">{isExecuting ? '⏳ Yes' : '❌ No'}</span>
              </div>
              <div className="flex justify-between">
                <span>Iterations Count:</span>
                <span className="font-medium">{session.iterations_count}</span>
              </div>
              <div className="flex justify-between">
                <span>Max Iterations:</span>
                <span className="font-medium">{maxIterations}</span>
              </div>
              <div className="flex justify-between">
                <span>Iteration Check:</span>
                <span className="font-medium">
                  {session.iterations_count < maxIterations ? '✅ Yes' : '❌ No'}
                </span>
              </div>
              <div className="flex justify-between font-bold border-t border-gray-400 pt-1 mt-1">
                <span>Can Execute:</span>
                <span className="font-medium">{canExecute ? '✅ Yes' : '❌ No'}</span>
              </div>
              <div className="flex justify-between">
                <span>Instructions Visible:</span>
                <span className="font-medium">{showInstructions ? '✅ Yes' : '❌ No'}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Manual Instructions */}
      {showInstructions && manualInstructions.length > 0 && (
        <ManualInstructionsView
          instructions={manualInstructions}
          browserUrl={session.devtools_url}
          onConfirmComplete={handleConfirmSetup}
          isConfirming={isConfirming}
        />
      )}

      {/* Manual Mode - Waiting for Confirmation */}
      {isSetupInProgress && session.mode === 'manual' && !showInstructions && (
        <Card className="border-yellow-200 bg-yellow-50">
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="animate-spin h-8 w-8 border-4 border-yellow-500 border-t-transparent rounded-full" />
              <div>
                <h3 className="text-lg font-semibold text-yellow-900">
                  Loading manual setup instructions...
                </h3>
                <p className="text-sm text-yellow-700">
                  Please wait while we prepare the step-by-step guide.
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Setup in Progress (Auto Mode) */}
      {isSetupInProgress && session.mode === 'auto' && (
        <Card className="border-blue-200 bg-blue-50">
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
              <div>
                <h3 className="text-lg font-semibold text-blue-900">
                  Auto-setup in progress...
                </h3>
                <p className="text-sm text-blue-700">
                  AI is executing prerequisite steps 1-{session.target_step_number - 1}. This may
                  take a few minutes.
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <div className="p-4">
            <div className="flex items-start gap-2">
              <span className="text-xl">⚠️</span>
              <div>
                <h3 className="font-semibold text-red-900">Error</h3>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Execute Step Card */}
      {isReady && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Execute Target Step {session.target_step_number}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Iteration Note (Optional)
                </label>
                <textarea
                  value={iterationNote}
                  onChange={(e) => setIterationNote(e.target.value)}
                  placeholder="Describe what you're trying or what changed..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  disabled={isExecuting || !canExecute}
                />
              </div>

              <Button
                variant="primary"
                size="lg"
                onClick={handleExecuteStep}
                disabled={!canExecute}
                className="w-full"
              >
                {isExecuting ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Executing Step {session.target_step_number}...
                  </>
                ) : (
                  <>🚀 Execute Step {session.target_step_number}</>
                )}
              </Button>

              {session.iterations_count >= maxIterations && (
                <div className="text-sm text-orange-600 bg-orange-50 p-3 rounded-lg">
                  ⚠️ Maximum iterations reached ({maxIterations}). Stop the session if you're done.
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Ready to Execute Message for Manual Mode */}
      {isReady && session.mode === 'manual' && session.iterations_count === 0 && (
        <Card className="border-green-200 bg-green-50">
          <div className="p-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl">✅</span>
              <div>
                <h3 className="text-lg font-semibold text-green-900 mb-2">
                  Browser Ready - Manual Setup Complete
                </h3>
                <p className="text-sm text-green-700">
                  The persistent browser is now open and ready. Navigate to your target page manually, 
                  then use the execute button below to test step {session.target_step_number}.
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Execution History */}
      {executionHistory.length > 0 && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Execution History</h3>
            <div className="space-y-4">
              {executionHistory.map((item, index) => (
                <ExecutionHistoryItem key={index} item={item} />
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

// Helper Components
function StatusBadge({ status }: { status: DebugSessionStatus }) {
  const getStatusColor = () => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-700';
      case 'executing':
        return 'bg-blue-100 text-blue-700';
      case 'setup_in_progress':
        return 'bg-yellow-100 text-yellow-700';
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      case 'cancelled':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase ${getStatusColor()}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

function ExecutionHistoryItem({ item }: { item: ExecutionHistory }) {
  const getResultColor = () => {
    switch (item.result) {
      case 'pass':
        return 'border-green-200 bg-green-50';
      case 'fail':
        return 'border-red-200 bg-red-50';
      case 'error':
        return 'border-orange-200 bg-orange-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getResultIcon = () => {
    switch (item.result) {
      case 'pass':
        return '✅';
      case 'fail':
        return '❌';
      case 'error':
        return '⚠️';
      default:
        return '○';
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getResultColor()}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{getResultIcon()}</span>
          <span className="font-semibold text-gray-900">Iteration {item.iteration}</span>
          <span className="text-sm text-gray-600">
            {new Date(item.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <span className="text-sm text-gray-600">{item.duration_seconds.toFixed(2)}s</span>
      </div>

      {item.note && (
        <div className="mb-2 text-sm text-gray-700 italic">
          <span className="font-medium">Note:</span> {item.note}
        </div>
      )}

      {item.actual_result && (
        <div className="text-sm text-gray-700 mb-2">
          <span className="font-medium">Result:</span> {item.actual_result}
        </div>
      )}

      {item.error_message && (
        <div className="text-sm text-red-700 bg-red-100 p-2 rounded">
          <span className="font-medium">Error:</span> {item.error_message}
        </div>
      )}

      {item.screenshot_path && (
        <div className="mt-2">
          <a
            href={item.screenshot_path}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-700 underline"
          >
            📸 View Screenshot
          </a>
        </div>
      )}
    </div>
  );
}
