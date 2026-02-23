import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, FileText, Database, Settings, PlayCircle, FolderOpen, User, Bot } from 'lucide-react';

const navItems = [
  { path: '/dashboard', icon: Home, label: 'Dashboard' },
  { path: '/tests', icon: FileText, label: 'Tests' },
  { path: '/test-suites', icon: FolderOpen, label: 'Test Suites' },
  { path: '/executions', icon: PlayCircle, label: 'Executions' },
  { path: '/knowledge-base', icon: Database, label: 'Knowledge Base' },
  { path: '/browser-profiles', icon: User, label: 'Browser Profiles' },
  { path: '/agent-workflow', icon: Bot, label: 'Agent Workflow' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 fixed left-0 top-16 bottom-0 z-40">
      <nav className="p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors font-medium ${
                isActive
                  ? 'bg-blue-700 text-white shadow-sm'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

