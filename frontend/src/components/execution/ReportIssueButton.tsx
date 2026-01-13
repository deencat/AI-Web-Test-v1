/**
 * ReportIssueButton Component
 * Allows users to manually report issues (especially false positives) for any test step
 */

import { useState } from 'react';
import type { TestExecutionDetail } from '../../types/execution';

interface ReportIssueButtonProps {
  executionId: number;
  step: TestExecutionDetail['steps'][0];
  onReportSuccess?: () => void;
}

export function ReportIssueButton({ executionId, step, onReportSuccess }: ReportIssueButtonProps) {
  const [showModal, setShowModal] = useState(false);

  const handleClick = () => {
    setShowModal(true);
  };

  const handleClose = () => {
    setShowModal(false);
  };

  const handleSuccess = () => {
    setShowModal(false);
    if (onReportSuccess) {
      onReportSuccess();
    }
  };

  return (
    <>
      <button
        onClick={handleClick}
        className="text-sm text-orange-600 hover:text-orange-800 font-medium"
        title="Report an issue with this step (e.g., false positive, wrong element clicked)"
      >
        ⚠️ Report Issue
      </button>

      {showModal && (
        <ReportIssueModal
          executionId={executionId}
          step={step}
          onClose={handleClose}
          onSuccess={handleSuccess}
        />
      )}
    </>
  );
}

interface ReportIssueModalProps {
  executionId: number;
  step: TestExecutionDetail['steps'][0];
  onClose: () => void;
  onSuccess: () => void;
}

function ReportIssueModal({ executionId, step, onClose, onSuccess }: ReportIssueModalProps) {
  const [issueType, setIssueType] = useState<'false_positive' | 'wrong_element' | 'timing' | 'other'>('false_positive');
  const [description, setDescription] = useState('');
  const [expectedBehavior, setExpectedBehavior] = useState('');
  const [actualBehavior, setActualBehavior] = useState('');
  const [correctSelector, setCorrectSelector] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Create feedback entry
      const token = localStorage.getItem('token');
      const feedbackResponse = await fetch('http://localhost:8000/api/v1/feedback', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          execution_id: executionId,
          step_index: step.step_number - 1,  // Convert to 0-based index
          failure_type: issueType === 'false_positive' ? 'other' : 'selector_not_found',
          error_message: `USER REPORTED: ${description}`,
          notes: `Issue Type: ${issueType}

Expected Behavior:
${expectedBehavior}

Actual Behavior:
${actualBehavior}

${correctSelector ? `Suggested Correct Selector: ${correctSelector}` : ''}

Reported by user via UI (manual review)`,
          failed_selector: correctSelector || 'unknown',
          selector_type: 'css',
          page_url: 'reported-from-ui',
          browser_type: 'chromium',
          tags: ['user-reported', issueType, 'ui-submission']
        })
      });

      if (!feedbackResponse.ok) {
        throw new Error(`Failed to create feedback: ${feedbackResponse.statusText}`);
      }

      const feedback = await feedbackResponse.json();

      // If user provided a correct selector, submit it as a correction
      if (correctSelector) {
        await fetch(`http://localhost:8000/api/v1/feedback/${feedback.id}/correction`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            corrected_step: {
              action: 'click',
              selector: correctSelector,
              value: '',
              description: step.step_description
            },
            correction_source: 'human',
            correction_confidence: 0.90,
            notes: 'User-provided correction via issue reporting'
          })
        });
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to report issue');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">
              ⚠️ Report Issue with Step {step.step_number}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Step Context */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">
              <strong>Step {step.step_number}:</strong> {step.step_description}
            </p>
            {step.expected_result && (
              <p className="text-sm text-gray-600">
                <strong>Expected:</strong> {step.expected_result}
              </p>
            )}
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Issue Type */}
            <div>
              <label htmlFor="issueType" className="block text-sm font-medium text-gray-700 mb-1">
                Issue Type
              </label>
              <select
                id="issueType"
                value={issueType}
                onChange={(e) => setIssueType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              >
                <option value="false_positive">False Positive (test passed but shouldn't have)</option>
                <option value="wrong_element">Wrong Element (clicked/filled wrong element)</option>
                <option value="timing">Timing Issue (too fast/slow)</option>
                <option value="other">Other Issue</option>
              </select>
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                What went wrong? <span className="text-red-500">*</span>
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={3}
                placeholder="Describe the issue you observed..."
                required
              />
            </div>

            {/* Expected Behavior */}
            <div>
              <label htmlFor="expectedBehavior" className="block text-sm font-medium text-gray-700 mb-1">
                Expected Behavior <span className="text-red-500">*</span>
              </label>
              <textarea
                id="expectedBehavior"
                value={expectedBehavior}
                onChange={(e) => setExpectedBehavior(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={2}
                placeholder="What should have happened?"
                required
              />
            </div>

            {/* Actual Behavior */}
            <div>
              <label htmlFor="actualBehavior" className="block text-sm font-medium text-gray-700 mb-1">
                Actual Behavior <span className="text-red-500">*</span>
              </label>
              <textarea
                id="actualBehavior"
                value={actualBehavior}
                onChange={(e) => setActualBehavior(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={2}
                placeholder="What actually happened?"
                required
              />
            </div>

            {/* Correct Selector (Optional) */}
            <div>
              <label htmlFor="correctSelector" className="block text-sm font-medium text-gray-700 mb-1">
                Correct Selector (Optional)
              </label>
              <input
                type="text"
                id="correctSelector"
                value={correctSelector}
                onChange={(e) => setCorrectSelector(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="e.g., button[type='submit']"
              />
              <p className="text-xs text-gray-500 mt-1">
                If you know the correct selector, provide it here and it will be submitted as a correction
              </p>
            </div>

            {/* Error Display */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={submitting}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Report Issue'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
