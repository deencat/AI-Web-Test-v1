import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bug } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DebugRangeDialog } from '../components/DebugRangeDialog';
import executionService from '../services/executionService';
import type {
  TestExecutionListItem,
  ExecutionStatus,
  ExecutionResult,
} from '../types/execution';

export function ExecutionHistoryPage() {
  const navigate = useNavigate();
  const [executions, setExecutions] = useState<TestExecutionListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedResult, setSelectedResult] = useState<string>('');
  const [debugDialogOpen, setDebugDialogOpen] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<TestExecutionListItem | null>(null);

  const fetchExecutions = async () => {
    setIsLoading(true);
    try {
      const params: any = {
        skip: 0,
        limit: 50,
      };
      if (selectedStatus) params.status = selectedStatus;
      if (selectedResult) params.result = selectedResult;

      const response = await executionService.getExecutions(params);
      setExecutions(response.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch executions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, [selectedStatus, selectedResult]);

  const handleViewExecution = (executionId: number) => {
    navigate(`/executions/${executionId}`);
  };

  const handleDeleteExecution = async (executionId: number) => {
    if (!confirm('Are you sure you want to delete this execution?')) {
      return;
    }

    try {
      await executionService.deleteExecution(executionId);
      // Refresh the list
      fetchExecutions();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete execution');
    }
  };

  const handleOpenDebugDialog = (execution: TestExecutionListItem) => {
    setSelectedExecution(execution);
    setDebugDialogOpen(true);
  };

  const handleDebugConfirm = (startStep: number, endStep: number | null, skipPrerequisites: boolean) => {
    if (!selectedExecution) return;

    // Build URL with parameters
    let url = `/debug/${selectedExecution.id}/${startStep}`;
    if (endStep) {
      url += `/${endStep}`;
    }
    url += skipPrerequisites ? '/manual' : '/auto';
    
    navigate(url);
    setDebugDialogOpen(false);
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Execution History</h1>
          <Button variant="secondary" size="md" onClick={fetchExecutions}>
            ↻ Refresh
          </Button>
        </div>

        {/* Filters */}
        <Card className="p-4">
          <div className="flex gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Result
              </label>
              <select
                value={selectedResult}
                onChange={(e) => setSelectedResult(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Results</option>
                <option value="pass">Pass</option>
                <option value="fail">Fail</option>
                <option value="error">Error</option>
                <option value="skip">Skip</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
            <span className="ml-3 text-gray-600">Loading executions...</span>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <Card className="p-6 border-red-200 bg-red-50">
            <p className="text-red-700">{error}</p>
          </Card>
        )}

        {/* Executions Table */}
        {!isLoading && !error && (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Test Case
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Result
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Steps
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Browser
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {executions.map((execution) => (
                    <tr
                      key={execution.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleViewExecution(execution.id)}
                    >
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        #{execution.id}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        Test #{execution.test_case_id}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <StatusBadge status={execution.status} />
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <ResultBadge result={execution.result} />
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className="text-green-700">{execution.passed_steps}</span> /{' '}
                        <span className="text-red-700">{execution.failed_steps}</span> /{' '}
                        <span className="text-gray-600">{execution.total_steps}</span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        {execution.duration_seconds
                          ? `${execution.duration_seconds.toFixed(1)}s`
                          : 'N/A'}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                        {execution.browser || 'N/A'}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(execution.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm space-x-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenDebugDialog(execution);
                          }}
                          className="inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-800 font-medium"
                          title="Open Debug Range Dialog"
                        >
                          <Bug className="w-4 h-4" />
                          Debug
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteExecution(execution.id);
                          }}
                          className="text-red-600 hover:text-red-800 font-medium"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {executions.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No executions found. Run some tests to see results here.
                </div>
              )}
            </div>
          </Card>
        )}
      </div>

      {/* Debug Range Dialog */}
      {selectedExecution && (
        <DebugRangeDialog
          open={debugDialogOpen}
          execution={selectedExecution}
          onConfirm={handleDebugConfirm}
          onCancel={() => setDebugDialogOpen(false)}
        />
      )}
    </Layout>
  );
}

// Helper Components
function StatusBadge({ status }: { status: ExecutionStatus }) {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-700',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-700',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
}

function ResultBadge({ result }: { result?: ExecutionResult }) {
  if (!result) {
    return <span className="text-gray-400 text-sm">N/A</span>;
  }

  const colors = {
    pass: 'bg-green-100 text-green-700',
    fail: 'bg-red-100 text-red-700',
    error: 'bg-orange-100 text-orange-700',
    skip: 'bg-gray-100 text-gray-700',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[result]}`}>
      {result.toUpperCase()}
    </span>
  );
}
