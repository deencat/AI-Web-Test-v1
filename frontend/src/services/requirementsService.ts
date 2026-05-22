/**
 * Requirements Service -- ReqIQ proxy (Phase 2 + s5.2 extensions)
 *
 * Calls the AI Web Test backend proxy endpoints at /api/v1/requirements/*
 * which forward requests to ReqIQ (port 3001) using a service account.
 * Callers never talk to ReqIQ directly.
 *
 * UI labels per handoff s6:
 *   Project  -> Workspace
 *   Source   -> Document
 *   latestCompositeScore -> Quality score
 */
import api from './api';

export interface ReqIQProject {
  id: string;
  name: string;
  createdAt: string;
}

export interface CapabilityItem {
  key: string;
  label: string;
  description?: string;
  sortOrder?: number;
}

export interface CoverageMatrixCapability {
  key: string;
  label: string;
  counts: { DRAFT: number; REVIEWED: number; BASELINE: number; SUPERSEDED: number };
  total: number;
}

export interface CoverageMatrix {
  projectId: string;
  capabilities: CoverageMatrixCapability[];
  uncategorized: { counts: { DRAFT: number; REVIEWED: number; BASELINE: number; SUPERSEDED: number }; total: number };
  totals: { DRAFT: number; REVIEWED: number; BASELINE: number; SUPERSEDED: number; total: number };
}

export interface WikiSuggestFeedbackItem {
  id: string;
  decision: 'accept' | 'reject' | 'accept_edited';
  reason?: string;
  reasonTags?: string[];
  requirementTitle?: string;
  capabilityKey?: string;
  createdAt: string;
}

export interface ReqIQRequirement {
  id: string;
  title: string;
  body?: string;
  state: 'DRAFT' | 'REVIEWED' | 'BASELINE' | 'SUPERSEDED';
  latestCompositeScore?: number;
  // Sprint 8a UAT scenario fields
  capabilityKey?: string;
  scenarioKind?: 'positive' | 'negative' | 'edge' | 'smoke';
  verificationLevel?: 'document_grounded' | 'behaviour_only' | 'smoke';
  customerOutcome?: string;
  // Sprint 8b wiki-suggest fields
  isWikiSuggest?: boolean;
  wikiSuggestBatchId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ReqIQRevision {
  id: string;
  requirementId: string;
  revisionIndex: number;
  title: string;
  body: string;
  compositeScore?: number;
  createdAt: string;
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
  status: 'ready' | 'insufficient' | 'no_sources' | 'error';
  threshold?: number;
  wikiContent?: string;
  wikiSource?: 'compiled' | 'rag' | 'none';
  wikiStale?: boolean;
  wikiCompiledAt?: string;
  wikiEmbeddingIndexVersion?: number;
  matchedRequirement?: {
    id: string;
    title: string;
    state: string;
    latestCompositeScore: number;
  };
  missing?: string[];
}

export interface WikiResult {
  projectId: string;
  markdown: string;
  compileStatus: 'ok' | 'edited' | 'no_sources' | 'failed';
  wikiStale: boolean;
  compiledAt?: string;
  citationCount?: number;
  embeddingIndexVersion?: number;
  featureHint?: string | null;
}

export interface WikiUpdateResult extends WikiResult {
  /** Present when indexInRag was true — summary of RAG upsert and reindex */
  ragSync?: {
    sourceId: string;
    chunkCount: number;
    reindex: Record<string, unknown>;
  };
}

export interface SuggestTestsResult {
  created: SuggestedTest[];
  errors: string[];
  model?: string;
}

const BASE = '/requirements';

const requirementsService = {
  // -- Workspaces -----------------------------------------------------------

  async listProjects(): Promise<ReqIQProject[]> {
    const res = await api.get<ReqIQProject[]>(`${BASE}/projects`);
    return res.data;
  },

  async listCapabilities(projectId: string): Promise<CapabilityItem[]> {
    const res = await api.get<CapabilityItem[]>(`${BASE}/${projectId}/capabilities`);
    return res.data;
  },

  async createProject(name: string): Promise<ReqIQProject> {
    const res = await api.post<ReqIQProject>(`${BASE}/projects`, { name });
    return res.data;
  },

  async getProject(projectId: string): Promise<ReqIQProject> {
    const res = await api.get<ReqIQProject>(`${BASE}/projects/${projectId}`);
    return res.data;
  },

  async updateProject(projectId: string, name: string): Promise<ReqIQProject> {
    const res = await api.patch<ReqIQProject>(`${BASE}/projects/${projectId}`, { name });
    return res.data;
  },

  // -- Requirements ---------------------------------------------------------

  async listRequirements(projectId: string, params?: { isWikiSuggest?: boolean; wikiSuggestBatchId?: string }): Promise<ReqIQRequirement[]> {
    const res = await api.get<ReqIQRequirement[]>(`${BASE}/${projectId}/requirements`, { params });
    return res.data;
  },

  async createRequirement(
    projectId: string,
    fields: Pick<ReqIQRequirement, 'title'> & Partial<Pick<ReqIQRequirement, 'body' | 'capabilityKey' | 'scenarioKind' | 'verificationLevel' | 'customerOutcome'>>,
  ): Promise<ReqIQRequirement> {
    const res = await api.post<ReqIQRequirement>(`${BASE}/${projectId}/requirements`, fields);
    return res.data;
  },

  async getRequirement(projectId: string, requirementId: string): Promise<ReqIQRequirement> {
    const res = await api.get<ReqIQRequirement>(`${BASE}/${projectId}/requirements/${requirementId}`);
    return res.data;
  },

  async updateRequirement(
    projectId: string,
    requirementId: string,
    fields: Partial<Pick<ReqIQRequirement, 'title' | 'body' | 'capabilityKey' | 'scenarioKind' | 'verificationLevel' | 'customerOutcome'>>,
  ): Promise<ReqIQRequirement> {
    const res = await api.patch<ReqIQRequirement>(
      `${BASE}/${projectId}/requirements/${requirementId}`,
      fields,
    );
    return res.data;
  },

  async deleteRequirement(projectId: string, requirementId: string): Promise<void> {
    await api.delete(`${BASE}/${projectId}/requirements/${requirementId}`);
  },

  async transitionRequirement(projectId: string, requirementId: string, state: string): Promise<ReqIQRequirement> {
    const res = await api.post<ReqIQRequirement>(
      `${BASE}/${projectId}/requirements/${requirementId}/transition`,
      { state },
    );
    return res.data;
  },

  async getRequirementAudit(projectId: string, requirementId: string): Promise<unknown[]> {
    const res = await api.get<unknown[]>(`${BASE}/${projectId}/requirements/${requirementId}/audit`);
    return res.data;
  },

  // -- Revisions + IQ -------------------------------------------------------

  async listRevisions(projectId: string, requirementId: string): Promise<ReqIQRevision[]> {
    const res = await api.get<ReqIQRevision[]>(
      `${BASE}/${projectId}/requirements/${requirementId}/revisions`,
    );
    return res.data;
  },

  async getRevision(projectId: string, requirementId: string, revisionIndex: number): Promise<ReqIQRevision> {
    const res = await api.get<ReqIQRevision>(
      `${BASE}/${projectId}/requirements/${requirementId}/revisions/${revisionIndex}`,
    );
    return res.data;
  },

  async runStubIq(projectId: string, requirementId: string, revisionIndex: number): Promise<unknown> {
    const res = await api.post(
      `${BASE}/${projectId}/requirements/${requirementId}/revisions/${revisionIndex}/stub-iq`,
    );
    return res.data;
  },

  async runLlmIq(projectId: string, requirementId: string, revisionIndex: number): Promise<unknown> {
    const res = await api.post(
      `${BASE}/${projectId}/requirements/${requirementId}/revisions/${revisionIndex}/llm-iq`,
    );
    return res.data;
  },

  // -- RAG query ------------------------------------------------------------

  async ragQuery(projectId: string, query: string, limit = 8): Promise<RagQueryResult> {
    const res = await api.post<RagQueryResult>(`${BASE}/${projectId}/query`, { query, limit });
    return res.data;
  },

  // -- Sources (Documents) --------------------------------------------------

  async uploadSources(projectId: string, files: File[]): Promise<UploadSourcesResult> {
    const form = new FormData();
    files.forEach(f => form.append('files', f, f.name));
    // Must delete the default 'Content-Type: application/json' set on the axios instance
    // so axios can auto-generate 'multipart/form-data; boundary=...' for this request.
    const res = await api.post<UploadSourcesResult>(
      `${BASE}/${projectId}/sources/upload`,
      form,
      { headers: { 'Content-Type': undefined } },
    );
    return res.data;
  },

  async listSources(projectId: string): Promise<ReqIQSource[]> {
    const res = await api.get<ReqIQSource[]>(`${BASE}/${projectId}/sources`);
    return res.data;
  },

  async deleteSource(projectId: string, sourceId: string): Promise<void> {
    await api.delete(`${BASE}/${projectId}/sources/${sourceId}`);
  },

  // -- Suggested tests ------------------------------------------------------

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

  async listSuggestedTests(projectId: string, requirementId: string): Promise<SuggestedTest[]> {
    const res = await api.get<SuggestedTest[]>(
      `${BASE}/${projectId}/requirements/${requirementId}/suggested-tests`,
    );
    return res.data;
  },

  async createSuggestedTest(
    projectId: string,
    requirementId: string,
    title: string,
    payload?: SuggestedTest['payload'],
  ): Promise<SuggestedTest> {
    const res = await api.post<SuggestedTest>(
      `${BASE}/${projectId}/requirements/${requirementId}/suggested-tests`,
      { title, ...(payload ? { payload } : {}) },
    );
    return res.data;
  },

  async getSuggestedTest(
    projectId: string,
    requirementId: string,
    suggestedTestId: string,
  ): Promise<SuggestedTest> {
    const res = await api.get<SuggestedTest>(
      `${BASE}/${projectId}/requirements/${requirementId}/suggested-tests/${suggestedTestId}`,
    );
    return res.data;
  },

  async updateSuggestedTest(
    projectId: string,
    requirementId: string,
    suggestedTestId: string,
    fields: Partial<Pick<SuggestedTest, 'title' | 'payload'>>,
  ): Promise<SuggestedTest> {
    const res = await api.patch<SuggestedTest>(
      `${BASE}/${projectId}/requirements/${requirementId}/suggested-tests/${suggestedTestId}`,
      fields,
    );
    return res.data;
  },

  async deleteSuggestedTest(
    projectId: string,
    requirementId: string,
    suggestedTestId: string,
  ): Promise<void> {
    await api.delete(
      `${BASE}/${projectId}/requirements/${requirementId}/suggested-tests/${suggestedTestId}`,
    );
  },

  // -- IQ / readiness -------------------------------------------------------

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

  // -- Wiki (Test context) --------------------------------------------------

  async getWiki(projectId: string): Promise<WikiResult> {
    const res = await api.get<WikiResult>(`${BASE}/projects/${projectId}/wiki`);
    return res.data;
  },

  async patchWiki(
    projectId: string,
    markdown: string,
    indexInRag = false,
  ): Promise<WikiUpdateResult> {
    const res = await api.patch<WikiUpdateResult>(
      `${BASE}/projects/${projectId}/wiki`,
      { markdown, indexInRag },
    );
    return res.data;
  },

  async compileWiki(projectId: string, feature = ''): Promise<WikiResult> {
    const params: Record<string, string> = {};
    if (feature) params.feature = feature;
    const res = await api.post<WikiResult>(
      `${BASE}/projects/${projectId}/wiki/compile`,
      undefined,
      { params },
    );
    return res.data;
  },

  // -- Inc 2: Wiki-suggest (Sprint 8b / 8c) --------------------------------

  async suggestFromWiki(
    projectId: string,
    opts?: { capabilityKeys?: string[]; maxScenarios?: number; hints?: string },
  ): Promise<{ batchId: string; created: ReqIQRequirement[]; dedupeDropped: number; feedbackApplied: number }> {
    const res = await api.post(`${BASE}/${projectId}/requirements/suggest-from-wiki`, opts ?? {});
    return res.data;
  },

  async wikiFeedback(
    projectId: string,
    requirementId: string,
    decision: 'accept' | 'reject',
    opts?: { reason?: string; reasonTags?: string[] },
  ): Promise<unknown> {
    const res = await api.post(`${BASE}/${projectId}/requirements/${requirementId}/wiki-feedback`, {
      decision,
      ...opts,
    });
    return res.data;
  },

  async getWikiSuggestProfile(projectId: string): Promise<unknown> {
    const res = await api.get(`${BASE}/${projectId}/wiki-suggest-profile`);
    return res.data;
  },

  async listWikiSuggestFeedback(projectId: string, opts?: { limit?: number; offset?: number }): Promise<{ items: WikiSuggestFeedbackItem[]; total: number }> {
    const res = await api.get(`${BASE}/${projectId}/wiki-suggest-feedback`, { params: opts });
    return res.data;
  },

  async deleteAllWikiSuggestFeedback(projectId: string): Promise<void> {
    await api.delete(`${BASE}/${projectId}/wiki-suggest-feedback`, { params: { confirm: '1' } });
  },

  async deleteDraftRequirements(projectId: string): Promise<{ deleted: number }> {
    const res = await api.delete<{ deleted: number }>(`${BASE}/${projectId}/requirements/drafts`, { params: { confirm: '1' } });
    return res.data;
  },

  // -- Inc 3: Coverage matrix, source-refs, export (Sprint 8c) -------------

  async getCoverageMatrix(projectId: string): Promise<CoverageMatrix> {
    const res = await api.get<CoverageMatrix>(`${BASE}/${projectId}/coverage-matrix`);
    return res.data;
  },

  async listSourceRefs(projectId: string, requirementId: string): Promise<unknown[]> {
    const res = await api.get<unknown[]>(`${BASE}/${projectId}/requirements/${requirementId}/source-refs`);
    return res.data;
  },

  async exportProject(projectId: string, params?: Record<string, string>): Promise<Blob> {
    const res = await api.get(`${BASE}/${projectId}/export`, {
      params,
      responseType: 'blob',
    });
    return res.data as Blob;
  },

  async exportRequirement(projectId: string, requirementId: string, params?: Record<string, string>): Promise<Blob> {
    const res = await api.get(`${BASE}/${projectId}/requirements/${requirementId}/export`, {
      params,
      responseType: 'blob',
    });
    return res.data as Blob;
  },
};

export default requirementsService;
