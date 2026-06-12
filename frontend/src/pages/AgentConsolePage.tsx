import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import {
  FactoryJobEvent,
  getFactoryJob,
  getHermesTrace,
  HermesTrace,
  pollFactoryJob,
  postAgentChat,
} from '../services/agentFactoryService';
import { isSuperadmin } from '../utils/roles';

export const AgentConsolePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobFromUrl = searchParams.get('job');
  const [message, setMessage] = useState('Run regression');
  const [reply, setReply] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(jobFromUrl);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [events, setEvents] = useState<FactoryJobEvent[]>([]);
  const [trace, setTrace] = useState<HermesTrace | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const allowed = isSuperadmin();

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    setEvents([]);
    setJobStatus(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const res = await postAgentChat(message.trim(), { project: 'Three-HK' });
      setReply(res.reply);
      setJobId(res.job_id);
      setJobStatus('queued');

      await pollFactoryJob(
        res.job_id,
        (ev) => setEvents((prev) => [...prev, ev]),
        async (status) => {
          setJobStatus(status);
          try {
            const t = await getHermesTrace(res.job_id);
            setTrace(t);
          } catch {
            setTrace(null);
          }
        },
        abortRef.current.signal,
      );
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

  const refreshJob = async () => {
    if (!jobId) return;
    const job = await getFactoryJob(jobId);
    setJobStatus(job.status);
    setEvents(job.events);
    try {
      const t = await getHermesTrace(jobId);
      setTrace(t);
      setTraceError(null);
    } catch (err: unknown) {
      setTrace(null);
      setTraceError(err instanceof Error ? err.message : 'Observatory unavailable');
    }
  };

  // Sync job id when opening a notification link (?job=uuid) while already on this page
  useEffect(() => {
    if (jobFromUrl && jobFromUrl !== jobId) {
      setJobId(jobFromUrl);
      setEvents([]);
      setTrace(null);
      setJobStatus(null);
    }
  }, [jobFromUrl, jobId]);

  useEffect(() => {
    if (jobId && allowed) {
      refreshJob().catch(() => undefined);
    }
  }, [jobId, allowed]);

  // Keep URL in sync when a new job starts from chat
  useEffect(() => {
    if (jobId && jobFromUrl !== jobId) {
      setSearchParams({ job: jobId }, { replace: true });
    }
  }, [jobId, jobFromUrl, setSearchParams]);

  if (!allowed) {
    return (
      <Layout>
        <div className="max-w-3xl mx-auto bg-white rounded-lg shadow p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Agent Console</h1>
          <p className="text-gray-600">
            Access requires the <code className="bg-gray-100 px-1 rounded">superadmin</code> role.
            Log in as <code className="bg-gray-100 px-1 rounded">superadmin</code> (not <code className="bg-gray-100 px-1 rounded">admin</code>).
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
            Chat with the QA factory orchestrator. One window routes to all specialist agents.
          </p>
        </div>

        <div className={`grid grid-cols-1 gap-6 ${jobId ? 'lg:grid-cols-3' : 'lg:grid-cols-2'}`}>
          <section className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Agent Chat</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <textarea
                className="w-full border border-gray-300 rounded-lg p-3 min-h-[120px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="e.g. Run regression for tag regression"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
              >
                {loading ? 'Running…' : 'Send'}
              </button>
            </form>
            {reply && (
              <p className="mt-4 text-sm text-gray-700 bg-blue-50 border border-blue-100 rounded p-3">{reply}</p>
            )}
            {error && (
              <p className="mt-4 text-sm text-red-700 bg-red-50 border border-red-100 rounded p-3">{error}</p>
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
                  onClick={refreshJob}
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
                    <span className="text-purple-700">{ev.profile || 'system'}</span>
                    {' '}
                    <span className="text-gray-800">{ev.message || ev.event_type}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {jobId && (
            <section className="bg-white rounded-lg shadow p-6 border border-amber-200">
              <h2 className="text-lg font-semibold mb-1">Agent Observatory</h2>
              <p className="text-xs text-amber-700 mb-4">Superadmin only — delegate payloads &amp; LLM turns</p>
              {traceError && (
                <p className="text-sm text-red-600 mb-2">{traceError}</p>
              )}
              {!trace ? (
                <p className="text-gray-500 text-sm">Load trace via Refresh on Job Monitor.</p>
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
                        {ev.profile || 'system'} · {ev.event_type}
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
