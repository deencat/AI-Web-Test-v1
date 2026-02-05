/**
 * Browser Profile Types
 * Created: February 3, 2026
 * Purpose: TypeScript interfaces for Browser Profile Session Persistence
 */

export interface BrowserProfile {
  id: number;
  user_id: number;
  profile_name: string;
  os_type: 'windows' | 'linux' | 'macos';
  browser_type: 'chromium' | 'firefox' | 'webkit';
  description?: string;
  created_at: string;
  updated_at: string;
  last_sync_at?: string;
  has_http_credentials?: boolean;
  http_username?: string | null;
}

export interface BrowserProfileCreate {
  profile_name: string;
  os_type: 'windows' | 'linux' | 'macos';
  browser_type: 'chromium' | 'firefox' | 'webkit';
  description?: string;
  http_username?: string;
  http_password?: string;
}

export interface BrowserProfileUpdate {
  profile_name?: string;
  os_type?: 'windows' | 'linux' | 'macos';
  browser_type?: 'chromium' | 'firefox' | 'webkit';
  description?: string;
  http_username?: string;
  http_password?: string;
  clear_http_credentials?: boolean;
}

export interface BrowserProfileListResponse {
  profiles: BrowserProfile[];
  total: number;
}

export interface BrowserProfileExportRequest {
  session_id: string;
}

export interface BrowserProfileExportResponse {
  success: boolean;
  message: string;
  profile_id: number;
  file_size_bytes: number;
  last_sync_at: string;
}

export interface BrowserProfileData {
  cookies: Array<{
    name: string;
    value: string;
    domain: string;
    path: string;
    secure?: boolean;
    httpOnly?: boolean;
    sameSite?: 'Strict' | 'Lax' | 'None';
    expires?: number;
  }>;
  localStorage: Record<string, string>;
  sessionStorage: Record<string, string>;
  exported_at: string;
}

export interface BrowserProfileUploadResponse {
  success: boolean;
  message: string;
  profile_data: BrowserProfileData;
  metadata?: {
    profile_id: number;
    profile_name: string;
    os_type: string;
    browser_type: string;
    exported_at: string;
  };
  file_size_bytes: number;
}

// UI-specific types
export interface BrowserProfileFormData {
  profile_name: string;
  os_type: string;
  browser_type: string;
  description: string;
  http_username?: string;
  http_password?: string;
}

export const OS_TYPES = [
  { value: 'windows', label: 'Windows', icon: '🪟' },
  { value: 'linux', label: 'Linux', icon: '🐧' },
  { value: 'macos', label: 'macOS', icon: '🍎' }
] as const;

export const BROWSER_TYPES = [
  { value: 'chromium', label: 'Chromium', icon: '🌐' },
  { value: 'firefox', label: 'Firefox', icon: '🦊' },
  { value: 'webkit', label: 'WebKit', icon: '🧭' }
] as const;
