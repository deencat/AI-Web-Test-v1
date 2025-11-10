export const mockUsers = [
  {
    id: '1',
    email: 'admin@aiwebtest.com',
    username: 'admin',
    full_name: 'Admin User',
    is_active: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    email: 'qa@aiwebtest.com',
    username: 'qa_engineer',
    full_name: 'QA Engineer',
    is_active: true,
    created_at: '2025-01-02T00:00:00Z',
  },
];

// Mock login function
export const mockLogin = (username: string, _password: string) => {
  // Accept any username/password for prototyping (password intentionally unused in mock)
  const user = mockUsers.find(u => u.username === username) || mockUsers[0];
  return {
    success: true,
    user,
    token: 'mock-jwt-token-' + Date.now(),
  };
};

