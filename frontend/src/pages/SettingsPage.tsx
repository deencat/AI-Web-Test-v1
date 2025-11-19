import React, { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';

export const SettingsPage: React.FC = () => {
  const [projectName, setProjectName] = useState('AI Web Test v1.0');
  const [defaultTimeout, setDefaultTimeout] = useState('30');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [slackNotifications, setSlackNotifications] = useState(false);
  const [testFailureAlerts, setTestFailureAlerts] = useState(true);
  const [selectedModel, setSelectedModel] = useState('claude-3-opus-20240229');
  const [temperature, setTemperature] = useState('0.7');
  const [maxTokens, setMaxTokens] = useState('4096');

  const handleSaveSettings = () => {
    alert('Settings saved successfully!\n\nThis would save to backend in production.');
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

        {/* Agent Configuration */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Agent Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-4">GPT-4</option>
              </select>
              <p className="text-sm text-gray-600 mt-1">
                Select the AI model for test generation
              </p>
            </div>
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
        </Card>

        {/* API Endpoint Configuration */}
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">API Endpoint</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Backend API URL
              </label>
              <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg">
                <code className="text-sm text-gray-900">http://localhost:8000/api</code>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Current backend API endpoint (read-only)
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                OpenRouter API Key
              </label>
              <div className="px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg font-mono text-sm text-gray-900">
                sk-or-••••••••••••••••••••••••••••
              </div>
              <p className="text-sm text-gray-600 mt-1">
                API key for OpenRouter integration (hidden for security)
              </p>
            </div>
          </div>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end gap-3">
          <Button variant="secondary">Reset to Defaults</Button>
          <Button variant="primary" onClick={handleSaveSettings}>
            Save Settings
          </Button>
        </div>
      </div>
    </Layout>
  );
};

