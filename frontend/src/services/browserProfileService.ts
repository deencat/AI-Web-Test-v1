/**
 * Browser Profile Service
 * Created: February 3, 2026
 * Purpose: API client for Browser Profile Session Persistence
 */

import api, { apiHelpers } from './api';
import {
  BrowserProfile,
  BrowserProfileCreate,
  BrowserProfileUpdate,
  BrowserProfileListResponse,
  BrowserProfileExportRequest,
  BrowserProfileUploadResponse
} from '../types/browserProfile';

class BrowserProfileService {
  private baseURL = '/browser-profiles';

  /**
   * Get all browser profiles for current user
   */
  async getAllProfiles(): Promise<BrowserProfileListResponse> {
    try {
      const response = await api.get<BrowserProfileListResponse>(this.baseURL);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get browser profile by ID
   */
  async getProfile(profileId: number): Promise<BrowserProfile> {
    try {
      const response = await api.get<BrowserProfile>(`${this.baseURL}/${profileId}`);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Create new browser profile
   */
  async createProfile(data: BrowserProfileCreate): Promise<BrowserProfile> {
    try {
      const response = await api.post<BrowserProfile>(this.baseURL, data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Update browser profile
   */
  async updateProfile(profileId: number, data: BrowserProfileUpdate): Promise<BrowserProfile> {
    try {
      const response = await api.patch<BrowserProfile>(`${this.baseURL}/${profileId}`, data);
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Delete browser profile
   */
  async deleteProfile(profileId: number): Promise<void> {
    try {
      await api.delete(`${this.baseURL}/${profileId}`);
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Export browser profile from debug session
   * Downloads profile as ZIP file
   */
  async exportProfile(profileId: number, sessionId: string): Promise<Blob> {
    try {
      const response = await api.post(
        `${this.baseURL}/${profileId}/export`,
        { session_id: sessionId } as BrowserProfileExportRequest,
        {
          responseType: 'blob', // Important for file download
        }
      );
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Upload browser profile ZIP file
   * Returns profile data for use in test execution
   */
  async uploadProfile(file: File): Promise<BrowserProfileUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post<BrowserProfileUploadResponse>(
        `${this.baseURL}/upload`,
        formData,
        {
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
   * Download profile export as file
   * Helper method to trigger browser download
   */
  downloadProfileBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Format profile name for filename
   */
  getProfileFilename(profile: BrowserProfile): string {
    const safeName = profile.profile_name.replace(/[^a-z0-9]/gi, '_');
    return `profile_${profile.id}_${safeName}.zip`;
  }

  /**
   * Get OS icon/emoji
   */
  getOSIcon(osType: string): string {
    const icons: Record<string, string> = {
      windows: '🪟',
      linux: '🐧',
      macos: '🍎',
    };
    return icons[osType] || '💻';
  }

  /**
   * Get browser icon/emoji
   */
  getBrowserIcon(browserType: string): string {
    const icons: Record<string, string> = {
      chromium: '🌐',
      firefox: '🦊',
      webkit: '🧭',
    };
    return icons[browserType] || '🌐';
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string | undefined): string {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  }
}

// Export singleton instance
export const browserProfileService = new BrowserProfileService();
export default browserProfileService;
