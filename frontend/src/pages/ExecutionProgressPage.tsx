import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { ScreenshotGallery } from '../components/execution/ScreenshotGallery';
import executionService from '../services/executionService';
import type { TestExecutionDetail, ExecutionStatus, ExecutionResult } from '../types/execution';

export function ExecutionProgressPage() {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const [execution, setExecution] = useState<TestExecutionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExecutionDetail = async () => {
    if (!executionId) return;

    try {
      const data = await executionService.getExecutionDetail(Number(executionId));
      setExecution(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch execution details');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutionDetail();

    // Auto-refresh every 2 seconds while execution is running
    const shouldPoll = execution?.status === 'pending' || execution?.status === 'running';
    
    if (shouldPoll) {
      const interval = setInterval(fetchExecutionDetail, 2000);
      return () => clearInterval(interval);
    }
  }, [executionId, execution?.status]);

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-4 text-lg text-gray-600">Loading execution details...</span>
        </div>
      </Layout>
    );
  }

  if (error || !execution) {
    return (
      <Layout>
        <Card className="p-6 border-red-200 bg-red-50">
          <h2 className="text-xl font-bold text-red-700 mb-2">Error</h2>
          <p className="text-red-600">{error || 'Execution not found'}</p>
          <Button
            variant="secondary"
            size="md"
            onClick={() => navigate('/executions')}
            className="mt-4"
          >
            ← Back to Executions
          </Button>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate('/executions')}
              className="mb-2"
            >
              ← Back to Executions
            </Button>
            <h1 className="text-3xl font-bold text-gray-900">
              Execution #{execution.id}
            </h1>
            <p className="text-gray-600 mt-1">Test Case ID: {execution.test_case_id}</p>
          </div>
          <ExecutionStatusBadge status={execution.status} result={execution.result} />
        </div>

        {/* Execution Overview */}
        <Card>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Execution Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-gray-600">Status</div>
                <div className="text-lg font-semibold text-gray-900 capitalize">
                  {execution.status}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Result</div>
                <div className="text-lg font-semibold text-gray-900 capitalize">
                  {execution.result || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Duration</div>
                <div className="text-lg font-semibold text-gray-900">
                  {execution.duration_seconds ? `${execution.duration_seconds.toFixed(1)}s` : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Browser</div>
                <div className="text-lg font-semibold text-gray-900 capitalize">
                  {execution.browser || 'N/A'}
                </div>
              </div>
            </div>

            {/* Progress Summary */}
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>
                  {execution.passed_steps + execution.failed_steps} / {execution.total_steps} steps
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all"
                  style={{
                    width: `${
                      ((execution.passed_steps + execution.failed_steps) / execution.total_steps) *
                      100
                    }%`,
                  }}
                />
              </div>
              <div className="flex justify-between mt-2 text-sm">
                <span className="text-green-700">✓ {execution.passed_steps} passed</span>
                <span className="text-red-700">✗ {execution.failed_steps} failed</span>
                <span className="text-gray-600">○ {execution.skipped_steps} skipped</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Step-by-Step Progress */}
        <Card>
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Steps</h2>
            <div className="space-y-4">
              {execution.steps.map((step) => (
                <StepCard key={step.id} step={step} />
              ))}
            </div>
          </div>
        </Card>

        {/* Screenshot Gallery */}
        <ScreenshotGallery steps={execution.steps} />

        {/* Error Message (if any) */}
        {execution.error_message && (
          <Card className="border-red-200 bg-red-50">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-red-700 mb-2">Error Details</h3>
              <pre className="text-sm text-red-600 whitespace-pre-wrap">
                {execution.error_message}
              </pre>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
}

// Helper Components
interface ExecutionStatusBadgeProps {
  status: ExecutionStatus;
  result?: ExecutionResult;
}

function ExecutionStatusBadge({ status, result }: ExecutionStatusBadgeProps) {
  const getStatusColor = () => {
    if (status === 'completed') {
      return result === 'pass' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
    }
    if (status === 'running') return 'bg-blue-100 text-blue-700';
    if (status === 'failed') return 'bg-red-100 text-red-700';
    if (status === 'cancelled') return 'bg-gray-100 text-gray-700';
    return 'bg-yellow-100 text-yellow-700';
  };

  const getStatusIcon = () => {
    if (status === 'completed') return result === 'pass' ? '✓' : '✗';
    if (status === 'running') return '●';
    if (status === 'failed') return '✗';
    if (status === 'cancelled') return '○';
    return '◷';
  };

  return (
    <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusColor()}`}>
      {getStatusIcon()} {status.toUpperCase()} {result && `(${result.toUpperCase()})`}
    </span>
  );
}

interface StepCardProps {
  step: TestExecutionDetail['steps'][0];
}

function StepCard({ step }: StepCardProps) {
  const getStepResultColor = () => {
    if (step.result === 'pass') return 'border-green-200 bg-green-50';
    if (step.result === 'fail') return 'border-red-200 bg-red-50';
    if (step.result === 'error') return 'border-orange-200 bg-orange-50';
    return 'border-gray-200 bg-gray-50';
  };

  const getStepResultIcon = () => {
    if (step.result === 'pass') return '✓';
    if (step.result === 'fail') return '✗';
    if (step.result === 'error') return '⚠';
    return '○';
  };

  const getStepResultText = () => {
    if (step.result === 'pass') return 'text-green-700';
    if (step.result === 'fail') return 'text-red-700';
    if (step.result === 'error') return 'text-orange-700';
    return 'text-gray-700';
  };

  return (
    <div className={`border rounded-lg p-4 ${getStepResultColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`text-xl font-bold ${getStepResultText()}`}>
              {getStepResultIcon()}
            </span>
            <span className="font-medium text-gray-900">
              Step {step.step_number}: {step.step_description}
            </span>
          </div>
          {step.expected_result && (
            <div className="mt-2 text-sm text-gray-600">
              <span className="font-medium">Expected:</span> {step.expected_result}
            </div>
          )}
          {step.actual_result && (
            <div className="mt-1 text-sm text-gray-700">
              <span className="font-medium">Actual:</span> {step.actual_result}
            </div>
          )}
          {step.error_message && (
            <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-sm text-red-700">
              <span className="font-medium">Error:</span> {step.error_message}
            </div>
          )}
          {step.duration_seconds !== undefined && (
            <div className="mt-2 text-sm text-gray-600">
              Duration: {step.duration_seconds.toFixed(2)}s
              {step.retry_count > 0 && ` (${step.retry_count} retries)`}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
