import type { ManualSetupInstruction } from '../../types/debug';

interface ManualInstructionsViewProps {
  instructions: ManualSetupInstruction[];
  browserUrl?: string;
  onConfirmComplete: () => void;
  isConfirming: boolean;
}

export function ManualInstructionsView({
  instructions,
  browserUrl,
  onConfirmComplete,
  isConfirming,
}: ManualInstructionsViewProps) {
  return (
    <div className="bg-white border border-blue-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📋</span>
          <div>
            <h3 className="text-lg font-semibold text-blue-900">
              Manual Setup Instructions
            </h3>
            <p className="text-sm text-blue-700">
              Complete these steps in the persistent browser, then confirm below
            </p>
          </div>
        </div>
      </div>

      {/* Browser URL */}
      {browserUrl && (
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <div className="text-sm">
            <span className="font-medium text-gray-700">Browser Debug URL:</span>
            <a
              href={browserUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-blue-600 hover:text-blue-700 underline"
            >
              {browserUrl}
            </a>
          </div>
        </div>
      )}

      {/* Instructions List */}
      <div className="px-6 py-4 space-y-4">
        {instructions.map((instruction, index) => (
          <div
            key={index}
            className="border-l-4 border-blue-500 pl-4 py-2"
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-bold">
                {instruction.step_number}
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-1">
                  {instruction.description}
                </h4>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Action:</span>
                    <p className="text-gray-600 mt-1">{instruction.action}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Expected State:</span>
                    <p className="text-gray-600 mt-1">{instruction.expected_state}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info Box */}
      <div className="px-6 py-3 bg-yellow-50 border-t border-yellow-200">
        <div className="flex items-start gap-2">
          <span className="text-lg">⚠️</span>
          <div className="text-sm text-yellow-800">
            <span className="font-medium">Important:</span> Complete all steps in order and verify
            the expected state before confirming. The debug session will use the browser's current
            state for step execution.
          </div>
        </div>
      </div>

      {/* Confirm Button */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <button
          onClick={onConfirmComplete}
          disabled={isConfirming}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isConfirming ? (
            <>
              <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
              <span>Confirming...</span>
            </>
          ) : (
            <>
              <span>✓</span>
              <span>I've Completed All Steps - Start Debug Session</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
