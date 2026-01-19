import React, { useState, useEffect } from 'react';
import { Card } from './common/Card';
import { Button } from './common/Button';
import { Input } from './common/Input';
import settingsService from '../services/settingsService';
import type {
  ExecutionSettings,
  ExecutionSettingsUpdate,
  StrategyInfo,
  FallbackStrategy,
} from '../types/api';

interface ExecutionSettingsPanelProps {
  onSettingsChange?: (settings: ExecutionSettings) => void;
}

export const ExecutionSettingsPanel: React.FC<ExecutionSettingsPanelProps> = ({
  onSettingsChange,
}) => {
  // State
  const [settings, setSettings] = useState<ExecutionSettings | null>(null);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // Form state
  const [selectedStrategy, setSelectedStrategy] = useState<FallbackStrategy>('option_c');
  const [timeoutPerTier, setTimeoutPerTier] = useState<number>(30);
  const [maxRetryPerTier, setMaxRetryPerTier] = useState<number>(1);
  const [trackTokenUsage, setTrackTokenUsage] = useState<boolean>(true);
  const [trackExecutionTime, setTrackExecutionTime] = useState<boolean>(true);
  const [trackSuccessRate, setTrackSuccessRate] = useState<boolean>(true);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    loadStrategies();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const data = await settingsService.getExecutionSettings();
      setSettings(data);

      // Update form state
      setSelectedStrategy(data.fallback_strategy);
      setTimeoutPerTier(data.timeout_per_tier_seconds);
      setMaxRetryPerTier(data.max_retry_per_tier);
      setTrackTokenUsage(data.track_token_usage);
      setTrackExecutionTime(data.track_execution_time);
      setTrackSuccessRate(data.track_success_rate);
    } catch (error: any) {
      console.error('Failed to load execution settings:', error);
      setSaveMessage({
        type: 'error',
        text: error.message || 'Failed to load settings',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadStrategies = async () => {
    try {
      const data = await settingsService.getExecutionStrategies();
      // API returns array directly, not wrapped in object
      setStrategies(Array.isArray(data) ? data : []);
    } catch (error: any) {
      console.error('Failed to load strategies:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);

    try {
      const updateData: ExecutionSettingsUpdate = {
        fallback_strategy: selectedStrategy,
        timeout_per_tier_seconds: timeoutPerTier,
        max_retry_per_tier: maxRetryPerTier,
        track_token_usage: trackTokenUsage,
        track_execution_time: trackExecutionTime,
        track_success_rate: trackSuccessRate,
      };

      const updated = await settingsService.updateExecutionSettings(updateData);
      setSettings(updated);

      setSaveMessage({
        type: 'success',
        text: '✅ Execution settings saved successfully!',
      });

      if (onSettingsChange) {
        onSettingsChange(updated);
      }

      setTimeout(() => setSaveMessage(null), 5000);
    } catch (error: any) {
      console.error('Failed to save execution settings:', error);
      setSaveMessage({
        type: 'error',
        text: error.message || 'Failed to save settings',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefresh = () => {
    loadSettings();
    loadStrategies();
  };

  const getCostColor = (level: string): string => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPerformanceColor = (level: string): string => {
    switch (level) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">3-Tier Execution Settings</h2>
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {/* Save Message */}
        {saveMessage && (
          <div
            className={`p-4 rounded-lg ${
              saveMessage.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {saveMessage.text}
          </div>
        )}

        {/* Fallback Strategy Selection */}
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Fallback Strategy</h3>
          <div className="space-y-4">
            {strategies.map((strategy) => (
              <div
                key={strategy.name}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedStrategy === strategy.name
                    ? 'border-blue-700 bg-blue-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }`}
                onClick={() => setSelectedStrategy(strategy.name)}
              >
                <div className="flex items-start gap-3">
                  {/* Radio Button */}
                  <input
                    type="radio"
                    checked={selectedStrategy === strategy.name}
                    onChange={() => setSelectedStrategy(strategy.name)}
                    className="mt-1 h-4 w-4 text-blue-700 focus:ring-blue-700"
                  />

                  {/* Content */}
                  <div className="flex-1">
                    {/* Title and Badges */}
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <h4 className="text-lg font-semibold text-gray-900">
                        {strategy.display_name}
                      </h4>
                      <span className={`px-2 py-1 text-xs font-medium rounded border ${getCostColor(strategy.cost_level)}`}>
                        💰 {strategy.cost_level} cost
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium rounded border ${getPerformanceColor(strategy.performance_level)}`}>
                        📈 {strategy.performance_level} performance
                      </span>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-600 mb-3">{strategy.description}</p>

                    {/* Fallback Chain */}
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-gray-700 mb-1">Fallback Chain:</p>
                      <div className="flex flex-wrap items-center gap-2">
                        {strategy.fallback_chain.map((tier, idx) => (
                          <React.Fragment key={idx}>
                            <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 border border-gray-300 rounded">
                              {tier}
                            </span>
                            {idx < strategy.fallback_chain.length - 1 && (
                              <span className="text-gray-400">→</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>

                    {/* Recommended For */}
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-gray-700">Recommended for:</p>
                      <p className="text-xs text-gray-600">{strategy.recommended_for}</p>
                    </div>

                    {/* Pros and Cons */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-semibold text-green-700 mb-1">Pros:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {strategy.pros.map((pro, idx) => (
                            <li key={idx} className="text-xs text-gray-600">
                              {pro}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-red-700 mb-1">Cons:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {strategy.cons.map((con, idx) => (
                            <li key={idx} className="text-xs text-gray-600">
                              {con}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <hr className="border-gray-300" />

        {/* Configuration Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Timeout per Tier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timeout per Tier (seconds)
            </label>
            <Input
              type="number"
              value={timeoutPerTier.toString()}
              onChange={(e) => setTimeoutPerTier(Number(e.target.value))}
              min={10}
              max={120}
              step={5}
            />
            <p className="mt-1 text-xs text-gray-500">
              Timeout for each tier execution (10-120 seconds)
            </p>
          </div>

          {/* Max Retry per Tier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Retry per Tier
            </label>
            <Input
              type="number"
              value={maxRetryPerTier.toString()}
              onChange={(e) => setMaxRetryPerTier(Number(e.target.value))}
              min={0}
              max={3}
              step={1}
            />
            <p className="mt-1 text-xs text-gray-500">Maximum retries per tier (0-3)</p>
          </div>
        </div>

        {/* Divider */}
        <hr className="border-gray-300" />

        {/* Analytics Tracking */}
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Analytics Tracking</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={trackTokenUsage}
                onChange={(e) => setTrackTokenUsage(e.target.checked)}
                className="h-4 w-4 text-blue-700 focus:ring-blue-700 border-gray-300 rounded"
              />
              <span className="text-sm font-medium text-gray-700">Track Token Usage</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={trackExecutionTime}
                onChange={(e) => setTrackExecutionTime(e.target.checked)}
                className="h-4 w-4 text-blue-700 focus:ring-blue-700 border-gray-300 rounded"
              />
              <span className="text-sm font-medium text-gray-700">Track Execution Time</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={trackSuccessRate}
                onChange={(e) => setTrackSuccessRate(e.target.checked)}
                className="h-4 w-4 text-blue-700 focus:ring-blue-700 border-gray-300 rounded"
              />
              <span className="text-sm font-medium text-gray-700">Track Success Rate</span>
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex gap-3">
          <Button variant="primary" onClick={handleSave} loading={isSaving}>
            {isSaving ? 'Saving...' : '💾 Save Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );
};
