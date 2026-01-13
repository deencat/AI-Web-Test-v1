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

export interface FeedbackExportParams {
  include_html?: boolean;
  include_screenshots?: boolean;
  since_date?: string;
  limit?: number;
}

export interface FeedbackExportData {
  export_version: string;
  exported_at: string;
  exported_by: string;
  total_count: number;
  sanitized: boolean;
  includes_html: boolean;
  includes_screenshots: boolean;
  feedback_items: any[];
}

export interface FeedbackImportResult {
  success: boolean;
  message: string;
  imported_count: number;
  skipped_count: number;
  updated_count: number;
  failed_count: number;
  total_processed: number;
  errors: string[];
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

  /**
   * Export feedback to JSON file
   * 
   * Sprint 4 Feature: Team Data Sync
   * 
   * @param params - Export parameters (html, screenshots, date filter, limit)
   * @returns Blob containing JSON data for download
   */
  async exportFeedback(params?: FeedbackExportParams): Promise<Blob> {
    try {
      const response = await api.get('/feedback/export', {
        params: {
          include_html: params?.include_html || false,
          include_screenshots: params?.include_screenshots || false,
          since_date: params?.since_date,
          limit: params?.limit || 1000,
        },
        responseType: 'blob', // Important: Get response as Blob for file download
      });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Import feedback from JSON file
   * 
   * Sprint 4 Feature: Team Data Sync
   * 
   * @param file - JSON file from export endpoint
   * @param mergeStrategy - How to handle duplicates: 'skip_duplicates', 'update_existing', 'create_all'
   * @returns Import result summary
   */
  async importFeedback(
    file: File,
    mergeStrategy: 'skip_duplicates' | 'update_existing' | 'create_all' = 'skip_duplicates'
  ): Promise<FeedbackImportResult> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post<FeedbackImportResult>(
        '/feedback/import',
        formData,
        {
          params: { merge_strategy: mergeStrategy },
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Download export file helper
   * 
   * @param blob - Blob data from exportFeedback
   * @param filename - Optional custom filename
   */
  downloadExportFile(blob: Blob, filename?: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `feedback-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}

export default new FeedbackService();
