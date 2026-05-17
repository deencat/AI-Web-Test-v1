/**
 * KnowledgeBasePage - ReqIQ-backed requirements workspace
 *
 * Labels per handoff s6:
 *   Project -> Workspace
 *   Source  -> Document
 *   latestCompositeScore -> Quality score
 *
 * Features (Phase 2 + s5.2):
 *   - Workspace select / create / rename
 *   - Document upload + list
 *   - Readiness panel
 *   - RAG query (content field)
 *   - Requirement list with state badge + quality score
 *   - Create / edit / lifecycle-transition requirement
 *   - Run Stub IQ / LLM IQ per requirement
 *   - Suggest tests -> Crawl & Save pre-fill
 *   - "Open ReqIQ Advanced" external link
 */
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, Plus, Pencil, Check, X, ChevronDown } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import requirementsService from '../services/requirementsService';
import type {
  ReqIQProject,
  ReqIQRequirement,
  ReqIQSource,
  LatestIqResult,
  ReadinessResult,
  RagQueryResult,
  SuggestedTest,
} from '../services/requirementsService';

// ---------------------------------------------------------------------------
// Tiny shared components
// ---------------------------------------------------------------------------

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

function QualityBadge({ score }: { score: number }) {
  const colour = score >= 80 ? 'text-green-700' : score >= 60 ? 'text-yellow-600' : 'text-red-600';
  return <span className={`text-xs font-bold ${colour}`}>Quality {score}</span>;
}

function SectionCard({ title, actions, children }: {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h2>
        {actions}
      </div>
      {children}
    </div>
  );
}

function SmallBtn({ onClick, disabled, variant = 'default', children }: {
  onClick: () => void;
  disabled?: boolean;
  variant?: 'default' | 'danger' | 'primary';
  children: React.ReactNode;
}) {
  const base = 'text-xs font-medium px-2 py-1 rounded border transition-colors disabled:opacity-40';
  const variants: Record<string, string> = {
    default: 'border-gray-300 text-gray-600 hover:bg-gray-50',
    primary: 'border-blue-600 text-blue-700 hover:bg-blue-50',
    danger: 'border-red-300 text-red-600 hover:bg-red-50',
  };
  return (
    <button className={`${base} ${variants[variant]}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

const REQIQ_APP_URL = 'http://localhost:8080/app';
const LIFECYCLE_STATES = ['DRAFT', 'REVIEWED', 'BASELINE', 'SUPERSEDED'];

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export const KnowledgeBasePage: React.FC = () => {
  const navigate = useNavigate();

  // -- workspaces -----------------------------------------------------------
  const [projects, setProjects] = useState<ReqIQProject[]>([]);
  const [projectId, setProjectId] = useState('');
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [creatingProject, setCreatingProject] = useState(false);
  const [renamingProject, setRenamingProject] = useState(false);
  const [renameValue, setRenameValue] = useState('');

  // -- documents ------------------------------------------------------------
  const [sources, setSources] = useState<ReqIQSource[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // -- readiness ------------------------------------------------------------
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [readinessQuery, setReadinessQuery] = useState('');

  // -- rag ------------------------------------------------------------------
  const [ragQuery, setRagQuery] = useState('');
  const [ragResult, setRagResult] = useState<RagQueryResult | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);

  // -- requirements ---------------------------------------------------------
  const [requirements, setRequirements] = useState<ReqIQRequirement[]>([]);
  const [reqLoading, setReqLoading] = useState(false);
  const [iqData, setIqData] = useState<Record<string, LatestIqResult>>({});
  const [showNewReq, setShowNewReq] = useState(false);
  const [newReqTitle, setNewReqTitle] = useState('');
  const [newReqBody, setNewReqBody] = useState('');
  const [creatingReq, setCreatingReq] = useState(false);
  const [editingReqId, setEditingReqId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);
  const [transitioningFor, setTransitioningFor] = useState<string | null>(null);
  const [runningIqFor, setRunningIqFor] = useState<string | null>(null);
  const [suggestingFor, setSuggestingFor] = useState<string | null>(null);

  // -- load projects --------------------------------------------------------
  useEffect(() => {
    requirementsService.listProjects()
      .then(data => {
        setProjects(data);
        if (data.length > 0) setProjectId(data[0].id);
      })
      .catch(err => setProjectsError(err?.response?.data?.detail ?? err.message ?? 'Failed to load workspaces'))
      .finally(() => setProjectsLoading(false));
  }, []);

  // -- load data when project changes ---------------------------------------
  useEffect(() => {
    if (!projectId) return;
    setSourcesLoading(true);
    setReqLoading(true);
    setIqData({});
    setReadiness(null);

    requirementsService.listSources(projectId)
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setSourcesLoading(false));

    requirementsService.listRequirements(projectId)
      .then(async reqs => {
        setRequirements(reqs);
        const scores: Record<string, LatestIqResult> = {};
        await Promise.allSettled(
          reqs.map(async r => {
            try {
              const iq = await requirementsService.getLatestIq(projectId, r.id);
              scores[r.id] = iq;
            } catch { /* ignore */ }
          })
        );
        setIqData(scores);
      })
      .catch(() => setRequirements([]))
      .finally(() => setReqLoading(false));
  }, [projectId]);

  // -- workspace actions ----------------------------------------------------
  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setCreatingProject(true);
    try {
      const p = await requirementsService.createProject(newProjectName.trim());
      setProjects(prev => [...prev, p]);
      setProjectId(p.id);
      setNewProjectName('');
      setShowNewProject(false);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Failed to create workspace: ${msg ?? String(err)}`);
    } finally {
      setCreatingProject(false);
    }
  }

  async function handleRenameProject() {
    if (!renameValue.trim() || !projectId) return;
    setRenamingProject(false);
    try {
      const updated = await requirementsService.updateProject(projectId, renameValue.trim());
      setProjects(prev => prev.map(p => p.id === projectId ? updated : p));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Rename failed: ${msg ?? String(err)}`);
    }
    setRenameValue('');
  }

  // -- document upload ------------------------------------------------------
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

  // -- readiness ------------------------------------------------------------
  async function handleCheckReadiness() {
    if (!projectId) return;
    setReadinessLoading(true);
    try {
      const result = await requirementsService.getReadiness(projectId, readinessQuery);
      setReadiness(result);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Readiness check failed: ${msg ?? String(err)}`);
    } finally {
      setReadinessLoading(false);
    }
  }

  // -- rag ------------------------------------------------------------------
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

  // -- requirement CRUD -----------------------------------------------------
  async function handleCreateRequirement(e: React.FormEvent) {
    e.preventDefault();
    if (!newReqTitle.trim() || !projectId) return;
    setCreatingReq(true);
    try {
      const req = await requirementsService.createRequirement(projectId, newReqTitle.trim(), newReqBody.trim());
      setRequirements(prev => [req, ...prev]);
      setNewReqTitle('');
      setNewReqBody('');
      setShowNewReq(false);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Failed to create requirement: ${msg ?? String(err)}`);
    } finally {
      setCreatingReq(false);
    }
  }

  function startEditReq(req: ReqIQRequirement) {
    setEditingReqId(req.id);
    setEditTitle(req.title);
    setEditBody(req.body ?? '');
  }

  async function handleSaveEdit(req: ReqIQRequirement) {
    if (!editTitle.trim() || !projectId) return;
    setSavingEdit(true);
    try {
      const updated = await requirementsService.updateRequirement(projectId, req.id, {
        title: editTitle.trim(),
        body: editBody.trim(),
      });
      setRequirements(prev => prev.map(r => r.id === req.id ? updated : r));
      setEditingReqId(null);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Save failed: ${msg ?? String(err)}`);
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleTransition(req: ReqIQRequirement, state: string) {
    if (!projectId) return;
    setTransitioningFor(req.id);
    try {
      const updated = await requirementsService.transitionRequirement(projectId, req.id, state);
      setRequirements(prev => prev.map(r => r.id === req.id ? updated : r));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Transition failed: ${msg ?? String(err)}`);
    } finally {
      setTransitioningFor(null);
    }
  }

  // -- IQ actions -----------------------------------------------------------
  async function handleRunIq(req: ReqIQRequirement, type: 'stub' | 'llm') {
    if (!projectId) return;
    setRunningIqFor(req.id);
    try {
      const revIdx = iqData[req.id]?.latestRevisionIndex ?? 0;
      if (type === 'stub') {
        await requirementsService.runStubIq(projectId, req.id, revIdx);
      } else {
        await requirementsService.runLlmIq(projectId, req.id, revIdx);
      }
      // refresh IQ score
      const updated = await requirementsService.getLatestIq(projectId, req.id);
      setIqData(prev => ({ ...prev, [req.id]: updated }));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`IQ run failed: ${msg ?? String(err)}`);
    } finally {
      setRunningIqFor(null);
    }
  }

  // -- suggest tests --------------------------------------------------------
  async function handleSuggestTests(req: ReqIQRequirement) {
    if (!projectId) return;
    setSuggestingFor(req.id);
    try {
      const result = await requirementsService.suggestTests(projectId, req.id, 3);
      const first: SuggestedTest | undefined = result.created[0];
      if (!first) {
        alert('No tests were suggested for this requirement.');
        return;
      }
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
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Suggest tests failed: ${msg ?? String(err)}`);
    } finally {
      setSuggestingFor(null);
    }
  }

  // -- render ---------------------------------------------------------------
  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Knowledge Base</h1>
            <p className="text-sm text-gray-500">Requirements, documents and RAG powered by ReqIQ.</p>
          </div>
          <a
            href={REQIQ_APP_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 border border-blue-200 rounded-lg px-3 py-2 hover:bg-blue-50 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            Open ReqIQ Advanced
          </a>
        </div>

        {/* Workspace selector */}
        <SectionCard
          title="Workspace"
          actions={
            <button
              onClick={() => setShowNewProject(v => !v)}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
            >
              <Plus className="w-3 h-3" /> New
            </button>
          }
        >
          {projectsLoading ? (
            <p className="text-sm text-gray-400">Loading workspaces...</p>
          ) : projectsError ? (
            <p className="text-sm text-red-600">{projectsError}</p>
          ) : projects.length === 0 && !showNewProject ? (
            <p className="text-sm text-gray-400">No workspaces found in ReqIQ.</p>
          ) : (
            <>
              {projects.length > 0 && (
                <div className="flex items-center gap-2">
                  {renamingProject ? (
                    <>
                      <input
                        autoFocus
                        className="flex-1 max-w-xs border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={renameValue}
                        onChange={e => setRenameValue(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') handleRenameProject(); if (e.key === 'Escape') setRenamingProject(false); }}
                      />
                      <SmallBtn variant="primary" onClick={handleRenameProject}><Check className="w-3 h-3" /></SmallBtn>
                      <SmallBtn onClick={() => setRenamingProject(false)}><X className="w-3 h-3" /></SmallBtn>
                    </>
                  ) : (
                    <>
                      <select
                        value={projectId}
                        onChange={e => setProjectId(e.target.value)}
                        className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1 max-w-xs"
                      >
                        {projects.map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                      <SmallBtn
                        onClick={() => {
                          const current = projects.find(p => p.id === projectId);
                          setRenameValue(current?.name ?? '');
                          setRenamingProject(true);
                        }}
                      >
                        <Pencil className="w-3 h-3 inline" /> Rename
                      </SmallBtn>
                    </>
                  )}
                </div>
              )}
              {showNewProject && (
                <form onSubmit={handleCreateProject} className="flex items-center gap-2">
                  <input
                    autoFocus
                    placeholder="New workspace name"
                    className="flex-1 max-w-xs border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={newProjectName}
                    onChange={e => setNewProjectName(e.target.value)}
                  />
                  <SmallBtn variant="primary" onClick={() => {}} disabled={creatingProject}>
                    {creatingProject ? '...' : 'Create'}
                  </SmallBtn>
                  <SmallBtn onClick={() => setShowNewProject(false)}><X className="w-3 h-3" /></SmallBtn>
                </form>
              )}
            </>
          )}
        </SectionCard>

        {projectId && (
          <>
            {/* Documents */}
            <SectionCard title="Documents">
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
                <p className="text-sm text-gray-400">Loading documents...</p>
              ) : sources.length === 0 ? (
                <p className="text-sm text-gray-400">No documents yet. Upload a file to get started.</p>
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

            {/* Readiness */}
            <SectionCard title="Readiness">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={readinessQuery}
                  onChange={e => setReadinessQuery(e.target.value)}
                  placeholder="Optional: describe a feature to check (e.g. 5G voucher purchase)"
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleCheckReadiness}
                  disabled={readinessLoading}
                  className="px-4 py-2 bg-blue-700 text-white text-sm font-semibold rounded-lg hover:bg-blue-800 disabled:opacity-50 transition-colors"
                >
                  {readinessLoading ? '...' : 'Check'}
                </button>
              </div>
              {readiness && (
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className={`text-2xl font-bold ${readiness.readinessScore >= 80 ? 'text-green-700' : readiness.readinessScore >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {readiness.readinessScore}%
                    </span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${readiness.status === 'ready' ? 'bg-green-100 text-green-700' : readiness.status === 'insufficient' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-600'}`}>
                      {readiness.status.replace('_', ' ')}
                    </span>
                  </div>
                  {readiness.wikiContent && (
                    <div className="rounded-md bg-gray-50 border border-gray-200 p-3 text-xs text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {readiness.wikiContent}
                    </div>
                  )}
                  {readiness.missing && readiness.missing.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mb-1">Missing coverage</p>
                      <ul className="list-disc list-inside space-y-0.5">
                        {readiness.missing.map((m, i) => (
                          <li key={i} className="text-xs text-gray-500">{m}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </SectionCard>

            {/* RAG query */}
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
                            {c.sourceFilename} &middot; chunk {c.chunkIndex}{c.score != null ? ` \u00b7 score ${c.score.toFixed(2)}` : ''}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </SectionCard>

            {/* Requirements */}
            <SectionCard
              title="Requirements"
              actions={
                <button
                  onClick={() => setShowNewReq(v => !v)}
                  className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                >
                  <Plus className="w-3 h-3" /> New
                </button>
              }
            >
              {/* New requirement form */}
              {showNewReq && (
                <form onSubmit={handleCreateRequirement} className="space-y-2 rounded-md border border-blue-200 bg-blue-50 p-3">
                  <input
                    autoFocus
                    placeholder="Requirement title *"
                    className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={newReqTitle}
                    onChange={e => setNewReqTitle(e.target.value)}
                    required
                  />
                  <textarea
                    placeholder="Body / description (optional)"
                    className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    value={newReqBody}
                    onChange={e => setNewReqBody(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={creatingReq || !newReqTitle.trim()}
                      className="px-3 py-1.5 bg-blue-700 text-white text-xs font-semibold rounded-lg hover:bg-blue-800 disabled:opacity-50"
                    >
                      {creatingReq ? 'Creating...' : 'Create Requirement'}
                    </button>
                    <SmallBtn onClick={() => setShowNewReq(false)}>Cancel</SmallBtn>
                  </div>
                </form>
              )}

              {reqLoading ? (
                <p className="text-sm text-gray-400">Loading requirements...</p>
              ) : requirements.length === 0 ? (
                <p className="text-sm text-gray-400">No requirements found. Create one above.</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {requirements.map(req => {
                    const iq = iqData[req.id];
                    const isEditing = editingReqId === req.id;
                    const isRunningIq = runningIqFor === req.id;
                    const isSuggesting = suggestingFor === req.id;
                    const isTransitioning = transitioningFor === req.id;

                    return (
                      <li key={req.id} className="py-4 space-y-2">
                        {isEditing ? (
                          <div className="space-y-2">
                            <input
                              className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                              value={editTitle}
                              onChange={e => setEditTitle(e.target.value)}
                            />
                            <textarea
                              className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                              rows={3}
                              value={editBody}
                              onChange={e => setEditBody(e.target.value)}
                              placeholder="Body / description"
                            />
                            <div className="flex gap-2">
                              <SmallBtn variant="primary" onClick={() => handleSaveEdit(req)} disabled={savingEdit}>
                                {savingEdit ? 'Saving...' : 'Save'}
                              </SmallBtn>
                              <SmallBtn onClick={() => setEditingReqId(null)}>Cancel</SmallBtn>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-start justify-between gap-4">
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-gray-900">{req.title}</p>
                                {req.body && (
                                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{req.body}</p>
                                )}
                                <div className="flex items-center gap-2 mt-1">
                                  <StateBadge state={req.state} />
                                  {iq && <QualityBadge score={iq.latestCompositeScore} />}
                                </div>
                              </div>
                              <SmallBtn onClick={() => startEditReq(req)}>
                                <Pencil className="w-3 h-3 inline" /> Edit
                              </SmallBtn>
                            </div>

                            {/* Lifecycle transition */}
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-xs text-gray-400 mr-1">Transition:</span>
                              {LIFECYCLE_STATES.filter(s => s !== req.state).map(s => (
                                <SmallBtn
                                  key={s}
                                  onClick={() => handleTransition(req, s)}
                                  disabled={isTransitioning}
                                >
                                  <ChevronDown className="w-3 h-3 inline" /> {s}
                                </SmallBtn>
                              ))}
                            </div>

                            {/* IQ + test actions */}
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <SmallBtn
                                variant="default"
                                onClick={() => handleRunIq(req, 'stub')}
                                disabled={isRunningIq}
                              >
                                {isRunningIq ? '...' : 'Run Stub IQ'}
                              </SmallBtn>
                              <SmallBtn
                                variant="default"
                                onClick={() => handleRunIq(req, 'llm')}
                                disabled={isRunningIq}
                              >
                                {isRunningIq ? '...' : 'Run LLM IQ'}
                              </SmallBtn>
                              <SmallBtn
                                variant="primary"
                                onClick={() => handleSuggestTests(req)}
                                disabled={isSuggesting}
                              >
                                {isSuggesting ? 'Generating...' : 'Suggest Tests'}
                              </SmallBtn>
                            </div>
                          </>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </SectionCard>
          </>
        )}
      </div>
    </Layout>
  );
};

export default KnowledgeBasePage;
