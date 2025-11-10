export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  user: User;
  token: string;
}

