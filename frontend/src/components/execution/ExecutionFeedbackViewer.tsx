/**
 * ExecutionFeedbackViewer Component
 * Sprint 4 - Displays execution feedback with failure context
 */

import { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import type { ExecutionFeedback } from '../../types/execution';
import executionFeedbackService from '../../services/executionFeedbackService';

interface ExecutionFeedbackViewerProps {
  executionId: number;
  onCorrectClick?: (feedback: ExecutionFeedback) => void;
}

export function ExecutionFeedbackViewer({ executionId, onCorrectClick }: ExecutionFeedbackViewerProps) {
  const [feedbackItems, setFeedbackItems] = useState<ExecutionFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFeedback();
  }, [executionId]);

  const loadFeedback = async () => {
    try {
      setLoading(true);
      setError(null);
      const items = await executionFeedbackService.getExecutionFeedback(executionId);
      setFeedbackItems(items);
    } catch (err) {
      console.error('Failed to load feedback:', err);
      setError('Failed to load execution feedback');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Execution Feedback</h2>
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-gray-500">Loading feedback...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Execution Feedback</h2>
        <div className="text-center py-8 text-red-600">
          <p>{error}</p>
          <button
            onClick={loadFeedback}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (feedbackItems.length === 0) {
    return (
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Execution Feedback</h2>
        <div className="text-center py-8 text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="mt-2">No feedback recorded for this execution.</p>
          <p className="text-sm text-gray-400 mt-1">
            Feedback is automatically captured when test steps fail.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-900">
          Execution Feedback ({feedbackItems.length})
        </h2>
        <button
          onClick={loadFeedback}
          className="text-sm text-indigo-600 hover:text-indigo-800"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-4">
        {feedbackItems.map((feedback) => (
          <FeedbackItem
            key={feedback.id}
            feedback={feedback}
            onCorrectClick={onCorrectClick}
          />
        ))}
      </div>
    </Card>
  );
}

interface FeedbackItemProps {
  feedback: ExecutionFeedback;
  onCorrectClick?: (feedback: ExecutionFeedback) => void;
}

function FeedbackItem({ feedback, onCorrectClick }: FeedbackItemProps) {
  const [expanded, setExpanded] = useState(false);

  const failureTypeColor = executionFeedbackService.getFailureTypeBadgeColor(feedback.failure_type);
  const failureTypeLabel = executionFeedbackService.getFailureTypeLabel(feedback.failure_type);

  const getBadgeClass = (color: string) => {
    const baseClass = 'px-2 py-1 rounded text-xs font-medium';
    switch (color) {
      case 'error':
        return `${baseClass} bg-red-100 text-red-800`;
      case 'warning':
        return `${baseClass} bg-yellow-100 text-yellow-800`;
      case 'success':
        return `${baseClass} bg-green-100 text-green-800`;
      case 'info':
        return `${baseClass} bg-blue-100 text-blue-800`;
      case 'primary':
        return `${baseClass} bg-indigo-100 text-indigo-800`;
      default:
        return `${baseClass} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {feedback.step_index !== null && feedback.step_index !== undefined && (
              <span className="text-sm font-medium text-gray-600">
                Step {feedback.step_index + 1}
              </span>
            )}
            {feedback.failure_type && (
              <span className={getBadgeClass(failureTypeColor)}>
                {failureTypeLabel}
              </span>
            )}
            {feedback.is_anomaly && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                ⚠️ Anomaly
              </span>
            )}
            {feedback.corrected_step && (
              <span className={getBadgeClass(
                executionFeedbackService.getCorrectionSourceBadgeColor(feedback.correction_source)
              )}>
                ✓ {executionFeedbackService.getCorrectionSourceLabel(feedback.correction_source)}
              </span>
            )}
          </div>

          {/* Error Message */}
          {feedback.error_message && (
            <p className="text-sm text-gray-800 mb-2 font-mono bg-gray-50 p-2 rounded">
              {feedback.error_message.length > 150 && !expanded
                ? `${feedback.error_message.substring(0, 150)}...`
                : feedback.error_message}
            </p>
          )}

          {/* Page URL */}
          {feedback.page_url && (
            <p className="text-xs text-gray-500 mb-1">
              <span className="font-medium">Page:</span>{' '}
              <a
                href={feedback.page_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:underline"
              >
                {feedback.page_url.length > 80
                  ? `${feedback.page_url.substring(0, 80)}...`
                  : feedback.page_url}
              </a>
            </p>
          )}

          {/* Failed Selector */}
          {feedback.failed_selector && (
            <p className="text-xs text-gray-500 mb-1">
              <span className="font-medium">Failed Selector ({feedback.selector_type}):</span>{' '}
              <code className="bg-gray-100 px-1 rounded">{feedback.failed_selector}</code>
            </p>
          )}

          {/* Timing */}
          {feedback.step_duration_ms && (
            <p className="text-xs text-gray-500">
              <span className="font-medium">Duration:</span> {feedback.step_duration_ms}ms
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 ml-4">
          {feedback.screenshot_url && (
            <a
              href={feedback.screenshot_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800"
              title="View Screenshot"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </a>
          )}
          
          {!feedback.corrected_step && onCorrectClick && (
            <button
              onClick={() => onCorrectClick(feedback)}
              className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
              title="Submit Correction"
            >
              Fix
            </button>
          )}

          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-400 hover:text-gray-600"
            title={expanded ? 'Show Less' : 'Show More'}
          >
            <svg
              className={`h-5 w-5 transform transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
          {/* Corrected Step */}
          {feedback.corrected_step && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Correction Applied:</h4>
              <pre className="text-xs bg-green-50 p-2 rounded overflow-auto">
                {JSON.stringify(feedback.corrected_step, null, 2)}
              </pre>
              {feedback.correction_confidence && (
                <p className="text-xs text-gray-600 mt-1">
                  Confidence: {executionFeedbackService.formatConfidence(feedback.correction_confidence)}
                </p>
              )}
            </div>
          )}

          {/* Anomaly Details */}
          {feedback.is_anomaly && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Anomaly Details:</h4>
              <p className="text-xs text-gray-600">
                Type: {feedback.anomaly_type || 'Unknown'}
                {feedback.anomaly_score && ` (Score: ${Math.round(feedback.anomaly_score * 100)}%)`}
              </p>
            </div>
          )}

          {/* Notes */}
          {feedback.notes && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-1">Notes:</h4>
              <p className="text-sm text-gray-600">{feedback.notes}</p>
            </div>
          )}

          {/* Metadata */}
          <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
            <p>Browser: {feedback.browser_type || 'Unknown'}</p>
            {feedback.viewport_width && feedback.viewport_height && (
              <p>Viewport: {feedback.viewport_width}×{feedback.viewport_height}</p>
            )}
            <p>Recorded: {new Date(feedback.created_at).toLocaleString()}</p>
          </div>
        </div>
      )}
    </div>
  );
}
