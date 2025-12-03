import { useEffect, useState } from 'react';
import { Card } from './common/Card';
import executionService from '../services/executionService';
import type { QueueStatus } from '../types/execution';

interface QueueStatusWidgetProps {
  refreshInterval?: number; // milliseconds, default 2000 (2 seconds)
  className?: string;
}

export function QueueStatusWidget({
  refreshInterval = 2000,
  className = '',
}: QueueStatusWidgetProps) {
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueueStatus = async () => {
    try {
      const status = await executionService.getQueueStatus();
      setQueueStatus(status);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queue status');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueStatus();

    // Set up polling
    const interval = setInterval(fetchQueueStatus, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="flex items-center justify-center p-4">
          <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-2 text-gray-600">Loading queue status...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`${className} border-red-200 bg-red-50`}>
        <div className="p-4 text-red-700">
          <span className="font-semibold">Error:</span> {error}
        </div>
      </Card>
    );
  }

  if (!queueStatus) {
    return null;
  }

  const statusColor =
    queueStatus.status === 'operational'
      ? 'text-green-700 bg-green-100'
      : 'text-red-700 bg-red-100';

  const utilizationPercentage =
    (queueStatus.total_running / queueStatus.max_concurrent) * 100;

  return (
    <Card className={className}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Execution Queue</h3>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
            {queueStatus.status === 'operational' ? '● Operational' : '● Stopped'}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Queued */}
          <div>
            <div className="text-sm text-gray-600">Queued</div>
            <div className="text-2xl font-bold text-blue-700">
              {queueStatus.total_queued}
            </div>
          </div>

          {/* Running */}
          <div>
            <div className="text-sm text-gray-600">Running</div>
            <div className="text-2xl font-bold text-green-700">
              {queueStatus.total_running} / {queueStatus.max_concurrent}
            </div>
          </div>

          {/* Completed */}
          <div>
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-2xl font-bold text-gray-700">
              {queueStatus.total_completed}
            </div>
          </div>

          {/* Utilization */}
          <div>
            <div className="text-sm text-gray-600">Utilization</div>
            <div className="text-2xl font-bold text-purple-700">
              {utilizationPercentage.toFixed(0)}%
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Execution Capacity</span>
            <span>
              {queueStatus.total_running} / {queueStatus.max_concurrent} slots used
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                queueStatus.is_under_limit ? 'bg-green-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(utilizationPercentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Warning if at capacity */}
        {!queueStatus.is_under_limit && (
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
            ⚠️ Queue at capacity. New executions will wait.
          </div>
        )}
      </div>
    </Card>
  );
}
