import React from 'react';
import { useNavigate } from 'react-router-dom';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8 fixed top-0 left-0 right-0 z-50">
      <div className="flex items-center gap-3">
        <span className="text-2xl">🤖</span>
        <span className="text-xl font-bold text-gray-900">AI Web Test</span>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{user?.full_name || 'User'}</span>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          Logout
        </button>
      </div>
    </header>
  );
};

