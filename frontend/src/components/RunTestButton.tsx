import { useState } from 'react';
import { Button } from './common/Button';
import executionService from '../services/executionService';
import { isUatUrl } from '../utils/urlUtils';

interface RunTestButtonProps {
  testCaseId: number;
  testCaseName?: string;
  testUrl?: string;
  onExecutionStart?: (executionId: number) => void;
  disabled?: boolean;
  className?: string;
}

export function RunTestButton({
  testCaseId,
  testCaseName,
  testUrl = '',
  onExecutionStart,
  disabled = false,
  className = '',
}: RunTestButtonProps) {
  const [isRunning, setIsRunning] = useState(false);

  const handleRunTest = async () => {
    setIsRunning(true);

    try {
      const response = await executionService.startExecution(testCaseId, {
        browser: 'chromium',
        environment: 'dev',
        base_url: testUrl || 'https://web.three.com.hk',
        triggered_by: 'manual',
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

  return (
    <div>
      <Button
        variant="primary"
        size="md"
        onClick={handleRunTest}
        disabled={disabled || isRunning}
        className={className}
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
      {isUatUrl(testUrl) && (
        <span className="block mt-1 text-xs text-blue-600 dark:text-blue-400">
          🔐 UAT credentials auto-applied
        </span>
      )}
    </div>
  );
}

