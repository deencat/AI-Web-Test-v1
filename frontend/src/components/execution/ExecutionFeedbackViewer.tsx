/**
 * Execution Feedback Viewer Component
 * Displays feedback entries for a test execution with correction workflow
 */

import { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import feedbackService, { ExecutionFeedback } from '../../services/feedbackService';
import { CorrectionModal } from './CorrectionModal';

interface ExecutionFeedbackViewerProps {
  executionId: number;
  onFeedbackUpdate?: () => void;
}

export function ExecutionFeedbackViewer({ executionId, onFeedbackUpdate }: ExecutionFeedbackViewerProps) {
  const [feedback, setFeedback] = useState<ExecutionFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFeedback, setSelectedFeedback] = useState<ExecutionFeedback | null>(null);
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);

  useEffect(() => {
    fetchFeedback();
  }, [executionId]);

  const fetchFeedback = async () => {
    setIsLoading(true);
    try {
      const data = await feedbackService.getExecutionFeedback(executionId);
      setFeedback(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feedback');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCorrect = (item: ExecutionFeedback) => {
    setSelectedFeedback(item);
    setShowCorrectionModal(true);
  };

  const handleCorrectionSubmit = async () => {
    setShowCorrectionModal(false);
    setSelectedFeedback(null);
    await fetchFeedback();
    onFeedbackUpdate?.();
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-3 text-gray-600">Loading feedback...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-red-600">
          <p className="font-semibold">Error loading feedback</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </Card>
    );
  }

  if (feedback.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <p>No feedback recorded for this execution</p>
          <p className="text-sm mt-1">Feedback is automatically collected when tests fail</p>
        </div>
      </Card>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Execution Feedback ({feedback.length})
          </h3>
          <Button variant="secondary" size="sm" onClick={fetchFeedback}>
            ↻ Refresh
          </Button>
        </div>

        {feedback.map((item) => (
          <FeedbackCard
            key={item.id}
            feedback={item}
            onCorrect={() => handleCorrect(item)}
          />
        ))}
      </div>

      {showCorrectionModal && selectedFeedback && (
        <CorrectionModal
          feedback={selectedFeedback}
          onClose={() => setShowCorrectionModal(false)}
          onSubmit={handleCorrectionSubmit}
        />
      )}
    </>
  );
}

// ============================================================================
// Feedback Card Component
// ============================================================================

interface FeedbackCardProps {
  feedback: ExecutionFeedback;
  onCorrect: () => void;
}

function FeedbackCard({ feedback, onCorrect }: FeedbackCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getFailureTypeColor = (type: string | null) => {
    switch (type) {
      case 'selector_not_found':
        return 'bg-red-100 text-red-800';
      case 'timeout':
        return 'bg-yellow-100 text-yellow-800';
      case 'assertion_failed':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const hasCorrection = !!feedback.corrected_step;

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {feedback.failure_type && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${getFailureTypeColor(feedback.failure_type)}`}>
                {feedback.failure_type.replace(/_/g, ' ').toUpperCase()}
              </span>
            )}
            {feedback.step_index !== null && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                Step {feedback.step_index}
              </span>
            )}
            {feedback.is_anomaly && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                ⚠️ Anomaly
              </span>
            )}
            {hasCorrection && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                ✓ Corrected
              </span>
            )}
          </div>

          <p className="text-sm text-gray-700 font-medium mb-1">
            {feedback.error_message || 'No error message'}
          </p>

          {feedback.failed_selector && (
            <div className="text-xs text-gray-600 mb-2">
              <span className="font-semibold">Selector:</span>{' '}
              <code className="bg-gray-100 px-1 py-0.5 rounded">{feedback.failed_selector}</code>
              {feedback.selector_type && ` (${feedback.selector_type})`}
            </div>
          )}

          {feedback.page_url && (
            <div className="text-xs text-gray-600 mb-2">
              <span className="font-semibold">Page:</span>{' '}
              <a href={feedback.page_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                {feedback.page_url}
              </a>
            </div>
          )}

          {feedback.notes && (
            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded mt-2">
              <span className="font-semibold">Notes:</span> {feedback.notes}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2 ml-4">
          {!hasCorrection && (
            <Button variant="primary" size="sm" onClick={onCorrect}>
              Add Correction
            </Button>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '▼ Less' : '▶ More'}
          </Button>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            {feedback.browser_type && (
              <div>
                <span className="font-semibold text-gray-700">Browser:</span>
                <span className="ml-2 text-gray-600">{feedback.browser_type}</span>
              </div>
            )}
            {feedback.step_duration_ms && (
              <div>
                <span className="font-semibold text-gray-700">Duration:</span>
                <span className="ml-2 text-gray-600">{feedback.step_duration_ms}ms</span>
              </div>
            )}
            {feedback.viewport_width && (
              <div>
                <span className="font-semibold text-gray-700">Viewport:</span>
                <span className="ml-2 text-gray-600">
                  {feedback.viewport_width}x{feedback.viewport_height}
                </span>
              </div>
            )}
            {feedback.memory_usage_mb && (
              <div>
                <span className="font-semibold text-gray-700">Memory:</span>
                <span className="ml-2 text-gray-600">{feedback.memory_usage_mb.toFixed(2)} MB</span>
              </div>
            )}
            {feedback.network_requests && (
              <div>
                <span className="font-semibold text-gray-700">Network Requests:</span>
                <span className="ml-2 text-gray-600">{feedback.network_requests}</span>
              </div>
            )}
            {feedback.anomaly_score && (
              <div>
                <span className="font-semibold text-gray-700">Anomaly Score:</span>
                <span className="ml-2 text-gray-600">{(feedback.anomaly_score * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>

          {hasCorrection && (
            <div className="mt-4 p-3 bg-green-50 rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-green-800">Correction Applied</span>
                {feedback.correction_confidence && (
                  <span className="text-sm text-green-700">
                    Confidence: {(feedback.correction_confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <div className="text-sm text-green-700">
                <span className="font-semibold">Source:</span> {feedback.correction_source}
              </div>
              {feedback.correction_applied_at && (
                <div className="text-xs text-green-600 mt-1">
                  Applied: {new Date(feedback.correction_applied_at).toLocaleString()}
                </div>
              )}
              <pre className="mt-2 text-xs bg-white p-2 rounded border border-green-200 overflow-x-auto">
                {JSON.stringify(feedback.corrected_step, null, 2)}
              </pre>
            </div>
          )}

          {feedback.screenshot_url && (
            <div className="mt-4">
              <span className="font-semibold text-gray-700 block mb-2">Screenshot:</span>
              <img
                src={feedback.screenshot_url}
                alt="Failure screenshot"
                className="max-w-full rounded border border-gray-300"
              />
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
