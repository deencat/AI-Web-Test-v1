import React, { useState, useEffect } from 'react';
import { Card } from './common/Card';
import settingsService from '../services/settingsService';
import type { TierDistributionStats, StrategyEffectivenessStats } from '../types/api';

export const TierAnalyticsPanel: React.FC = () => {
  const [tierStats, setTierStats] = useState<TierDistributionStats | null>(null);
  const [strategyStats, setStrategyStats] = useState<StrategyEffectivenessStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [tierData, strategyData] = await Promise.all([
        settingsService.getTierDistribution(),
        settingsService.getStrategyEffectiveness(),
      ]);
      setTierStats(tierData);
      setStrategyStats(strategyData.strategies || []);
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      setError(err.message || 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    loadAnalytics();
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center items-center min-h-[300px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-2 px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!tierStats || tierStats.total_executions === 0) {
    return (
      <Card>
        <div className="text-center p-8">
          <p className="text-gray-600 mb-2">No execution data available yet</p>
          <p className="text-sm text-gray-500">
            Run some tests to see tier distribution and analytics
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tier Distribution */}
      <Card>
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Tier Distribution</h2>
            <button
              onClick={handleRefresh}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Tier 1 */}
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-green-900">Tier 1: Playwright</h3>
                <span className="text-2xl">⚡</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Executions:</span>
                  <span className="font-semibold text-green-900">
                    {tierStats.tier1_executions}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Percentage:</span>
                  <span className="font-semibold text-green-900">
                    {tierStats.tier1_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Success Rate:</span>
                  <span className="font-semibold text-green-900">
                    {tierStats.tier1_success_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Avg Time:</span>
                  <span className="font-semibold text-green-900">
                    {tierStats.tier1_avg_time_ms.toFixed(0)}ms
                  </span>
                </div>
              </div>
              {/* Progress Bar */}
              <div className="mt-3 h-2 bg-green-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-600"
                  style={{ width: `${tierStats.tier1_percentage}%` }}
                ></div>
              </div>
            </div>

            {/* Tier 2 */}
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-yellow-900">Tier 2: Hybrid</h3>
                <span className="text-2xl">🔄</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-yellow-700">Executions:</span>
                  <span className="font-semibold text-yellow-900">
                    {tierStats.tier2_executions}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-yellow-700">Percentage:</span>
                  <span className="font-semibold text-yellow-900">
                    {tierStats.tier2_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-yellow-700">Success Rate:</span>
                  <span className="font-semibold text-yellow-900">
                    {tierStats.tier2_success_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-yellow-700">Avg Time:</span>
                  <span className="font-semibold text-yellow-900">
                    {tierStats.tier2_avg_time_ms.toFixed(0)}ms
                  </span>
                </div>
              </div>
              {/* Progress Bar */}
              <div className="mt-3 h-2 bg-yellow-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-yellow-600"
                  style={{ width: `${tierStats.tier2_percentage}%` }}
                ></div>
              </div>
            </div>

            {/* Tier 3 */}
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-red-900">Tier 3: Stagehand</h3>
                <span className="text-2xl">🤖</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-red-700">Executions:</span>
                  <span className="font-semibold text-red-900">
                    {tierStats.tier3_executions}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-red-700">Percentage:</span>
                  <span className="font-semibold text-red-900">
                    {tierStats.tier3_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-red-700">Success Rate:</span>
                  <span className="font-semibold text-red-900">
                    {tierStats.tier3_success_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-red-700">Avg Time:</span>
                  <span className="font-semibold text-red-900">
                    {tierStats.tier3_avg_time_ms.toFixed(0)}ms
                  </span>
                </div>
              </div>
              {/* Progress Bar */}
              <div className="mt-3 h-2 bg-red-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-600"
                  style={{ width: `${tierStats.tier3_percentage}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Executions</p>
                <p className="text-2xl font-bold text-gray-900">{tierStats.total_executions}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Tier 1 Efficiency</p>
                <p className="text-2xl font-bold text-green-700">
                  {tierStats.tier1_percentage.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Fallback Rate</p>
                <p className="text-2xl font-bold text-yellow-700">
                  {(tierStats.tier2_percentage + tierStats.tier3_percentage).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">AI Usage (Tier 3)</p>
                <p className="text-2xl font-bold text-red-700">
                  {tierStats.tier3_percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Strategy Effectiveness */}
      {strategyStats.length > 0 && (
        <Card>
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-900">Strategy Effectiveness</h2>

            <div className="space-y-4">
              {strategyStats.map((stat) => (
                <div
                  key={stat.strategy}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {stat.strategy === 'option_a'
                        ? 'Option A: Cost-Conscious'
                        : stat.strategy === 'option_b'
                        ? 'Option B: AI-First'
                        : 'Option C: Maximum Reliability'}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-3 py-1 text-sm font-medium rounded-full ${
                          stat.estimated_cost === 'low'
                            ? 'bg-green-100 text-green-800'
                            : stat.estimated_cost === 'medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        💰 {stat.estimated_cost} cost
                      </span>
                      <span
                        className={`px-3 py-1 text-sm font-medium rounded-full ${
                          stat.success_rate >= 95
                            ? 'bg-green-100 text-green-800'
                            : stat.success_rate >= 85
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        ✅ {stat.success_rate.toFixed(1)}% success
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-gray-600">Total Executions</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {stat.total_executions}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Successful</p>
                      <p className="text-lg font-semibold text-green-700">
                        {stat.successful_executions}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Failed</p>
                      <p className="text-lg font-semibold text-red-700">
                        {stat.failed_executions}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Avg Time</p>
                      <p className="text-lg font-semibold text-blue-700">
                        {stat.avg_execution_time_ms.toFixed(0)}ms
                      </p>
                    </div>
                  </div>

                  {/* Tier Distribution for this Strategy */}
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      Final Tier Distribution:
                    </p>
                    <div className="flex gap-2">
                      <div className="flex-1 bg-gray-100 rounded-lg p-2">
                        <p className="text-xs text-gray-600">Tier 1</p>
                        <p className="text-sm font-semibold text-green-700">
                          {stat.tier1_percentage.toFixed(1)}%
                        </p>
                      </div>
                      <div className="flex-1 bg-gray-100 rounded-lg p-2">
                        <p className="text-xs text-gray-600">Tier 2</p>
                        <p className="text-sm font-semibold text-yellow-700">
                          {stat.tier2_percentage.toFixed(1)}%
                        </p>
                      </div>
                      <div className="flex-1 bg-gray-100 rounded-lg p-2">
                        <p className="text-xs text-gray-600">Tier 3</p>
                        <p className="text-sm font-semibold text-red-700">
                          {stat.tier3_percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
