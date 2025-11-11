import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { mockLogin } from '../mock/users';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate empty fields
    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);

    // Simulate API delay
    setTimeout(() => {
      const user = mockLogin(username, password);
      
      if (user) {
        // Generate mock token and store in localStorage
        const token = `mock-token-${Date.now()}`;
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        
        // Navigate to dashboard
        navigate('/dashboard');
      } else {
        setError('Invalid credentials');
      }
      
      setLoading(false);
    }, 500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🤖 AI Web Test
          </h1>
          <p className="text-gray-600">Intelligent Test Automation Platform</p>
        </div>

        <Card>
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            Sign In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="w-full"
            >
              Sign In
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>Demo credentials: any username/password</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

