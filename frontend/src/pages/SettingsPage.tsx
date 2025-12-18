import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import settingsService from '../services/settingsService';
import type { AvailableProvider, UserSettings } from '../types/api';

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
      
      setSaveMessage({ 
        type: 'success', 
        text: `✅ Settings saved! Using ${generationProvider.toUpperCase()} for generation and ${executionProvider.toUpperCase()} for execution.` 
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

        {/* Save Button */}
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={handleResetSettings}>
            Reset to Defaults
          </Button>
          <Button 
            variant="primary" 
            onClick={handleSaveSettings}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>
    </Layout>
  );
};
