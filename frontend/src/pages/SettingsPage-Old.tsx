import React, { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { apiClient } from '../api/client';

interface AvailableProvider {
  name: string;
  display_name: string;
  is_configured: boolean;
  models: string[];
  recommended_model: string | null;
}

interface UserSettings {
  id: number;
  user_id: number;
  generation_provider: string;
  generation_model: string;
  generation_temperature: number;
  generation_max_tokens: number;
  execution_provider: string;
  execution_model: string;
  execution_temperature: number;
  execution_max_tokens: number;
  created_at: string;
  updated_at: string | null;
}

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
      const providersRes = await apiClient.get('/api/v1/settings/available-providers');
      setAvailableProviders(providersRes.data.providers);
      
      // Load user settings
      const settingsRes = await apiClient.get('/api/v1/settings/provider');
      const settings = settingsRes.data;
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
      
      const response = await apiClient.put('/api/v1/settings/provider', updateData);
      setUserSettings(response.data);
      
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
        text: error.response?.data?.detail || 'Failed to save settings' 
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
      await apiClient.delete('/api/v1/settings/provider');
      
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
        text: error.response?.data?.detail || 'Failed to reset settings' 
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

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Configure application preferences and agent settings</p>
        </div>

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

        {/* AI Model Provider Configuration (Sprint 3) */}
        <Card>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">AI Model Provider</h2>
              <p className="text-sm text-gray-600 mt-1">Configure AI models for test execution automation</p>
            </div>
            <div className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
              Test Execution Only
            </div>
          </div>
          
          {/* Info Banner - Configuration Guide */}
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-1">Configuration Guide</p>
                <p className="text-xs text-blue-800 mb-2">
                  All API keys and models are configured in <code className="bg-blue-100 px-1 rounded">backend/.env</code>. 
                  Use this page as a reference for available options.
                </p>
                <ul className="space-y-1 text-xs text-blue-800">
                  <li>• <strong>Test Execution:</strong> Set MODEL_PROVIDER=google/cerebras/openrouter</li>
                  <li>• <strong>Test Generation:</strong> Always uses OpenRouter (hardcoded)</li>
                </ul>
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Provider for Test Execution
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Choose which AI provider to use for browser automation (Stagehand/Playwright)
              </p>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => setModelProvider('google')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    modelProvider === 'google'
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">Google</div>
                  <div className="text-xs text-gray-600 mt-1">Gemini Models</div>
                  <div className="text-xs text-green-600 mt-1 font-medium">FREE</div>
                  <div className="text-xs text-gray-500 mt-1">Best for execution</div>
                </button>
                <button
                  onClick={() => setModelProvider('cerebras')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    modelProvider === 'cerebras'
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">Cerebras</div>
                  <div className="text-xs text-gray-600 mt-1">Llama 3.1</div>
                  <div className="text-xs text-blue-600 mt-1 font-medium">ULTRA FAST</div>
                  <div className="text-xs text-gray-500 mt-1">0.5-1s inference</div>
                </button>
                <button
                  onClick={() => setModelProvider('openrouter')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    modelProvider === 'openrouter'
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">OpenRouter</div>
                  <div className="text-xs text-gray-600 mt-1">14+ Models</div>
                  <div className="text-xs text-purple-600 mt-1 font-medium">VARIETY</div>
                  <div className="text-xs text-gray-500 mt-1">Many options</div>
                </button>
              </div>
            </div>

            {/* Google Configuration */}
            {modelProvider === 'google' && (
              <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="p-3 bg-blue-100 border border-blue-300 rounded-lg">
                  <p className="text-sm text-blue-900 mb-2">
                    <strong>Configuration Required in Backend:</strong>
                  </p>
                  <code className="text-xs text-blue-800 bg-blue-50 px-2 py-1 rounded block">
                    # backend/.env<br/>
                    GOOGLE_API_KEY=your-key-here<br/>
                    GOOGLE_MODEL=gemini-2.5-flash
                  </code>
                  <p className="text-xs text-blue-700 mt-2">
                    Get free API key: <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline font-medium">Google AI Studio</a>
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Model (Reference Only)
                  </label>
                  <select
                    value={googleModel}
                    onChange={(e) => setGoogleModel(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                  >
                    <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Experimental)</option>
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash (Latest)</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                  </select>
                  <p className="text-xs text-gray-600 mt-1">
                    Model selection here is for reference. Set GOOGLE_MODEL in backend .env to change active model.
                  </p>
                </div>
              </div>
            )}

            {/* Cerebras Configuration */}
            {modelProvider === 'cerebras' && (
              <div className="space-y-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="p-3 bg-purple-100 border border-purple-300 rounded-lg">
                  <p className="text-sm text-purple-900 mb-2">
                    <strong>Configuration Required in Backend:</strong>
                  </p>
                  <code className="text-xs text-purple-800 bg-purple-50 px-2 py-1 rounded block">
                    # backend/.env<br/>
                    CEREBRAS_API_KEY=your-key-here<br/>
                    CEREBRAS_MODEL=llama-3.3-70b
                  </code>
                  <p className="text-xs text-purple-700 mt-2">
                    Get API key: <a href="https://cloud.cerebras.ai/" target="_blank" rel="noopener noreferrer" className="underline font-medium">Cerebras Cloud</a>
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Model (Reference Only)
                  </label>
                  <select
                    value={cerebrasModel}
                    onChange={(e) => setCerebrasModel(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                  >
                    <option value="llama3.1-8b">Llama 3.1 8B (Fast)</option>
                    <option value="llama3.1-70b">Llama 3.1 70B (Powerful)</option>
                    <option value="llama-3.3-70b">Llama 3.3 70B (Latest)</option>
                  </select>
                  <p className="text-xs text-gray-600 mt-1">
                    Model selection here is for reference. Set CEREBRAS_MODEL in backend .env to change active model.
                  </p>
                </div>
              </div>
            )}

            {/* OpenRouter Configuration */}
            {modelProvider === 'openrouter' && (
              <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="p-3 bg-green-100 border border-green-300 rounded-lg">
                  <p className="text-sm text-green-900 mb-2">
                    <strong>Configuration Required in Backend:</strong>
                  </p>
                  <code className="text-xs text-green-800 bg-green-50 px-2 py-1 rounded block">
                    # backend/.env<br/>
                    OPENROUTER_API_KEY=your-key-here<br/>
                    OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
                  </code>
                  <p className="text-xs text-green-700 mt-2">
                    Get API key: <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" className="underline font-medium">OpenRouter</a>
                  </p>
                  <p className="text-xs text-green-800 mt-2 pt-2 border-t border-green-300">
                    <strong>Note:</strong> OpenRouter is used for both test execution AND test generation
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preferred Model (Reference Only)
                  </label>
                  <select
                    value={openrouterModel}
                    onChange={(e) => setOpenrouterModel(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-white"
                  >
                    <optgroup label="FREE Models">
                      <option value="google/gemini-2.0-flash-exp:free">Google Gemini 2.0 Flash</option>
                      <option value="meta-llama/llama-3.2-3b-instruct:free">Meta Llama 3.2 3B</option>
                      <option value="meta-llama/llama-3.3-70b-instruct:free">Meta Llama 3.3 70B (Latest)</option>
                      <option value="mistralai/mistral-7b-instruct:free">Mistral 7B</option>
                    </optgroup>
                    <optgroup label="Premium Models">
                      <option value="anthropic/claude-3-opus">Claude 3 Opus</option>
                      <option value="openai/gpt-4-turbo">GPT-4 Turbo</option>
                      <option value="google/gemini-pro-1.5">Gemini Pro 1.5</option>
                    </optgroup>
                  </select>
                  <p className="text-xs text-gray-600 mt-1">
                    Model selection here is for reference. Set OPENROUTER_MODEL in backend .env to change active model.
                  </p>
                </div>
              </div>
            )}

            {/* Advanced Settings */}
            <div className="pt-4 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Advanced Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature: {temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-600 mt-1">
                    <span>Precise (0.0)</span>
                    <span>Creative (1.0)</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="4096"
                  />
                  <p className="text-sm text-gray-600 mt-1">
                    Maximum tokens for AI responses
                  </p>
                </div>
              </div>
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
                <code className="text-sm text-gray-900">http://localhost:8000/api</code>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Current backend API endpoint (configured in .env)
              </p>
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
              <p className="text-sm text-gray-600 mt-1">
                Interactive API documentation and testing interface
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Version Information
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                  <div className="text-xs text-gray-600">Frontend</div>
                  <div className="font-mono text-sm text-gray-900 mt-1">v1.0.0</div>
                </div>
                <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                  <div className="text-xs text-gray-600">Backend API</div>
                  <div className="font-mono text-sm text-gray-900 mt-1">v1.0.0</div>
                </div>
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

