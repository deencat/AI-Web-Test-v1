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
  WikiResult,
  RagQueryResult,
  SuggestedTest,
  CapabilityItem,
  CoverageMatrix,
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
  const [deletingSourceId, setDeletingSourceId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // -- readiness ------------------------------------------------------------
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [readinessQuery, setReadinessQuery] = useState('');

  // -- wiki (Test context) --------------------------------------------------
  const [wiki, setWiki] = useState<WikiResult | null>(null);
  const [wikiLoading, setWikiLoading] = useState(false);
  const [compilingWiki, setCompilingWiki] = useState(false);
  const [wikiError, setWikiError] = useState<string | null>(null);

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
  const [newReqCapabilityKey, setNewReqCapabilityKey] = useState('');
  const [newReqScenarioKind, setNewReqScenarioKind] = useState('');
  const [newReqVerificationLevel, setNewReqVerificationLevel] = useState('');
  const [newReqCustomerOutcome, setNewReqCustomerOutcome] = useState('');
  const [creatingReq, setCreatingReq] = useState(false);
  const [deletingReqId, setDeletingReqId] = useState<string | null>(null);
  const [editingReqId, setEditingReqId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);
  const [transitioningFor, setTransitioningFor] = useState<string | null>(null);
  const [runningIqFor, setRunningIqFor] = useState<string | null>(null);
  const [suggestingFor, setSuggestingFor] = useState<string | null>(null);

  // -- wiki-suggest (Inc 2) -------------------------------------------------
  const [generatingWikiDrafts, setGeneratingWikiDrafts] = useState(false);
  const [wikiDraftBatchId, setWikiDraftBatchId] = useState<string | null>(null);
  const [givingFeedbackFor, setGivingFeedbackFor] = useState<string | null>(null);

  // -- coverage + export (Inc 3) --------------------------------------------
  const [coverageMatrix, setCoverageMatrix] = useState<CoverageMatrix | null>(null);
  const [loadingCoverage, setLoadingCoverage] = useState(false);
  const [exportingProject, setExportingProject] = useState(false);

  // -- capabilities list (Sprint 8a) ----------------------------------------
  const [capabilities, setCapabilities] = useState<CapabilityItem[]>([]);

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
    setWiki(null);
    setWikiError(null);

    // Load wiki (Test context) immediately on workspace switch
    setWikiLoading(true);
    requirementsService.getWiki(projectId)
      .then(setWiki)
      .catch(() => setWiki(null))
      .finally(() => setWikiLoading(false));

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

    requirementsService.listCapabilities(projectId)
      .then(setCapabilities)
      .catch(() => setCapabilities([]));
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
      const data = (err as { response?: { data?: unknown } })?.response?.data;
      const msg = typeof data === 'object' && data !== null && 'detail' in data
        ? (typeof (data as { detail: unknown }).detail === 'string'
            ? (data as { detail: string }).detail
            : JSON.stringify((data as { detail: unknown }).detail))
        : String(err);
      setUploadResult(`Upload failed: ${msg}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  // -- delete document ------------------------------------------------------
  async function handleDeleteSource(sourceId: string, filename: string) {
    if (!projectId) return;
    if (!window.confirm(`Remove document "${filename}"?\n\nThis deletes the file and its search index entries. Other documents are not affected.`)) return;
    setDeletingSourceId(sourceId);
    try {
      await requirementsService.deleteSource(projectId, sourceId);
      setSources(prev => prev.filter(s => s.id !== sourceId));
    } catch (err: unknown) {
      const data = (err as { response?: { data?: unknown } })?.response?.data;
      const msg = typeof data === 'object' && data !== null && 'detail' in data
        ? JSON.stringify((data as { detail: unknown }).detail)
        : String(err);
      alert(`Delete failed: ${msg}`);
    } finally {
      setDeletingSourceId(null);
    }
  }

  // -- readiness ------------------------------------------------------------
  async function handleCheckReadiness() {
    if (!projectId) return;
    setReadinessLoading(true);
    try {
      const result = await requirementsService.getReadiness(projectId, readinessQuery);
      setReadiness(result);
      // Sync wiki state from readiness wikiContent when wiki is not yet loaded
      if (!wiki && result.wikiContent) {
        setWiki({
          projectId,
          markdown: result.wikiContent,
          compileStatus: 'ok',
          wikiStale: result.wikiStale ?? false,
          compiledAt: result.wikiCompiledAt,
        });
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Readiness check failed: ${msg ?? String(err)}`);
    } finally {
      setReadinessLoading(false);
    }
  }

  // -- wiki (Test context) --------------------------------------------------
  async function handleCompileWiki() {
    if (!projectId) return;
    setCompilingWiki(true);
    setWikiError(null);
    try {
      const result = await requirementsService.compileWiki(projectId);
      setWiki(result);
    } catch (err: unknown) {
      const data = (err as { response?: { data?: unknown } })?.response?.data;
      const msg = typeof data === 'object' && data !== null && 'detail' in data
        ? JSON.stringify((data as { detail: unknown }).detail)
        : String(err);
      setWikiError(`Compile failed: ${msg}`);
    } finally {
      setCompilingWiki(false);
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
      const req = await requirementsService.createRequirement(projectId, {
        title: newReqTitle.trim(),
        body: newReqBody.trim() || undefined,
        capabilityKey: newReqCapabilityKey.trim() || undefined,
        scenarioKind: (newReqScenarioKind || undefined) as ReqIQRequirement['scenarioKind'],
        verificationLevel: (newReqVerificationLevel || undefined) as ReqIQRequirement['verificationLevel'],
        customerOutcome: newReqCustomerOutcome.trim() || undefined,
      });
      setRequirements(prev => [req, ...prev]);
      setNewReqTitle('');
      setNewReqBody('');
      setNewReqCapabilityKey('');
      setNewReqScenarioKind('');
      setNewReqVerificationLevel('');
      setNewReqCustomerOutcome('');
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

  async function handleLoadCoverage() {
    if (!projectId) return;
    setLoadingCoverage(true);
    try {
      const matrix = await requirementsService.getCoverageMatrix(projectId);
      setCoverageMatrix(matrix);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Coverage matrix failed: ${msg ?? String(err)}`);
    } finally {
      setLoadingCoverage(false);
    }
  }

  async function handleExportProject(format: 'markdown' | 'pdf' | 'manifest') {
    if (!projectId) return;
    setExportingProject(true);
    try {
      const blob = await requirementsService.exportProject(projectId, { format });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export.${format === 'markdown' ? 'md' : format === 'pdf' ? 'pdf' : 'json'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Export failed: ${msg ?? String(err)}`);
    } finally {
      setExportingProject(false);
    }
  }

  async function handleGenerateWikiDrafts() {
    if (!projectId) return;
    setGeneratingWikiDrafts(true);
    try {
      const result = await requirementsService.suggestFromWiki(projectId);
      setWikiDraftBatchId(result.batchId);
      // prepend newly created requirements
      setRequirements(prev => [...result.created, ...prev]);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Generate drafts failed: ${msg ?? String(err)}`);
    } finally {
      setGeneratingWikiDrafts(false);
    }
  }

  async function handleWikiFeedback(req: ReqIQRequirement, decision: 'accept' | 'reject') {
    if (!projectId) return;
    setGivingFeedbackFor(req.id);
    try {
      await requirementsService.wikiFeedback(projectId, req.id, decision);
      if (decision === 'reject') {
        setRequirements(prev => prev.filter(r => r.id !== req.id));
      } else {
        // accepted — just remove the wiki-suggest badge by re-fetching or toggling local state
        setRequirements(prev =>
          prev.map(r => r.id === req.id ? { ...r, isWikiSuggest: false } : r),
        );
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Feedback failed: ${msg ?? String(err)}`);
    } finally {
      setGivingFeedbackFor(null);
    }
  }

  async function handleDeleteRequirement(req: ReqIQRequirement) {
    if (!projectId) return;
    if (!confirm(`Delete requirement "${req.title}"? This cannot be undone.`)) return;
    setDeletingReqId(req.id);
    try {
      await requirementsService.deleteRequirement(projectId, req.id);
      setRequirements(prev => prev.filter(r => r.id !== req.id));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Delete failed: ${msg ?? String(err)}`);
    } finally {
      setDeletingReqId(null);
    }
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
                    <li key={s.id} className="py-2 flex items-center justify-between gap-2">
                      <span className="text-sm text-gray-800 truncate max-w-xs">{s.originalFilename}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'ready' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                          {s.status}
                        </span>
                        <SmallBtn
                          variant="danger"
                          onClick={() => handleDeleteSource(s.id, s.originalFilename)}
                          disabled={deletingSourceId === s.id}
                        >
                          {deletingSourceId === s.id ? 'Removing…' : 'Remove'}
                        </SmallBtn>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            {/* Readiness */}
            {/* Test context (compiled wiki) */}
            <SectionCard
              title="Test context"
              actions={
                <SmallBtn
                  onClick={handleCompileWiki}
                  disabled={compilingWiki || !projectId}
                  variant="default"
                >
                  {compilingWiki ? 'Refreshing…' : 'Refresh'}
                </SmallBtn>
              }
            >
              {wikiError && <p className="text-sm text-red-600">{wikiError}</p>}
              {wikiLoading ? (
                <p className="text-sm text-gray-400">Loading Test context…</p>
              ) : !wiki ? (
                <p className="text-sm text-gray-400">No Test context yet — upload documents and wait for indexing.</p>
              ) : (
                <div className="space-y-2">
                  {/* wikiSource banner */}
                  {wiki.wikiStale && (
                    <div className="flex items-center gap-2 rounded-md bg-orange-50 border border-orange-200 px-3 py-2 text-xs text-orange-700">
                      ⚠ Documents or index changed — Test context may be outdated. Click Refresh to recompile.
                    </div>
                  )}
                  {/* compile status chip */}
                  {wiki.compileStatus !== 'ok' && (
                    <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
                      {wiki.compileStatus === 'no_sources'
                        ? 'No documents indexed yet. Upload a file and wait for reindex.'
                        : 'Test context failed to compile. Try refreshing.'}
                    </div>
                  )}
                  {wiki.compileStatus === 'ok' && wiki.markdown && (
                    <div className="rounded-md bg-gray-50 border border-gray-200 p-3 text-xs text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto font-mono leading-relaxed">
                      {wiki.markdown}
                    </div>
                  )}
                  <div className="flex items-center gap-3 text-xs text-gray-400">
                    {wiki.citationCount != null && <span>Based on {wiki.citationCount} source excerpt{wiki.citationCount !== 1 ? 's' : ''}</span>}
                    {wiki.compiledAt && <span>· Compiled {new Date(wiki.compiledAt).toLocaleString()}</span>}
                  </div>
                </div>
              )}
            </SectionCard>

            {/* Ready for testing? */}
            <SectionCard title="Ready for testing?">
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
                    {readiness.wikiSource === 'rag' && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-50 text-yellow-700 border border-yellow-200">
                        provisional — upload documents and wait for indexing
                      </span>
                    )}
                    {readiness.wikiStale && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-orange-50 text-orange-700 border border-orange-200">
                        ⚠ Test context may be outdated
                      </span>
                    )}
                  </div>
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

            {/* Coverage matrix + Export (Inc 3) */}
            <SectionCard
              title="Coverage & Export"
              actions={
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleLoadCoverage}
                    disabled={loadingCoverage}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                  >
                    {loadingCoverage ? '...' : 'Refresh coverage'}
                  </button>
                  <button
                    onClick={() => handleExportProject('markdown')}
                    disabled={exportingProject}
                    className="text-xs text-green-600 hover:text-green-800 disabled:opacity-50"
                  >
                    ↓ MD
                  </button>
                  <button
                    onClick={() => handleExportProject('pdf')}
                    disabled={exportingProject}
                    className="text-xs text-green-600 hover:text-green-800 disabled:opacity-50"
                  >
                    ↓ PDF
                  </button>
                  <button
                    onClick={() => handleExportProject('manifest')}
                    disabled={exportingProject}
                    className="text-xs text-green-600 hover:text-green-800 disabled:opacity-50"
                  >
                    ↓ Manifest
                  </button>
                </div>
              }
            >
              {coverageMatrix ? (
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-100 text-gray-600">
                      <th className="text-left px-2 py-1 font-semibold">Capability</th>
                      <th className="px-2 py-1 text-center">Draft</th>
                      <th className="px-2 py-1 text-center">Reviewed</th>
                      <th className="px-2 py-1 text-center">Baseline</th>
                      <th className="px-2 py-1 text-center">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {coverageMatrix.capabilities.map(cap => (
                      <tr key={cap.key} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="px-2 py-1 font-medium text-gray-800">{cap.label}</td>
                        <td className={`px-2 py-1 text-center ${cap.counts.DRAFT > 0 ? 'text-yellow-700 font-semibold' : 'text-gray-400'}`}>{cap.counts.DRAFT}</td>
                        <td className={`px-2 py-1 text-center ${cap.counts.REVIEWED > 0 ? 'text-blue-700 font-semibold' : 'text-gray-400'}`}>{cap.counts.REVIEWED}</td>
                        <td className={`px-2 py-1 text-center ${cap.counts.BASELINE > 0 ? 'text-green-700 font-semibold' : 'text-gray-400'}`}>{cap.counts.BASELINE}</td>
                        <td className="px-2 py-1 text-center font-semibold">{cap.total}</td>
                      </tr>
                    ))}
                    {coverageMatrix.uncategorized.total > 0 && (
                      <tr className="border-t border-gray-100 italic text-gray-500">
                        <td className="px-2 py-1">Uncategorized</td>
                        <td className="px-2 py-1 text-center">{coverageMatrix.uncategorized.counts.DRAFT}</td>
                        <td className="px-2 py-1 text-center">{coverageMatrix.uncategorized.counts.REVIEWED}</td>
                        <td className="px-2 py-1 text-center">{coverageMatrix.uncategorized.counts.BASELINE}</td>
                        <td className="px-2 py-1 text-center font-semibold">{coverageMatrix.uncategorized.total}</td>
                      </tr>
                    )}
                    <tr className="border-t-2 border-gray-300 bg-gray-50 font-semibold">
                      <td className="px-2 py-1">Total</td>
                      <td className="px-2 py-1 text-center">{coverageMatrix.totals.DRAFT}</td>
                      <td className="px-2 py-1 text-center">{coverageMatrix.totals.REVIEWED}</td>
                      <td className="px-2 py-1 text-center">{coverageMatrix.totals.BASELINE}</td>
                      <td className="px-2 py-1 text-center">{coverageMatrix.totals.total}</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <p className="text-xs text-gray-400">Click "Refresh coverage" to load the coverage matrix.</p>
              )}
            </SectionCard>

            {/* Requirements */}
            <SectionCard
              title="Requirements"
              actions={
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleGenerateWikiDrafts}
                    disabled={generatingWikiDrafts}
                    className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 disabled:opacity-50"
                  >
                    {generatingWikiDrafts ? '...' : '✦ Generate drafts'}
                  </button>
                  <button
                    onClick={() => setShowNewReq(v => !v)}
                    className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                  >
                    <Plus className="w-3 h-3" /> New
                  </button>
                </div>
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
                  <input
                    placeholder="Customer outcome (optional)"
                    className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={newReqCustomerOutcome}
                    onChange={e => setNewReqCustomerOutcome(e.target.value)}
                  />
                  {capabilities.length > 0 ? (
                    <select
                      className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={newReqCapabilityKey}
                      onChange={e => setNewReqCapabilityKey(e.target.value)}
                    >
                      <option value="">Capability (optional)</option>
                      {capabilities.map(cap => (
                        <option key={cap.key} value={cap.key}>{cap.label}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      placeholder="Capability key (optional, e.g. purchase_journey)"
                      className="w-full border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={newReqCapabilityKey}
                      onChange={e => setNewReqCapabilityKey(e.target.value)}
                    />
                  )}
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={newReqScenarioKind}
                      onChange={e => setNewReqScenarioKind(e.target.value)}
                    >
                      <option value="">Scenario kind (optional)</option>
                      <option value="positive">positive</option>
                      <option value="negative">negative</option>
                      <option value="edge">edge</option>
                      <option value="smoke">smoke</option>
                    </select>
                    <select
                      className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={newReqVerificationLevel}
                      onChange={e => setNewReqVerificationLevel(e.target.value)}
                    >
                      <option value="">Verification level (optional)</option>
                      <option value="document_grounded">document_grounded</option>
                      <option value="behaviour_only">behaviour_only</option>
                      <option value="smoke">smoke</option>
                    </select>
                  </div>
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
                    const isDeleting = deletingReqId === req.id;

                    const scenarioKindColor: Record<string, string> = {
                      positive: 'bg-green-50 text-green-700 border-green-200',
                      negative: 'bg-red-50 text-red-700 border-red-200',
                      edge: 'bg-orange-50 text-orange-700 border-orange-200',
                      smoke: 'bg-gray-50 text-gray-600 border-gray-200',
                    };

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
                                {req.customerOutcome && (
                                  <p className="text-xs text-blue-600 mt-0.5 italic">{req.customerOutcome}</p>
                                )}
                                {req.body && (
                                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{req.body}</p>
                                )}
                                <div className="flex items-center gap-2 mt-1 flex-wrap">
                                  <StateBadge state={req.state} />
                                  {iq && <QualityBadge score={iq.latestCompositeScore} />}
                                  {req.scenarioKind && (
                                    <span className={`text-xs px-1.5 py-0.5 rounded-full border ${scenarioKindColor[req.scenarioKind] ?? 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                                      {req.scenarioKind}
                                    </span>
                                  )}
                                  {req.capabilityKey && (
                                    <span className="text-xs px-1.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                                      {req.capabilityKey}
                                    </span>
                                  )}
                                  {req.isWikiSuggest && (
                                    <span className="text-xs px-1.5 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-200">
                                      ✦ wiki draft
                                    </span>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-1">
                                <SmallBtn onClick={() => startEditReq(req)}>
                                  <Pencil className="w-3 h-3 inline" /> Edit
                                </SmallBtn>
                                {req.state === 'DRAFT' && (
                                  <SmallBtn
                                    variant="danger"
                                    onClick={() => handleDeleteRequirement(req)}
                                    disabled={isDeleting}
                                  >
                                    {isDeleting ? '...' : 'Delete'}
                                  </SmallBtn>
                                )}
                              </div>
                            </div>

                            {/* Wiki-suggest review actions */}
                            {req.isWikiSuggest && req.state === 'DRAFT' && (
                              <div className="flex items-center gap-2 px-2 py-1.5 rounded-md bg-violet-50 border border-violet-200">
                                <span className="text-xs text-violet-700 flex-1">AI-generated draft — review and accept or reject</span>
                                <SmallBtn
                                  variant="primary"
                                  onClick={() => handleWikiFeedback(req, 'accept')}
                                  disabled={givingFeedbackFor === req.id}
                                >
                                  ✓ Keep
                                </SmallBtn>
                                <SmallBtn
                                  variant="danger"
                                  onClick={() => handleWikiFeedback(req, 'reject')}
                                  disabled={givingFeedbackFor === req.id}
                                >
                                  ✗ Reject
                                </SmallBtn>
                              </div>
                            )}

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
