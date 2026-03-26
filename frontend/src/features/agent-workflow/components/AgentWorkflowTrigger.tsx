/**
 * AgentWorkflowTrigger — Sprint 10 Real API integration (Developer B)
 *
 * Form that triggers the 4-agent AI test generation workflow.
 * Calls agentWorkflowService.generateTests() which hits POST /api/v2/generate-tests
 * and returns a WorkflowStatusResponse (202 Accepted) with a workflow_id.
 */
import React, { useState } from 'react';
import { Button } from '../../../components/common/Button';
import agentWorkflowService from '../../../services/agentWorkflowService';
import browserProfileService from '../../../services/browserProfileService';
import type { GenerateTestsRequest } from '../../../types/agentWorkflow.types';
import type { BrowserProfile } from '../../../types/browserProfile';

export interface AgentWorkflowTriggerProps {
  /** Invoked with the new workflow_id once the workflow is accepted by the backend */
  onWorkflowStarted: (workflowId: string) => void;
  className?: string;
}

export const AgentWorkflowTrigger: React.FC<AgentWorkflowTriggerProps> = ({
  onWorkflowStarted,
  className = '',
}) => {
  const [url, setUrl] = useState('');
  const [userInstruction, setUserInstruction] = useState('');
  const [depth, setDepth] = useState<1 | 2 | 3>(1);
  const [profiles, setProfiles] = useState<BrowserProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState('');

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [isHttpAuthOpen, setIsHttpAuthOpen] = useState(false);
  const [httpUsername, setHttpUsername] = useState('');
  const [httpPassword, setHttpPassword] = useState('');
  const [gmailEmail, setGmailEmail] = useState('');
  const [gmailPassword, setGmailPassword] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Sprint 10.8 — new fields
  const [filePaths, setFilePaths] = useState<string[]>(['']);
  const [selectedScenarioTypes, setSelectedScenarioTypes] = useState<string[]>([]);
  const [maxScenarios, setMaxScenarios] = useState('');
  const [maxBrowserSteps, setMaxBrowserSteps] = useState('');
  const [maxFlowTimeout, setMaxFlowTimeout] = useState('');
  const [focusGoalOnly, setFocusGoalOnly] = useState(false);

  React.useEffect(() => {
    let isMounted = true;

    const loadProfiles = async () => {
      try {
        const response = await browserProfileService.getAllProfiles();
        if (isMounted) {
          setProfiles(response.profiles);
        }
      } catch {
        if (isMounted) {
          setProfiles([]);
        }
      }
    };

    loadProfiles();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setSubmitError('Please enter a valid URL.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    let browserProfileData;
    let resolvedHttpCredentials;

    if (selectedProfileId) {
      try {
        browserProfileData = await browserProfileService.loadProfileSession(Number(selectedProfileId));
        resolvedHttpCredentials = browserProfileData.http_credentials;
      } catch (error) {
        setSubmitError(error instanceof Error ? error.message : 'Failed to load browser profile session.');
        setIsSubmitting(false);
        return;
      }
    }

    const request: GenerateTestsRequest = {
      url: url.trim(),
      depth,
      ...(userInstruction.trim() && { user_instruction: userInstruction.trim() }),
      ...(loginEmail.trim() && loginPassword
        ? { login_credentials: { email: loginEmail.trim(), password: loginPassword } }
        : {}),
      ...((httpUsername.trim() && httpPassword)
        ? { http_credentials: { username: httpUsername.trim(), password: httpPassword } }
        : resolvedHttpCredentials
          ? { http_credentials: resolvedHttpCredentials }
        : {}),
      ...(browserProfileData ? { browser_profile_data: browserProfileData } : {}),
      ...(gmailEmail.trim() && gmailPassword
        ? { gmail_credentials: { email: gmailEmail.trim(), password: gmailPassword } }
        : {}),
      ...(filePaths.some(p => p.trim()) && { available_file_paths: filePaths.filter(p => p.trim()) }),
      ...(selectedScenarioTypes.length > 0 && { scenario_types: selectedScenarioTypes }),
      ...(maxScenarios !== '' && !isNaN(Number(maxScenarios)) && Number(maxScenarios) > 0 && { max_scenarios: Number(maxScenarios) }),
      ...(maxBrowserSteps !== '' && !isNaN(Number(maxBrowserSteps)) && Number(maxBrowserSteps) > 0 && { max_browser_steps: Number(maxBrowserSteps) }),
      ...(maxFlowTimeout !== '' && !isNaN(Number(maxFlowTimeout)) && Number(maxFlowTimeout) > 0 && { max_flow_timeout_seconds: Number(maxFlowTimeout) }),
      ...(focusGoalOnly && { focus_goal_only: true }),
    };

    try {
      const response = await agentWorkflowService.generateTests(request);
      onWorkflowStarted(response.workflow_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to start workflow.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>
      <h2 className="text-xl font-semibold text-gray-900 mb-1">AI Test Generation</h2>
      <p className="text-sm text-gray-500 mb-5">
        Provide a URL and the 4-agent workflow will analyse the page and generate test cases automatically.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4" data-testid="agent-workflow-form">
        {/* URL */}
        <div>
          <label htmlFor="workflow-url" className="block text-sm font-medium text-gray-700 mb-1">
            Target URL <span className="text-red-500">*</span>
          </label>
          <input
            id="workflow-url"
            data-testid="url-input"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/login"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label htmlFor="browser-profile" className="block text-sm font-medium text-gray-700 mb-1">
            Browser profile <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <select
            id="browser-profile"
            data-testid="browser-profile-select"
            value={selectedProfileId}
            onChange={(e) => setSelectedProfileId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          >
            <option value="">No saved browser profile</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={String(profile.id)}>
                {profile.profile_name}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Reuse saved cookies and storage from a synced browser profile to keep purchase-flow state.
          </p>
        </div>

        {/* User instruction */}
        <div>
          <label htmlFor="workflow-instruction" className="block text-sm font-medium text-gray-700 mb-1">
            Instructions <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            id="workflow-instruction"
            data-testid="instruction-input"
            type="text"
            value={userInstruction}
            onChange={(e) => setUserInstruction(e.target.value)}
            placeholder="e.g. Test login flow with invalid credentials"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          />
        </div>

        {/* File paths */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            File paths <span className="text-gray-400 font-normal">(for eKYC / file upload, optional)</span>
          </label>
          {filePaths.map((fp, idx) => (
            <div key={idx} className="flex items-center gap-2 mb-2">
              <input
                data-testid={`file-path-input-${idx}`}
                type="text"
                value={fp}
                onChange={(e) => {
                  const updated = [...filePaths];
                  updated[idx] = e.target.value;
                  setFilePaths(updated);
                }}
                placeholder="C:\path\to\file.jpg"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isSubmitting}
              />
              {filePaths.length > 1 && (
                <button
                  type="button"
                  data-testid={`file-path-remove-${idx}`}
                  onClick={() => setFilePaths(filePaths.filter((_, i) => i !== idx))}
                  className="text-gray-400 hover:text-red-500 text-sm"
                  disabled={isSubmitting}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            data-testid="add-file-path-button"
            onClick={() => setFilePaths([...filePaths, ''])}
            className="text-sm text-blue-600 hover:text-blue-800"
            disabled={isSubmitting}
          >
            + Add file path
          </button>
        </div>

        {/* Login credentials (website) */}
        <fieldset className="border border-gray-200 rounded-lg p-4 space-y-3">
          <legend className="text-sm font-medium text-gray-700 px-1">
            Login credentials <span className="text-gray-400 font-normal">(website, optional)</span>
          </legend>
          <p className="text-xs text-gray-500">
            Required for flows that need login. Used to generate steps with real email/password (same as Phase 2).
          </p>
          <div>
            <label htmlFor="login-email" className="block text-sm font-medium text-gray-700 mb-1">
              Login email
            </label>
            <input
              id="login-email"
              data-testid="login-email-input"
              type="text"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              placeholder="e.g. user@example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="login-password"
              data-testid="login-password-input"
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              placeholder="Website password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            />
          </div>
        </fieldset>

        <div className="border border-gray-200 rounded-lg p-4 space-y-3">
          <button
            type="button"
            data-testid="http-auth-toggle"
            className="text-sm font-medium text-gray-700"
            onClick={() => setIsHttpAuthOpen((current) => !current)}
            disabled={isSubmitting}
          >
            HTTP Basic Auth <span className="text-gray-400 font-normal">(preprod, optional)</span>
          </button>
          {isHttpAuthOpen && (
            <>
              <p className="text-xs text-gray-500 mt-3">
                Required if your target URL is behind a network-level login prompt (HTTP Basic Auth).
              </p>
              <div>
                <label htmlFor="http-username" className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  id="http-username"
                  data-testid="http-username-input"
                  type="text"
                  value={httpUsername}
                  onChange={(e) => setHttpUsername(e.target.value)}
                  placeholder="Preprod username"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
              <div>
                <label htmlFor="http-password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  id="http-password"
                  data-testid="http-password-input"
                  type="password"
                  value={httpPassword}
                  onChange={(e) => setHttpPassword(e.target.value)}
                  placeholder="Preprod password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
            </>
          )}
        </div>

        {/* Gmail credentials (for OTP) */}
        <fieldset className="border border-gray-200 rounded-lg p-4 space-y-3">
          <legend className="text-sm font-medium text-gray-700 px-1">
            Gmail credentials <span className="text-gray-400 font-normal">(for OTP, optional)</span>
          </legend>
          <p className="text-xs text-gray-500">
            Only if the flow uses OTP or email verification and the agent should retrieve the code from Gmail.
          </p>
          <div>
            <label htmlFor="gmail-email" className="block text-sm font-medium text-gray-700 mb-1">
              Gmail email
            </label>
            <input
              id="gmail-email"
              data-testid="gmail-email-input"
              type="text"
              value={gmailEmail}
              onChange={(e) => setGmailEmail(e.target.value)}
              placeholder="e.g. user@gmail.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            />
          </div>
          <div>
            <label htmlFor="gmail-password" className="block text-sm font-medium text-gray-700 mb-1">
              Gmail password
            </label>
            <input
              id="gmail-password"
              data-testid="gmail-password-input"
              type="password"
              value={gmailPassword}
              onChange={(e) => setGmailPassword(e.target.value)}
              placeholder="Gmail password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            />
          </div>
        </fieldset>

        {/* Crawl depth */}
        <div>
          <label htmlFor="workflow-depth" className="block text-sm font-medium text-gray-700 mb-1">
            Crawl depth
          </label>
          <select
            id="workflow-depth"
            data-testid="depth-select"
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value) as 1 | 2 | 3)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          >
            <option value={1}>1 — Current page only</option>
            <option value={2}>2 — Include linked pages</option>
            <option value={3}>3 — Deep crawl</option>
          </select>
        </div>

        {/* Advanced options */}
        <details data-testid="advanced-options" className="border border-gray-200 rounded-lg p-4">
          <summary className="text-sm font-medium text-gray-700 cursor-pointer select-none">
            Advanced options
          </summary>

          <div className="mt-4 space-y-4">
            {/* Scenario types */}
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">
                Scenario types <span className="text-gray-400 font-normal">(default: all)</span>
              </p>
              <div className="flex flex-wrap gap-3">
                {(['functional', 'accessibility', 'security', 'edge_case', 'usability', 'performance'] as const).map((type) => (
                  <label key={type} className="flex items-center gap-1 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      data-testid={`scenario-type-${type}`}
                      checked={selectedScenarioTypes.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedScenarioTypes([...selectedScenarioTypes, type]);
                        } else {
                          setSelectedScenarioTypes(selectedScenarioTypes.filter((t) => t !== type));
                        }
                      }}
                      disabled={isSubmitting}
                    />
                    {type}
                  </label>
                ))}
              </div>
            </div>

            {/* Numeric limits */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label htmlFor="max-scenarios" className="block text-sm font-medium text-gray-700 mb-1">
                  Max scenarios
                </label>
                <input
                  id="max-scenarios"
                  data-testid="max-scenarios-input"
                  type="number"
                  min={1}
                  max={100}
                  value={maxScenarios}
                  onChange={(e) => setMaxScenarios(e.target.value)}
                  placeholder="12 (default: no limit)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
              <div>
                <label htmlFor="max-browser-steps" className="block text-sm font-medium text-gray-700 mb-1">
                  Max browser steps
                </label>
                <input
                  id="max-browser-steps"
                  data-testid="max-browser-steps-input"
                  type="number"
                  min={1}
                  max={500}
                  value={maxBrowserSteps}
                  onChange={(e) => setMaxBrowserSteps(e.target.value)}
                  placeholder="200 (default: 120)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
              <div>
                <label htmlFor="max-flow-timeout" className="block text-sm font-medium text-gray-700 mb-1">
                  Flow timeout (s)
                </label>
                <input
                  id="max-flow-timeout"
                  data-testid="max-flow-timeout-input"
                  type="number"
                  min={60}
                  max={7200}
                  value={maxFlowTimeout}
                  onChange={(e) => setMaxFlowTimeout(e.target.value)}
                  placeholder="1200 (default: 1200)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isSubmitting}
                />
              </div>
            </div>

            {/* Goal-focused mode */}
            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                data-testid="focus-goal-only-checkbox"
                checked={focusGoalOnly}
                onChange={(e) => setFocusGoalOnly(e.target.checked)}
                disabled={isSubmitting}
                className="mt-0.5"
              />
              <span>
                <span className="font-medium">Goal-focused mode</span>
                <span className="block text-xs text-gray-500">
                  Only generate scenarios aligned with your instruction (trims low-relevance scenarios first)
                </span>
              </span>
            </label>
          </div>
        </details>

        {/* Error */}
        {submitError && (
          <p data-testid="submit-error" className="text-sm text-red-600">
            {submitError}
          </p>
        )}

        {/* Submit */}
        <Button
          type="submit"
          data-testid="generate-button"
          disabled={isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Starting…' : 'Generate Tests'}
        </Button>
      </form>
    </div>
  );
};
