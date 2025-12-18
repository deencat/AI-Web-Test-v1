import { useState } from 'react';
import { Button } from '../common/Button';
import type { DebugMode } from '../../types/debug';

interface DebugModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStart: (mode: DebugMode, targetStepNumber: number) => void;
  totalSteps: number;
  executionId: number;
}

export function DebugModeModal({
  isOpen,
  onClose,
  onStart,
  totalSteps,
  executionId,
}: DebugModeModalProps) {
  const [selectedMode, setSelectedMode] = useState<DebugMode>('manual');
  const [targetStep, setTargetStep] = useState<number>(1);
  const [isStarting, setIsStarting] = useState(false);

  if (!isOpen) return null;

  const handleStart = async () => {
    setIsStarting(true);
    try {
      await onStart(selectedMode, targetStep);
    } finally {
      setIsStarting(false);
    }
  };

  const estimatedSetupCost = selectedMode === 'auto' ? 600 : 0;
  const executionCost = 100;
  const totalCost = estimatedSetupCost + executionCost;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              🐛 Start Debug Session
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              disabled={isStarting}
            >
              ×
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Debug a specific test step with persistent browser session
          </p>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-6">
          {/* Target Step Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Target Step to Debug
            </label>
            <select
              value={targetStep}
              onChange={(e) => setTargetStep(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isStarting}
            >
              {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
                <option key={step} value={step}>
                  Step {step}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              The step you want to debug and iterate on
            </p>
          </div>

          {/* Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Choose Setup Mode
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Manual Mode */}
              <button
                onClick={() => setSelectedMode('manual')}
                disabled={isStarting}
                className={`p-4 border-2 rounded-lg text-left transition-all ${
                  selectedMode === 'manual'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">👤 Manual Setup</h3>
                  <span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-700 rounded">
                    FREE
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  You manually execute prerequisite steps 1 through {targetStep - 1} following
                  provided instructions
                </p>
                <div className="space-y-1 text-xs text-gray-700">
                  <div className="flex justify-between">
                    <span>Setup Cost:</span>
                    <span className="font-semibold text-green-600">0 tokens</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Per Iteration:</span>
                    <span className="font-semibold">{executionCost} tokens</span>
                  </div>
                  <div className="flex justify-between border-t border-gray-200 pt-1 mt-1">
                    <span>Estimated Total:</span>
                    <span className="font-semibold">{executionCost} tokens</span>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  ✓ 85% token cost reduction
                  <br />✓ Full control over setup
                  <br />✓ Faster to get started
                </div>
              </button>

              {/* Auto Mode */}
              <button
                onClick={() => setSelectedMode('auto')}
                disabled={isStarting}
                className={`p-4 border-2 rounded-lg text-left transition-all ${
                  selectedMode === 'auto'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">🤖 Auto Setup</h3>
                  <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-700 rounded">
                    AI-POWERED
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  AI automatically executes prerequisite steps 1 through {targetStep - 1} for you
                </p>
                <div className="space-y-1 text-xs text-gray-700">
                  <div className="flex justify-between">
                    <span>Setup Cost:</span>
                    <span className="font-semibold">{estimatedSetupCost} tokens</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Per Iteration:</span>
                    <span className="font-semibold">{executionCost} tokens</span>
                  </div>
                  <div className="flex justify-between border-t border-gray-200 pt-1 mt-1">
                    <span>Estimated Total:</span>
                    <span className="font-semibold">{totalCost} tokens</span>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  ✓ 68% token cost reduction
                  <br />✓ Fully automated
                  <br />✓ No manual work required
                </div>
              </button>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">💡 How Debug Mode Works</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Launches a persistent browser with DevTools enabled</li>
              <li>• Maintains CSRF tokens, cookies, and session state</li>
              <li>• Execute step {targetStep} multiple times with different approaches</li>
              <li>• See real-time results and screenshots for each iteration</li>
              <li>• Costs ~100 tokens per iteration (vs 2000+ for full re-execution)</li>
            </ul>
          </div>

          {/* Execution ID Info */}
          <div className="text-xs text-gray-500">
            <span className="font-medium">Execution ID:</span> {executionId}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <Button
            variant="secondary"
            size="md"
            onClick={onClose}
            disabled={isStarting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleStart}
            disabled={isStarting}
          >
            {isStarting ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                Starting...
              </>
            ) : (
              <>🚀 Start Debug Session</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
