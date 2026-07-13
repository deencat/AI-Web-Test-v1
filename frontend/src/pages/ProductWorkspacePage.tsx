import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { EditProductModal } from '../components/EditProductModal';
import { ProductAdvancedReqIQ } from '../components/products/ProductAdvancedReqIQ';
import {
  compileProductWiki,
  deleteProductDocument,
  deriveWorkflowStep,
  generateTestsFromWiki,
  getProduct,
  getProductStatus,
  getProductWiki,
  keepTestScenario,
  listProductRequirements,
  listProductSources,
  ProductDetail,
  ProductRequirement,
  ProductSource,
  ProductWorkspaceStatus,
  ProductWorkflowStep,
  removeTestScenario,
  runOvernight,
  saveProductWiki,
  uploadAcceptAttribute,
  uploadProductDocuments,
} from '../services/productWorkspaceService';

function StepBadge({ n, label, active, done }: { n: number; label: string; active: boolean; done: boolean }) {
  return (
    <div className={`flex items-center gap-2 text-sm ${active ? 'font-semibold text-blue-800' : done ? 'text-green-700' : 'text-gray-400'}`}>
      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs border ${
        done ? 'bg-green-100 border-green-300' : active ? 'bg-blue-100 border-blue-400' : 'bg-gray-50 border-gray-200'
      }`}>{done ? '✓' : n}</span>
      <span>{label}</span>
    </div>
  );
}

export const ProductWorkspacePage: React.FC = () => {
  const { productId = '' } = useParams();
  const fileRef = useRef<HTMLInputElement>(null);

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [status, setStatus] = useState<ProductWorkspaceStatus | null>(null);
  const [sources, setSources] = useState<ProductSource[]>([]);
  const [requirements, setRequirements] = useState<ProductRequirement[]>([]);
  const [wikiText, setWikiText] = useState('');
  const [wikiEditing, setWikiEditing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [prod, st, src, wiki, reqs] = await Promise.all([
        getProduct(productId),
        getProductStatus(productId),
        listProductSources(productId).catch(() => []),
        getProductWiki(productId).catch(() => ({})),
        listProductRequirements(productId).catch(() => []),
      ]);
      setProduct(prod);
      setStatus(st.status);
      setSources(src);
      setWikiText((wiki as { markdown?: string; content?: string }).markdown
        || (wiki as { content?: string }).content || '');
      setRequirements(
        (reqs as ProductRequirement[]).map((r) => ({
          id: r.id,
          title: r.title,
          state: r.state,
          customerOutcome: r.customerOutcome,
          isWikiSuggest: r.isWikiSuggest,
        })),
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    load();
  }, [load]);

  const run = async (label: string, fn: () => Promise<void>) => {
    setBusy(label);
    setErr(null);
    setMsg(null);
    try {
      await fn();
      await load();
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      setErr(ax.response?.data?.detail || (e instanceof Error ? e.message : 'Something went wrong'));
    } finally {
      setBusy(null);
    }
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files?.length) return;
    await run('upload', async () => {
      await uploadProductDocuments(productId, Array.from(files));
      setMsg(`Added ${files.length} file(s). When ready, click Update summary.`);
    });
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleRemoveDoc = async (sourceId: string, name: string) => {
    if (!window.confirm(`Remove "${name}" from this product?`)) return;
    setDeletingId(sourceId);
    try {
      await deleteProductDocument(productId, sourceId);
      setMsg('Document removed.');
      await load();
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      setErr(ax.response?.data?.detail || 'Could not remove document');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading && !product) {
    return <Layout><div className="p-8">Loading…</div></Layout>;
  }
  if (!product) {
    return <Layout><div className="p-8 text-red-600">{err || 'Product not found'}</div></Layout>;
  }

  const step: ProductWorkflowStep = deriveWorkflowStep(status, sources.length);
  const summaryDone = Boolean(status?.wiki_ready && !status?.wiki_stale);
  const docsDone = sources.length > 0;

  const scenarioHint = (() => {
    if (sources.length === 0) {
      return 'Start by uploading any documents you have — you can add more later (e.g. June promo deck, then July pack).';
    }
    if (!status?.wiki_ready) {
      return 'Documents received. Click Update summary so the system understands base offer vs timed promos.';
    }
    if (status.wiki_stale) {
      return 'New or changed documents detected — update the summary so June/July offers and tests stay correct.';
    }
    if (requirements.length === 0) {
      return 'Summary is ready. Create tests from it, then run overnight if you want automated checks.';
    }
    return 'Review suggested tests below. Keep what matters; remove what does not apply.';
  })();

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto space-y-6">
        <div className="flex justify-between items-start gap-4">
          <div>
            <Link to="/products" className="text-sm text-gray-500 hover:underline">← Products &amp; offers</Link>
            <h1 className="text-2xl font-bold mt-1">{product.title}</h1>
            {product.title_zh && <p className="text-gray-600">{product.title_zh}</p>}
          </div>
          <Button onClick={() => setShowSettings(true)}>Settings</Button>
        </div>

        <Card>
          <div className="p-4 flex flex-wrap gap-6 justify-between items-center border-b">
            <StepBadge n={1} label="Documents" active={step === 'documents'} done={docsDone} />
            <StepBadge n={2} label="Summary" active={step === 'summary'} done={summaryDone} />
            <StepBadge n={3} label="Tests" active={step === 'tests'} done={requirements.some((r) => r.state !== 'DRAFT')} />
          </div>
          <p className="p-4 text-sm text-gray-700 bg-blue-50">{scenarioHint}</p>
        </Card>

        {err && <p className="text-red-600 text-sm bg-red-50 p-3 rounded">{String(err)}</p>}
        {msg && <p className="text-green-700 text-sm bg-green-50 p-3 rounded">{msg}</p>}

        <Card>
          <div className="p-4 border-b flex justify-between items-center">
            <div>
              <h2 className="font-semibold">Documents</h2>
              <p className="text-xs text-gray-500 mt-1">
                Marketing PPT · SSCO URS/MVP · <strong>UX/UI flow images (PNG)</strong> · offer Excel · T&amp;C · SMS/email
              </p>
              <p className="text-xs text-gray-500 mt-1">
                UX/UI images become <strong>Purchase journeys</strong> in Summary when you click Update summary.
              </p>
            </div>
            <label className={`cursor-pointer ${busy === 'upload' ? 'opacity-50' : ''}`}>
              <span className="inline-block px-4 py-2 bg-blue-700 text-white text-sm rounded-lg hover:bg-blue-800">
                {busy === 'upload' ? 'Uploading…' : '+ Add files'}
              </span>
              <input
                ref={fileRef}
                type="file"
                multiple
                className="hidden"
                accept={uploadAcceptAttribute()}
                disabled={!!busy}
                onChange={(e) => handleUpload(e.target.files)}
              />
            </label>
          </div>
          <ul className="divide-y text-sm max-h-52 overflow-y-auto">
            {sources.length === 0 ? (
              <li className="p-6 text-gray-400 text-center">No documents yet</li>
            ) : (
              sources.map((s) => {
                const name = s.originalFilename || s.filename || s.name || 'Document';
                return (
                  <li key={s.id} className="p-3 flex justify-between items-center gap-2">
                    <span className="truncate">{name}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      {s.status && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          s.status === 'ready' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>{s.status}</span>
                      )}
                      <button
                        type="button"
                        className="text-xs text-red-600 hover:underline disabled:opacity-40"
                        disabled={deletingId === s.id}
                        onClick={() => handleRemoveDoc(s.id, name)}
                      >
                        {deletingId === s.id ? '…' : 'Remove'}
                      </button>
                    </div>
                  </li>
                );
              })
            )}
          </ul>
        </Card>

        <Card>
          <div className="p-4 border-b flex flex-wrap gap-2 justify-between items-center">
            <h2 className="font-semibold">Summary</h2>
            <div className="flex gap-2">
              <Button
                disabled={!!busy || sources.length === 0}
                onClick={() => run('summary', async () => {
                  const res = await compileProductWiki(productId);
                  setMsg(res.message);
                  await load();
                })}
              >
                {busy === 'summary' ? 'Updating…' : 'Update summary'}
              </Button>
              {wikiText && !wikiEditing && <Button onClick={() => setWikiEditing(true)}>Edit</Button>}
              {wikiEditing && (
                <>
                  <Button onClick={() => run('save-wiki', async () => {
                    await saveProductWiki(productId, wikiText);
                    setWikiEditing(false);
                    setMsg('Summary saved.');
                  })}>Save</Button>
                  <Button onClick={() => { setWikiEditing(false); load(); }}>Cancel</Button>
                </>
              )}
            </div>
          </div>
          <div className="p-4">
            {wikiEditing ? (
              <textarea className="w-full min-h-64 font-mono text-xs border rounded p-3" value={wikiText} onChange={(e) => setWikiText(e.target.value)} />
            ) : wikiText ? (
              <pre className="whitespace-pre-wrap text-sm text-gray-800 max-h-96 overflow-y-auto bg-gray-50 p-4 rounded">{wikiText}</pre>
            ) : (
              <p className="text-gray-400 text-sm">
                The summary lists base offer, active promos (with dates), ended promos,{' '}
                <strong>Purchase journeys</strong> (from UX/UI images), UX notes, and notification copy.
              </p>
            )}
          </div>
        </Card>

        <Card>
          <div className="p-4 border-b flex flex-wrap gap-2 justify-between items-center">
            <h2 className="font-semibold">Tests</h2>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={!!busy || !status?.wiki_ready}
                onClick={() => run('tests', async () => {
                  const res = await generateTestsFromWiki(productId);
                  const guided = res.journey_guided ? ' (using Purchase journey steps)' : '';
                  setMsg(`Added ${res.created} test scenario(s)${guided}. Review and keep the ones you need.`);
                  await load();
                })}
              >
                {busy === 'tests' ? 'Creating…' : 'Create tests from summary'}
              </Button>
              <Button
                disabled={!!busy || !status?.wiki_ready}
                onClick={() => run('overnight', async () => {
                  const res = await runOvernight(productId);
                  setMsg(`Automated run started (${res.journey_count} flows).`);
                })}
              >
                {busy === 'overnight' ? 'Starting…' : 'Run overnight'}
              </Button>
            </div>
          </div>
          <ul className="divide-y text-sm max-h-64 overflow-y-auto">
            {requirements.length === 0 ? (
              <li className="p-6 text-gray-400 text-center">Tests appear here after you create them from the summary.</li>
            ) : (
              requirements.map((r) => (
                <li key={r.id} className="p-3 flex justify-between gap-3 items-start">
                  <div className="min-w-0">
                    <div className="font-medium">{r.title}</div>
                    {r.customerOutcome && <div className="text-gray-500 text-xs mt-1">{r.customerOutcome}</div>}
                    <span className="text-xs text-gray-400">{r.state}</span>
                  </div>
                  {r.state === 'DRAFT' && (
                    <div className="flex gap-1 shrink-0">
                      <button
                        type="button"
                        className="text-xs px-2 py-1 rounded bg-green-50 text-green-800 border border-green-200"
                        onClick={() => run(`keep-${r.id}`, async () => {
                          await keepTestScenario(productId, r.id);
                          setMsg('Test kept.');
                        })}
                      >
                        Keep
                      </button>
                      <button
                        type="button"
                        className="text-xs px-2 py-1 rounded bg-gray-50 text-gray-600 border"
                        onClick={() => run(`drop-${r.id}`, async () => {
                          await removeTestScenario(productId, r.id);
                          setMsg('Test removed.');
                        })}
                      >
                        Not needed
                      </button>
                    </div>
                  )}
                </li>
              ))
            )}
          </ul>
        </Card>

        <ProductAdvancedReqIQ
          projectId={product.reqiq_project_id}
          onRequirementsChanged={load}
        />

        <EditProductModal
          productId={productId}
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
          onSaved={() => { setMsg('Settings saved.'); load(); }}
        />
      </div>
    </Layout>
  );
};
