import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK !== 'false'; // Default to true

// Derive the server origin from VITE_API_URL (strips /api/v1 or any sub-path).
// Used by the v2 client so requests go to /api/v2/... not /api/v1/api/v2/...
const API_ORIGIN = new URL(API_BASE_URL).origin; // e.g. http://127.0.0.1:8000

function addInterceptors(instance: AxiosInstance): void {
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = localStorage.getItem('token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: AxiosError) => Promise.reject(error)
  );

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
          window.location.href = '/login';
        }
      }
      if (error.response?.status === 403) console.error('Access forbidden:', error.response.data);
      if (error.response?.status === 500) console.error('Server error:', error.response.data);
      if (!error.response) console.error('Network error:', error.message);
      return Promise.reject(error);
    }
  );
}

// v1 Axios instance (legacy API)
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds - increased for AI test generation which can be slow
  headers: {
    'Content-Type': 'application/json',
  },
});

// v2 Axios instance — baseURL is the server origin only (/api/v2 paths are added by the service)
export const apiV2: AxiosInstance = axios.create({
  baseURL: API_ORIGIN,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

addInterceptors(apiV2);

// Apply interceptors to the legacy v1 instance
addInterceptors(api);

// API Helper functions
export const apiHelpers = {
  /**
   * Check if we should use mock data
   */
  useMockData(): boolean {
    return USE_MOCK_DATA;
  },

  /**
   * Get error message from API error
   */
  getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
      return (
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        'An error occurred'
      );
    }
    return 'An unexpected error occurred';
  },

  /**
   * Format API error for display
   */
  formatError(error: unknown): { message: string; details?: string } {
    if (axios.isAxiosError(error)) {
      return {
        message:
          error.response?.data?.message ||
          error.response?.data?.detail ||
          error.message ||
          'An error occurred',
        details:
          error.response?.data?.details ||
          error.response?.data?.statusText ||
          error.response?.statusText,
      };
    }
    return { message: 'An unexpected error occurred' };
  },
};

export default api;

