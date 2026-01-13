/**
 * Execution Feedback Service
 * Sprint 4 - API client for execution feedback endpoints
 */

import apiClient from './api';
import type {
  ExecutionFeedback,
  ExecutionFeedbackListResponse,
  ExecutionFeedbackCreate,
  ExecutionFeedbackUpdate,
  CorrectionSubmit,
  ExecutionFeedbackStats,
  FailureType,
  CorrectionSource
} from '../types/execution';

// ============================================================================
// Feedback CRUD Operations
// ============================================================================

/**
 * Get feedback by ID
 */
export const getFeedback = async (feedbackId: number): Promise<ExecutionFeedback> => {
  const response = await apiClient.get<ExecutionFeedback>(`/feedback/${feedbackId}`);
  return response.data;
};

/**
 * Get all feedback for a specific execution
 */
export const getExecutionFeedback = async (
  executionId: number,
  skip: number = 0,
  limit: number = 100
): Promise<ExecutionFeedback[]> => {
  const response = await apiClient.get<ExecutionFeedback[]>(`/executions/${executionId}/feedback`, {
    params: { skip, limit }
  });
  return response.data;
};

/**
 * List feedback with filters
 */
export const listFeedback = async (params?: {
  skip?: number;
  limit?: number;
  failure_type?: FailureType;
  correction_source?: CorrectionSource;
  is_anomaly?: boolean;
  has_correction?: boolean;
  execution_id?: number;
}): Promise<ExecutionFeedbackListResponse> => {
  const response = await apiClient.get<ExecutionFeedbackListResponse>('/feedback', { params });
  return response.data;
};

/**
 * Create feedback entry (typically done automatically by execution service)
 */
export const createFeedback = async (
  feedback: ExecutionFeedbackCreate
): Promise<ExecutionFeedback> => {
  const response = await apiClient.post<ExecutionFeedback>('/feedback', feedback);
  return response.data;
};

/**
 * Update feedback metadata
 */
export const updateFeedback = async (
  feedbackId: number,
  updates: ExecutionFeedbackUpdate
): Promise<ExecutionFeedback> => {
  const response = await apiClient.put<ExecutionFeedback>(`/feedback/${feedbackId}`, updates);
  return response.data;
};

/**
 * Delete feedback entry
 */
export const deleteFeedback = async (feedbackId: number): Promise<void> => {
  await apiClient.delete(`/feedback/${feedbackId}`);
};

// ============================================================================
// Correction Workflow
// ============================================================================

/**
 * Submit a correction for a feedback entry
 * This is the primary way users provide learning data to the system
 */
export const submitCorrection = async (
  feedbackId: number,
  correction: CorrectionSubmit
): Promise<ExecutionFeedback> => {
  const response = await apiClient.post<ExecutionFeedback>(
    `/feedback/${feedbackId}/correction`,
    correction
  );
  return response.data;
};

// ============================================================================
// Statistics
// ============================================================================

/**
 * Get overall feedback statistics
 */
export const getFeedbackStats = async (): Promise<ExecutionFeedbackStats> => {
  const response = await apiClient.get<ExecutionFeedbackStats>('/feedback/stats/summary');
  return response.data;
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get failure type badge color
 */
export const getFailureTypeBadgeColor = (failureType?: string): string => {
  switch (failureType) {
    case 'selector_not_found':
      return 'warning';
    case 'timeout':
      return 'error';
    case 'assertion_failed':
      return 'error';
    case 'network_error':
      return 'info';
    case 'permission_error':
      return 'error';
    case 'navigation_error':
      return 'warning';
    default:
      return 'default';
  }
};

/**
 * Get failure type display name
 */
export const getFailureTypeLabel = (failureType?: string): string => {
  switch (failureType) {
    case 'selector_not_found':
      return 'Selector Not Found';
    case 'timeout':
      return 'Timeout';
    case 'assertion_failed':
      return 'Assertion Failed';
    case 'network_error':
      return 'Network Error';
    case 'permission_error':
      return 'Permission Denied';
    case 'navigation_error':
      return 'Navigation Error';
    case 'unknown_error':
      return 'Unknown Error';
    default:
      return 'No Failure';
  }
};

/**
 * Get correction source badge color
 */
export const getCorrectionSourceBadgeColor = (source?: string): string => {
  switch (source) {
    case 'human':
      return 'success';
    case 'ai_suggestion':
      return 'info';
    case 'auto_applied':
      return 'primary';
    default:
      return 'default';
  }
};

/**
 * Get correction source label
 */
export const getCorrectionSourceLabel = (source?: string): string => {
  switch (source) {
    case 'human':
      return 'Human Corrected';
    case 'ai_suggestion':
      return 'AI Suggested';
    case 'auto_applied':
      return 'Auto Applied';
    default:
      return 'No Correction';
  }
};

/**
 * Get confidence percentage display
 */
export const formatConfidence = (confidence?: number): string => {
  if (confidence === undefined || confidence === null) return 'N/A';
  return `${Math.round(confidence * 100)}%`;
};

/**
 * Get confidence color based on value
 */
export const getConfidenceColor = (confidence?: number): string => {
  if (!confidence) return 'default';
  if (confidence >= 0.85) return 'success';
  if (confidence >= 0.6) return 'warning';
  return 'error';
};

export default {
  getFeedback,
  getExecutionFeedback,
  listFeedback,
  createFeedback,
  updateFeedback,
  deleteFeedback,
  submitCorrection,
  getFeedbackStats,
  getFailureTypeBadgeColor,
  getFailureTypeLabel,
  getCorrectionSourceBadgeColor,
  getCorrectionSourceLabel,
  formatConfidence,
  getConfidenceColor
};
