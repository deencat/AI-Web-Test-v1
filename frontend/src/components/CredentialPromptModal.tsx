/**
 * CredentialPromptModal — Sprint 10.14
 *
 * Asks the tester for CRM login credentials before starting a test execution.
 * Security guarantees:
 * - Password field is type="password" — never rendered as plaintext.
 * - Parent component clears state immediately after the POST is dispatched.
 * - Credentials are never written to localStorage / sessionStorage.
 */

import React, { useEffect, useRef, useState } from 'react';
import { Button } from './common/Button';
import { X, Lock } from 'lucide-react';

export interface CredentialPromptResult {
  username: string;
  password: string;
}

interface CredentialPromptModalProps {
  /** Called with credentials when the user confirms. */
  onConfirm: (result: CredentialPromptResult) => void;
  /** Called when the user cancels the dialog. */
  onCancel: () => void;
  /** Pre-fill username from session cache. Password is never pre-filled. */
  initialUsername?: string;
  testCaseName?: string;
}

export const CredentialPromptModal: React.FC<CredentialPromptModalProps> = ({
  onConfirm,
  onCancel,
  initialUsername = '',
  testCaseName,
}) => {
  const [username, setUsername] = useState(initialUsername);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const usernameRef = useRef<HTMLInputElement>(null);

  // Auto-focus username field (or password if username is pre-filled)
  useEffect(() => {
    usernameRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) {
      setError('Username is required.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }
    setError(null);
    onConfirm({ username: username.trim(), password });
  };

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="crm-modal-title"
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md p-6 relative">
        {/* Close button */}
        <button
          type="button"
          onClick={onCancel}
          aria-label="Cancel and close"
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
            <Lock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <h2
              id="crm-modal-title"
              className="text-lg font-semibold text-gray-900 dark:text-gray-100"
            >
              CRM Login Required
            </h2>
            {testCaseName && (
              <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                {testCaseName}
              </p>
            )}
          </div>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-300 mb-5">
          This test requires your CRM credentials. They will be used only for this
          run and are{' '}
          <span className="font-semibold text-amber-600 dark:text-amber-400">
            never stored
          </span>{' '}
          in the system.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          {/* Username */}
          <div className="mb-4">
            <label
              htmlFor="crm-username"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Username
            </label>
            <input
              id="crm-username"
              ref={usernameRef}
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                         focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="your.name@company.com"
              data-testid="crm-username-input"
            />
          </div>

          {/* Password — always type="password" */}
          <div className="mb-5">
            <label
              htmlFor="crm-password"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Password
            </label>
            <input
              id="crm-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                         focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="••••••••"
              data-testid="crm-password-input"
            />
          </div>

          {/* Validation error */}
          {error && (
            <p
              role="alert"
              className="text-sm text-red-600 dark:text-red-400 mb-4"
              data-testid="crm-modal-error"
            >
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              size="md"
              onClick={onCancel}
              data-testid="crm-modal-cancel"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              data-testid="crm-modal-confirm"
            >
              <Lock className="w-4 h-4 mr-1" />
              Run Test
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
