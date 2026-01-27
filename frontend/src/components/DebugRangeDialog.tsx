/**
 * Debug Range Dialog - Phase 4 Enhancement
 * 
 * Allows users to select a step range for debugging with options for:
 * - Start and end step numbers
 * - Auto-navigate vs Manual navigation modes
 * - Skip prerequisites flag
 * - Validation and preview
 */

import React, { useState, useEffect } from 'react';
import { X, Play, Navigation, AlertCircle, Info } from 'lucide-react';
import type { TestExecutionListItem } from '../types/execution';

interface DebugRangeDialogProps {
  open: boolean;
  execution: TestExecutionListItem;
  onConfirm: (startStep: number, endStep: number | null, skipPrerequisites: boolean) => void;
  onCancel: () => void;
}

type NavigationMode = 'auto' | 'manual';

export const DebugRangeDialog: React.FC<DebugRangeDialogProps> = ({
  open,
  execution,
  onConfirm,
  onCancel,
}) => {
  const [startStep, setStartStep] = useState<string>('1');
  const [endStep, setEndStep] = useState<string>('');
  const [navigationMode, setNavigationMode] = useState<NavigationMode>('auto');
  const [errors, setErrors] = useState<{ start?: string; end?: string }>({});

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setStartStep('1');
      setEndStep('');
      setNavigationMode('auto');
      setErrors({});
    }
  }, [open]);

  // Validation
  const validate = (): boolean => {
    const newErrors: { start?: string; end?: string } = {};
    
    const startNum = parseInt(startStep);
    if (isNaN(startNum) || startNum < 1) {
      newErrors.start = 'Start step must be >= 1';
    }
    if (startNum > execution.total_steps) {
      newErrors.start = `Start step must be <= ${execution.total_steps}`;
    }

    if (endStep) {
      const endNum = parseInt(endStep);
      if (isNaN(endNum) || endNum < 1) {
        newErrors.end = 'End step must be >= 1';
      } else if (endNum > execution.total_steps) {
        newErrors.end = `End step must be <= ${execution.total_steps}`;
      } else if (endNum < startNum) {
        newErrors.end = 'End step must be >= start step';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleConfirm = () => {
    if (!validate()) return;

    const startNum = parseInt(startStep);
    const endNum = endStep ? parseInt(endStep) : null;
    const skipPrereqs = navigationMode === 'manual';

    onConfirm(startNum, endNum, skipPrereqs);
  };

  const getPreview = (): string => {
    const startNum = parseInt(startStep);
    const endNum = endStep ? parseInt(endStep) : null;

    if (isNaN(startNum)) return '';

    let preview = '';
    
    if (navigationMode === 'auto') {
      const prereqCount = startNum - 1;
      if (prereqCount > 0) {
        preview += `1. AI will execute steps 1-${prereqCount} (setup)\n`;
      }
      preview += `2. Debug ${endNum ? `steps ${startNum}-${endNum}` : `step ${startNum}`}\n`;
      preview += `3. Est. time: ${prereqCount * 6 + 10} seconds`;
    } else {
      preview += `1. Manual navigation (skip prerequisites)\n`;
      preview += `2. Debug ${endNum ? `steps ${startNum}-${endNum}` : `step ${startNum}`} immediately\n`;
      preview += `3. Est. time: 5 seconds`;
    }

    return preview;
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg">
              <Play className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Debug Step Range</h2>
              <p className="text-sm text-gray-500">
                Execution #{execution.id} ({execution.total_steps} steps total)
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-6">
          {/* Step Range Inputs */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Step
              </label>
              <input
                type="number"
                min="1"
                max={execution.total_steps}
                value={startStep}
                onChange={(e) => setStartStep(e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                  errors.start
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                placeholder="1"
              />
              {errors.start && (
                <p className="mt-1 text-sm text-red-600">{errors.start}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Step (optional)
              </label>
              <input
                type="number"
                min="1"
                max={execution.total_steps}
                value={endStep}
                onChange={(e) => setEndStep(e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                  errors.end
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                placeholder={`${execution.total_steps}`}
              />
              {errors.end && (
                <p className="mt-1 text-sm text-red-600">{errors.end}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Leave empty to debug until the end
              </p>
            </div>
          </div>

          {/* Navigation Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Navigation Mode
            </label>
            <div className="space-y-3">
              <label
                className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  navigationMode === 'auto'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="navigationMode"
                  value="auto"
                  checked={navigationMode === 'auto'}
                  onChange={() => setNavigationMode('auto')}
                  className="mt-1"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center gap-2">
                    <Play className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-gray-900">Auto Navigate</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    AI will automatically execute prerequisite steps (1 to {parseInt(startStep) - 1 || 0})
                    to reach the target state before debugging starts.
                  </p>
                  <div className="mt-2 text-xs text-gray-500">
                    ⚡ Uses ~{(parseInt(startStep) - 1) * 100 || 0} tokens • {(parseInt(startStep) - 1) * 6 || 0}s setup time
                  </div>
                </div>
              </label>

              <label
                className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  navigationMode === 'manual'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="navigationMode"
                  value="manual"
                  checked={navigationMode === 'manual'}
                  onChange={() => setNavigationMode('manual')}
                  className="mt-1"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center gap-2">
                    <Navigation className="w-4 h-4 text-purple-600" />
                    <span className="font-medium text-gray-900">Manual Navigation</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    You've already navigated to the desired state manually.
                    Start debugging immediately without executing prerequisites.
                  </p>
                  <div className="mt-2 text-xs text-gray-500">
                    ⚡ Uses 0 tokens • Instant start
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-start gap-2 mb-2">
              <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900">What will happen:</h4>
                <pre className="mt-2 text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {getPreview() || 'Enter start step to see preview'}
                </pre>
              </div>
            </div>
          </div>

          {/* Warning for manual mode */}
          {navigationMode === 'manual' && parseInt(startStep) > 1 && (
            <div className="flex items-start gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <strong>Manual Navigation Mode:</strong> Make sure you've already navigated
                to the correct state in your browser before starting. The debugger will
                assume you're at step {parseInt(startStep) - 1 || 0} and continue from step {startStep}.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Start Debugging
          </button>
        </div>
      </div>
    </div>
  );
};
