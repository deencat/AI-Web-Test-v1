import api, { apiHelpers } from './api';
import { Settings, UpdateSettingsRequest } from '../types/api';

/**
 * Settings Service
 * Handles application settings management
 */

// Mock default settings
const mockSettings: Settings = {
  project_name: 'AI Web Test v1.0',
  default_timeout: 30,
  email_notifications: true,
  slack_notifications: false,
  test_failure_alerts: true,
  ai_model: 'claude-3-opus-20240229',
  temperature: 0.7,
  max_tokens: 8192,
  parallel_runs: 3,
  retry_count: 2,
  timeout_multiplier: 1.5,
  github_webhook_url: '',
  slack_channel: '#qa-alerts',
  backend_api_url: 'http://localhost:8000/api',
  openrouter_api_key: '••••••••••••••••',
};

class SettingsService {
  /**
   * Get current settings
   */
  async getSettings(): Promise<Settings> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      // Return a copy to prevent direct mutation
      return { ...mockSettings };
    }

    // Real API call
    try {
      const response = await api.get<Settings>('/settings');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Update settings
   */
  async updateSettings(data: UpdateSettingsRequest): Promise<Settings> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      // Update mock settings
      Object.assign(mockSettings, data);
      return { ...mockSettings };
    }

    // Real API call
    try {
      const response = await api.put<Settings>('/settings', data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Reset settings to defaults
   */
  async resetSettings(): Promise<Settings> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      // Reset to default values
      Object.assign(mockSettings, {
        project_name: 'AI Web Test v1.0',
        default_timeout: 30,
        email_notifications: true,
        slack_notifications: false,
        test_failure_alerts: true,
        ai_model: 'claude-3-opus-20240229',
        temperature: 0.7,
        max_tokens: 8192,
        parallel_runs: 3,
        retry_count: 2,
        timeout_multiplier: 1.5,
        github_webhook_url: '',
        slack_channel: '#qa-alerts',
      });
      return { ...mockSettings };
    }

    // Real API call
    try {
      const response = await api.post<Settings>('/settings/reset');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Validate settings
   */
  validateSettings(settings: Partial<Settings>): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Validate project name
    if (settings.project_name !== undefined) {
      if (settings.project_name.trim().length === 0) {
        errors.push('Project name cannot be empty');
      }
      if (settings.project_name.length > 100) {
        errors.push('Project name must be less than 100 characters');
      }
    }

    // Validate default timeout
    if (settings.default_timeout !== undefined) {
      if (settings.default_timeout < 1 || settings.default_timeout > 300) {
        errors.push('Default timeout must be between 1 and 300 seconds');
      }
    }

    // Validate temperature
    if (settings.temperature !== undefined) {
      if (settings.temperature < 0 || settings.temperature > 2) {
        errors.push('Temperature must be between 0 and 2');
      }
    }

    // Validate max tokens
    if (settings.max_tokens !== undefined) {
      if (settings.max_tokens < 100 || settings.max_tokens > 100000) {
        errors.push('Max tokens must be between 100 and 100,000');
      }
    }

    // Validate parallel runs
    if (settings.parallel_runs !== undefined) {
      if (settings.parallel_runs < 1 || settings.parallel_runs > 10) {
        errors.push('Parallel runs must be between 1 and 10');
      }
    }

    // Validate retry count
    if (settings.retry_count !== undefined) {
      if (settings.retry_count < 0 || settings.retry_count > 5) {
        errors.push('Retry count must be between 0 and 5');
      }
    }

    // Validate timeout multiplier
    if (settings.timeout_multiplier !== undefined) {
      if (settings.timeout_multiplier < 1 || settings.timeout_multiplier > 5) {
        errors.push('Timeout multiplier must be between 1 and 5');
      }
    }

    // Validate GitHub webhook URL
    if (settings.github_webhook_url !== undefined && settings.github_webhook_url.trim() !== '') {
      try {
        new URL(settings.github_webhook_url);
      } catch {
        errors.push('GitHub webhook URL must be a valid URL');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Get user's AI provider settings (Sprint 3)
   */
  async getUserProviderSettings(): Promise<any> {
    // Real API call (no mock for Sprint 3 feature)
    try {
      const response = await api.get('/settings/provider');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Update user's AI provider settings (Sprint 3)
   */
  async updateUserProviderSettings(data: any): Promise<any> {
    // Real API call (no mock for Sprint 3 feature)
    try {
      const response = await api.put('/settings/provider', data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get available AI providers (Sprint 3)
   */
  async getAvailableProviders(): Promise<any> {
    // Real API call (no mock for Sprint 3 feature)
    try {
      const response = await api.get('/settings/available-providers');
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete user provider settings (reset to defaults)
   */
  async deleteUserProviderSettings(): Promise<void> {
    try {
      await api.delete('/settings/provider');
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new SettingsService();

