/**
 * Collapsible Advanced (ReqIQ) panel for product workspace.
 * Restores high-value Knowledge Base features without cluttering the 3-step flow.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronUp, ExternalLink, Pencil, Plus } from 'lucide-react';
import { Card } from '../common/Card';
import requirementsService from '../../services/requirementsService';
import type {
  CapabilityItem,
  CoverageMatrix,
  LatestIqResult,
  RagQueryResult,
  ReadinessResult,
  ReqIQIqSnapshot,
  ReqIQRequirement,
  ReqIQRevision,
  SuggestedTest,
  WikiSuggestFeedbackItem,
} from '../../services/requirementsService';

const REQIQ_APP_URL = 'http://localhost:8080/app';
const LIFECYCLE_STATES = ['DRAFT', 'REVIEWED', 'BASELINE', 'SUPERSEDED'];
const REJECT_TAGS = ['wrong_step', 'duplicate', 'out_of_scope', 'wrong_capability', 'too_vague', 'incorrect_outcome'];

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
    <button type="button" className={`${base} ${variants[variant]}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

function SubSection({ title, actions, children }: {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {actions}
      </div>
      {children}
    </div>
  );
}

export interface ProductAdvancedReqIQProps {
  projectId: string;
  onRequirementsChanged?: () => void;
}

export const ProductAdvancedReqIQ: React.FC<ProductAdvancedReqIQProps> = ({
  projectId,
  onRequirementsChanged,
}) => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const [readinessQuery, setReadinessQuery] = useState('');
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);

  const [ragQuery, setRagQuery] = useState('');
  const [ragResult, setRagResult] = useState<RagQueryResult | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);

  const [coverageMatrix, setCoverageMatrix] = useState<CoverageMatrix | null>(null);
  const [loadingCoverage, setLoadingCoverage] = useState(false);
  const [exportingProject, setExportingProject] = useState(false);

  const [capabilities, setCapabilities] = useState<CapabilityItem[]>([]);
  const [draftHints, setDraftHints] = useState('');
  const [draftCapabilityKeys, setDraftCapabilityKeys] = useState('');
  const [draftMaxScenarios, setDraftMaxScenarios] = useState(10);
  const [generatingWikiDrafts, setGeneratingWikiDrafts] = useState(false);
  const [deletingAllDrafts, setDeletingAllDrafts] = useState(false);
  const [wikiSuggestProfile, setWikiSuggestProfile] = useState<{
    totalAccepts?: number;
    totalRejects?: number;
    topReasonTags?: { tag: string }[];
  } | null>(null);
  const [showReviewHistory, setShowReviewHistory] = useState(false);
  const [feedbackHistory, setFeedbackHistory] = useState<WikiSuggestFeedbackItem[]>([]);
  const [feedbackTotal, setFeedbackTotal] = useState(0);
  const [loadingFeedback, setLoadingFeedback] = useState(false);
  const [clearingFeedback, setClearingFeedback] = useState(false);

  const [requirements, setRequirements] = useState<ReqIQRequirement[]>([]);
  const [reqLoading, setReqLoading] = useState(false);
  const [iqData, setIqData] = useState<Record<string, LatestIqResult>>({});
  const [iqBreakdown, setIqBreakdown] = useState<Record<string, ReqIQIqSnapshot>>({});

  const [showNewReq, setShowNewReq] = useState(false);
  const [newReqTitle, setNewReqTitle] = useState('');
  const [newReqBody, setNewReqBody] = useState('');
  const [newReqCustomerOutcome, setNewReqCustomerOutcome] = useState('');
  const [newReqCapabilityKey, setNewReqCapabilityKey] = useState('');
  const [newReqScenarioKind, setNewReqScenarioKind] = useState('');
  const [newReqVerificationLevel, setNewReqVerificationLevel] = useState('');
  const [creatingReq, setCreatingReq] = useState(false);

  const [editingReqId, setEditingReqId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const [reviewEditId, setReviewEditId] = useState<string | null>(null);
  const [reviewEditTitle, setReviewEditTitle] = useState('');
  const [reviewEditOutcome, setReviewEditOutcome] = useState('');
  const [savingReviewEdit, setSavingReviewEdit] = useState(false);

  const [givingFeedbackFor, setGivingFeedbackFor] = useState<string | null>(null);
  const [rejectDialogReq, setRejectDialogReq] = useState<ReqIQRequirement | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [rejectTags, setRejectTags] = useState<string[]>([]);

  const [runningIqFor, setRunningIqFor] = useState<string | null>(null);
  const [suggestingFor, setSuggestingFor] = useState<string | null>(null);
  const [transitioningFor, setTransitioningFor] = useState<string | null>(null);
  const [deletingReqId, setDeletingReqId] = useState<string | null>(null);

  const [toast, setToast] = useState<string | null>(null);
  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 5000);
  };

  const loadRequirements = useCallback(async (pid: string) => {
    setReqLoading(true);
    try {
      const reqs = await requirementsService.listRequirements(pid);
      setRequirements(reqs);
      const scores: Record<string, LatestIqResult> = {};
      await Promise.allSettled(
        reqs.map(async (r) => {
          try {
            scores[r.id] = await requirementsService.getLatestIq(pid, r.id);
          } catch { /* ignore */ }
        }),
      );
      setIqData(scores);
    } catch {
      setRequirements([]);
    } finally {
      setReqLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open || !projectId) return;
    setReadiness(null);
    setRagResult(null);
    setCoverageMatrix(null);
    loadRequirements(projectId);
    requirementsService.listCapabilities(projectId).then(setCapabilities).catch(() => setCapabilities([]));
    requirementsService.getWikiSuggestProfile(projectId)
      .then((p) => setWikiSuggestProfile(p as typeof wikiSuggestProfile))
      .catch(() => setWikiSuggestProfile(null));
  }, [open, projectId, loadRequirements]);

  const notifyParent = () => onRequirementsChanged?.();

  async function handleCheckReadiness() {
    setReadinessLoading(true);
    try {
      setReadiness(await requirementsService.getReadiness(projectId, readinessQuery));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Readiness check failed: ${msg ?? String(err)}`);
    } finally {
      setReadinessLoading(false);
    }
  }

  async function handleRagQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!ragQuery.trim()) return;
    setRagLoading(true);
    setRagError(null);
    setRagResult(null);
    try {
      setRagResult(await requirementsService.ragQuery(projectId, ragQuery.trim()));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setRagError(msg ?? 'Query failed');
    } finally {
      setRagLoading(false);
    }
  }

  async function handleLoadCoverage() {
    setLoadingCoverage(true);
    try {
      setCoverageMatrix(await requirementsService.getCoverageMatrix(projectId));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Coverage failed: ${msg ?? String(err)}`);
    } finally {
      setLoadingCoverage(false);
    }
  }

  async function handleExportProject(format: 'markdown' | 'pdf' | 'manifest') {
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
    setGeneratingWikiDrafts(true);
    const capKeys = draftCapabilityKeys.split(',').map((s) => s.trim()).filter(Boolean);
    try {
      const result = await requirementsService.suggestFromWiki(projectId, {
        hints: draftHints.trim() || undefined,
        capabilityKeys: capKeys.length > 0 ? capKeys : undefined,
        maxScenarios: draftMaxScenarios,
      });
      showToast(`Created ${result.created.length} draft(s)`);
      await loadRequirements(projectId);
      notifyParent();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : JSON.stringify(detail ?? err));
    } finally {
      setGeneratingWikiDrafts(false);
    }
  }

  async function handleDeleteAllDrafts() {
    if (!window.confirm('Delete all DRAFT scenarios? This cannot be undone.')) return;
    setDeletingAllDrafts(true);
    try {
      const result = await requirementsService.deleteDraftRequirements(projectId);
      showToast(`Deleted ${result.deleted} DRAFT scenario(s).`);
      await loadRequirements(projectId);
      notifyParent();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ?? String(err));
    } finally {
      setDeletingAllDrafts(false);
    }
  }

  async function handleLoadFeedbackHistory() {
    setLoadingFeedback(true);
    try {
      const result = await requirementsService.listWikiSuggestFeedback(projectId, { limit: 50 });
      const items = Array.isArray(result) ? result : result.items ?? [];
      setFeedbackHistory(items);
      setFeedbackTotal(Array.isArray(result) ? items.length : result.total ?? items.length);
    } finally {
      setLoadingFeedback(false);
    }
  }

  async function handleWikiFeedback(req: ReqIQRequirement, decision: 'accept' | 'reject', opts?: { reason?: string; reasonTags?: string[] }) {
    setGivingFeedbackFor(req.id);
    try {
      await requirementsService.wikiFeedback(projectId, req.id, decision, opts);
      if (decision === 'reject') {
        setRequirements((prev) => prev.filter((r) => r.id !== req.id));
      } else {
        try {
          const transitioned = await requirementsService.transitionRequirement(projectId, req.id, 'REVIEWED');
          setRequirements((prev) => prev.map((r) => (r.id === req.id ? transitioned : r)));
        } catch {
          setRequirements((prev) => prev.map((r) => (r.id === req.id ? { ...r, isWikiSuggest: false } : r)));
        }
      }
      notifyParent();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : JSON.stringify(detail ?? err));
    } finally {
      setGivingFeedbackFor(null);
    }
  }

  async function handleCreateRequirement(e: React.FormEvent) {
    e.preventDefault();
    if (!newReqTitle.trim()) return;
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
      setRequirements((prev) => [req, ...prev]);
      setNewReqTitle('');
      setNewReqBody('');
      setNewReqCapabilityKey('');
      setNewReqScenarioKind('');
      setNewReqVerificationLevel('');
      setNewReqCustomerOutcome('');
      setShowNewReq(false);
      notifyParent();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ?? String(err));
    } finally {
      setCreatingReq(false);
    }
  }

  async function handleRunIq(req: ReqIQRequirement, type: 'stub' | 'llm') {
    setRunningIqFor(req.id);
    try {
      const revIdx = iqData[req.id]?.latestRevisionIndex ?? 0;
      const revision: ReqIQRevision = type === 'stub'
        ? await requirementsService.runStubIq(projectId, req.id, revIdx)
        : await requirementsService.runLlmIq(projectId, req.id, revIdx);
      if (revision.iqSnapshot) {
        setIqBreakdown((prev) => ({ ...prev, [req.id]: revision.iqSnapshot! }));
      }
      const latestIq = await requirementsService.getLatestIq(projectId, req.id);
      setIqData((prev) => ({ ...prev, [req.id]: latestIq }));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ?? String(err));
    } finally {
      setRunningIqFor(null);
    }
  }

  async function handleSuggestTests(req: ReqIQRequirement) {
    setSuggestingFor(req.id);
    try {
      const isPurchaseJourney = req.capabilityKey === 'purchase_journey';
      const hints = [
        req.customerOutcome ? `Test objective: ${req.customerOutcome}` : '',
        'STYLE: imperative browser commands, not BDD.',
        isPurchaseJourney ? 'SCOPE: full E2E purchase journey with login sentinel.' : '',
      ].filter(Boolean).join('\n');
      const result = await requirementsService.suggestTests(projectId, req.id, 1, hints);
      const first: SuggestedTest | undefined = result.created[0];
      if (!first) {
        alert('No tests suggested.');
        return;
      }
      const steps = first.payload?.steps ?? [];
      const oracle = first.payload?.oracle ?? '';
      const instruction = [
        ...(first.payload?.preconditions ?? []),
        ...steps.map((s) => s.action),
        oracle ? `STOP at ${oracle}.` : '',
      ].filter(Boolean).join('\n');
      const params = new URLSearchParams({
        test_title: first.title,
        test_description: req.customerOutcome ?? req.title,
        user_instruction: instruction,
      });
      navigate(`/crawl-and-save?${params.toString()}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ?? String(err));
    } finally {
      setSuggestingFor(null);
    }
  }

  const wikiDrafts = requirements.filter((r) => r.isWikiSuggest && r.state === 'DRAFT');
  const listedReqs = requirements.filter((r) => !(r.isWikiSuggest && r.state === 'DRAFT'));

  return (
    <Card>
      {toast && (
        <div className="mx-4 mt-4 text-sm bg-gray-900 text-white px-3 py-2 rounded-lg">{toast}</div>
      )}
      <button
        type="button"
        className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <div>
          <h2 className="font-semibold text-gray-900">Advanced (ReqIQ)</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Readiness, Q&amp;A, coverage, full scenario editor, IQ scoring
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <a
            href={REQIQ_APP_URL}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 border border-blue-200 rounded-lg px-2 py-1"
          >
            <ExternalLink className="w-3 h-3" />
            ReqIQ Advanced
          </a>
          {open ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4 border-t">
          <SubSection title="Ready for testing?">
            <div className="flex gap-2">
              <input
                type="text"
                value={readinessQuery}
                onChange={(e) => setReadinessQuery(e.target.value)}
                placeholder="Optional: describe a feature to check"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
              <button
                type="button"
                onClick={handleCheckReadiness}
                disabled={readinessLoading}
                className="px-4 py-2 bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50"
              >
                {readinessLoading ? '…' : 'Check'}
              </button>
            </div>
            {readiness && (
              <div className="flex items-center gap-3 text-sm">
                <span className="text-2xl font-bold">{readiness.readinessScore}%</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100">{readiness.status}</span>
              </div>
            )}
          </SubSection>

          <SubSection title="Ask a question">
            <form onSubmit={handleRagQuery} className="flex gap-2">
              <input
                type="text"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                placeholder="Ask about acceptance criteria, flows, pricing…"
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
                disabled={ragLoading}
              />
              <button type="submit" disabled={ragLoading || !ragQuery.trim()} className="px-4 py-2 bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50">
                {ragLoading ? '…' : 'Ask'}
              </button>
            </form>
            {ragError && <p className="text-sm text-red-600">{ragError}</p>}
            {ragResult && (
              <div className="text-sm bg-gray-50 border rounded p-3 whitespace-pre-wrap">{ragResult.content}</div>
            )}
          </SubSection>

          <SubSection
            title="Coverage & export"
            actions={(
              <div className="flex gap-2">
                <button type="button" onClick={handleLoadCoverage} disabled={loadingCoverage} className="text-xs text-blue-600">
                  {loadingCoverage ? '…' : 'Refresh'}
                </button>
                <button type="button" onClick={() => handleExportProject('markdown')} disabled={exportingProject} className="text-xs text-green-600">↓ MD</button>
                <button type="button" onClick={() => handleExportProject('pdf')} disabled={exportingProject} className="text-xs text-green-600">↓ PDF</button>
              </div>
            )}
          >
            {coverageMatrix ? (
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="text-left p-1">Capability</th>
                    <th className="p-1">Draft</th>
                    <th className="p-1">Reviewed</th>
                    <th className="p-1">Baseline</th>
                    <th className="p-1">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {coverageMatrix.capabilities.map((cap) => (
                    <tr key={cap.key} className="border-t">
                      <td className="p-1">{cap.label}</td>
                      <td className="p-1 text-center">{cap.counts.DRAFT}</td>
                      <td className="p-1 text-center">{cap.counts.REVIEWED}</td>
                      <td className="p-1 text-center">{cap.counts.BASELINE}</td>
                      <td className="p-1 text-center font-semibold">{cap.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-xs text-gray-400">Click Refresh to load coverage matrix.</p>
            )}
          </SubSection>

          <SubSection title="Draft scenarios from wiki (advanced)">
            <p className="text-xs text-gray-500">Filter by capability, add hints, or clear all drafts.</p>
            {wikiSuggestProfile && (wikiSuggestProfile.totalAccepts || wikiSuggestProfile.totalRejects) ? (
              <p className="text-xs text-orange-600">
                History: {wikiSuggestProfile.totalAccepts ?? 0} kept, {wikiSuggestProfile.totalRejects ?? 0} rejected
              </p>
            ) : null}
            <input
              type="text"
              value={draftHints}
              onChange={(e) => setDraftHints(e.target.value)}
              placeholder="Author hints (optional)"
              className="w-full border rounded px-2 py-1 text-sm"
            />
            <input
              type="text"
              value={draftCapabilityKeys}
              onChange={(e) => setDraftCapabilityKeys(e.target.value)}
              placeholder="Capability keys (comma-separated)"
              className="w-full border rounded px-2 py-1 text-sm"
            />
            {capabilities.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {capabilities.map((cap) => (
                  <button
                    key={cap.key}
                    type="button"
                    onClick={() => {
                      const keys = draftCapabilityKeys.split(',').map((s) => s.trim()).filter(Boolean);
                      setDraftCapabilityKeys(
                        keys.includes(cap.key) ? keys.filter((k) => k !== cap.key).join(', ') : [...keys, cap.key].join(', '),
                      );
                    }}
                    className={`text-xs px-2 py-0.5 rounded-full border ${draftCapabilityKeys.includes(cap.key) ? 'bg-blue-100 border-blue-300' : 'bg-gray-50'}`}
                  >
                    {cap.label}
                  </button>
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <SmallBtn onClick={handleGenerateWikiDrafts} disabled={generatingWikiDrafts}>
                {generatingWikiDrafts ? 'Generating…' : 'Generate drafts'}
              </SmallBtn>
              <SmallBtn onClick={handleDeleteAllDrafts} disabled={deletingAllDrafts}>
                {deletingAllDrafts ? 'Deleting…' : 'Delete all DRAFTs'}
              </SmallBtn>
              <SmallBtn onClick={() => { setShowReviewHistory((v) => !v); if (!showReviewHistory) handleLoadFeedbackHistory(); }}>
                Review history ({feedbackTotal})
              </SmallBtn>
              <SmallBtn
                onClick={async () => {
                  if (!window.confirm('Clear all feedback history?')) return;
                  setClearingFeedback(true);
                  try {
                    await requirementsService.deleteAllWikiSuggestFeedback(projectId);
                    setFeedbackHistory([]);
                    setFeedbackTotal(0);
                  } finally {
                    setClearingFeedback(false);
                  }
                }}
                disabled={clearingFeedback}
              >
                Clear feedback
              </SmallBtn>
            </div>
            {showReviewHistory && (
              <ul className="text-xs max-h-32 overflow-y-auto divide-y">
                {feedbackHistory.filter((f) => f.decision === 'reject').map((f) => (
                  <li key={f.id} className="py-1">{f.requirementTitle} — {f.reason || 'no reason'}</li>
                ))}
              </ul>
            )}
          </SubSection>

          {wikiDrafts.length > 0 && (
            <SubSection title={`Wiki draft review (${wikiDrafts.length})`}>
              <ul className="space-y-3">
                {wikiDrafts.map((req) => (
                  <li key={req.id} className="text-sm border-b pb-2">
                    {reviewEditId === req.id ? (
                      <div className="space-y-2">
                        <input className="w-full border rounded px-2 py-1 text-sm" value={reviewEditTitle} onChange={(e) => setReviewEditTitle(e.target.value)} />
                        <textarea className="w-full border rounded px-2 py-1 text-sm" rows={2} value={reviewEditOutcome} onChange={(e) => setReviewEditOutcome(e.target.value)} />
                        <div className="flex gap-2">
                          <SmallBtn
                            variant="primary"
                            disabled={savingReviewEdit}
                            onClick={async () => {
                              setSavingReviewEdit(true);
                              try {
                                await requirementsService.updateRequirement(projectId, req.id, {
                                  title: reviewEditTitle.trim(),
                                  customerOutcome: reviewEditOutcome.trim() || undefined,
                                });
                                const final = await requirementsService.transitionRequirement(projectId, req.id, 'REVIEWED').catch(
                                  () => requirementsService.getRequirement(projectId, req.id),
                                );
                                setRequirements((prev) => prev.map((r) => (r.id === req.id ? final : r)));
                                setReviewEditId(null);
                                notifyParent();
                              } finally {
                                setSavingReviewEdit(false);
                              }
                            }}
                          >
                            Save
                          </SmallBtn>
                          <SmallBtn onClick={() => setReviewEditId(null)}>Cancel</SmallBtn>
                        </div>
                      </div>
                    ) : (
                      <>
                        <p className="font-medium">{req.title}</p>
                        {req.customerOutcome && <p className="text-gray-500 italic text-xs">{req.customerOutcome}</p>}
                        <div className="flex gap-1 mt-2 flex-wrap">
                          <SmallBtn onClick={() => handleWikiFeedback(req, 'accept')} disabled={givingFeedbackFor === req.id}>Keep</SmallBtn>
                          <SmallBtn onClick={() => { setReviewEditId(req.id); setReviewEditTitle(req.title); setReviewEditOutcome(req.customerOutcome ?? ''); }}>Edit</SmallBtn>
                          <SmallBtn onClick={() => handleWikiFeedback(req, 'reject')} disabled={givingFeedbackFor === req.id}>Reject</SmallBtn>
                          <SmallBtn onClick={() => setRejectDialogReq(req)}>Reject with reasons…</SmallBtn>
                        </div>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </SubSection>
          )}

          <SubSection
            title="Requirements (full editor)"
            actions={(
              <button type="button" onClick={() => setShowNewReq((v) => !v)} className="flex items-center gap-1 text-xs text-blue-600">
                <Plus className="w-3 h-3" /> New
              </button>
            )}
          >
            {showNewReq && (
              <form onSubmit={handleCreateRequirement} className="space-y-2 border border-blue-200 bg-blue-50 p-3 rounded">
                <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Title *" value={newReqTitle} onChange={(e) => setNewReqTitle(e.target.value)} required />
                <textarea className="w-full border rounded px-2 py-1 text-sm" placeholder="Body" rows={2} value={newReqBody} onChange={(e) => setNewReqBody(e.target.value)} />
                <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Customer outcome" value={newReqCustomerOutcome} onChange={(e) => setNewReqCustomerOutcome(e.target.value)} />
                {capabilities.length > 0 ? (
                  <select className="w-full border rounded px-2 py-1 text-sm" value={newReqCapabilityKey} onChange={(e) => setNewReqCapabilityKey(e.target.value)}>
                    <option value="">Capability (optional)</option>
                    {capabilities.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
                  </select>
                ) : (
                  <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Capability key" value={newReqCapabilityKey} onChange={(e) => setNewReqCapabilityKey(e.target.value)} />
                )}
                <button type="submit" disabled={creatingReq} className="px-3 py-1 bg-blue-700 text-white text-xs rounded">Create</button>
              </form>
            )}
            {reqLoading ? (
              <p className="text-sm text-gray-400">Loading…</p>
            ) : listedReqs.length === 0 ? (
              <p className="text-sm text-gray-400">No requirements yet.</p>
            ) : (
              <ul className="divide-y text-sm max-h-96 overflow-y-auto">
                {listedReqs.map((req) => {
                  const iq = iqData[req.id];
                  const snap = iqBreakdown[req.id];
                  return (
                    <li key={req.id} className="py-3 space-y-2">
                      {editingReqId === req.id ? (
                        <div className="space-y-2">
                          <input className="w-full border rounded px-2 py-1" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
                          <textarea className="w-full border rounded px-2 py-1" rows={2} value={editBody} onChange={(e) => setEditBody(e.target.value)} />
                          <div className="flex gap-2">
                            <SmallBtn
                              variant="primary"
                              disabled={savingEdit}
                              onClick={async () => {
                                setSavingEdit(true);
                                try {
                                  const updated = await requirementsService.updateRequirement(projectId, req.id, {
                                    title: editTitle.trim(),
                                    body: editBody.trim(),
                                  });
                                  setRequirements((prev) => prev.map((r) => (r.id === req.id ? updated : r)));
                                  setEditingReqId(null);
                                } finally {
                                  setSavingEdit(false);
                                }
                              }}
                            >
                              Save
                            </SmallBtn>
                            <SmallBtn onClick={() => setEditingReqId(null)}>Cancel</SmallBtn>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="flex justify-between gap-2">
                            <div>
                              <p className="font-medium">{req.title}</p>
                              {req.customerOutcome && <p className="text-xs text-blue-600 italic">{req.customerOutcome}</p>}
                              <div className="flex gap-1 mt-1 flex-wrap">
                                <StateBadge state={req.state} />
                                {iq && <QualityBadge score={iq.latestCompositeScore} />}
                                {req.capabilityKey && <span className="text-xs bg-purple-50 text-purple-700 px-1 rounded">{req.capabilityKey}</span>}
                              </div>
                            </div>
                            <SmallBtn onClick={() => { setEditingReqId(req.id); setEditTitle(req.title); setEditBody(req.body ?? ''); }}>
                              <Pencil className="w-3 h-3 inline" />
                            </SmallBtn>
                          </div>
                          {snap && (
                            <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">{snap.rationale || 'IQ scores updated.'}</p>
                          )}
                          <div className="flex flex-wrap gap-1">
                            {LIFECYCLE_STATES.filter((s) => s !== req.state).map((s) => (
                              <SmallBtn
                                key={s}
                                disabled={transitioningFor === req.id}
                                onClick={async () => {
                                  setTransitioningFor(req.id);
                                  try {
                                    const updated = await requirementsService.transitionRequirement(projectId, req.id, s);
                                    setRequirements((prev) => prev.map((r) => (r.id === req.id ? updated : r)));
                                    notifyParent();
                                  } finally {
                                    setTransitioningFor(null);
                                  }
                                }}
                              >
                                → {s}
                              </SmallBtn>
                            ))}
                          </div>
                          <div className="flex flex-wrap gap-1">
                            <SmallBtn onClick={() => handleRunIq(req, 'stub')} disabled={runningIqFor === req.id}>Stub IQ</SmallBtn>
                            <SmallBtn onClick={() => handleRunIq(req, 'llm')} disabled={runningIqFor === req.id}>LLM IQ</SmallBtn>
                            <SmallBtn variant="primary" onClick={() => handleSuggestTests(req)} disabled={suggestingFor === req.id}>Suggest tests</SmallBtn>
                            {req.state === 'DRAFT' && (
                              <SmallBtn
                                variant="danger"
                                disabled={deletingReqId === req.id}
                                onClick={async () => {
                                  if (!window.confirm(`Delete "${req.title}"?`)) return;
                                  setDeletingReqId(req.id);
                                  try {
                                    await requirementsService.deleteRequirement(projectId, req.id);
                                    setRequirements((prev) => prev.filter((r) => r.id !== req.id));
                                    notifyParent();
                                  } finally {
                                    setDeletingReqId(null);
                                  }
                                }}
                              >
                                Delete
                              </SmallBtn>
                            )}
                          </div>
                        </>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </SubSection>
        </div>
      )}

      {rejectDialogReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md space-y-3">
            <p className="font-semibold text-sm">Reject wiki draft</p>
            <p className="text-xs text-gray-500">{rejectDialogReq.title}</p>
            <textarea className="w-full border rounded p-2 text-sm" rows={2} value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} placeholder="Reason" />
            <div className="flex flex-wrap gap-1">
              {REJECT_TAGS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => setRejectTags((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]))}
                  className={`text-xs px-2 py-0.5 rounded-full border ${rejectTags.includes(tag) ? 'bg-red-100 border-red-300' : 'bg-gray-50'}`}
                >
                  {tag}
                </button>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <SmallBtn onClick={() => { setRejectDialogReq(null); setRejectReason(''); setRejectTags([]); }}>Cancel</SmallBtn>
              <SmallBtn
                variant="danger"
                onClick={async () => {
                  await handleWikiFeedback(rejectDialogReq, 'reject', {
                    reason: rejectReason.trim() || undefined,
                    reasonTags: rejectTags.length ? rejectTags : undefined,
                  });
                  setRejectDialogReq(null);
                  setRejectReason('');
                  setRejectTags([]);
                }}
              >
                Reject
              </SmallBtn>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

export default ProductAdvancedReqIQ;
