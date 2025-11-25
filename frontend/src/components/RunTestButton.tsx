import { useState } from 'react';
import { Button } from './common/Button';
import executionService from '../services/executionService';

interface RunTestButtonProps {
  testCaseId: number;
  testCaseName?: string;
  priority?: 1 | 5 | 10;
  onExecutionStart?: (executionId: number) => void;
  disabled?: boolean;
  className?: string;
}

export function RunTestButton({
  testCaseId,
  testCaseName,
  priority = 5,
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
        triggered_by: 'manual',
        priority,
      });

      // Show success notification
      console.log(`Test ${testCaseName || testCaseId} queued for execution`, response);
      
      // Notify parent component
      if (onExecutionStart) {
        onExecutionStart(response.id);
      }

      // Optional: Navigate to execution detail page
      // navigate(`/executions/${response.id}`);
    } catch (error) {
      console.error('Failed to start execution:', error);
      alert(error instanceof Error ? error.message : 'Failed to start execution');
    } finally {
      setIsRunning(false);
    }
  };

  return (
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
  );
}
