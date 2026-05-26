/**
 * RunTestButton — Sprint 10.14 update
 *
 * When the test case has `requires_runtime_credentials = true`, the button shows
 * a CredentialPromptModal before dispatching the execution request.
 *
 * Credentials are sourced from EphemeralCredentialContext (session-level cache)
 * and cleared from component state immediately after POST dispatch.
 * They are NEVER written to localStorage, sessionStorage, or any store.
 */
import { useState } from 'react';
import { Button } from './common/Button';
import { CredentialPromptModal, CredentialPromptResult } from './CredentialPromptModal';
import { useEphemeralCredentials } from '../context/EphemeralCredentialContext';
import executionService from '../services/executionService';
import { isUatUrl } from '../utils/urlUtils';

interface RunTestButtonProps {
  testCaseId: number;
  testCaseName?: string;
  testUrl?: string;
  onExecutionStart?: (executionId: number) => void;
  disabled?: boolean;
  className?: string;
  /** Sprint 10.14: when true, prompt for CRM credentials before each run */
  requiresRuntimeCredentials?: boolean;
}

export function RunTestButton({
  testCaseId,
  testCaseName,
  testUrl = '',
  onExecutionStart,
  disabled = false,
  className = '',
  requiresRuntimeCredentials = false,
}: RunTestButtonProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [showCredentialModal, setShowCredentialModal] = useState(false);

  // Session-level credential cache (never persisted)
  const { credentials: cachedCredentials, setCredentials } = useEphemeralCredentials();

  const dispatchExecution = async (loginCredentials?: { username: string; password: string }) => {
    setIsRunning(true);
    try {
      const response = await executionService.startExecution(testCaseId, {
        browser: 'chromium',
        environment: 'dev',
        base_url: testUrl || 'https://web.three.com.hk',
        triggered_by: 'manual',
        ...(loginCredentials ? { login_credentials: loginCredentials } : {}),
      });

      console.log(`Test ${testCaseName || testCaseId} queued for execution`, response);

      if (onExecutionStart) {
        onExecutionStart(response.id);
      }
    } catch (error) {
      console.error('Failed to start execution:', error);
      alert(error instanceof Error ? error.message : 'Failed to start execution');
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunTest = async () => {
    if (!requiresRuntimeCredentials) {
      await dispatchExecution();
      return;
    }

    // Re-use cached credentials from this tab session without re-prompting
    if (cachedCredentials) {
      await dispatchExecution(cachedCredentials);
      return;
    }

    // No cached credentials — show the prompt modal
    setShowCredentialModal(true);
  };

  const handleCredentialConfirm = async (result: CredentialPromptResult) => {
    setShowCredentialModal(false);
    // Cache for subsequent runs within the same tab session
    setCredentials(result);
    await dispatchExecution(result);
  };

  const handleCredentialCancel = () => {
    setShowCredentialModal(false);
  };

  return (
    <div>
      <Button
        variant="primary"
        size="md"
        onClick={handleRunTest}
        disabled={disabled || isRunning}
        className={className}
        data-testid="run-test-button"
      >
        {isRunning ? (
          <>
            <span className="inline-block animate-spin mr-2">⚙</span>
            Queuing...
          </>
        ) : (
          <>
            <span className="mr-2">▶</span>
            Run Test
          </>
        )}
      </Button>

      {/* CRM credential required badge */}
      {requiresRuntimeCredentials && (
        <span
          className="block mt-1 text-xs text-amber-600 dark:text-amber-400"
          data-testid="crm-required-badge"
        >
          🔐 Login required
        </span>
      )}

      {/* UAT auto-credential badge */}
      {!requiresRuntimeCredentials && isUatUrl(testUrl) && (
        <span className="block mt-1 text-xs text-blue-600 dark:text-blue-400">
          🔐 UAT credentials auto-applied
        </span>
      )}

      {/* Credential prompt modal */}
      {showCredentialModal && (
        <CredentialPromptModal
          testCaseName={testCaseName}
          initialUsername={cachedCredentials?.username ?? ''}
          onConfirm={handleCredentialConfirm}
          onCancel={handleCredentialCancel}
        />
      )}
    </div>
  );
}

