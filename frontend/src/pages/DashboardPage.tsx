import React, { useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { mockDashboardStats, mockTests, mockAgentActivity } from '../mock/tests';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState(mockDashboardStats);
  const [recentTests, setRecentTests] = useState(mockTests.slice(0, 5));
  const [agentActivity, setAgentActivity] = useState(mockAgentActivity);

  useEffect(() => {
    // Simulate loading data
    setStats(mockDashboardStats);
    setRecentTests(mockTests.slice(0, 5));
    setAgentActivity(mockAgentActivity);
  }, []);

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here's your test overview.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Tests</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total_tests}</p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Passed</p>
                <p className="text-3xl font-bold text-success">{stats.passed}</p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Failed</p>
                <p className="text-3xl font-bold text-danger">{stats.failed}</p>
              </div>
              <div className="text-4xl">❌</div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Agents</p>
                <p className="text-3xl font-bold text-primary">{stats.active_agents}</p>
              </div>
              <div className="text-4xl">🤖</div>
            </div>
          </Card>
        </div>

        {/* Recent Test Results */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Test Results</h2>
          <div className="space-y-3">
            {recentTests.map((test) => (
              <div
                key={test.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    test.status === 'passed' ? 'bg-success' :
                    test.status === 'failed' ? 'bg-danger' :
                    'bg-warning animate-pulse'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900">{test.name}</p>
                    <p className="text-sm text-gray-600">{test.id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {test.status === 'running' ? 'Running...' : `${test.execution_time}s`}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(test.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Agent Activity */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Agent Activity</h2>
          <div className="space-y-3">
            {agentActivity.map((activity) => (
              <div
                key={activity.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'active' ? 'bg-success animate-pulse' :
                    'bg-gray-400'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-900">{activity.agent}</p>
                    <p className="text-sm text-gray-600">{activity.current_task}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 capitalize">{activity.status}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

