import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, FileText, Database, Settings, PlayCircle, FolderOpen, Bot, Library, Globe, MessageSquare, Map, ListOrdered, Stethoscope, Layers, Package } from 'lucide-react';
import { isAdmin, isFactoryOperator, ADMIN_ONLY_PATHS } from '../../utils/roles';

const navItems = [
  { path: '/dashboard', icon: Home, label: 'Dashboard' },
  { path: '/products', icon: Package, label: 'Products' },
  { path: '/tests', icon: FileText, label: 'Tests' },
  { path: '/step-library', icon: Library, label: 'Step Library' },
  { path: '/crawl-and-save', icon: Globe, label: 'Crawl & Save' },
  { path: '/test-suites', icon: FolderOpen, label: 'Test Suites' },
  { path: '/executions', icon: PlayCircle, label: 'Executions' },
  { path: '/knowledge-base', icon: Database, label: 'Knowledge Base' },
  { path: '/programs', icon: Layers, label: 'Programs (admin)' },
  { path: '/agent-workflow', icon: Bot, label: 'Agent Workflow' },
  { path: '/agent-console', icon: MessageSquare, label: 'Agent Console' },
  { path: '/journey-registry', icon: Map, label: 'Journey Registry' },
  { path: '/backlog', icon: ListOrdered, label: 'Backlog' },
  { path: '/heal-review', icon: Stethoscope, label: 'Heal Review' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

const FACTORY_OPERATOR_PATHS = new Set(['/agent-console']);

export const Sidebar: React.FC = () => {
  const factoryOperator = isFactoryOperator();
  const admin = isAdmin();
  const visibleItems = navItems.filter((item) => {
    if (!factoryOperator && FACTORY_OPERATOR_PATHS.has(item.path)) return false;
    if (!admin && ADMIN_ONLY_PATHS.has(item.path)) return false;
    return true;
  });

  return (
    <aside className="w-64 bg-white border-r border-gray-200 fixed left-0 top-16 bottom-0 z-40">
      <nav className="p-4 space-y-2">
        {visibleItems.map((item) => (
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
