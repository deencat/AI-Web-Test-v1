/**
 * Feedback Service
 * Handles execution feedback, corrections, and learning system data
 */

import api, { apiHelpers } from './api';

// ============================================================================
// Types
// ============================================================================

export interface ExecutionFeedback {
  id: number;
  execution_id: number;
  step_index: number | null;
  failure_type: string | null;
  error_message: string | null;
  screenshot_url: string | null;
  page_url: string | null;
  browser_type: string | null;
  failed_selector: string | null;
  selector_type: string | null;
  viewport_width: number | null;
  viewport_height: number | null;
  corrected_step: any | null;
  correction_source: string | null;
  correction_confidence: number | null;
  correction_applied_at: string | null;
  corrected_by_user_id: number | null;
  step_duration_ms: number | null;
  memory_usage_mb: number | null;
  network_requests: number | null;
  is_anomaly: boolean;
  anomaly_score: number | null;
  anomaly_type: string | null;
  notes: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutionFeedbackListItem {
  id: number;
  execution_id: number;
  step_index: number | null;
  failure_type: string | null;
  error_message: string | null;
  screenshot_url: string | null;
  page_url: string | null;
  browser_type: string | null;
  failed_selector: string | null;
  selector_type: string | null;
  correction_source: string | null;
  correction_confidence: number | null;
  is_anomaly: boolean;
  anomaly_score: number | null;
  created_at: string;
}

export interface FeedbackListResponse {
  items: ExecutionFeedbackListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface FeedbackStats {
  total_feedback: number;
  total_failures: number;
  total_corrected: number;
  total_anomalies: number;
  correction_rate: number;
  top_failure_types: Array<{ type: string; count: number }>;
  top_failed_selectors: Array<{ selector: string; count: number }>;
}

export interface CorrectionSubmit {
  corrected_step: any;
  correction_source: string;
  correction_confidence?: number;
  notes?: string;
}

export interface FeedbackCreate {
  execution_id: number;
  step_index?: number;
  failure_type?: string;
  error_message?: string;
  screenshot_url?: string;
  page_url?: string;
  browser_type?: string;
  failed_selector?: string;
  selector_type?: string;
  notes?: string;
  tags?: string[];
}

// ============================================================================
// Feedback Service Class
// ============================================================================

class FeedbackService {
  /**
   * Get feedback entries for a specific execution
   */
  async getExecutionFeedback(
    executionId: number,
    skip: number = 0,
    limit: number = 100
  ): Promise<ExecutionFeedback[]> {
    try {
      const response = await api.get<ExecutionFeedback[]>(
        `/executions/${executionId}/feedback`,
        { params: { skip, limit } }
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * List all feedback with filters
   */
  async listFeedback(params?: {
    skip?: number;
    limit?: number;
    failure_type?: string;
    correction_source?: string;
    is_anomaly?: boolean;
    has_correction?: boolean;
    execution_id?: number;
  }): Promise<FeedbackListResponse> {
    try {
      const response = await api.get<FeedbackListResponse>('/feedback', { params });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get a specific feedback entry by ID
   */
  async getFeedback(feedbackId: number): Promise<ExecutionFeedback> {
    try {
      const response = await api.get<ExecutionFeedback>(`/feedback/${feedbackId}`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Create a new feedback entry
   */
  async createFeedback(feedback: FeedbackCreate): Promise<ExecutionFeedback> {
    try {
      const response = await api.post<ExecutionFeedback>('/feedback', feedback);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Submit a correction for a feedback entry
   */
  async submitCorrection(
    feedbackId: number,
    correction: CorrectionSubmit
  ): Promise<ExecutionFeedback> {
    try {
      const response = await api.post<ExecutionFeedback>(
        `/feedback/${feedbackId}/correction`,
        correction
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Update feedback metadata
   */
  async updateFeedback(
    feedbackId: number,
    updates: Partial<ExecutionFeedback>
  ): Promise<ExecutionFeedback> {
    try {
      const response = await api.put<ExecutionFeedback>(`/feedback/${feedbackId}`, updates);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete a feedback entry
   */
  async deleteFeedback(feedbackId: number): Promise<void> {
    try {
      await api.delete(`/feedback/${feedbackId}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get feedback statistics
   */
  async getStats(): Promise<FeedbackStats> {
    try {
      const response = await api.get<FeedbackStats>('/feedback/stats/summary');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new FeedbackService();
