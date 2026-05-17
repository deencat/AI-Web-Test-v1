/**
 * KnowledgeBasePage — Phase 2 rewrite
 *
 * Replaced the local SQLite KB UI with a ReqIQ-backed requirements view.
 * Route and component name are unchanged; only the content was rewritten.
 *
 * Panels:
 *   1. Project selector
 *   2. Sources list + upload
 *   3. RAG query box
 *   4. Requirements list (with IQ score + state badge)
 *   5. "Generate suggested tests" per requirement -> navigates to Crawl & Save pre-filled
 */
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import requirementsService from '../services/requirementsService';
import type {
  ReqIQProject,
  ReqIQRequirement,
  ReqIQSource,
  RagQueryResult,
  SuggestedTest,
} from '../services/requirementsService';

// tiny helpers

function StateBadge({ state }: { state: string }) {
  const colours: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-600',
    REVIEWED: 'bg-blue-100 text-blue-700',
    BASELINE: 'bg-green-100 text-green-700',
    SUPERSEDED: 'bg-red-100 text-red-600',
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colours[state] ?? 'bg-gray-100 text-gray-600'}`}>
      {state}
    </span>
  );
}

function IqBadge({ score }: { score: number }) {
  const colour = score >= 80 ? 'text-green-700' : score >= 60 ? 'text-yellow-600' : 'text-red-600';
  return <span className={`text-xs font-bold ${colour}`}>IQ {score}</span>;
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
      <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h2>
      {children}
    </div>
  );
}

export const KnowledgeBasePage: React.FC = () => {
  const navigate = useNavigate();

  const [projects, setProjects] = useState<ReqIQProject[]>([]);
  const [projectId, setProjectId] = useState('');
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState<string | null>(null);

  const [sources, setSources] = useState<ReqIQSource[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [requirements, setRequirements] = useState<ReqIQRequirement[]>([]);
  const [reqLoading, setReqLoading] = useState(false);
  const [iqScores, setIqScores] = useState<Record<string, number>>({});

  const [ragQuery, setRagQuery] = useState('');
  const [ragResult, setRagResult] = useState<RagQueryResult | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);

  const [suggestingFor, setSuggestingFor] = useState<string | null>(null);

  useEffect(() => {
    requirementsService.listProjects()
      .then(data => {
        setProjects(data);
        if (data.length > 0) setProjectId(data[0].id);
      })
      .catch(err => setProjectsError(err?.response?.data?.detail ?? err.message ?? 'Failed to load projects'))
      .finally(() => setProjectsLoading(false));
  }, []);

  useEffect(() => {
    if (!projectId) return;
    setSourcesLoading(true);
    setReqLoading(true);
    setIqScores({});

    requirementsService.listSources(projectId)
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setSourcesLoading(false));

    requirementsService.listRequirements(projectId)
      .then(async reqs => {
        setRequirements(reqs);
        const scores: Record<string, number> = {};
        await Promise.allSettled(
          reqs.map(async r => {
            try {
              const iq = await requirementsService.getLatestIq(projectId, r.id);
              scores[r.id] = iq.latestCompositeScore;
            } catch { /* ignore */ }
          })
        );
        setIqScores(scores);
      })
      .catch(() => setRequirements([]))
      .finally(() => setReqLoading(false));
  }, [projectId]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (!files.length || !projectId) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const result = await requirementsService.uploadSources(projectId, files);
      setUploadResult(`Uploaded ${result.uploadedCount} file(s). Processing...`);
      setTimeout(() => {
        requirementsService.listSources(projectId).then(setSources).catch(() => {});
      }, 3000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setUploadResult(`Upload failed: ${msg ?? String(err)}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  async function handleRagQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!ragQuery.trim() || !projectId) return;
    setRagLoading(true);
    setRagError(null);
    setRagResult(null);
    try {
      const result = await requirementsService.ragQuery(projectId, ragQuery.trim());
      setRagResult(result);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setRagError(msg ?? 'RAG query failed');
    } finally {
      setRagLoading(false);
    }
  }

  async function handleSuggestTests(req: ReqIQRequirement) {
    if (!projectId) return;
    setSuggestingFor(req.id);
    try {
      const result = await requirementsService.suggestTests(projectId, req.id, 3);
      const first: SuggestedTest | undefined = result.created[0];
      if (!first) return;
      const steps = first.payload?.steps ?? [];
      const oracle = first.payload?.oracle ?? '';
      const instruction = [
        ...steps.map(s => s.action),
        oracle ? `STOP when: ${oracle}` : '',
      ].filter(Boolean).join('\n');
      const params = new URLSearchParams({
        test_title: first.title,
        test_description: `Generated from ReqIQ requirement: ${req.title}`,
        user_instruction: instruction,
      });
      navigate(`/crawl-and-save?${params.toString()}`);
    } catch {
      // silently ignore
    } finally {
      setSuggestingFor(null);
    }
  }

  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Knowledge Base</h1>
          <p className="text-sm text-gray-500">Requirements, source documents and RAG powered by ReqIQ.</p>
        </div>

        <SectionCard title="Project">
          {projectsLoading ? (
            <p className="text-sm text-gray-400">Loading projects...</p>
          ) : projectsError ? (
            <p className="text-sm text-red-600">{projectsError}</p>
          ) : projects.length === 0 ? (
            <p className="text-sm text-gray-400">No projects found in ReqIQ.</p>
          ) : (
            <select
              value={projectId}
              onChange={e => setProjectId(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full max-w-sm"
            >
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
        </SectionCard>

        {projectId && (
          <>
            <SectionCard title="Source Documents">
              <div className="flex items-center gap-3">
                <label className={`cursor-pointer px-4 py-2 bg-blue-700 text-white text-sm font-semibold rounded-lg hover:bg-blue-800 transition-colors ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
                  {uploading ? 'Uploading...' : 'Upload Files'}
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    accept=".pdf,.docx,.doc,.md,.txt,.pptx,.png,.jpg"
                    onChange={handleUpload}
                    disabled={uploading}
                  />
                </label>
                <span className="text-xs text-gray-400">PDF, DOCX, MD, TXT, PPTX, PNG</span>
              </div>
              {uploadResult && <p className="text-sm text-blue-700">{uploadResult}</p>}
              {sourcesLoading ? (
                <p className="text-sm text-gray-400">Loading sources...</p>
              ) : sources.length === 0 ? (
                <p className="text-sm text-gray-400">No source documents yet. Upload a file to get started.</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {sources.map(s => (
                    <li key={s.id} className="py-2 flex items-center justify-between">
                      <span className="text-sm text-gray-800 truncate max-w-xs">{s.originalFilename}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'ready' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                        {s.status}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard title="Ask a Question">
              <form onSubmit={handleRagQuery} className="flex gap-2">
                <input
                  type="text"
                  value={ragQuery}
                  onChange={e => setRagQuery(e.target.value)}
                  placeholder="What are the acceptance criteria for the 5G Voucher Plan purchase flow?"
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={ragLoading}
                />
                <button
                  type="submit"
                  disabled={ragLoading || !ragQuery.trim()}
                  className="px-4 py-2 bg-blue-700 text-white text-sm font-semibold rounded-lg hover:bg-blue-800 disabled:opacity-50 transition-colors"
                >
                  {ragLoading ? '...' : 'Ask'}
                </button>
              </form>
              {ragError && <p className="text-sm text-red-600">{ragError}</p>}
              {ragResult && (
                <div className="space-y-3">
                  <div className="rounded-md bg-gray-50 border border-gray-200 p-4 text-sm text-gray-800 whitespace-pre-wrap">
                    {ragResult.content}
                  </div>
                  {ragResult.citations.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">Sources</p>
                      <ul className="space-y-1">
                        {ragResult.citations.map((c, i) => (
                          <li key={i} className="text-xs text-gray-500">
                            {c.sourceFilename} · chunk {c.chunkIndex} · score {c.score.toFixed(2)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Requirements">
              {reqLoading ? (
                <p className="text-sm text-gray-400">Loading requirements...</p>
              ) : requirements.length === 0 ? (
                <p className="text-sm text-gray-400">No requirements found for this project.</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {requirements.map(req => (
                    <li key={req.id} className="py-3 flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{req.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <StateBadge state={req.state} />
                          {iqScores[req.id] !== undefined && <IqBadge score={iqScores[req.id]} />}
                        </div>
                      </div>
                      <button
                        onClick={() => handleSuggestTests(req)}
                        disabled={suggestingFor === req.id}
                        className="shrink-0 text-xs px-3 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                      >
                        {suggestingFor === req.id ? 'Generating...' : 'Suggest Tests'}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>
          </>
        )}
      </div>
    </Layout>
  );
};
