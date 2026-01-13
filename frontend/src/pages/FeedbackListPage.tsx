/**
 * Feedback List Page
 * View and manage all execution feedback with advanced filtering
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import feedbackService, { ExecutionFeedbackListItem, FeedbackStats } from '../services/feedbackService';

export function FeedbackListPage() {
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState<ExecutionFeedbackListItem[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [failureType, setFailureType] = useState<string>('');
  const [correctionSource, setCorrectionSource] = useState<string>('');
  const [isAnomaly, setIsAnomaly] = useState<boolean | undefined>(undefined);
  const [hasCorrection, setHasCorrection] = useState<boolean | undefined>(undefined);

  // Pagination
  const [skip, setSkip] = useState(0);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchFeedback();
    fetchStats();
  }, [skip, failureType, correctionSource, isAnomaly, hasCorrection]);

  const fetchFeedback = async () => {
    setIsLoading(true);
    try {
      const response = await feedbackService.listFeedback({
        skip,
        limit,
        failure_type: failureType || undefined,
        correction_source: correctionSource || undefined,
        is_anomaly: isAnomaly,
        has_correction: hasCorrection
      });
      setFeedback(response.items);
      setTotal(response.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch feedback');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await feedbackService.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const handleClearFilters = () => {
    setFailureType('');
    setCorrectionSource('');
    setIsAnomaly(undefined);
    setHasCorrection(undefined);
    setSkip(0);
  };

  const handleViewExecution = (executionId: number) => {
    navigate(`/executions/${executionId}`);
  };

  const nextPage = () => setSkip(skip + limit);
  const prevPage = () => setSkip(Math.max(0, skip - limit));

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Execution Feedback</h1>
          <Button variant="secondary" size="md" onClick={fetchFeedback}>
            ↻ Refresh
          </Button>
        </div>

        {/* Statistics Dashboard */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <StatsCard title="Total Feedback" value={stats.total_feedback} />
            <StatsCard title="Total Failures" value={stats.total_failures} color="red" />
            <StatsCard title="Corrected" value={stats.total_corrected} color="green" />
            <StatsCard title="Anomalies" value={stats.total_anomalies} color="purple" />
            <StatsCard
              title="Correction Rate"
              value={`${stats.correction_rate.toFixed(1)}%`}
              color={stats.correction_rate > 50 ? 'green' : 'yellow'}
            />
          </div>
        )}

        {/* Filters */}
        <Card className="p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Failure Type</label>
              <select
                value={failureType}
                onChange={(e) => {
                  setFailureType(e.target.value);
                  setSkip(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">All Types</option>
                <option value="selector_not_found">Selector Not Found</option>
                <option value="timeout">Timeout</option>
                <option value="assertion_failed">Assertion Failed</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Correction Source</label>
              <select
                value={correctionSource}
                onChange={(e) => {
                  setCorrectionSource(e.target.value);
                  setSkip(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">All Sources</option>
                <option value="human">Human</option>
                <option value="ai_suggestion">AI Suggestion</option>
                <option value="auto_applied">Auto-Applied</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Anomaly Status</label>
              <select
                value={isAnomaly === undefined ? '' : isAnomaly ? 'true' : 'false'}
                onChange={(e) => {
                  const value = e.target.value;
                  setIsAnomaly(value === '' ? undefined : value === 'true');
                  setSkip(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">All</option>
                <option value="true">Anomalies Only</option>
                <option value="false">Normal Only</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Correction Status</label>
              <select
                value={hasCorrection === undefined ? '' : hasCorrection ? 'true' : 'false'}
                onChange={(e) => {
                  const value = e.target.value;
                  setHasCorrection(value === '' ? undefined : value === 'true');
                  setSkip(0);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">All</option>
                <option value="true">Corrected Only</option>
                <option value="false">Uncorrected Only</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex justify-end">
            <Button variant="secondary" size="sm" onClick={handleClearFilters}>
              Clear Filters
            </Button>
          </div>
        </Card>

        {/* Feedback List */}
        <Card>
          {isLoading && (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <span className="ml-3 text-gray-600">Loading feedback...</span>
            </div>
          )}

          {error && (
            <div className="p-6 text-red-600">
              <p className="font-semibold">Error loading feedback</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {!isLoading && !error && feedback.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              <p>No feedback entries found</p>
              <p className="text-sm mt-1">Try adjusting your filters</p>
            </div>
          )}

          {!isLoading && !error && feedback.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Execution</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Failure Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {feedback.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">#{item.id}</td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => handleViewExecution(item.execution_id)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Exec #{item.execution_id}
                          </button>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          {item.failure_type && (
                            <span className="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-800">
                              {item.failure_type.replace(/_/g, ' ')}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-700 max-w-xs truncate">
                          {item.error_message || '-'}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="flex gap-1">
                            {item.is_anomaly && (
                              <span className="px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                                Anomaly
                              </span>
                            )}
                            {item.correction_source && (
                              <span className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-800">
                                Corrected
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(item.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-right text-sm">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleViewExecution(item.execution_id)}
                          >
                            View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="px-4 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} results
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={prevPage} disabled={skip === 0}>
                    ← Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={nextPage}
                    disabled={skip + limit >= total}
                  >
                    Next →
                  </Button>
                </div>
              </div>
            </>
          )}
        </Card>
      </div>
    </Layout>
  );
}

// ============================================================================
// Stats Card Component
// ============================================================================

interface StatsCardProps {
  title: string;
  value: number | string;
  color?: 'red' | 'green' | 'purple' | 'yellow';
}

function StatsCard({ title, value, color }: StatsCardProps) {
  const colorClasses = {
    red: 'bg-red-100 text-red-800',
    green: 'bg-green-100 text-green-800',
    purple: 'bg-purple-100 text-purple-800',
    yellow: 'bg-yellow-100 text-yellow-800'
  };

  const bgClass = color ? colorClasses[color] : 'bg-gray-100 text-gray-800';

  return (
    <Card className="p-4">
      <div className="text-sm text-gray-600 mb-1">{title}</div>
      <div className={`text-2xl font-bold ${bgClass} px-2 py-1 rounded inline-block`}>
        {value}
      </div>
    </Card>
  );
}
