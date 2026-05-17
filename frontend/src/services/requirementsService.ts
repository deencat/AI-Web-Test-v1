/**
 * Requirements Service — ReqIQ proxy (Phase 2)
 *
 * Calls the AI Web Test backend proxy endpoints at /api/v1/requirements/*
 * which forward requests to ReqIQ (port 3001) using a service account.
 * Callers never talk to ReqIQ directly.
 */
import api from './api';

export interface ReqIQProject {
  id: string;
  name: string;
  createdAt: string;
}

export interface ReqIQRequirement {
  id: string;
  title: string;
  body?: string;
  state: 'DRAFT' | 'REVIEWED' | 'BASELINE' | 'SUPERSEDED';
  createdAt: string;
  updatedAt: string;
}

export interface RagCitation {
  index?: number;
  chunkId?: string;
  sourceId?: string;
  sourceFilename: string;
  chunkIndex: number;
  score?: number;
  excerpt?: string;
}

export interface SuggestedTestStep {
  action: string;
  expected?: string;
}

export interface SuggestedTest {
  id?: string;
  title: string;
  payload?: {
    preconditions?: string[];
    steps: SuggestedTestStep[];
    oracle?: string;
    automation?: { viable: boolean; markers?: string[] };
  };
}

export interface RagQueryResult {
  content: string;
  citations: RagCitation[];
  suggestedTests?: SuggestedTest[];
}

export interface ReqIQSource {
  id: string;
  originalFilename: string;
  status: string;
  createdAt?: string;
}

export interface UploadSourcesResult {
  projectId: string;
  uploadedCount: number;
  rejectedCount: number;
  uploaded: ReqIQSource[];
  rejected: Array<{ filename: string; reason: string }>;
}

export interface LatestIqResult {
  requirementId: string;
  latestCompositeScore: number;
  latestRevisionIndex: number;
  updatedAt: string;
}

export interface ReadinessResult {
  projectId: string;
  readinessScore: number;
  status: 'ready' | 'insufficient' | 'no_sources';
  wikiContent?: string;
  matchedRequirement?: {
    id: string;
    title: string;
    state: string;
    latestCompositeScore: number;
  };
  missing?: string[];
}

export interface SuggestTestsResult {
  created: SuggestedTest[];
  errors: string[];
  model?: string;
}

const BASE = '/requirements';

const requirementsService = {
  async listProjects(): Promise<ReqIQProject[]> {
    const res = await api.get<ReqIQProject[]>(`${BASE}/projects`);
    return res.data;
  },

  async listRequirements(projectId: string): Promise<ReqIQRequirement[]> {
    const res = await api.get<ReqIQRequirement[]>(`${BASE}/${projectId}/requirements`);
    return res.data;
  },

  async ragQuery(projectId: string, query: string, limit = 8): Promise<RagQueryResult> {
    const res = await api.post<RagQueryResult>(`${BASE}/${projectId}/query`, { query, limit });
    return res.data;
  },

  async uploadSources(projectId: string, files: File[]): Promise<UploadSourcesResult> {
    const form = new FormData();
    files.forEach(f => form.append('files', f, f.name));
    const res = await api.post<UploadSourcesResult>(
      `${BASE}/${projectId}/sources/upload`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return res.data;
  },

  async listSources(projectId: string): Promise<ReqIQSource[]> {
    const res = await api.get<ReqIQSource[]>(`${BASE}/${projectId}/sources`);
    return res.data;
  },

  async suggestTests(
    projectId: string,
    requirementId: string,
    maxTests = 3,
    hints = '',
  ): Promise<SuggestTestsResult> {
    const res = await api.post<SuggestTestsResult>(
      `${BASE}/${projectId}/requirements/${requirementId}/suggest-tests`,
      { maxTests, hints },
    );
    return res.data;
  },

  async getLatestIq(projectId: string, requirementId: string): Promise<LatestIqResult> {
    const res = await api.get<LatestIqResult>(
      `${BASE}/${projectId}/requirements/${requirementId}/latest-iq`,
    );
    return res.data;
  },

  async getReadiness(projectId: string, query = '', feature = ''): Promise<ReadinessResult> {
    const params: Record<string, string> = {};
    if (query) params.query = query;
    if (feature) params.feature = feature;
    const res = await api.get<ReadinessResult>(`${BASE}/${projectId}/readiness`, { params });
    return res.data;
  },
};

export default requirementsService;
