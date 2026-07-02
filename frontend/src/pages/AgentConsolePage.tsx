import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import {
  FactoryJob,
  FactoryJobEvent,
  getFactoryJob,
  getHermesTrace,
  HermesTrace,
  pollFactoryJob,
  postAgentChat,
} from '../services/agentFactoryService';
import { factoryProfileDisplayName } from '../constants/factoryProfiles';
import { isFactoryOperator, isSuperadmin } from '../utils/roles';

const TERMINAL_JOB_STATUSES = new Set(['completed', 'failed', 'cancelled']);

export const AgentConsolePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobId = searchParams.get('job');
  const [message, setMessage] = useState(() => (isSuperadmin() ? '' : 'Run regression'));
  const [reply, setReply] = useState<string | null>(null);
  const [orchestratorReply, setOrchestratorReply] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [events, setEvents] = useState<FactoryJobEvent[]>([]);
  const [trace, setTrace] = useState<HermesTrace | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollAbortRef = useRef<AbortController | null>(null);

  const allowed = isFactoryOperator();
  const openChat = isSuperadmin();

  const loadHermesTrace = useCallback(async (id: string) => {
    try {
      const t = await getHermesTrace(id);
      setTrace(t);
      setTraceError(null);
    } catch (err: unknown) {
      setTrace(null);
      setTraceError(err instanceof Error ? err.message : 'Observatory unavailable');
    }
  }, []);

  const applyJobUpdate = useCallback((job: FactoryJob) => {
    setJobStatus(job.status);
    if (job.orchestrator_reply) {
      setOrchestratorReply(job.orchestrator_reply);
      setError(null);
    } else if (job.status === 'failed' && job.error_message) {
      setError(job.error_message);
    }
  }, []);

  const refreshJob = useCallback(async () => {
    if (!jobId) return;
    const job = await getFactoryJob(jobId);
    setEvents(job.events);
    applyJobUpdate(job);
    await loadHermesTrace(jobId);
  }, [jobId, loadHermesTrace, applyJobUpdate]);

  useEffect(() => {
    pollAbortRef.current?.abort();
    if (!jobId || !allowed) {
      return undefined;
    }

    const ac = new AbortController();
    pollAbortRef.current = ac;
    setEvents([]);
    setTrace(null);
    setTraceError(null);
    setJobStatus(null);
    setOrchestratorReply(null);

    let cancelled = false;

    const run = async () => {
      try {
        const initial = await getFactoryJob(jobId);
        if (cancelled) return;
        setEvents(initial.events);
        applyJobUpdate(initial);

        if (TERMINAL_JOB_STATUSES.has(initial.status)) {
          await loadHermesTrace(jobId);
          return;
        }

        await pollFactoryJob(
          jobId,
          (ev) => setEvents((prev) => [...prev, ev]),
          (status) => {
            setJobStatus(status);
            if (TERMINAL_JOB_STATUSES.has(status)) {
              getFactoryJob(jobId)
                .then((job) => applyJobUpdate(job))
                .catch(() => undefined);
              loadHermesTrace(jobId).catch(() => undefined);
            }
          },
          ac.signal,
          (job) => applyJobUpdate(job),
        );
      } catch {
        if (!cancelled) {
          setJobStatus('unknown');
        }
      }
    };

    run().catch(() => undefined);

    return () => {
      cancelled = true;
      ac.abort();
    };
  }, [jobId, allowed, loadHermesTrace, applyJobUpdate]);

  useEffect(() => {
    return () => {
      pollAbortRef.current?.abort();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    setReply(null);
    setOrchestratorReply(null);

    try {
      const res = await postAgentChat(message.trim(), { project: 'Three-HK' });
      setReply(res.reply);
      setSearchParams({ job: res.job_id }, { replace: true });
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? String((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Request failed')
          : 'Request failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!allowed) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto bg-white rounded-lg shadow p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Agent Console</h1>
          <p className="text-gray-600">
            Access requires the <code className="bg-gray-100 px-1 rounded">agent_operator</code> role or
            higher (admin, superadmin).
          </p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Console</h1>
          <p className="text-gray-600 mt-1">
            {openChat
              ? 'Open chat with the QA Orchestrator — any message is forwarded to the factory node. Prefix with ! to run a structured command (e.g. !drain backlog).'
              : 'Structured factory commands only. Try: Run regression, Drain backlog, Scan changes, Heal failures, or Full cycle.'}
          </p>
        </div>

        <div className={`grid grid-cols-1 gap-6 ${jobId && openChat ? 'lg:grid-cols-3' : 'lg:grid-cols-2'}`}>
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Agent Chat</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <textarea
                className="w-full border border-gray-300 rounded-lg p-3 min-h-[120px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={
                  openChat
                    ? 'Ask anything… or run command with ! (e.g. !drain backlog)'
                    : 'e.g. Run regression, Drain backlog, Scan changes'
                }
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
              >
                {loading ? 'Sending…' : 'Send'}
              </button>
            </form>
            {orchestratorReply && (
              <div className="mt-4 text-sm bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-xs font-semibold text-purple-800 uppercase tracking-wide mb-2">
                  QA Orchestrator
                </p>
                <p className="text-gray-800 whitespace-pre-wrap">{orchestratorReply}</p>
              </div>
            )}
            {reply && (
              <p className="mt-4 text-xs text-gray-500">{reply}</p>
            )}
            {error && (
              <p className="mt-4 text-sm text-red-700 bg-red-50 border border-red-100 rounded p-3">{error}</p>
            )}
            {jobStatus === 'running' && !orchestratorReply && !error && (
              <p className="mt-4 text-sm text-gray-500 italic">Waiting for QA Orchestrator…</p>
            )}
            {jobId && (
              <p className="mt-2 text-xs text-gray-500">
                Job: <code>{jobId}</code>
                {jobStatus && <> · Status: <strong>{jobStatus}</strong></>}
              </p>
            )}
          </section>

          <section className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Job Monitor</h2>
              {jobId && (
                <button
                  type="button"
                  onClick={() => refreshJob().catch(() => undefined)}
                  className="text-sm text-blue-700 hover:underline"
                >
                  Refresh
                </button>
              )}
            </div>
            {!jobId ? (
              <p className="text-gray-500 text-sm">Submit a chat message to start a factory job.</p>
            ) : events.length === 0 ? (
              <p className="text-gray-500 text-sm">Waiting for events…</p>
            ) : (
              <ul className="space-y-2 max-h-[420px] overflow-y-auto text-sm font-mono">
                {events.map((ev) => (
                  <li key={ev.id} className="border-l-4 border-blue-400 pl-3 py-1">
                    <span className="text-gray-400">{new Date(ev.created_at).toLocaleTimeString()}</span>
                    {' '}
                    <span className="text-purple-700">{factoryProfileDisplayName(ev.profile)}</span>
                    {' '}
                    <span className="text-gray-800">{ev.message || ev.event_type}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {jobId && openChat && (
            <section className="bg-white rounded-lg shadow p-6 border border-amber-200">
              <h2 className="text-lg font-semibold mb-1">Agent Observatory</h2>
              <p className="text-xs text-amber-700 mb-4">Superadmin only — delegate payloads &amp; LLM turns</p>
              {traceError && (
                <p className="text-sm text-red-600 mb-2">{traceError}</p>
              )}
              {!trace ? (
                <p className="text-gray-500 text-sm">Trace loads when the job finishes, or use Refresh.</p>
              ) : (
                <div className="space-y-3 max-h-[420px] overflow-y-auto text-xs">
                  {trace.hermes_session_ids.length > 0 && (
                    <p className="text-gray-600">
                      Sessions: {trace.hermes_session_ids.join(', ')}
                    </p>
                  )}
                  {trace.events.map((ev) => (
                    <details key={ev.id} className="border border-gray-200 rounded p-2">
                      <summary className="cursor-pointer font-mono">
                        {factoryProfileDisplayName(ev.profile)} · {ev.event_type}
                      </summary>
                      {ev.message && <p className="mt-1 text-gray-700">{ev.message}</p>}
                      {ev.payload_full && (
                        <pre className="mt-2 bg-gray-50 p-2 overflow-x-auto rounded">
                          {JSON.stringify(ev.payload_full, null, 2)}
                        </pre>
                      )}
                      {ev.llm_turns && ev.llm_turns.length > 0 && (
                        <pre className="mt-2 bg-purple-50 p-2 overflow-x-auto rounded">
                          {JSON.stringify(ev.llm_turns, null, 2)}
                        </pre>
                      )}
                    </details>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default AgentConsolePage;
