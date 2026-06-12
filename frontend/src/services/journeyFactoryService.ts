import api from './api';

export interface JourneyRegistryEntry {
  id: number;
  slug: string;
  project: string;
  name: string;
  feature_url: string;
  tags?: string[] | null;
  capability_keys?: string[] | null;
  reference_test_id?: number | null;
  requires_login: boolean;
  stop_at_page_hint?: string | null;
}

export interface JourneyRegistryListResponse {
  project_meta?: {
    project: string;
    reqiq_project_id?: string | null;
    default_env_config?: Record<string, unknown> | null;
  } | null;
  items: JourneyRegistryEntry[];
  total: number;
}

export interface JourneyBacklogItem {
  id: number;
  project: string;
  journey_slug: string;
  status: string;
  priority: number;
  params?: Record<string, unknown> | null;
  factory_job_id?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JourneyBacklogListResponse {
  items: JourneyBacklogItem[];
  total: number;
}

export interface JourneySnapshotStatus {
  has_baseline: boolean;
  material_change: boolean;
  summary: string;
  last_captured_at?: string | null;
}

export async function getRegistrySnapshotStatus(
  project?: string,
): Promise<Record<string, JourneySnapshotStatus>> {
  const { data } = await api.get<Record<string, JourneySnapshotStatus>>(
    '/agent/registry/snapshot-status',
    { params: project ? { project } : undefined },
  );
  return data;
}

export async function listJourneyRegistry(project?: string): Promise<JourneyRegistryListResponse> {
  const { data } = await api.get<JourneyRegistryListResponse>('/agent/registry', {
    params: project ? { project } : undefined,
  });
  return data;
}

export async function createJourneyRegistryEntry(body: {
  slug: string;
  project: string;
  name: string;
  feature_url: string;
  tags?: string[];
  capability_keys?: string[];
  reference_test_id?: number | null;
  requires_login?: boolean;
  stop_at_page_hint?: string | null;
}): Promise<JourneyRegistryEntry> {
  const { data } = await api.post<JourneyRegistryEntry>('/agent/registry', body);
  return data;
}

export async function deleteJourneyRegistryEntry(entryId: number): Promise<void> {
  await api.delete(`/agent/registry/${entryId}`);
}

export async function listJourneyBacklog(params?: {
  status?: string;
  project?: string;
  limit?: number;
}): Promise<JourneyBacklogListResponse> {
  const { data } = await api.get<JourneyBacklogListResponse>('/agent/backlog', { params });
  return data;
}

export async function enqueueJourney(body: {
  journey_slug: string;
  project?: string;
  priority?: number;
}): Promise<JourneyBacklogItem> {
  const { data } = await api.post<JourneyBacklogItem>('/agent/backlog', body);
  return data;
}
