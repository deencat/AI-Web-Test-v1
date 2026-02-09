/**
 * Interactive Debug Panel - Phase 3 Enhancement
 * 
 * Provides a comprehensive visual interface for multi-step debugging with:
 * - Visual step list with status indicators
 * - Play/Pause/Next/Stop controls
 * - Live execution logs
 * - Progress tracking
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  Square,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';
import debugService from '../services/debugService';
import executionService from '../services/executionService';
import type {
  DebugSessionStartRequest,
  DebugSessionStatusResponse,
  DebugNextStepResponse,
} from '../types/debug';

interface InteractiveDebugPanelProps {
  executionId: number;
  targetStepNumber: number;
  endStepNumber?: number;
  mode: 'auto' | 'manual';
  onClose?: () => void;
}

interface DebugStep {
  stepNumber: number;
  description: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  duration?: number;
  screenshot?: string;
  error?: string;
}

interface ExecutionLogEntry {
  timestamp: Date;
  level: 'info' | 'success' | 'error' | 'debug';
  message: string;
}

export const InteractiveDebugPanel: React.FC<InteractiveDebugPanelProps> = ({
  executionId,
  targetStepNumber,
  endStepNumber,
  mode,
  onClose,
}) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [steps, setSteps] = useState<DebugStep[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [logs, setLogs] = useState<ExecutionLogEntry[]>([]);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const autoStartTriggered = React.useRef(false);

  // Add log entry
  const addLog = useCallback((level: ExecutionLogEntry['level'], message: string) => {
    setLogs(prev => [...prev, { timestamp: new Date(), level, message }]);
  }, []);

  // Initialize debug session
  useEffect(() => {
    console.log('[DEBUG] InteractiveDebugPanel mounted/updated');
    let isMounted = true; // Prevent race conditions

    const initializeSession = async () => {
      try {
        console.log('[DEBUG] initializeSession starting...');
        addLog('info', `Starting debug session for execution ${executionId}, step ${targetStepNumber}${endStepNumber ? ` to ${endStepNumber}` : ''}...`);
        
        const request: DebugSessionStartRequest = {
          execution_id: executionId,
          target_step_number: targetStepNumber,
          end_step_number: endStepNumber || null,
          mode,
          skip_prerequisites: mode === 'manual',
        };

        console.log('[DEBUG] Calling debugService.startSession with:', request);
        const response = await debugService.startSession(request);
        
        if (!isMounted) {
          console.log('[DEBUG] Component unmounted, aborting session initialization');
          return;
        }
        
        console.log('[DEBUG] Session created:', response.session_id);
        setSessionId(response.session_id);
        
        addLog('success', `Debug session ${response.session_id} created successfully`);
        addLog('info', response.message);

        // Wait for setup to complete if auto mode
        if (mode === 'auto' && !request.skip_prerequisites) {
          addLog('info', 'Waiting for prerequisite steps to complete...');
          await pollSessionStatus(response.session_id);
          addLog('info', 'Prerequisites complete. Auto mode will start execution automatically...');
        } else {
          // Manual mode or skip_prerequisites: Load steps immediately
          addLog('info', 'Loading test steps...');
          await initializeSteps({ status: 'ready' } as DebugSessionStatusResponse);
          addLog('success', 'Session is ready for debugging');
        }

        setIsInitializing(false);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        addLog('error', `Failed to start session: ${errorMessage}`);
        setError(errorMessage);
        setIsInitializing(false);
      }
    };

    initializeSession();
    
    return () => {
      console.log('[DEBUG] InteractiveDebugPanel unmounting, setting isMounted=false');
      isMounted = false;
    };
  }, [executionId, targetStepNumber, endStepNumber, mode, addLog]);

  // Auto-start execution in Auto mode after steps are loaded
  React.useEffect(() => {
    if (
      mode === 'auto' && 
      !isInitializing && 
      steps.length > 0 && 
      sessionId && 
      !autoStartTriggered.current &&
      !isPlaying &&
      currentStepIndex === 0
    ) {
      console.log('[DEBUG] ✅ Auto-starting execution NOW!');
      autoStartTriggered.current = true; // Prevent multiple triggers
      addLog('info', '🚀 Auto-play starting...');
      
      // Use setTimeout to ensure state updates have propagated
      setTimeout(() => {
        setIsPlaying(true);
        setIsPaused(false);
        // The executeNextStep will be called by the play button logic
        setTimeout(() => {
          executeNextStep();
        }, 100);
      }, 500);
    }
  }, [mode, isInitializing, steps.length, sessionId, isPlaying, currentStepIndex, addLog]);

  // Poll session status until ready
  const pollSessionStatus = async (sid: string, maxAttempts = 30) => {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const status = await debugService.getSessionStatus(sid);

        if (status.status === 'ready') {
          addLog('success', 'Session is ready for debugging');
          // Initialize steps based on total count
          initializeSteps(status);
          return;
        } else if (status.status === 'failed') {
          throw new Error(status.error_message || 'Session setup failed');
        }

        // Wait 2 seconds before next poll
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (err) {
        throw err;
      }
    }
    throw new Error('Session setup timed out');
  };

  // Initialize steps array from actual test execution
  const initializeSteps = async (_status: DebugSessionStatusResponse) => {
    console.log('[DEBUG] initializeSteps called');
    try {
      // Fetch the actual test execution to get real steps
      const executionDetail = await executionService.getExecutionDetail(executionId);
      console.log('[DEBUG] Execution detail:', executionDetail);
      
      if (executionDetail.steps && Array.isArray(executionDetail.steps)) {
        const stepsList: DebugStep[] = executionDetail.steps.map((step) => ({
          stepNumber: step.step_number,
          description: step.step_description,
          status: step.step_number < targetStepNumber ? 'success' : 'pending',
        }));
        
        // Filter to range if endStepNumber is provided
        const filteredSteps = endStepNumber 
          ? stepsList.filter(s => s.stepNumber >= targetStepNumber && s.stepNumber <= endStepNumber)
          : stepsList.filter(s => s.stepNumber >= targetStepNumber);
        
        console.log('[DEBUG] Filtered steps:', filteredSteps.length, 'steps');
        setSteps(filteredSteps);
        setCurrentStepIndex(0); // Start at first step in the range
        
        addLog('info', `Loaded ${filteredSteps.length} steps ${endStepNumber ? `(${targetStepNumber}-${endStepNumber})` : `(${targetStepNumber}+)`}`);
      } else {
        // Fallback if steps not available
        const mockSteps: DebugStep[] = Array.from({ length: 5 }, (_, i) => ({
          stepNumber: targetStepNumber + i,
          description: `Step ${targetStepNumber + i}`,
          status: 'pending',
        }));
        setSteps(mockSteps);
        setCurrentStepIndex(0);
        addLog('info', 'Could not load actual steps, using placeholder steps');
      }
    } catch (err) {
      addLog('error', `Failed to load steps: ${err instanceof Error ? err.message : 'Unknown error'}`);
      // Fallback to mock steps
      const mockSteps: DebugStep[] = Array.from({ length: 5 }, (_, i) => ({
        stepNumber: targetStepNumber + i,
        description: `Step ${targetStepNumber + i}`,
        status: 'pending',
      }));
      setSteps(mockSteps);
      setCurrentStepIndex(0);
    }
  };

  // Execute next step
  const executeNextStep = async () => {
    if (!sessionId) return;

    try {
      const currentStep = steps[currentStepIndex];
      if (!currentStep) {
        addLog('info', 'No more steps to execute');
        setIsPlaying(false);
        return;
      }

      // Update step status to running
      setSteps(prev => 
        prev.map((step, idx) => 
          idx === currentStepIndex ? { ...step, status: 'running' } : step
        )
      );

      addLog('info', `Executing step ${currentStep.stepNumber}: ${currentStep.description}...`);

      const result: DebugNextStepResponse = await debugService.executeNextStep(sessionId);

      // Update step with result
      setSteps(prev =>
        prev.map((step, idx) =>
          idx === currentStepIndex
            ? {
                ...step,
                status: result.success ? 'success' : 'failed',
                duration: result.duration_seconds,
                screenshot: result.screenshot_path,
                error: result.error_message,
                description: result.step_description,
              }
            : step
        )
      );

      if (result.success) {
        addLog('success', `Step ${result.step_number} completed in ${result.duration_seconds.toFixed(2)}s`);
        if (result.next_step_preview) {
          addLog('debug', `Next: ${result.next_step_preview}`);
        }
      } else {
        addLog('error', `Step ${result.step_number} failed: ${result.error_message}`);
        setIsPlaying(false);
        setIsPaused(true);
      }

      // Move to next step
      if (result.has_more_steps && !result.range_complete) {
        setCurrentStepIndex(prev => prev + 1);
        
        // Continue playing ONLY if in auto-play mode (not single-step)
        if (isPlaying && !isPaused) {
          setTimeout(() => executeNextStep(), 500);
        } else {
          // Single-step mode: Stop after one step
          addLog('info', 'Step completed. Click Next Step to continue.');
        }
      } else {
        if (result.range_complete) {
          addLog('success', `Debug range completed! Steps ${targetStepNumber} to ${result.end_step_number || result.total_steps}`);
        } else {
          addLog('success', `All steps completed! Total: ${result.total_steps}`);
        }
        setIsPlaying(false);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      addLog('error', `Execution failed: ${errorMessage}`);
      setSteps(prev =>
        prev.map((step, idx) =>
          idx === currentStepIndex ? { ...step, status: 'failed', error: errorMessage } : step
        )
      );
      setIsPlaying(false);
      setIsPaused(true);
    }
  };

  // Control handlers
  const handlePlay = () => {
    setIsPlaying(true);
    setIsPaused(false);
    executeNextStep();
  };

  const handlePause = () => {
    setIsPlaying(false);
    setIsPaused(true);
    addLog('info', 'Execution paused');
  };

  const handleNext = () => {
    // Single-step mode: Ensure isPlaying is false so it doesn't auto-continue
    setIsPlaying(false);
    setIsPaused(false);
    executeNextStep();
  };

  const handleStop = async () => {
    if (!sessionId) return;
    
    try {
      addLog('info', 'Stopping debug session...');
      await debugService.stopSession(sessionId);
      addLog('success', 'Debug session stopped successfully');
      setIsPlaying(false);
      
      if (onClose) {
        onClose();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      addLog('error', `Failed to stop session: ${errorMessage}`);
    }
  };

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Clock className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Initializing debug session...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-800 font-semibold mb-2">Failed to Start Debug Session</p>
          <p className="text-gray-600 text-sm">{error}</p>
          {onClose && (
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm"
            >
              Close
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="interactive-debug-panel bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Interactive Debug Session</h2>
            <p className="text-sm text-blue-100 mt-1">
              Session: {sessionId?.substring(0, 8)}... | Mode: {mode.toUpperCase()} | Execution: #{executionId}
            </p>
          </div>
          <button
            onClick={handleStop}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <Square className="w-4 h-4" />
            Stop Session
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
        {/* Left: Step List */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 rounded-lg p-4 h-[600px] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              Test Steps
              <span className="text-sm font-normal text-gray-500">
                ({currentStepIndex + 1} / {steps.length})
              </span>
            </h3>
            
            <div className="space-y-2">
              {steps.map((step, idx) => (
                <div
                  key={step.stepNumber}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    idx === currentStepIndex
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Status Icon */}
                    {step.status === 'success' && (
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                    )}
                    {step.status === 'failed' && (
                      <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    )}
                    {step.status === 'running' && (
                      <Clock className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5 animate-spin" />
                    )}
                    {step.status === 'pending' && (
                      <div className="w-5 h-5 rounded-full border-2 border-gray-300 flex-shrink-0 mt-0.5" />
                    )}

                    {/* Step Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">
                          Step {step.stepNumber}
                        </span>
                        {step.duration && (
                          <span className="text-xs text-gray-500">
                            {step.duration.toFixed(2)}s
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 truncate" title={step.description}>
                        {step.description}
                      </p>
                      {step.error && (
                        <p className="text-xs text-red-600 mt-1 line-clamp-2">
                          {step.error}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Controls & Logs */}
        <div className="lg:col-span-2 space-y-6">
          {/* Debug Controls */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Controls</h3>
            
            <div className="flex items-center gap-4">
              {!isPlaying ? (
                <button
                  onClick={handlePlay}
                  disabled={currentStepIndex >= steps.length || steps.length === 0}
                  className="px-6 py-3 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                  title={steps.length === 0 ? 'Waiting for steps to load...' : ''}
                >
                  <Play className="w-5 h-5" />
                  {isPaused ? 'Resume' : 'Play'}
                </button>
              ) : (
                <button
                  onClick={handlePause}
                  className="px-6 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Pause className="w-5 h-5" />
                  Pause
                </button>
              )}

              <button
                onClick={handleNext}
                disabled={isPlaying || currentStepIndex >= steps.length || steps.length === 0}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                title={steps.length === 0 ? 'Waiting for steps to load...' : ''}
              >
                <SkipForward className="w-5 h-5" />
                Next Step
              </button>

              <div className="ml-auto text-sm text-gray-600">
                {isPlaying && <span className="text-green-600 font-medium">● Executing...</span>}
                {isPaused && <span className="text-yellow-600 font-medium">⏸ Paused</span>}
                {!isPlaying && !isPaused && (
                  <span className="text-gray-500">Ready</span>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{Math.round((currentStepIndex / steps.length) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(currentStepIndex / steps.length) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Execution Logs */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Execution Log</h3>
            
            <div className="bg-gray-900 rounded-lg p-4 h-[360px] overflow-y-auto font-mono text-sm">
              {logs.length === 0 ? (
                <p className="text-gray-500">No logs yet...</p>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, idx) => (
                    <div key={idx} className="flex gap-3">
                      <span className="text-gray-500 flex-shrink-0">
                        {log.timestamp.toLocaleTimeString()}
                      </span>
                      <span
                        className={`flex-1 ${
                          log.level === 'error'
                            ? 'text-red-400'
                            : log.level === 'success'
                            ? 'text-green-400'
                            : log.level === 'debug'
                            ? 'text-blue-400'
                            : 'text-gray-300'
                        }`}
                      >
                        [{log.level.toUpperCase()}] {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveDebugPanel;
