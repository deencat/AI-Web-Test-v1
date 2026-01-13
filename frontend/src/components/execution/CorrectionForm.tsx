/**
 * CorrectionForm Component
 * Sprint 4 - Form for submitting corrections to failed test steps
 */

import { useState } from 'react';
import type { ExecutionFeedback, CorrectionSubmit, CorrectionSource } from '../../types/execution';
import executionFeedbackService from '../../services/executionFeedbackService';

interface CorrectionFormProps {
  feedback: ExecutionFeedback;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function CorrectionForm({ feedback, onSuccess, onCancel }: CorrectionFormProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [correctionSource, setCorrectionSource] = useState<CorrectionSource>('human');
  const [confidence, setConfidence] = useState(0.8);
  const [selector, setSelector] = useState(feedback.failed_selector || '');
  const [selectorType, setSelectorType] = useState<'css' | 'xpath' | 'text' | 'aria'>(
    (feedback.selector_type as 'css' | 'xpath' | 'text' | 'aria') || 'css'
  );
  const [notes, setNotes] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selector.trim()) {
      setError('Corrected selector is required');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const correction: CorrectionSubmit = {
        corrected_step: {
          selector: selector.trim(),
          selector_type: selectorType,
          description: `Corrected selector for step ${(feedback.step_index ?? 0) + 1}`,
          original_selector: feedback.failed_selector,
          original_error: feedback.error_message
        },
        correction_source: correctionSource,
        correction_confidence: confidence,
        notes: notes.trim() || undefined
      };

      await executionFeedbackService.submitCorrection(feedback.id, correction);
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      console.error('Failed to submit correction:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit correction');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Submit Correction</h3>

      {/* Feedback Context */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Failed Step Context</h4>
        {feedback.step_index !== null && feedback.step_index !== undefined && (
          <p className="text-sm text-gray-600 mb-1">Step: {feedback.step_index + 1}</p>
        )}
        {feedback.failure_type && (
          <p className="text-sm text-gray-600 mb-1">
            Failure Type: {executionFeedbackService.getFailureTypeLabel(feedback.failure_type)}
          </p>
        )}
        {feedback.error_message && (
          <p className="text-sm text-gray-600 font-mono bg-white p-2 rounded mt-2">
            {feedback.error_message.substring(0, 200)}
            {feedback.error_message.length > 200 && '...'}
          </p>
        )}
        {feedback.failed_selector && (
          <p className="text-sm text-gray-600 mt-2">
            <span className="font-medium">Failed Selector:</span>{' '}
            <code className="bg-white px-1 rounded">{feedback.failed_selector}</code>
          </p>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Corrected Selector */}
        <div>
          <label htmlFor="selector" className="block text-sm font-medium text-gray-700 mb-1">
            Corrected Selector *
          </label>
          <input
            type="text"
            id="selector"
            value={selector}
            onChange={(e) => setSelector(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono text-sm"
            placeholder="e.g., #login-button or .submit-btn"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the working selector that should be used instead
          </p>
        </div>

        {/* Selector Type */}
        <div>
          <label htmlFor="selectorType" className="block text-sm font-medium text-gray-700 mb-1">
            Selector Type
          </label>
          <select
            id="selectorType"
            value={selectorType}
            onChange={(e) => setSelectorType(e.target.value as 'css' | 'xpath' | 'text' | 'aria')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="css">CSS Selector</option>
            <option value="xpath">XPath</option>
            <option value="text">Text</option>
            <option value="aria">ARIA</option>
          </select>
        </div>

        {/* Correction Source */}
        <div>
          <label htmlFor="correctionSource" className="block text-sm font-medium text-gray-700 mb-1">
            Correction Source
          </label>
          <select
            id="correctionSource"
            value={correctionSource}
            onChange={(e) => setCorrectionSource(e.target.value as CorrectionSource)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="human">Human Corrected</option>
            <option value="ai_suggestion">AI Suggested (accepted by user)</option>
            <option value="auto_applied">Auto Applied (high confidence)</option>
          </select>
        </div>

        {/* Confidence Slider */}
        <div>
          <label htmlFor="confidence" className="block text-sm font-medium text-gray-700 mb-1">
            Confidence: {Math.round(confidence * 100)}%
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              id="confidence"
              min="0"
              max="1"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <span className={`text-sm font-medium px-2 py-1 rounded ${
              executionFeedbackService.getConfidenceColor(confidence) === 'success'
                ? 'bg-green-100 text-green-800'
                : executionFeedbackService.getConfidenceColor(confidence) === 'warning'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {Math.round(confidence * 100)}%
            </span>
          </div>
          <p className="mt-1 text-xs text-gray-500">
            How confident are you that this correction will work? (≥85% = high confidence)
          </p>
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
            Notes (Optional)
          </label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            placeholder="Add any additional context or explanation..."
          />
          <p className="mt-1 text-xs text-gray-500">
            E.g., "Selector changed in recent UI update" or "Updated to more stable selector"
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={submitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={submitting || !selector.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Submitting...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Submit Correction
              </>
            )}
          </button>
        </div>
      </form>

      {/* Help Text */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex">
          <svg className="h-5 w-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h4 className="text-sm font-medium text-blue-800">💡 How this helps</h4>
            <p className="mt-1 text-sm text-blue-700">
              Your correction will be used by the AI learning system to:
            </p>
            <ul className="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
              <li>Automatically suggest fixes for similar failures</li>
              <li>Improve test generation accuracy</li>
              <li>Build a knowledge base of working selectors</li>
              <li>Detect patterns in test failures</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
