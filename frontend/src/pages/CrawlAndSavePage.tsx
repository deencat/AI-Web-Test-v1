import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import stepLibraryService from '../services/stepLibraryService';
import type { StepLibraryModule } from '../types/stepLibrary.types';

const _viteApiUrl = import.meta.env.VITE_API_URL ?? '';
const API_BASE = _viteApiUrl.startsWith('http') ? new URL(_viteApiUrl).origin : 'http://localhost:8000';

interface LoginCredentials {
  username: string;
  password: string;
}

interface FormState {
  url: string;
  user_instruction: string;
  stop_at_page_hint: string;
  login_module: string;
  existing_subscriber_module: string;
  new_subscriber_module: string;
  subscriber_type_hint: string;
  test_title: string;
  test_description: string;
  login_username: string;
  login_password: string;
  max_browser_steps: string;
  max_flow_timeout_seconds: string;
  reference_test_id: string;
  tags: string;
}

const EMPTY_FORM: FormState = {
  url: '',
  user_instruction: '',
  stop_at_page_hint: '',
  login_module: '',
  existing_subscriber_module: '',
  new_subscriber_module: '',
  subscriber_type_hint: 'auto',
  test_title: '',
  test_description: '',
  login_username: '',
  login_password: '',
  max_browser_steps: '50',
  max_flow_timeout_seconds: '600',
  reference_test_id: '',
  tags: '',
};

type WorkflowStatus = 'idle' | 'running' | 'completed' | 'failed';

interface WorkflowPoll {
  status: string;
  current_agent?: string;
}

interface WorkflowResult {
  result?: {
    test_case_id?: number;
    total_steps?: number;
    crawled_steps_count?: number;
    login_module?: string;
    subscriber_type?: string;
    existing_subscriber_module?: string;
    new_subscriber_module?: string;
  };
  error?: string;
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function CrawlAndSavePage() {
  const [searchParams] = useSearchParams();

  const [form, setForm] = useState<FormState>(() => ({
    ...EMPTY_FORM,
    test_title: searchParams.get('test_title') ?? '',
    test_description: searchParams.get('test_description') ?? '',
    user_instruction: searchParams.get('user_instruction') ?? '',
    stop_at_page_hint: searchParams.get('stop_at_page_hint') ?? '',
    tags: searchParams.get('tags') ?? '',
  }));
  const [modules, setModules] = useState<StepLibraryModule[]>([]);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus>('idle');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [pollMessage, setPollMessage] = useState<string>('');
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  }

  useEffect(() => {
    stepLibraryService.list().then(setModules).catch(() => {/* silently ignore if not logged in yet */});
  }, []);

  async function pollWorkflow(id: string) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/workflows/${id}`, {
          headers: { ...getAuthHeaders() },
        });
        if (!res.ok) return;
        const data: WorkflowPoll = await res.json();
        const agentLabel = data.current_agent ? ` · ${data.current_agent}` : '';
        setPollMessage(`Status: ${data.status}${agentLabel}`);

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval);
          setWorkflowStatus(data.status === 'completed' ? 'completed' : 'failed');

          const resResult = await fetch(`${API_BASE}/api/v2/workflows/${id}/results`, {
            headers: { ...getAuthHeaders() },
          });
          if (resResult.ok) {
            const resultData: WorkflowResult = await resResult.json();
            setResult(resultData);
          }
        }
      } catch {
        // network hiccup — keep polling
      }
    }, 10000);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    setResult(null);
    setWorkflowId(null);
    setPollMessage('');

    const credentials: LoginCredentials | undefined =
      form.login_username.trim()
        ? { username: form.login_username.trim(), password: form.login_password.trim() }
        : undefined;

    const body: Record<string, unknown> = {
      url: form.url.trim(),
      user_instruction: form.user_instruction.trim(),
      test_title: form.test_title.trim(),
      test_description: form.test_description.trim(),
      subscriber_type_hint: form.subscriber_type_hint,
    };

    if (form.stop_at_page_hint.trim()) body.stop_at_page_hint = form.stop_at_page_hint.trim();
    if (form.login_module.trim()) body.login_module = form.login_module.trim();
    if (form.existing_subscriber_module.trim()) body.existing_subscriber_module = form.existing_subscriber_module.trim();
    if (form.new_subscriber_module.trim()) body.new_subscriber_module = form.new_subscriber_module.trim();
    if (credentials) body.login_credentials = credentials;
    if (form.max_browser_steps.trim()) body.max_browser_steps = parseInt(form.max_browser_steps, 10);
    if (form.max_flow_timeout_seconds.trim()) body.max_flow_timeout_seconds = parseInt(form.max_flow_timeout_seconds, 10);
    if (form.reference_test_id.trim()) body.reference_test_id = parseInt(form.reference_test_id, 10);
    if (form.tags.trim()) body.tags = form.tags.split(',').map(t => t.trim()).filter(Boolean);

    try {
      setWorkflowStatus('running');
      const res = await fetch(`${API_BASE}/api/v2/crawl-and-save-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.text();
        throw new Error(`${res.status}: ${err}`);
      }

      const data = await res.json();
      const id: string = data.workflow_id;
      setWorkflowId(id);
      setPollMessage('Workflow started — polling every 10 s…');
      pollWorkflow(id);
    } catch (err: unknown) {
      setWorkflowStatus('failed');
      setSubmitError(err instanceof Error ? err.message : String(err));
    }
  }

  function handleReset() {
    setForm(EMPTY_FORM);
    setWorkflowStatus('idle');
    setWorkflowId(null);
    setPollMessage('');
    setResult(null);
    setSubmitError(null);
  }

  const isRunning = workflowStatus === 'running';

  return (
    <Layout>
      <div className="p-6 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Crawl &amp; Save</h1>
        <p className="text-sm text-gray-500 mb-6">
          Browser-use crawls the navigational flow; Step Library modules handle reusable login and checkout steps.
          The resulting test case is saved to the test library.
        </p>

        {/* ── Result banner ── */}
        {workflowStatus === 'completed' && result?.result?.test_case_id && (
          <div className="mb-6 rounded-lg border border-green-300 bg-green-50 p-4">
            <p className="font-semibold text-green-800 mb-1">✓ Test case saved!</p>
            <p className="text-sm text-green-700">
              Test Case ID:{' '}
              <a
                href={`/tests/${result.result.test_case_id}`}
                className="underline font-medium"
              >
                {result.result.test_case_id}
              </a>
              {' · '}
              <a href="/tests/saved" className="underline font-medium">View all saved tests</a>
            </p>
            <p className="text-sm text-green-700 mt-1">
              Steps: {result.result.total_steps ?? '—'} total ({result.result.crawled_steps_count ?? '—'} crawled)
              {result.result.subscriber_type && ` · Subscriber type: ${result.result.subscriber_type}`}
            </p>
            <button
              onClick={handleReset}
              className="mt-3 text-xs text-green-700 underline hover:text-green-900"
            >
              Start a new crawl
            </button>
          </div>
        )}

        {workflowStatus === 'failed' && (
          <div className="mb-6 rounded-lg border border-red-300 bg-red-50 p-4">
            <p className="font-semibold text-red-800 mb-1">Workflow failed</p>
            <p className="text-sm text-red-700">{result?.error ?? submitError ?? 'Unknown error'}</p>
            <button
              onClick={handleReset}
              className="mt-3 text-xs text-red-700 underline hover:text-red-900"
            >
              Try again
            </button>
          </div>
        )}

        {/* ── Poll status ── */}
        {isRunning && (
          <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 flex items-center gap-3">
            <svg className="animate-spin h-4 w-4 text-blue-600 shrink-0" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <p className="text-sm text-blue-800">
              {pollMessage}
              {workflowId && (
                <span className="ml-2 text-blue-500 text-xs font-mono">#{workflowId}</span>
              )}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* ── Target URL ── */}
          <section className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Target</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">URL <span className="text-red-500">*</span></label>
              <input
                type="url"
                name="url"
                required
                value={form.url}
                onChange={handleChange}
                disabled={isRunning}
                placeholder="https://example.com/..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">User Instruction <span className="text-red-500">*</span></label>
              <textarea
                name="user_instruction"
                required
                rows={6}
                value={form.user_instruction}
                onChange={handleChange}
                disabled={isRunning}
                placeholder="Describe the navigation flow for browser-use to crawl…"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 resize-y font-mono"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stop at Page Hint</label>
              <input
                type="text"
                name="stop_at_page_hint"
                value={form.stop_at_page_hint}
                onChange={handleChange}
                disabled={isRunning}
                placeholder="e.g. SIM Card Setting"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
              <p className="text-xs text-gray-400 mt-1">Browser-use stops crawling when this page/state is detected.</p>
            </div>
          </section>

          {/* ── Step Library modules ── */}
          <section className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Step Library Modules</h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Login Module</label>
                <select
                  name="login_module"
                  value={form.login_module}
                  onChange={handleChange}
                  disabled={isRunning}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                >
                  <option value="">— none —</option>
                  {modules.map(m => (
                    <option key={m.id} value={m.name}>{m.display_name} ({m.name})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Subscriber Type Hint</label>
                <select
                  name="subscriber_type_hint"
                  value={form.subscriber_type_hint}
                  onChange={handleChange}
                  disabled={isRunning}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                >
                  <option value="auto">auto (detect from history)</option>
                  <option value="existing">existing</option>
                  <option value="new">new</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Existing Subscriber Module</label>
                <select
                  name="existing_subscriber_module"
                  value={form.existing_subscriber_module}
                  onChange={handleChange}
                  disabled={isRunning}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                >
                  <option value="">— none —</option>
                  {modules.map(m => (
                    <option key={m.id} value={m.name}>{m.display_name} ({m.name})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Subscriber Module</label>
                <select
                  name="new_subscriber_module"
                  value={form.new_subscriber_module}
                  onChange={handleChange}
                  disabled={isRunning}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                >
                  <option value="">— none —</option>
                  {modules.map(m => (
                    <option key={m.id} value={m.name}>{m.display_name} ({m.name})</option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* ── Test metadata ── */}
          <section className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Test Metadata</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Test Title <span className="text-red-500">*</span></label>
              <input
                type="text"
                name="test_title"
                required
                value={form.test_title}
                onChange={handleChange}
                disabled={isRunning}
                placeholder="Short descriptive name for the saved test case"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Test Description <span className="text-red-500">*</span></label>
              <textarea
                name="test_description"
                required
                rows={3}
                value={form.test_description}
                onChange={handleChange}
                disabled={isRunning}
                placeholder="Longer description of what this test covers…"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 resize-y"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
              <input
                type="text"
                name="tags"
                value={form.tags}
                onChange={handleChange}
                disabled={isRunning}
                placeholder="5g, voucher-plan, purchase-flow  (comma-separated)"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
              />
            </div>
          </section>

          {/* ── Login credentials ── */}
          <section className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Login Credentials</h2>
            <p className="text-xs text-gray-400">Only used by browser-use during the crawl phase; not stored in the saved test case.</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username / Email</label>
                <input
                  type="text"
                  name="login_username"
                  value={form.login_username}
                  onChange={handleChange}
                  disabled={isRunning}
                  autoComplete="off"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  name="login_password"
                  value={form.login_password}
                  onChange={handleChange}
                  disabled={isRunning}
                  autoComplete="new-password"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                />
              </div>
            </div>
          </section>

          {/* ── Advanced ── */}
          <section className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Advanced</h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Browser Steps</label>
                <input
                  type="number"
                  name="max_browser_steps"
                  min={1}
                  max={200}
                  value={form.max_browser_steps}
                  onChange={handleChange}
                  disabled={isRunning}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (seconds)</label>
                <input
                  type="number"
                  name="max_flow_timeout_seconds"
                  min={60}
                  max={3600}
                  value={form.max_flow_timeout_seconds}
                  onChange={handleChange}
                  disabled={isRunning}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference Test ID</label>
                <input
                  type="number"
                  name="reference_test_id"
                  min={1}
                  value={form.reference_test_id}
                  onChange={handleChange}
                  disabled={isRunning}
                  placeholder="e.g. 1217"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                />
                <p className="text-xs text-gray-400 mt-1">LLM review pass compares against this model-answer test.</p>
              </div>
            </div>
          </section>

          {/* ── Submit ── */}
          <div className="flex items-center gap-4">
            <button
              type="submit"
              disabled={isRunning}
              className="px-6 py-2.5 bg-blue-700 text-white text-sm font-semibold rounded-lg hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? 'Running…' : 'Start Crawl & Save'}
            </button>

            {!isRunning && (workflowStatus === 'idle') && (
              <button
                type="button"
                onClick={handleReset}
                className="px-4 py-2.5 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Reset
              </button>
            )}

            {submitError && workflowStatus !== 'failed' && (
              <p className="text-sm text-red-600">{submitError}</p>
            )}
          </div>
        </form>
      </div>
    </Layout>
  );
}
