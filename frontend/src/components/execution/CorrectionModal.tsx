/**
 * Correction Modal Component
 * Allows users to submit corrections for failed test steps
 */

import { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import feedbackService, { ExecutionFeedback, CorrectionSubmit } from '../../services/feedbackService';

interface CorrectionModalProps {
  feedback: ExecutionFeedback;
  onClose: () => void;
  onSubmit: () => void;
}

export function CorrectionModal({ feedback, onClose, onSubmit }: CorrectionModalProps) {
  const [correctionSource, setCorrectionSource] = useState<string>('human');
  const [confidence, setConfidence] = useState<number>(0.9);
  const [notes, setNotes] = useState<string>('');
  const [correctedStep, setCorrectedStep] = useState<string>(
    JSON.stringify(
      {
        action: 'click',
        selector: feedback.failed_selector || '',
        selector_type: feedback.selector_type || 'css',
        description: 'Corrected step'
      },
      null,
      2
    )
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // Parse JSON
      const parsed = JSON.parse(correctedStep);

      const correction: CorrectionSubmit = {
        corrected_step: parsed,
        correction_source: correctionSource,
        correction_confidence: confidence,
        notes: notes || undefined
      };

      await feedbackService.submitCorrection(feedback.id, correction);
      onSubmit();
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format for corrected step');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to submit correction');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Submit Correction</h2>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Original Failure Info */}
          <div className="mb-6 p-4 bg-red-50 rounded">
            <h3 className="font-semibold text-red-900 mb-2">Original Failure</h3>
            <div className="text-sm text-red-800 space-y-1">
              {feedback.failure_type && (
                <div>
                  <span className="font-medium">Type:</span> {feedback.failure_type}
                </div>
              )}
              {feedback.error_message && (
                <div>
                  <span className="font-medium">Error:</span> {feedback.error_message}
                </div>
              )}
              {feedback.failed_selector && (
                <div>
                  <span className="font-medium">Selector:</span>{' '}
                  <code className="bg-red-100 px-1 py-0.5 rounded">{feedback.failed_selector}</code>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
              {error}
            </div>
          )}

          {/* Corrected Step JSON */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Corrected Step (JSON) <span className="text-red-500">*</span>
            </label>
            <textarea
              value={correctedStep}
              onChange={(e) => setCorrectedStep(e.target.value)}
              className="w-full h-48 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder='{"action": "click", "selector": ".login-btn", "selector_type": "css"}'
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Enter the corrected test step as JSON. Include the working selector and any other step details.
            </p>
          </div>

          {/* Correction Source */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Correction Source <span className="text-red-500">*</span>
            </label>
            <select
              value={correctionSource}
              onChange={(e) => setCorrectionSource(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            >
              <option value="human">Human (Manual Fix)</option>
              <option value="ai_suggestion">AI Suggestion (Accepted)</option>
              <option value="auto_applied">Auto-Applied (High Confidence)</option>
            </select>
          </div>

          {/* Confidence Slider */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confidence: {(confidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Low (0%)</span>
              <span>Medium (50%)</span>
              <span>High (100%)</span>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Add any notes about this correction (e.g., why the selector changed, what you learned)"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Submit Correction'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
