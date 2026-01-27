import api, { apiHelpers } from './api';
import type {
  DebugSessionStartRequest,
  DebugSessionStartResponse,
  DebugStepExecuteRequest,
  DebugStepExecuteResponse,
  DebugNextStepResponse,
  DebugSessionStatusResponse,
  DebugSessionStopResponse,
  DebugSessionManualInstructionsResponse,
  DebugSessionConfirmSetupResponse,
  DebugSessionListResponse,
} from '../types/debug';

/**
 * Debug Mode Service
 * Handles persistent browser debug sessions for step-by-step test debugging
 */

class DebugService {
  /**
   * Start a new debug session
   */
  async startSession(request: DebugSessionStartRequest): Promise<DebugSessionStartResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (request.mode === 'manual') {
        return {
          session_id: 'mock-session-' + Date.now(),
          mode: 'manual',
          status: 'ready',
          message: 'Manual setup mode - Please complete the setup steps',
          browser_url: 'chrome://inspect',
          manual_setup_instructions: [
            {
              step_number: 1,
              description: 'Navigate to login page',
              action: 'Open https://example.com/login in the persistent browser',
              expected_state: 'Login form is visible',
            },
            {
              step_number: 2,
              description: 'Enter credentials',
              action: 'Type "admin@example.com" in email field and "password123" in password field',
              expected_state: 'Credentials are filled in the form',
            },
            {
              step_number: 3,
              description: 'Submit login',
              action: 'Click the "Login" button',
              expected_state: 'Redirected to dashboard, user is authenticated',
            },
          ],
          estimated_setup_cost: 0,
          execution_cost: 100,
        };
      } else {
        return {
          session_id: 'mock-session-' + Date.now(),
          mode: 'auto',
          status: 'setup_in_progress',
          message: 'Auto-setup in progress - AI is executing prerequisite steps',
          browser_url: 'chrome://inspect',
          estimated_setup_cost: 600,
          execution_cost: 100,
        };
      }
    }

    // Real API call
    try {
      const response = await api.post<DebugSessionStartResponse>('/debug/start', request);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Execute the target step in the debug session
   */
  async executeStep(request: DebugStepExecuteRequest): Promise<DebugStepExecuteResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const success = Math.random() > 0.3; // 70% success rate
      
      if (success) {
        return {
          session_id: request.session_id,
          iteration_number: Math.floor(Math.random() * 5) + 1,
          result: 'pass',
          actual_result: 'Step executed successfully',
          duration_seconds: 2.5,
          screenshot_path: '/screenshots/debug-step-pass.png',
          message: 'Step executed successfully',
        };
      } else {
        return {
          session_id: request.session_id,
          iteration_number: Math.floor(Math.random() * 5) + 1,
          result: 'fail',
          error_message: 'Element not found or interaction failed',
          duration_seconds: 1.8,
          screenshot_path: '/screenshots/debug-step-fail.png',
          message: 'Step execution failed',
        };
      }
    }

    // Real API call
    try {
      const response = await api.post<DebugStepExecuteResponse>('/debug/execute-step', request);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Execute the next step in sequence (multi-step debugging)
   */
  async executeNextStep(sessionId: string): Promise<DebugNextStepResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const currentStep = Math.floor(Math.random() * 8) + 1;
      const totalSteps = 10;
      const success = Math.random() > 0.2; // 80% success rate
      
      return {
        session_id: sessionId,
        step_number: currentStep,
        step_description: `Mock step ${currentStep} description`,
        success,
        error_message: success ? undefined : 'Element not found',
        screenshot_path: `/screenshots/step_${currentStep}.png`,
        duration_seconds: 0.5 + Math.random(),
        tokens_used: 100,
        has_more_steps: currentStep < totalSteps,
        next_step_preview: currentStep < totalSteps ? `Step ${currentStep + 1} description` : undefined,
        total_steps: totalSteps,
      };
    }

    // Real API call
    try {
      const response = await api.post<DebugNextStepResponse>(`/debug/${sessionId}/execute-next`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get debug session status
   */
  async getSessionStatus(sessionId: string): Promise<DebugSessionStatusResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        session_id: sessionId,
        mode: 'auto',
        status: 'ready',
        target_step_number: 4,
        prerequisite_steps_count: 3,
        current_step: 4,
        setup_completed: true,
        tokens_used: 800,
        iterations_count: 2,
        started_at: new Date(Date.now() - 300000).toISOString(),
        last_activity_at: new Date().toISOString(),
        devtools_url: 'chrome://inspect',
      };
    }

    // Real API call
    try {
      const response = await api.get<DebugSessionStatusResponse>(`/debug/${sessionId}/status`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Stop a debug session and cleanup
   */
  async stopSession(sessionId: string): Promise<DebugSessionStopResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        session_id: sessionId,
        message: 'Debug session stopped successfully',
        final_status: 'completed',
        total_iterations: 5,
        total_tokens_used: 1100,
      };
    }

    // Real API call
    try {
      const response = await api.post<DebugSessionStopResponse>('/debug/stop', { session_id: sessionId });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get manual setup instructions
   */
  async getManualInstructions(sessionId: string): Promise<DebugSessionManualInstructionsResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      return {
        session_id: sessionId,
        instructions: [
          {
            step_number: 1,
            description: 'Navigate to login page',
            action: 'Open https://example.com/login in the persistent browser',
            expected_state: 'Login form is visible',
          },
          {
            step_number: 2,
            description: 'Enter credentials',
            action: 'Type "admin@example.com" in email field and "password123" in password field',
            expected_state: 'Credentials are filled in the form',
          },
        ],
        estimated_time_minutes: 3,
        message: 'Manual setup instructions retrieved',
      };
    }

    // Real API call
    try {
      const response = await api.get<DebugSessionManualInstructionsResponse>(
        `/debug/${sessionId}/instructions`
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Confirm manual setup completion
   */
  async confirmSetupComplete(sessionId: string): Promise<DebugSessionConfirmSetupResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        session_id: sessionId,
        status: 'ready',
        message: 'Manual setup confirmed - Session is ready for step execution',
      };
    }

    // Real API call
    try {
      const response = await api.post<DebugSessionConfirmSetupResponse>('/debug/confirm-setup', {
        session_id: sessionId,
      });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get list of debug sessions
   */
  async getSessions(params?: { skip?: number; limit?: number }): Promise<DebugSessionListResponse> {
    if (apiHelpers.useMockData()) {
      // Mock implementation
      const mockSessions = Array.from({ length: 5 }, (_, i) => ({
        session_id: `mock-session-${i + 1}`,
        mode: (i % 2 === 0 ? 'auto' : 'manual') as 'auto' | 'manual',
        status: (['ready', 'executing', 'completed'] as const)[i % 3],
        execution_id: i + 1,
        target_step_number: Math.floor(Math.random() * 5) + 1,
        current_iteration: Math.floor(Math.random() * 3) + 1,
        total_tokens_used: Math.floor(Math.random() * 1500) + 500,
        started_at: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        last_activity_at: new Date(Date.now() - Math.random() * 600000).toISOString(),
      }));

      return {
        sessions: mockSessions.slice(params?.skip || 0, (params?.skip || 0) + (params?.limit || 20)),
        total: mockSessions.length,
        active_sessions: 2,
      };
    }

    // Real API call
    try {
      const response = await api.get<DebugSessionListResponse>('/debug/sessions', { params });
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new DebugService();
