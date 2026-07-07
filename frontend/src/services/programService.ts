import api from './api';

export interface PlatformProfileSummary {
  name: string;
  title?: string | null;
}

export interface ProgramCreateRequest {
  slug: string;
  title: string;
  kind?: 'pilot' | 'production' | 'example';
  test_scope?: string;
  platform_profile?: string | null;
  registry_project?: string;
  initiative_title?: string;
}

export interface InitiativeSummary {
  id: string;
  kind: string;
  title: string;
  effective_from: string;
  effective_to?: string | null;
  resolved_effective_to?: string | null;
  relationship?: 'replace' | 'stack' | null;
  relates_to: string[];
  audience?: 'new_signups' | 'all' | 'existing_only' | null;
  capability_keys: string[];
  platform_components: string[];
  regression_tags: string[];
}

export interface ProgramSummary {
  slug: string;
  title: string;
  kind?: string | null;
  test_scope?: string | null;
  initiative_count: number;
  active_initiative_count: number;
}

export interface ProgramDetail {
  slug: string;
  program: Record<string, unknown>;
  platform_components: Array<{ id: string; title: string; modules?: string[] }>;
  reference_layers: Array<{
    id: string;
    title: string;
    automate: boolean;
    parity_note?: string | null;
  }>;
  initiatives: InitiativeSummary[];
  hub_gaps: Record<string, unknown>[];
  factory?: Record<string, unknown> | null;
  orchestration_suites: Record<string, unknown>[];
}

export interface InitiativeDetailResponse {
  program_slug: string;
  initiative: InitiativeSummary;
  raw?: Record<string, unknown> | null;
  journeys: Array<{
    id: number;
    slug: string;
    name: string;
    feature_url: string;
    tags?: string[] | null;
    retired: boolean;
  }>;
}

export async function listPlatformProfiles(): Promise<{ items: PlatformProfileSummary[] }> {
  const { data } = await api.get('/programs/platform-profiles');
  return data;
}

export async function createProgram(body: ProgramCreateRequest): Promise<{ slug: string; message: string }> {
  const { data } = await api.post('/programs', body);
  return data;
}

export async function listPrograms(): Promise<{ items: ProgramSummary[]; total: number }> {
  const { data } = await api.get('/programs');
  return data;
}

export async function getProgram(slug: string): Promise<ProgramDetail> {
  const { data } = await api.get<ProgramDetail>(`/programs/${slug}`);
  return data;
}

export async function getInitiative(slug: string, initiativeId: string): Promise<InitiativeDetailResponse> {
  const { data } = await api.get<InitiativeDetailResponse>(`/programs/${slug}/initiatives/${initiativeId}`);
  return data;
}

export async function getProgramManifestRaw(slug: string): Promise<{ slug: string; yaml_content: string }> {
  const { data } = await api.get(`/programs/${slug}/manifest`);
  return data;
}

export async function saveProgramManifest(slug: string, yamlContent: string): Promise<{ slug: string; message: string }> {
  const { data } = await api.put(`/programs/${slug}/manifest`, { yaml_content: yamlContent });
  return data;
}

export async function seedProgramJourneys(
  slug: string,
): Promise<{ slug: string; journeys_upserted: number; journeys_retired: number; tests_retired: number }> {
  const { data } = await api.post(`/programs/${slug}/seed-journeys`);
  return data;
}

export async function getReqIQOnboarding(slug: string): Promise<{ steps: string[] }> {
  const { data } = await api.get(`/programs/${slug}/reqiq-onboarding`);
  return data;
}

export async function getOrchestrationSuites(slug: string): Promise<{ suites: unknown[] }> {
  const { data } = await api.get(`/programs/${slug}/orchestration-suites`);
  return data;
}
