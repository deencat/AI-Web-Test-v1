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

const BOILERPLATE_REPLIES = new Set([
  'orchestrator cli finished',
  'open chat completed',
  'orchestrator reply',
]);

function isBoilerplateReply(text: string): boolean {
  const lower = text.trim().toLowerCase();
  if (!lower || BOILERPLATE_REPLIES.has(lower)) return true;
  if (lower.startsWith('orchestrator cli started')) return true;
  if (lower.startsWith('bridge completed')) return true;
  return false;
}

function isSystemStatusMessage(text: string): boolean {
  const lower = text.trim().toLowerCase();
  if (!lower || isBoilerplateReply(text)) return true;
  if (lower.startsWith('job queued:')) return true;
  if (lower.startsWith('job accepted')) return true;
  if (lower.startsWith('open chat:')) return true;
  if (lower.includes('initializing agent')) return true;
  if (lower.startsWith('query:')) return true;
  return false;
}

function looksLikeVerboseCliDump(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes('initializing agent') ||
    lower.startsWith('query:') ||
    (text.includes('{') && text.includes('"status"') && !extractJsonSummaryOnly(text))
  );
}

function normalizeSummaryText(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

function extractJsonSummaryOnly(raw: string | null | undefined): string | null {
  if (!raw?.trim()) return null;
  const trimmed = raw.trim();

  const candidates = [trimmed];
  const firstBrace = trimmed.indexOf('{');
  const lastBrace = trimmed.lastIndexOf('}');
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    candidates.push(trimmed.slice(firstBrace, lastBrace + 1));
  }

  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(candidate) as { summary?: unknown };
      if (typeof parsed.summary === 'string' && parsed.summary.trim()) {
        return normalizeSummaryText(parsed.summary);
      }
    } catch {
      // Hermes CLI often pretty-prints JSON with line breaks inside string values.
    }
  }

  const summaryMatch = trimmed.match(/"summary"\s*:\s*"([\s\S]*?)"\s*,/);
  if (summaryMatch?.[1]) {
    return normalizeSummaryText(summaryMatch[1]);
  }

  return null;
}

function extractAssistantReplyFromEvent(ev: FactoryJobEvent): string | null {
  const turns = ev.llm_turns;
  if (!Array.isArray(turns)) return null;
  for (let i = turns.length - 1; i >= 0; i -= 1) {
    const turn = turns[i] as Record<string, unknown>;
    if (turn?.role === 'assistant' && typeof turn.content === 'string' && turn.content.trim()) {
      return turn.content.trim();
    }
  }
  return null;
}

function extractChatReplyFromJob(
  events: FactoryJobEvent[],
  orchestratorReply: string | null,
): string | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const ev = events[i];
    const fromTurns = extractAssistantReplyFromEvent(ev);
    if (!fromTurns) continue;

    const jsonSummary = extractJsonSummaryOnly(fromTurns);
    if (jsonSummary) return jsonSummary;

    const profile = (ev.profile || '').toLowerCase();
    if (
      ev.event_type === 'delegate_complete' &&
      profile.includes('orchestrator') &&
      !isSystemStatusMessage(fromTurns) &&
      !looksLikeVerboseCliDump(fromTurns)
    ) {
      return fromTurns;
    }
  }

  for (let i = events.length - 1; i >= 0; i -= 1) {
    const payloadSummary = events[i].payload_summary?.summary;
    if (typeof payloadSummary === 'string' && payloadSummary.trim()) {
      return payloadSummary.trim();
    }
  }

  const apiReply = orchestratorReply?.trim();
  if (!apiReply || isSystemStatusMessage(apiReply)) return null;

  const jsonSummary = extractJsonSummaryOnly(apiReply);
  if (jsonSummary) return jsonSummary;

  if (!looksLikeVerboseCliDump(apiReply) && !apiReply.includes('{')) {
    return apiReply;
  }

  return null;
}

function extractHermesResumeSession(events: FactoryJobEvent[]): string | null {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    const fromPayload = events[i].payload_summary?.hermes_resume_session;
    if (typeof fromPayload === 'string' && fromPayload.trim()) {
      return fromPayload.trim();
    }
    const fromTurns = extractAssistantReplyFromEvent(events[i]);
    if (fromTurns) {
      const sessionMatch =
        fromTurns.match(/Session:\s*(\S+)/) ?? fromTurns.match(/hermes --resume (\S+)/);
      if (sessionMatch?.[1]) return sessionMatch[1].trim();
    }
  }
  return null;
}

function getMonitorMessage(ev: FactoryJobEvent): string {
  const assistantReply = extractAssistantReplyFromEvent(ev);
  if (assistantReply) {
    const summary = extractJsonSummaryOnly(assistantReply);
    if (summary) return summary;
    if (!isBoilerplateReply(assistantReply) && !isSystemStatusMessage(assistantReply)) {
      return assistantReply;
    }
  }
  const fromMessage = extractJsonSummaryOnly(ev.message);
  if (fromMessage) return fromMessage;
  return ev.message || ev.event_type;
}

type ChatBubble = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
};

export const AgentConsolePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobId = searchParams.get('job');
  const [message, setMessage] = useState(() => (isSuperadmin() ? '' : 'Run regression'));
  const [orchestratorReply, setOrchestratorReply] = useState<string | null>(null);
  const [chatBubbles, setChatBubbles] = useState<ChatBubble[]>([]);
  const [hermesResumeSession, setHermesResumeSession] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [events, setEvents] = useState<FactoryJobEvent[]>([]);
  const [trace, setTrace] = useState<HermesTrace | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollAbortRef = useRef<AbortController | null>(null);
  const lastAssistantReplyKeyRef = useRef<string | null>(null);
  const activeJobIdRef = useRef<string | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  const allowed = isFactoryOperator();
  const openChat = isSuperadmin();
  const assistantChatReply = extractChatReplyFromJob(events, orchestratorReply);
  const waitingForReply =
    Boolean(jobId) &&
    (loading || (jobStatus === 'running' && !assistantChatReply && !error));

  useEffect(() => {
    if (jobId) activeJobIdRef.current = jobId;
  }, [jobId]);

  useEffect(() => {
    if (!assistantChatReply || !jobId || jobId !== activeJobIdRef.current) return;
    if (!TERMINAL_JOB_STATUSES.has(jobStatus || '')) return;
    const key = `${jobId}:${assistantChatReply}`;
    if (lastAssistantReplyKeyRef.current === key) return;
    lastAssistantReplyKeyRef.current = key;
    setChatBubbles((prev) => [
      ...prev,
      {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: assistantChatReply,
      },
    ]);
  }, [assistantChatReply, jobId, jobStatus]);

  useEffect(() => {
    if (!jobId || !TERMINAL_JOB_STATUSES.has(jobStatus || '')) return;
    const session = extractHermesResumeSession(events);
    if (session) setHermesResumeSession(session);
  }, [jobId, jobStatus, events]);

  useEffect(() => {
    chatScrollRef.current?.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [chatBubbles, waitingForReply]);

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
    if (!message.trim() || loading) return;
    setLoading(true);
    setError(null);
    setOrchestratorReply(null);
    setEvents([]);
    setJobStatus('queued');
    lastAssistantReplyKeyRef.current = null;
    const userText = message.trim();
    setChatBubbles((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        text: userText,
      },
    ]);

    try {
      const chatContext: Record<string, unknown> = { project: 'Three-HK' };
      if (hermesResumeSession) {
        chatContext.hermes_resume_session = hermesResumeSession;
      }
      const res = await postAgentChat(userText, chatContext);
      setSearchParams({ job: res.job_id }, { replace: true });
      setMessage('');
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

  const handleMessageKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Enter' || e.shiftKey || e.nativeEvent.isComposing) return;
    e.preventDefault();
    e.currentTarget.form?.requestSubmit();
  };

  const handleNewConversation = () => {
    pollAbortRef.current?.abort();
    activeJobIdRef.current = null;
    lastAssistantReplyKeyRef.current = null;
    setHermesResumeSession(null);
    setChatBubbles([]);
    setEvents([]);
    setTrace(null);
    setTraceError(null);
    setOrchestratorReply(null);
    setJobStatus(null);
    setError(null);
    setSearchParams({}, { replace: true });
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
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Console</h1>
          <p className="text-gray-600 mt-1">
            {openChat
              ? 'Open chat with the QA Orchestrator — any message is forwarded to the factory node. Prefix with ! to run a structured command (e.g. !drain backlog).'
              : 'Structured factory commands only. Try: Run regression, Drain backlog, Scan changes, Heal failures, or Full cycle.'}
          </p>
        </div>

        <div
          className={`grid grid-cols-1 gap-6 ${
            jobId && openChat ? 'lg:grid-cols-12' : 'lg:grid-cols-3'
          }`}
        >
          <section
            className={`bg-white rounded-lg shadow p-6 ${
              jobId && openChat ? 'lg:col-span-7' : 'lg:col-span-2'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Agent Chat</h2>
              {openChat && (chatBubbles.length > 0 || hermesResumeSession) && (
                <button
                  type="button"
                  onClick={handleNewConversation}
                  className="text-sm text-gray-600 hover:text-gray-900 hover:underline"
                >
                  New conversation
                </button>
              )}
            </div>
            {hermesResumeSession && (
              <p className="text-xs text-gray-500 mb-3">
                Hermes session active — follow-up messages keep chat context.
              </p>
            )}
            <div
              ref={chatScrollRef}
              className="mb-4 border border-gray-200 rounded-lg bg-gray-50 p-4 min-h-[280px] max-h-[420px] overflow-y-auto space-y-3"
            >
              {chatBubbles.length === 0 && !waitingForReply ? (
                <p className="text-sm text-gray-500">
                  Conversation will appear here. Ask naturally, or use <code>!command</code> for structured actions.
                </p>
              ) : (
                chatBubbles.map((bubble) => (
                  <div
                    key={bubble.id}
                    className={
                      bubble.role === 'user'
                        ? 'bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3 max-w-[85%] ml-auto'
                        : 'mr-12 bg-white text-gray-900 rounded-2xl rounded-bl-md px-4 py-3 border border-gray-200 shadow-sm max-w-[85%]'
                    }
                  >
                    {bubble.role === 'assistant' && (
                      <p className="text-xs text-purple-700 mb-1 font-semibold">QA Orchestrator</p>
                    )}
                    <p className="text-sm whitespace-pre-wrap break-words">{bubble.text}</p>
                  </div>
                ))
              )}
              {waitingForReply && (
                <div className="mr-12 bg-white text-gray-500 rounded-2xl rounded-bl-md px-4 py-3 border border-gray-200 shadow-sm max-w-[85%]">
                  <p className="text-xs text-purple-700 mb-1 font-semibold">QA Orchestrator</p>
                  <p className="text-sm italic">Thinking…</p>
                </div>
              )}
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <textarea
                className="w-full border border-gray-300 rounded-lg p-3 min-h-[120px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleMessageKeyDown}
                placeholder={
                  openChat
                    ? 'Ask anything… Press Enter to send, Shift+Enter for a new line'
                    : 'e.g. Run regression, Drain backlog — Enter to send'
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

          <section
            className={`bg-white rounded-lg shadow p-6 ${
              jobId && openChat ? 'lg:col-span-3' : 'lg:col-span-1'
            }`}
          >
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
                  <li key={ev.id} className="border-l-4 border-blue-400 pl-3 py-1 break-words">
                    <span className="text-gray-400">{new Date(ev.created_at).toLocaleTimeString()}</span>
                    {' '}
                    <span className="text-purple-700">{factoryProfileDisplayName(ev.profile)}</span>
                    {' '}
                    <span className="text-gray-800 whitespace-pre-wrap">{getMonitorMessage(ev)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {jobId && openChat && (
            <section className="bg-white rounded-lg shadow p-6 border border-amber-200 lg:col-span-2">
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
