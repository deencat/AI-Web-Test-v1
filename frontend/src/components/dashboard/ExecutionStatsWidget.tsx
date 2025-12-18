import { useEffect, useState } from 'react';
import { Card } from '../common/Card';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import executionService from '../../services/executionService';
import type { ExecutionStatistics } from '../../types/execution';

export function ExecutionStatsWidget() {
  const [stats, setStats] = useState<ExecutionStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const data = await executionService.getStatistics();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
          <span className="ml-3 text-gray-600">Loading statistics...</span>
        </div>
      </Card>
    );
  }

  if (error || !stats) {
    return (
      <Card className="p-6 border-red-200 bg-red-50">
        <p className="text-red-700">{error || 'No statistics available'}</p>
      </Card>
    );
  }

  // Prepare data for charts
  const statusData = Object.entries(stats.by_status).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const resultData = Object.entries(stats.by_result).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const browserData = Object.entries(stats.by_browser || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const environmentData = Object.entries(stats.by_environment || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const timeSeriesData = [
    { period: 'Last 24h', executions: stats.executions_last_24h },
    { period: 'Last 7d', executions: stats.executions_last_7d },
    { period: 'Last 30d', executions: stats.executions_last_30d },
  ];

  // Colors for charts
  const STATUS_COLORS = {
    Pending: '#f59e0b',
    Running: '#3b82f6',
    Completed: '#10b981',
    Failed: '#ef4444',
    Cancelled: '#6b7280',
  };

  const RESULT_COLORS = {
    Pass: '#10b981',
    Fail: '#ef4444',
    Error: '#f97316',
    Skip: '#6b7280',
  };

  const getStatusColor = (name: string) =>
    STATUS_COLORS[name as keyof typeof STATUS_COLORS] || '#6b7280';

  const getResultColor = (name: string) =>
    RESULT_COLORS[name as keyof typeof RESULT_COLORS] || '#6b7280';

  return (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Executions</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_executions}</p>
            </div>
            <div className="text-4xl">📊</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pass Rate</p>
              <p className="text-3xl font-bold text-green-600">{stats.pass_rate.toFixed(1)}%</p>
            </div>
            <div className="text-4xl">✅</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Duration</p>
              <p className="text-3xl font-bold text-blue-600">
                {stats.average_duration_seconds?.toFixed(1) || '0.0'}s
              </p>
            </div>
            <div className="text-4xl">⏱️</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Time</p>
              <p className="text-3xl font-bold text-purple-600">
                {stats.total_duration_hours.toFixed(1)}h
              </p>
            </div>
            <div className="text-4xl">🕐</div>
          </div>
        </Card>
      </div>

      {/* Charts Row 1: Status and Result Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution Pie Chart */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${((percent || 0) * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getStatusColor(entry.name)} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 flex flex-wrap justify-center gap-4">
            {statusData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: getStatusColor(item.name) }}
                />
                <span className="text-sm text-gray-700">
                  {item.name}: {item.value}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Result Distribution Pie Chart */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Result Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={resultData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${((percent || 0) * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {resultData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getResultColor(entry.name)} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 flex flex-wrap justify-center gap-4">
            {resultData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: getResultColor(item.name) }}
                />
                <span className="text-sm text-gray-700">
                  {item.name}: {item.value}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Charts Row 2: Browser and Environment Distribution */}
      {(browserData.length > 0 || environmentData.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Browser Distribution Bar Chart */}
          {browserData.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Browser Distribution
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={browserData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" name="Executions" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Environment Distribution Bar Chart */}
          {environmentData.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Environment Distribution
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={environmentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#10b981" name="Executions" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}

      {/* Time Series Line Chart */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Executions Over Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={timeSeriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="executions"
              stroke="#8b5cf6"
              strokeWidth={2}
              name="Executions"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Most Executed Tests */}
      {stats.most_executed_tests && stats.most_executed_tests.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Most Executed Tests</h3>
          <div className="space-y-3">
            {stats.most_executed_tests.map((test, index) => (
              <div
                key={test.test_case_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-gray-400">#{index + 1}</span>
                  <div>
                    <p className="font-medium text-gray-900">{test.test_case_title}</p>
                    <p className="text-sm text-gray-600">Test ID: {test.test_case_id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-blue-600">{test.execution_count}</p>
                  <p className="text-xs text-gray-500">executions</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
