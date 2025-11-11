import { User } from '../types/api';

export const mockUsers: User[] = [
  {
    id: '1',
    email: 'admin@aiwebtest.com',
    username: 'admin',
    role: 'admin',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    email: 'qa@aiwebtest.com',
    username: 'qa_engineer',
    role: 'qa',
    created_at: '2025-01-02T00:00:00Z',
  },
];

// Mock login function
export const mockLogin = (username: string, _password: string): User | null => {
  // Accept any username/password for prototyping (password intentionally unused in mock)
  const user = mockUsers.find(u => u.username === username) || mockUsers[0];
  return user;
};

