import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import {
  AgentConversation,
  AgentConversationMessage,
  FactoryJob,
  FactoryJobEvent,
  createAgentConversation,
  getActiveAgentConversation,
  getAgentConversation,
  getFactoryJob,
  getHermesTrace,
  HermesTrace,
  postAgentChat,
  streamFactoryJob,
  syncAgentConversationJob,
} from '../services/agentFactoryService';
import { factoryProfileDisplayName } from '../constants/factoryProfiles';
import { isFactoryOperator, isSuperadmin } from '../utils/roles';
import {
  cleanHermesResumeSession,
  extractChatReplyFromJob,
  extractHermesResumeSession,
  getMonitorMessage,
} from '../utils/agentChatParsing';

const TERMINAL_JOB_STATUSES = new Set(['completed', 'failed', 'cancelled']);

type ChatBubble = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
};

function messagesToBubbles(messages: AgentConversationMessage[]): ChatBubble[] {
  return messages
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({
      id: `msg-${m.id}`,
      role: m.role as 'user' | 'assistant',
      text: m.text,
    }));
}

function applyConversationState(
  conversation: AgentConversation,
  setters: {
    setConversationId: (id: string) => void;
    setChatBubbles: React.Dispatch<React.SetStateAction<ChatBubble[]>>;
    setHermesResumeSession: (s: string | null) => void;
  },
) {
  setters.setConversationId(conversation.conversation_id);
  setters.setChatBubbles(messagesToBubbles(conversation.messages));
  setters.setHermesResumeSession(cleanHermesResumeSession(conversation.hermes_resume_session));
}

export const AgentConsolePage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobId = searchParams.get('job');
  const conversationParam = searchParams.get('conversation');

  const [conversationId, setConversationId] = useState<string | null>(conversationParam);
  const [message, setMessage] = useState('');
  const [orchestratorReply, setOrchestratorReply] = useState<string | null>(null);
  const [chatBubbles, setChatBubbles] = useState<ChatBubble[]>([]);
  const [hermesResumeSession, setHermesResumeSession] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [events, setEvents] = useState<FactoryJobEvent[]>([]);
  const [trace, setTrace] = useState<HermesTrace | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [conversationLoading, setConversationLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chatOnly, setChatOnly] = useState(true);

  const streamCloseRef = useRef<(() => void) | null>(null);
  const lastAssistantReplyKeyRef = useRef<string | null>(null);
  const activeJobIdRef = useRef<string | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  const allowed = isFactoryOperator();
  const openChat = allowed;
  const showObservatory = isSuperadmin();
  const showOpsChrome = !chatOnly;

  const assistantChatReply = extractChatReplyFromJob(events, orchestratorReply);
  const waitingForReply =
    Boolean(jobId) &&
    (loading || (jobStatus === 'running' && !assistantChatReply && !error));

  const conversationSetters = {
    setConversationId,
    setChatBubbles,
    setHermesResumeSession,
  };

  const updateSearchParams = useCallback(
    (next: { job?: string | null; conversation?: string | null }) => {
      const params: Record<string, string> = {};
      const conv = next.conversation ?? conversationId;
      const job = next.job !== undefined ? next.job : jobId;
      if (conv) params.conversation = conv;
      if (job) params.job = job;
      setSearchParams(params, { replace: true });
    },
    [conversationId, jobId, setSearchParams],
  );

  useEffect(() => {
    if (!allowed) {
      setConversationLoading(false);
      return;
    }

    let cancelled = false;

    const load = async () => {
      setConversationLoading(true);
      try {
        const conversation = conversationParam
          ? await getAgentConversation(conversationParam)
          : await getActiveAgentConversation();
        if (cancelled) return;
        applyConversationState(conversation, conversationSetters);
        if (!conversationParam) {
          updateSearchParams({ conversation: conversation.conversation_id });
        }
      } catch {
        if (!cancelled) {
          setError('Could not load conversation history.');
        }
      } finally {
        if (!cancelled) setConversationLoading(false);
      }
    };

    load().catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, [allowed, conversationParam, updateSearchParams]);

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
        id: `assistant-live-${Date.now()}`,
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
    if (!conversationId || !jobId || !TERMINAL_JOB_STATUSES.has(jobStatus || '')) return;

    syncAgentConversationJob(conversationId, jobId)
      .then((conversation) => {
        applyConversationState(conversation, conversationSetters);
      })
      .catch(() => undefined);
  }, [conversationId, jobId, jobStatus]);

  useEffect(() => {
    chatScrollRef.current?.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [chatBubbles, waitingForReply]);

  const loadHermesTrace = useCallback(async (id: string) => {
    if (!showObservatory) return;
    try {
      const t = await getHermesTrace(id);
      setTrace(t);
      setTraceError(null);
    } catch (err: unknown) {
      setTrace(null);
      setTraceError(err instanceof Error ? err.message : 'Observatory unavailable');
    }
  }, [showObservatory]);

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
    streamCloseRef.current?.();
    streamCloseRef.current = null;

    if (!jobId || !allowed) {
      return undefined;
    }

    setEvents([]);
    setTrace(null);
    setTraceError(null);
    setJobStatus(null);
    setOrchestratorReply(null);

    let cancelled = false;

    const start = async () => {
      try {
        const initial = await getFactoryJob(jobId);
        if (cancelled) return;
        setEvents(initial.events);
        applyJobUpdate(initial);

        if (TERMINAL_JOB_STATUSES.has(initial.status)) {
          await loadHermesTrace(jobId);
          return;
        }

        const close = streamFactoryJob(
          jobId,
          {
            onEvent: (ev) => {
              setEvents((prev) => {
                if (prev.some((existing) => existing.id === ev.id)) return prev;
                return [...prev, ev];
              });
            },
            onComplete: (status) => {
              setJobStatus(status);
              getFactoryJob(jobId)
                .then((job) => {
                  setEvents(job.events);
                  applyJobUpdate(job);
                })
                .catch(() => undefined);
              loadHermesTrace(jobId).catch(() => undefined);
            },
            onError: () => {
              if (cancelled) return;
              getFactoryJob(jobId)
                .then((job) => {
                  setEvents(job.events);
                  applyJobUpdate(job);
                })
                .catch(() => undefined);
            },
          },
        );
        streamCloseRef.current = close;
      } catch {
        if (!cancelled) setJobStatus('unknown');
      }
    };

    start().catch(() => undefined);

    return () => {
      cancelled = true;
      streamCloseRef.current?.();
      streamCloseRef.current = null;
    };
  }, [jobId, allowed, loadHermesTrace, applyJobUpdate]);

  useEffect(() => {
    return () => {
      streamCloseRef.current?.();
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
      const chatContext: Record<string, unknown> = {
        project: 'Three-HK',
        conversation_id: conversationId,
      };
      const resume = cleanHermesResumeSession(hermesResumeSession);
      if (resume) {
        chatContext.hermes_resume_session = resume;
      }
      const res = await postAgentChat(userText, chatContext);
      if (res.conversation_id) {
        setConversationId(res.conversation_id);
      }
      updateSearchParams({
        job: res.job_id,
        conversation: res.conversation_id || conversationId,
      });
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

  const handleNewConversation = async () => {
    streamCloseRef.current?.();
    activeJobIdRef.current = null;
    lastAssistantReplyKeyRef.current = null;
    setEvents([]);
    setTrace(null);
    setTraceError(null);
    setOrchestratorReply(null);
    setJobStatus(null);
    setError(null);

    try {
      const conversation = await createAgentConversation();
      applyConversationState(conversation, conversationSetters);
      updateSearchParams({ job: null, conversation: conversation.conversation_id });
    } catch {
      setHermesResumeSession(null);
      setChatBubbles([]);
      setConversationId(null);
      updateSearchParams({ job: null, conversation: null });
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

  const gridClass = chatOnly
    ? 'grid grid-cols-1 gap-6'
    : `grid grid-cols-1 gap-6 ${
        jobId && openChat ? 'lg:grid-cols-12' : 'lg:grid-cols-3'
      }`;

  const chatColClass = chatOnly
    ? ''
    : jobId && openChat
      ? 'lg:col-span-7'
      : 'lg:col-span-2';

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Agent Console</h1>
            <p className="text-gray-600 mt-1">
              {openChat
                ? 'Open chat with the QA Orchestrator — any message is forwarded to the factory node. Prefix with ! to run a structured command (e.g. !drain backlog).'
                : 'Structured factory commands only.'}
            </p>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={chatOnly}
              onChange={(e) => setChatOnly(e.target.checked)}
              className="rounded border-gray-300 text-blue-700 focus:ring-blue-500"
            />
            Chat only
          </label>
        </div>

        <div className={gridClass}>
          <section className={`bg-white rounded-lg shadow p-6 ${chatColClass}`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Agent Chat</h2>
              {openChat && (chatBubbles.length > 0 || hermesResumeSession || conversationId) && (
                <button
                  type="button"
                  onClick={() => handleNewConversation().catch(() => undefined)}
                  className="text-sm text-gray-600 hover:text-gray-900 hover:underline"
                >
                  New conversation
                </button>
              )}
            </div>
            {conversationLoading && (
              <p className="text-xs text-gray-500 mb-3">Loading conversation…</p>
            )}
            {hermesResumeSession && (
              <p className="text-xs text-gray-500 mb-3">
                Hermes session active — follow-up messages keep chat context.
              </p>
            )}
            <div
              ref={chatScrollRef}
              className="mb-4 border border-gray-200 rounded-lg bg-gray-50 p-4 min-h-[280px] max-h-[520px] overflow-y-auto space-y-3"
            >
              {chatBubbles.length === 0 && !waitingForReply && !conversationLoading ? (
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
                disabled={loading || conversationLoading}
              />
              <button
                type="submit"
                disabled={loading || conversationLoading}
                className="px-4 py-2 bg-blue-700 text-white rounded-lg hover:bg-blue-800 disabled:opacity-50"
              >
                {loading ? 'Sending…' : 'Send'}
              </button>
            </form>
            {error && (
              <p className="mt-4 text-sm text-red-700 bg-red-50 border border-red-100 rounded p-3">{error}</p>
            )}
            {showOpsChrome && jobId && (
              <p className="mt-2 text-xs text-gray-500">
                Job: <code>{jobId}</code>
                {jobStatus && <> · Status: <strong>{jobStatus}</strong></>}
              </p>
            )}
          </section>

          {showOpsChrome && (
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
          )}

          {showOpsChrome && jobId && showObservatory && (
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
