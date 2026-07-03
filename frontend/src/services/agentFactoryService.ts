import api from './api';

export interface FactoryJobEvent {
  id: number;
  event_type: string;
  profile?: string | null;
  message?: string | null;
  payload_summary?: Record<string, unknown> | null;
  llm_turns?: Record<string, unknown>[] | null;
  created_at: string;
}

export interface FactoryJob {
  job_id: string;
  job_type: string;
  project?: string | null;
  params?: Record<string, unknown> | null;
  status: string;
  error_message?: string | null;
  orchestrator_reply?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  events: FactoryJobEvent[];
}

export interface AgentChatResponse {
  job_id: string;
  conversation_id?: string | null;
  reply: string;
}

export interface AgentConversationMessage {
  id: number;
  role: 'user' | 'assistant' | 'system' | string;
  text: string;
  job_id?: string | null;
  created_at: string;
}

export interface AgentConversation {
  conversation_id: string;
  project?: string | null;
  hermes_resume_session?: string | null;
  is_active: boolean;
  messages: AgentConversationMessage[];
  created_at: string;
  updated_at: string;
}

export interface AgentConversationListItem {
  conversation_id: string;
  preview?: string | null;
  message_count: number;
  is_active: boolean;
  updated_at: string;
  created_at: string;
}

export async function postAgentChat(message: string, context: Record<string, unknown> = {}): Promise<AgentChatResponse> {
  const { data } = await api.post<AgentChatResponse>('/agent/chat', { message, context });
  return data;
}

export async function listAgentConversations(limit = 100): Promise<AgentConversationListItem[]> {
  const { data } = await api.get<{ items: AgentConversationListItem[] }>('/agent/conversations', {
    params: { limit },
  });
  return data.items;
}

export async function activateAgentConversation(conversationId: string): Promise<AgentConversation> {
  const { data } = await api.post<AgentConversation>(
    `/agent/conversations/${conversationId}/activate`,
  );
  return data;
}

export async function getActiveAgentConversation(project = 'Three-HK'): Promise<AgentConversation> {
  const { data } = await api.get<AgentConversation>('/agent/conversations/active', {
    params: { project },
  });
  return data;
}

export async function getAgentConversation(conversationId: string): Promise<AgentConversation> {
  const { data } = await api.get<AgentConversation>(`/agent/conversations/${conversationId}`);
  return data;
}

export async function createAgentConversation(project = 'Three-HK'): Promise<AgentConversation> {
  const { data } = await api.post<AgentConversation>('/agent/conversations/new', null, {
    params: { project },
  });
  return data;
}

export async function syncAgentConversationJob(
  conversationId: string,
  jobId: string,
): Promise<AgentConversation> {
  const { data } = await api.post<AgentConversation>(
    `/agent/conversations/${conversationId}/sync-job/${jobId}`,
  );
  return data;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

function factoryJobStreamUrl(jobId: string): string {
  const token = localStorage.getItem('token') || '';
  const base = API_BASE_URL.startsWith('http')
    ? API_BASE_URL
    : `${window.location.origin}${API_BASE_URL}`;
  return `${base}/agent/jobs/${jobId}/stream?token=${encodeURIComponent(token)}`;
}

/** Stream factory job events via SSE (lower latency than polling). */
export function streamFactoryJob(
  jobId: string,
  handlers: {
    onEvent: (event: FactoryJobEvent) => void;
    onComplete: (status: string) => void;
    onError?: () => void;
  },
): () => void {
  const source = new EventSource(factoryJobStreamUrl(jobId));

  source.addEventListener('job_event', (raw) => {
    try {
      const event = JSON.parse((raw as MessageEvent).data) as FactoryJobEvent;
      handlers.onEvent(event);
    } catch {
      handlers.onError?.();
    }
  });

  source.addEventListener('job_complete', (raw) => {
    try {
      const payload = JSON.parse((raw as MessageEvent).data) as { status?: string };
      handlers.onComplete(payload.status || 'completed');
    } catch {
      handlers.onComplete('completed');
    }
    source.close();
  });

  source.addEventListener('error', () => {
    handlers.onError?.();
    source.close();
  });

  return () => source.close();
}

export async function getFactoryJob(jobId: string): Promise<FactoryJob> {
  const { data } = await api.get<FactoryJob>(`/agent/jobs/${jobId}`);
  return data;
}

export async function createFactoryJob(body: {
  job_type: string;
  project?: string;
  params?: Record<string, unknown>;
}): Promise<{ job_id: string; status: string }> {
  const { data } = await api.post('/agent/jobs', body);
  return data;
}

/** Poll job events (JWT-friendly; SSE can be added in HF-6 with cookie auth). */
export const FACTORY_JOB_POLL_INTERVAL_MS = 3000;
export interface HealReviewItem {
  id: number;
  execution_id: number;
  test_case_id?: number | null;
  reason: string;
  status: string;
  created_at: string;
  resolved_at?: string | null;
  resolved_by_user_id?: number | null;
}

export interface HealReviewListResponse {
  items: HealReviewItem[];
  total: number;
}

export async function listHealReview(status?: string): Promise<HealReviewListResponse> {
  const { data } = await api.get<HealReviewListResponse>('/agent/heal-review', {
    params: status ? { status } : {},
  });
  return data;
}

export interface HermesTraceEvent {
  id: number;
  event_type: string;
  profile?: string | null;
  parent_profile?: string | null;
  message?: string | null;
  payload_summary?: Record<string, unknown> | null;
  payload_full?: Record<string, unknown> | null;
  llm_turns?: Record<string, unknown>[] | null;
  hermes_session_id?: string | null;
  created_at: string;
}

export interface HermesTrace {
  job_id: string;
  job_type: string;
  status: string;
  hermes_session_ids: string[];
  events: HermesTraceEvent[];
}

export async function getHermesTrace(jobId: string): Promise<HermesTrace> {
  const { data } = await api.get<HermesTrace>(`/agent/jobs/${jobId}/hermes-trace`);
  return data;
}

export async function resolveHealReviewItem(itemId: number): Promise<HealReviewItem> {
  const { data } = await api.patch<HealReviewItem>(`/agent/heal-review/${itemId}`, {
    status: 'resolved',
  });
  return data;
}

export async function pollFactoryJob(
  jobId: string,
  onEvent: (event: FactoryJobEvent) => void,
  onComplete: (status: string) => void,
  signal?: AbortSignal,
  onJobUpdate?: (job: FactoryJob) => void,
): Promise<void> {
  let afterId = 0;
  const terminal = new Set(['completed', 'failed', 'cancelled']);

  while (!signal?.aborted) {
    const job = await getFactoryJob(jobId);
    onJobUpdate?.(job);
    for (const ev of job.events) {
      if (ev.id > afterId) {
        onEvent(ev);
        afterId = ev.id;
      }
    }
    if (terminal.has(job.status)) {
      onComplete(job.status);
      return;
    }
    await new Promise((r) => setTimeout(r, FACTORY_JOB_POLL_INTERVAL_MS));
  }
}
