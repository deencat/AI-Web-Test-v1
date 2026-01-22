import React, { useState } from 'react';

export interface LoopBlock {
  id: string;
  start_step: number;
  end_step: number;
  iterations: number;
  description: string;
  variables?: Record<string, string>;
}

interface LoopBlockEditorProps {
  totalSteps: number;
  loopBlocks: LoopBlock[];
  onChange: (loopBlocks: LoopBlock[]) => void;
}

export const LoopBlockEditor: React.FC<LoopBlockEditorProps> = ({
  totalSteps,
  loopBlocks,
  onChange
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [startStep, setStartStep] = useState(1);
  const [endStep, setEndStep] = useState(1);
  const [iterations, setIterations] = useState(3);
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

  const validateLoopBlock = (): string[] => {
    const validationErrors: string[] = [];

    // Validate start step
    if (startStep < 1 || startStep > totalSteps) {
      validationErrors.push(`Start step must be between 1 and ${totalSteps}`);
    }

    // Validate end step
    if (endStep < startStep) {
      validationErrors.push('End step must be greater than or equal to start step');
    }

    if (endStep > totalSteps) {
      validationErrors.push(`End step cannot exceed ${totalSteps}`);
    }

    // Validate iterations
    if (iterations < 1) {
      validationErrors.push('Iterations must be at least 1');
    }

    if (iterations > 100) {
      validationErrors.push('Maximum 100 iterations allowed');
    }

    // Check for overlapping loops
    const newLoopStart = startStep;
    const newLoopEnd = endStep;

    for (const loop of loopBlocks) {
      // Check if ranges overlap
      if (
        (newLoopStart <= loop.end_step && newLoopEnd >= loop.start_step) ||
        (loop.start_step <= newLoopEnd && loop.end_step >= newLoopStart)
      ) {
        validationErrors.push(
          `This loop overlaps with existing loop "${loop.description}" (steps ${loop.start_step}-${loop.end_step})`
        );
      }
    }

    return validationErrors;
  };

  const calculateExecutionPlan = () => {
    const loopSteps = endStep - startStep + 1;
    const loopExecutions = loopSteps * iterations;
    const nonLoopSteps = totalSteps - loopSteps;
    const totalExecutions = nonLoopSteps + loopExecutions;

    return {
      loopSteps,
      loopExecutions,
      nonLoopSteps,
      totalExecutions
    };
  };

  const handleCreateLoop = () => {
    const validationErrors = validateLoopBlock();

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    const newLoop: LoopBlock = {
      id: `loop_${Date.now()}`,
      start_step: startStep,
      end_step: endStep,
      iterations: iterations,
      description: description || `Loop steps ${startStep}-${endStep}`
    };

    onChange([...loopBlocks, newLoop]);
    
    // Reset form
    setIsCreating(false);
    setStartStep(1);
    setEndStep(1);
    setIterations(3);
    setDescription('');
    setErrors([]);
  };

  const handleDeleteLoop = (loopId: string) => {
    onChange(loopBlocks.filter(loop => loop.id !== loopId));
  };

  const handleCancel = () => {
    setIsCreating(false);
    setErrors([]);
  };

  const executionPlan = calculateExecutionPlan();

  return (
    <div className="loop-block-editor border border-gray-300 rounded-lg p-4 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800">
          🔁 Loop Blocks
        </h3>
        {!isCreating && (
          <button
            onClick={() => setIsCreating(true)}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            disabled={totalSteps < 2}
          >
            + Create Loop
          </button>
        )}
      </div>

      {/* Info message when no steps */}
      {totalSteps < 2 && (
        <div className="text-sm text-gray-500 italic">
          Add at least 2 test steps before creating loops
        </div>
      )}

      {/* Existing loops list */}
      {loopBlocks.length > 0 && (
        <div className="mb-4 space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Active Loops ({loopBlocks.length}):</h4>
          {loopBlocks.map((loop) => {
            const loopSteps = loop.end_step - loop.start_step + 1;
            const totalLoopExecutions = loopSteps * loop.iterations;
            
            return (
              <div
                key={loop.id}
                className="bg-blue-50 border border-blue-200 rounded p-3 flex items-start justify-between"
              >
                <div className="flex-1">
                  <div className="font-medium text-sm text-gray-800">
                    {loop.description}
                  </div>
                  <div className="mt-1 text-xs text-gray-600">
                    <span className="inline-block mr-3">
                      📍 Steps: {loop.start_step}-{loop.end_step} ({loopSteps} steps)
                    </span>
                    <span className="inline-block mr-3">
                      🔢 Iterations: {loop.iterations}
                    </span>
                    <span className="inline-block">
                      ⚡ Total: {totalLoopExecutions} executions
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteLoop(loop.id)}
                  className="ml-3 px-2 py-1 text-xs text-red-600 hover:text-red-800 hover:bg-red-100 rounded"
                  title="Delete loop"
                >
                  ✕ Delete
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Create loop form */}
      {isCreating && (
        <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-800 mb-3">
            Create New Loop Block
          </h4>

          {/* Error messages */}
          {errors.length > 0 && (
            <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded">
              {errors.map((error, index) => (
                <div key={index} className="text-xs text-red-700">
                  ⚠️ {error}
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 mb-3">
            {/* Start Step */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Start Step
              </label>
              <input
                type="number"
                min="1"
                max={totalSteps}
                value={startStep}
                onChange={(e) => {
                  setStartStep(parseInt(e.target.value) || 1);
                  setErrors([]);
                }}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* End Step */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                End Step
              </label>
              <input
                type="number"
                min={startStep}
                max={totalSteps}
                value={endStep}
                onChange={(e) => {
                  setEndStep(parseInt(e.target.value) || 1);
                  setErrors([]);
                }}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            {/* Iterations */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Iterations (1-100)
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={iterations}
                onChange={(e) => {
                  setIterations(parseInt(e.target.value) || 1);
                  setErrors([]);
                }}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={`Loop steps ${startStep}-${endStep}`}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Execution preview */}
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded">
            <div className="text-xs font-medium text-gray-700 mb-1">
              📊 Execution Preview:
            </div>
            <div className="text-xs text-gray-600">
              • Loop steps: {executionPlan.loopSteps} (steps {startStep}-{endStep})
            </div>
            <div className="text-xs text-gray-600">
              • Loop executions: {executionPlan.loopExecutions} ({executionPlan.loopSteps} steps × {iterations} iterations)
            </div>
            <div className="text-xs text-gray-600">
              • Non-loop steps: {executionPlan.nonLoopSteps}
            </div>
            <div className="text-xs font-semibold text-blue-700 mt-1">
              • Total executions: {executionPlan.totalExecutions} steps
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex justify-end space-x-2">
            <button
              onClick={handleCancel}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateLoop}
              className="px-3 py-1 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
            >
              Create Loop Block
            </button>
          </div>
        </div>
      )}

      {/* Help text */}
      {!isCreating && loopBlocks.length === 0 && totalSteps >= 2 && (
        <div className="text-xs text-gray-500 mt-2">
          💡 Tip: Use loops to repeat step sequences (e.g., upload 5 files, fill 3 forms)
        </div>
      )}
    </div>
  );
};

export default LoopBlockEditor;
