import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { FeedbackDataSync } from '../components/FeedbackDataSync';
import { ExecutionSettingsPanel } from '../components/ExecutionSettingsPanel';
import { TierAnalyticsPanel } from '../components/TierAnalyticsPanel';
import settingsService from '../services/settingsService';
import type { AvailableProvider, UserSettings, ExecutionSettingsUpdate } from '../types/api';

export const SettingsPage: React.FC = () => {
  const [projectName, setProjectName] = useState('AI Web Test v1.0');
  const [defaultTimeout, setDefaultTimeout] = useState('30');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [slackNotifications, setSlackNotifications] = useState(false);
  const [testFailureAlerts, setTestFailureAlerts] = useState(true);
  
  // AI Provider Settings (Dynamic from API)
  const [availableProviders, setAvailableProviders] = useState<AvailableProvider[]>([]);
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  
  // Generation settings
  const [generationProvider, setGenerationProvider] = useState<string>('google');
  const [generationModel, setGenerationModel] = useState<string>('gemini-2.0-flash-exp');
  const [generationTemperature, setGenerationTemperature] = useState<number>(0.7);
  const [generationMaxTokens, setGenerationMaxTokens] = useState<number>(4096);
  
  // Execution settings
  const [executionProvider, setExecutionProvider] = useState<string>('google');
  const [executionModel, setExecutionModel] = useState<string>('gemini-2.0-flash-exp');
  const [executionTemperature, setExecutionTemperature] = useState<number>(0.7);
  const [executionMaxTokens, setExecutionMaxTokens] = useState<number>(4096);

  // Sprint 5.5: 3-Tier Execution Settings (from child component)
  const [executionSettingsFormState, setExecutionSettingsFormState] = useState<ExecutionSettingsUpdate | null>(null);

  // Sprint 5: Stagehand Provider settings
  const [stagehandProvider, setStagehandProvider] = useState<'python' | 'typescript'>('python');
  const [stagehandHealth, setStagehandHealth] = useState<{
    python: { status: 'healthy' | 'unhealthy' | 'checking', error?: string };
    typescript: { status: 'healthy' | 'unhealthy' | 'checking', error?: string };
  }>({
    python: { status: 'checking' },
    typescript: { status: 'checking' }
  });

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    loadStagehandSettings();
  }, []);

  const loadStagehandSettings = async () => {
    try {
      // Load current provider
      const providerRes = await settingsService.getStagehandProvider();
      setStagehandProvider(providerRes.provider);
      
      // Check health of both providers
      checkProvidersHealth();
    } catch (error: any) {
      console.error('Failed to load Stagehand settings:', error);
    }
  };

  const checkProvidersHealth = async () => {
    // Check Python
    setStagehandHealth(prev => ({ ...prev, python: { status: 'checking' } }));
    const pythonHealth = await settingsService.checkStagehandHealth('python');
    setStagehandHealth(prev => ({ 
      ...prev, 
      python: { 
        status: pythonHealth.status, 
        error: pythonHealth.error 
      } 
    }));

    // Check TypeScript
    setStagehandHealth(prev => ({ ...prev, typescript: { status: 'checking' } }));
    const typescriptHealth = await settingsService.checkStagehandHealth('typescript');
    setStagehandHealth(prev => ({ 
      ...prev, 
      typescript: { 
        status: typescriptHealth.status, 
        error: typescriptHealth.error 
      } 
    }));
  };

  const handleStagehandProviderChange = async (provider: 'python' | 'typescript') => {
    try {
      setIsSaving(true);
      await settingsService.updateStagehandProvider(provider);
      setStagehandProvider(provider);
      setSaveMessage({ 
        type: 'success', 
        text: `✅ Switched to ${provider === 'python' ? 'Python' : 'TypeScript'} Stagehand provider!` 
      });
      setTimeout(() => setSaveMessage(null), 5000);
    } catch (error: any) {
      console.error('Failed to update Stagehand provider:', error);
      setSaveMessage({ 
        type: 'error', 
        text: error.message || 'Failed to update Stagehand provider' 
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      // Load available providers
      const providersRes = await settingsService.getAvailableProviders();
      setAvailableProviders(providersRes.providers);
      
      // Load user settings
      const settings = await settingsService.getUserProviderSettings();
      setUserSettings(settings);
      
      // Update form state
      setGenerationProvider(settings.generation_provider);
      setGenerationModel(settings.generation_model);
      setGenerationTemperature(settings.generation_temperature);
      setGenerationMaxTokens(settings.generation_max_tokens);
      setExecutionProvider(settings.execution_provider);
      setExecutionModel(settings.execution_model);
      setExecutionTemperature(settings.execution_temperature);
      setExecutionMaxTokens(settings.execution_max_tokens);
    } catch (error: any) {
      console.error('Failed to load settings:', error);
      setSaveMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    setSaveMessage(null);
    
    try {
      // Save AI Provider Settings
      const updateData = {
        generation_provider: generationProvider,
        generation_model: generationModel,
        generation_temperature: generationTemperature,
        generation_max_tokens: generationMaxTokens,
        execution_provider: executionProvider,
        execution_model: executionModel,
        execution_temperature: executionTemperature,
        execution_max_tokens: executionMaxTokens
      };
      
      const updated = await settingsService.updateUserProviderSettings(updateData);
      setUserSettings(updated);
      
      // Save 3-Tier Execution Settings (if form state is available)
      if (executionSettingsFormState) {
        await settingsService.updateExecutionSettings(executionSettingsFormState);
      }
      
      setSaveMessage({ 
        type: 'success', 
        text: `✅ All settings saved successfully! Using ${generationProvider.toUpperCase()} for generation, ${executionProvider.toUpperCase()} for execution, and ${executionSettingsFormState?.fallback_strategy?.toUpperCase() || 'default'} execution strategy.` 
      });
      
      // Clear message after 5 seconds
      setTimeout(() => setSaveMessage(null), 5000);
    } catch (error: any) {
      console.error('Failed to save settings:', error);
      setSaveMessage({ 
        type: 'error', 
        text: error.message || 'Failed to save settings' 
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetSettings = async () => {
    if (!confirm('Are you sure you want to reset all AI provider settings to defaults?')) {
      return;
    }
    
    setIsLoading(true);
    try {
      // Delete user settings to reset to defaults
      await settingsService.deleteUserProviderSettings();
      
      // Reload settings
      await loadSettings();
      
      // Reset local state
      setProjectName('AI Web Test v1.0');
      setDefaultTimeout('30');
      setEmailNotifications(true);
      setSlackNotifications(false);
      setTestFailureAlerts(true);
      
      setSaveMessage({ type: 'success', text: '✅ Settings reset to defaults' });
      setTimeout(() => setSaveMessage(null), 5000);
    } catch (error: any) {
      console.error('Failed to reset settings:', error);
      setSaveMessage({ 
        type: 'error', 
        text: error.message || 'Failed to reset settings' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Get models for selected provider
  const getModelsForProvider = (providerName: string): string[] => {
    const provider = availableProviders.find(p => p.name === providerName);
    return provider?.models || [];
  };

  // Check if provider is configured
  const isProviderConfigured = (providerName: string): boolean => {
    const provider = availableProviders.find(p => p.name === providerName);
    return provider?.is_configured || false;
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading settings...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Configure application preferences and AI provider settings</p>
        </div>

        {/* Save Message */}
        {saveMessage && (
          <div className={`p-4 rounded-lg ${
            saveMessage.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <p className={`text-sm ${
              saveMessage.type === 'success' ? 'text-green-800' : 'text-red-800'
            }`}>
              {saveMessage.text}
            </p>
          </div>
        )}

        {/* General Settings */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">General Settings</h2>
          <div className="space-y-4">
            <Input
              label="Project Name"
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Enter project name"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Timeout (seconds)
              </label>
              <input
                type="number"
                value={defaultTimeout}
                onChange={(e) => setDefaultTimeout(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="30"
              />
              <p className="text-sm text-gray-600 mt-1">
                Default timeout for test execution
              </p>
            </div>
          </div>
        </Card>

        {/* Notification Settings */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Notification Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-600">Receive email alerts for important events</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={emailNotifications}
                  onChange={(e) => setEmailNotifications(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Slack Notifications</p>
                <p className="text-sm text-gray-600">Send notifications to Slack channel</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={slackNotifications}
                  onChange={(e) => setSlackNotifications(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">Test Failure Alerts</p>
                <p className="text-sm text-gray-600">Get immediate alerts when tests fail</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={testFailureAlerts}
                  onChange={(e) => setTestFailureAlerts(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>
          </div>
        </Card>

        {/* AI Provider Configuration - Test Generation */}
        <Card>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">AI Provider - Test Generation</h2>
              <p className="text-sm text-gray-600 mt-1">Configure AI model for generating test cases</p>
            </div>
            <div className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
              Dynamic Configuration
            </div>
          </div>

          <div className="space-y-4">
            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Provider
              </label>
              <div className="grid grid-cols-3 gap-3">
                {availableProviders.map((provider) => (
                  <button
                    key={provider.name}
                    onClick={() => {
                      setGenerationProvider(provider.name);
                      setGenerationModel(provider.recommended_model || provider.models[0]);
                    }}
                    disabled={!provider.is_configured}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      generationProvider === provider.name
                        ? 'border-primary bg-primary/5'
                        : provider.is_configured
                        ? 'border-gray-200 hover:border-gray-300'
                        : 'border-gray-200 opacity-50 cursor-not-allowed'
                    }`}
                  >
                    <div className="font-semibold text-gray-900">{provider.display_name}</div>
                    <div className="text-xs text-gray-600 mt-1">{provider.models.length} models</div>
                    <div className={`text-xs mt-1 font-medium ${
                      provider.is_configured ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {provider.is_configured ? '✓ Configured' : '✗ No API Key'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Model Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model
              </label>
              <select
                value={generationModel}
                onChange={(e) => setGenerationModel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              >
                {getModelsForProvider(generationProvider).map((model) => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature: {generationTemperature.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={generationTemperature}
                onChange={(e) => setGenerationTemperature(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>Precise (0.0)</span>
                <span>Creative (2.0)</span>
              </div>
            </div>

            {/* Max Tokens */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                value={generationMaxTokens}
                onChange={(e) => setGenerationMaxTokens(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                min="100"
                max="32000"
              />
            </div>
          </div>
        </Card>

        {/* AI Provider Configuration - Test Execution */}
        <Card>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">AI Provider - Test Execution</h2>
              <p className="text-sm text-gray-600 mt-1">Configure AI model for browser automation (Stagehand/Playwright)</p>
            </div>
            <div className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
              Dynamic Configuration
            </div>
          </div>

          <div className="space-y-4">
            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Provider
              </label>
              <div className="grid grid-cols-3 gap-3">
                {availableProviders.map((provider) => (
                  <button
                    key={provider.name}
                    onClick={() => {
                      setExecutionProvider(provider.name);
                      setExecutionModel(provider.recommended_model || provider.models[0]);
                    }}
                    disabled={!provider.is_configured}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      executionProvider === provider.name
                        ? 'border-primary bg-primary/5'
                        : provider.is_configured
                        ? 'border-gray-200 hover:border-gray-300'
                        : 'border-gray-200 opacity-50 cursor-not-allowed'
                    }`}
                  >
                    <div className="font-semibold text-gray-900">{provider.display_name}</div>
                    <div className="text-xs text-gray-600 mt-1">{provider.models.length} models</div>
                    <div className={`text-xs mt-1 font-medium ${
                      provider.is_configured ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {provider.is_configured ? '✓ Configured' : '✗ No API Key'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Model Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model
              </label>
              <select
                value={executionModel}
                onChange={(e) => setExecutionModel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white"
              >
                {getModelsForProvider(executionProvider).map((model) => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature: {executionTemperature.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={executionTemperature}
                onChange={(e) => setExecutionTemperature(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>Precise (0.0)</span>
                <span>Creative (2.0)</span>
              </div>
            </div>

            {/* Max Tokens */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                value={executionMaxTokens}
                onChange={(e) => setExecutionMaxTokens(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                min="100"
                max="32000"
              />
            </div>
          </div>
        </Card>

        {/* Sprint 5: Stagehand Provider Selection */}
        <Card>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Stagehand Provider</h2>
              <p className="text-sm text-gray-600 mt-1">Choose browser automation implementation</p>
            </div>
            <div className="flex gap-2">
              <div className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                Sprint 5
              </div>
              <button
                onClick={checkProvidersHealth}
                className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full hover:bg-gray-200 transition-colors"
              >
                🔄 Check Health
              </button>
            </div>
          </div>

          {/* Provider Selection */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            {/* Python Stagehand */}
            <button
              onClick={() => handleStagehandProviderChange('python')}
              disabled={isSaving || stagehandHealth.python.status === 'unhealthy'}
              className={`p-6 rounded-lg border-2 transition-all text-left ${
                stagehandProvider === 'python'
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                  : stagehandHealth.python.status === 'unhealthy'
                  ? 'border-gray-200 opacity-50 cursor-not-allowed'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🐍</span>
                  <h3 className="text-lg font-semibold text-gray-900">Python Stagehand</h3>
                </div>
                {stagehandProvider === 'python' && (
                  <span className="px-2 py-1 bg-blue-500 text-white text-xs font-medium rounded">
                    Active
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-600 mb-3">
                Built-in Python implementation with @browserbasehq/stagehand
              </p>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                {stagehandHealth.python.status === 'checking' && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <span className="animate-spin">⏳</span>
                    Checking...
                  </span>
                )}
                {stagehandHealth.python.status === 'healthy' && (
                  <span className="flex items-center gap-1 text-xs text-green-600">
                    <span>✓</span>
                    Healthy
                  </span>
                )}
                {stagehandHealth.python.status === 'unhealthy' && (
                  <span className="flex items-center gap-1 text-xs text-red-600">
                    <span>✗</span>
                    Unavailable
                  </span>
                )}
              </div>
            </button>

            {/* TypeScript Stagehand */}
            <button
              onClick={() => handleStagehandProviderChange('typescript')}
              disabled={isSaving || stagehandHealth.typescript.status === 'unhealthy'}
              className={`p-6 rounded-lg border-2 transition-all text-left ${
                stagehandProvider === 'typescript'
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                  : stagehandHealth.typescript.status === 'unhealthy'
                  ? 'border-gray-200 opacity-50 cursor-not-allowed'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">⚡</span>
                  <h3 className="text-lg font-semibold text-gray-900">TypeScript Stagehand</h3>
                </div>
                {stagehandProvider === 'typescript' && (
                  <span className="px-2 py-1 bg-blue-500 text-white text-xs font-medium rounded">
                    Active
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-600 mb-3">
                Node.js microservice with native @browserbasehq/stagehand
              </p>

              {/* Status Badge */}
              <div className="flex items-center gap-2">
                {stagehandHealth.typescript.status === 'checking' && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <span className="animate-spin">⏳</span>
                    Checking...
                  </span>
                )}
                {stagehandHealth.typescript.status === 'healthy' && (
                  <span className="flex items-center gap-1 text-xs text-green-600">
                    <span>✓</span>
                    Healthy - Port 3001
                  </span>
                )}
                {stagehandHealth.typescript.status === 'unhealthy' && (
                  <div className="flex flex-col gap-1">
                    <span className="flex items-center gap-1 text-xs text-red-600">
                      <span>✗</span>
                      Service Not Running
                    </span>
                    <span className="text-xs text-gray-500">
                      Run: cd stagehand-service && npm run dev
                    </span>
                  </div>
                )}
              </div>
            </button>
          </div>

          {/* Feature Comparison Table */}
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Feature Comparison</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-gray-700 font-medium">Feature</th>
                    <th className="px-4 py-2 text-center text-gray-700 font-medium">Python</th>
                    <th className="px-4 py-2 text-center text-gray-700 font-medium">TypeScript</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr>
                    <td className="px-4 py-2 text-gray-900">Browser Automation</td>
                    <td className="px-4 py-2 text-center">✓</td>
                    <td className="px-4 py-2 text-center">✓</td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td className="px-4 py-2 text-gray-900">AI-Powered Selectors</td>
                    <td className="px-4 py-2 text-center">✓</td>
                    <td className="px-4 py-2 text-center">✓</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-900">Session Management</td>
                    <td className="px-4 py-2 text-center">✓</td>
                    <td className="px-4 py-2 text-center">✓</td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td className="px-4 py-2 text-gray-900">Performance</td>
                    <td className="px-4 py-2 text-center text-gray-600">Good</td>
                    <td className="px-4 py-2 text-center text-green-600 font-medium">Better</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-900">Setup Required</td>
                    <td className="px-4 py-2 text-center text-green-600">None (Built-in)</td>
                    <td className="px-4 py-2 text-center text-yellow-600">Microservice</td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td className="px-4 py-2 text-gray-900">Native API Support</td>
                    <td className="px-4 py-2 text-center text-gray-400">-</td>
                    <td className="px-4 py-2 text-center text-green-600 font-medium">✓</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Info Box */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex gap-3">
              <span className="text-blue-600 text-lg">ℹ️</span>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-blue-900 mb-1">About Dual Stagehand Provider</h4>
                <p className="text-sm text-blue-800">
                  Choose between Python (built-in, always available) or TypeScript (requires microservice on port 3001).
                  TypeScript offers better performance and native API support. Switch anytime without breaking existing tests.
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Team Collaboration - Feedback Data Sync */}
        <div>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Team Collaboration</h2>
            <p className="text-gray-600 mt-1">Share feedback data across team members with different databases</p>
          </div>
          <FeedbackDataSync />
        </div>

        {/* Sprint 5.5: 3-Tier Execution Engine */}
        <div>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900">3-Tier Execution Engine</h2>
            <p className="text-gray-600 mt-1">Configure intelligent fallback strategies and view execution analytics</p>
          </div>
          <ExecutionSettingsPanel 
            showSaveButton={false}
            onFormStateChange={setExecutionSettingsFormState}
          />
        </div>

        {/* Tier Analytics */}
        <div>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Execution Analytics</h2>
            <p className="text-gray-600 mt-1">View tier distribution and strategy effectiveness metrics</p>
          </div>
          <TierAnalyticsPanel />
        </div>

        {/* System Information */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Backend API URL
              </label>
              <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                <code className="text-sm text-gray-900">http://localhost:8000/api/v1</code>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Documentation
              </label>
              <div className="flex gap-2">
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm"
                >
                  Swagger UI
                </a>
                <a
                  href="http://localhost:8000/redoc"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
                >
                  ReDoc
                </a>
              </div>
            </div>
          </div>
        </Card>

        {/* Save Button for ALL Settings */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-lg p-6 shadow-lg">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                <h3 className="text-lg font-bold text-blue-900">Save All Settings</h3>
              </div>
              <p className="text-sm text-blue-800 mb-1">
                This will save all settings on this page:
              </p>
              <ul className="text-xs text-blue-700 space-y-1 ml-4">
                <li>• General Settings (Project Name, Timeout)</li>
                <li>• Notification Settings (Email, Slack, Alerts)</li>
                <li>• AI Provider Settings (Generation & Execution)</li>
                <li>• 3-Tier Execution Settings (Strategy, Timeout, Analytics)</li>
              </ul>
            </div>
            <div className="flex gap-3">
              <Button variant="secondary" onClick={handleResetSettings} disabled={isSaving}>
                Reset to Defaults
              </Button>
              <Button 
                variant="primary" 
                onClick={handleSaveSettings}
                disabled={isSaving}
              >
                {isSaving ? 'Saving All Settings...' : '💾 Save All Settings'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
