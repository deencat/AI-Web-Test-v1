import api, { apiHelpers } from './api';
import { LoginRequest, LoginResponse, User } from '../types/api';
import { mockLogin } from '../mock/users';

/**
 * Authentication Service
 * Handles login, logout, and user session management
 */

class AuthService {
  /**
   * Login user
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const mockUser = mockLogin(username, password);
      if (mockUser) {
        const token = `mock-token-${Date.now()}`;
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(mockUser));
        
        return {
          token,
          user: mockUser,
        };
      } else {
        throw new Error('Invalid credentials');
      }
    }

    // Real API call
    try {
      // FastAPI OAuth2 expects form data, not JSON
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post<{ access_token: string; token_type: string }>(
        '/auth/login',
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );

      // Store token
      const token = response.data.access_token;
      localStorage.setItem('token', token);

      // Fetch user data using the token
      const userResponse = await api.get<User>('/auth/me');
      localStorage.setItem('user', JSON.stringify(userResponse.data));

      return {
        token,
        user: userResponse.data,
      };
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return;
    }

    // Real API call
    try {
      await api.post('/auth/logout');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } catch (error) {
      // Still clear local storage even if API call fails
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }

  /**
   * Get current user from localStorage
   */
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;

    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  /**
   * Get authentication token
   */
  getToken(): string | null {
    return localStorage.getItem('token');
  }

  /**
   * Refresh user data from API
   */
  async refreshUser(): Promise<User> {
    // Use mock data if configured
    if (apiHelpers.useMockData()) {
      const currentUser = this.getCurrentUser();
      if (currentUser) {
        return currentUser;
      }
      throw new Error('No user logged in');
    }

    // Real API call
    try {
      const response = await api.get<User>('/auth/me');
      localStorage.setItem('user', JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      throw new Error(apiHelpers.getErrorMessage(error));
    }
  }
}

export default new AuthService();

