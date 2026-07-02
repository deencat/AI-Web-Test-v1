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
  reply: string;
}

export async function postAgentChat(message: string, context: Record<string, unknown> = {}): Promise<AgentChatResponse> {
  const { data } = await api.post<AgentChatResponse>('/agent/chat', { message, context });
  return data;
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
