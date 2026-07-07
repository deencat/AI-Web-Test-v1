import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { EditProductModal } from '../components/EditProductModal';
import {
  compileProductWiki,
  generateTestsFromWiki,
  getProduct,
  getProductStatus,
  getProductWiki,
  listProductRequirements,
  listProductSources,
  ProductDetail,
  ProductWorkspaceStatus,
  runOvernight,
  saveProductWiki,
  uploadAcceptAttribute,
  uploadProductDocuments,
} from '../services/productWorkspaceService';

type ReqRow = { id: string; title: string; state: string; customerOutcome?: string };

export const ProductWorkspacePage: React.FC = () => {
  const { productId = '' } = useParams();
  const fileRef = useRef<HTMLInputElement>(null);

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [status, setStatus] = useState<ProductWorkspaceStatus | null>(null);
  const [sources, setSources] = useState<unknown[]>([]);
  const [requirements, setRequirements] = useState<ReqRow[]>([]);
  const [wikiText, setWikiText] = useState('');
  const [wikiEditing, setWikiEditing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

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
        (reqs as ReqRow[]).map((r) => ({
          id: r.id,
          title: r.title,
          state: r.state,
          customerOutcome: r.customerOutcome,
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
      setMsg(`Added ${files.length} file(s). Click “Update summary” when ready.`);
    });
    if (fileRef.current) fileRef.current.value = '';
  };

  if (loading && !product) {
    return <Layout><div className="p-8">Loading…</div></Layout>;
  }
  if (!product) {
    return <Layout><div className="p-8 text-red-600">{err || 'Product not found'}</div></Layout>;
  }

  const needsSummary = !status?.wiki_ready || status.wiki_stale;

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <Link to="/products" className="text-sm text-gray-500 hover:underline">← All products</Link>
            <h1 className="text-2xl font-bold mt-1">{product.title}</h1>
            {product.title_zh && <p className="text-gray-600">{product.title_zh}</p>}
          </div>
          <Button onClick={() => setShowSettings(true)}>Settings</Button>
        </div>

        <Card>
          <div className="p-4 bg-blue-50 text-sm text-blue-900 rounded-lg border border-blue-100">
            <strong>How it works:</strong> Drop in documents from Marketing (PPT), SSCO (URS, MVP configs), SMCD (UI images), T&amp;C, and notification templates — anytime, in batches.
            The system reads everything, writes one <strong>summary</strong> (base offer, June promo, July promo, etc.), and creates <strong>tests</strong>. When a promo ends, outdated tests are retired automatically.
          </div>
        </Card>

        {err && <p className="text-red-600 text-sm bg-red-50 p-3 rounded">{String(err)}</p>}
        {msg && <p className="text-green-700 text-sm bg-green-50 p-3 rounded">{msg}</p>}
        {needsSummary && sources.length > 0 && (
          <p className="text-amber-800 text-sm bg-amber-50 p-3 rounded">
            You have new or changed documents — click <strong>Update summary</strong> so tests stay current.
          </p>
        )}

        {/* 1 — Documents */}
        <Card>
          <div className="p-4 border-b flex justify-between items-center">
            <div>
              <h2 className="font-semibold">1. Add documents</h2>
              <p className="text-xs text-gray-500">{status?.source_count ?? sources.length} file(s)</p>
            </div>
            <label className={`cursor-pointer ${busy === 'upload' ? 'opacity-50' : ''}`}>
              <span className="inline-block px-4 py-2 bg-blue-700 text-white text-sm rounded-lg hover:bg-blue-800">
                {busy === 'upload' ? 'Uploading…' : 'Choose files'}
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
          <ul className="divide-y text-sm max-h-40 overflow-y-auto">
            {sources.length === 0 ? (
              <li className="p-4 text-gray-400">No documents yet — upload whenever files are ready.</li>
            ) : (
              sources.map((s, i) => {
                const row = s as { id?: string; filename?: string; name?: string };
                return <li key={row.id || i} className="p-3">{row.filename || row.name || 'Document'}</li>;
              })
            )}
          </ul>
        </Card>

        {/* 2 — Summary */}
        <Card>
          <div className="p-4 border-b flex flex-wrap gap-2 justify-between items-center">
            <h2 className="font-semibold">2. Summary (wiki)</h2>
            <div className="flex gap-2">
              <Button
                disabled={!!busy || sources.length === 0}
                onClick={() => run('summary', async () => {
                  const res = await compileProductWiki(productId);
                  setMsg(res.message);
                })}
              >
                {busy === 'summary' ? 'Working…' : 'Update summary'}
              </Button>
              {wikiText && !wikiEditing && (
                <Button onClick={() => setWikiEditing(true)}>Edit text</Button>
              )}
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
              <p className="text-gray-400 text-sm">After uploading, click Update summary to extract base offer, promos, UX, T&amp;C, and notifications.</p>
            )}
          </div>
        </Card>

        {/* 3 — Tests */}
        <Card>
          <div className="p-4 border-b flex flex-wrap gap-2 justify-between items-center">
            <div>
              <h2 className="font-semibold">3. Tests</h2>
              <p className="text-xs text-gray-500">{requirements.length} scenario(s)</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={!!busy || !status?.wiki_ready}
                onClick={() => run('tests', async () => {
                  const res = await generateTestsFromWiki(productId);
                  setMsg(`Created ${res.created} test scenario(s) from the summary.`);
                })}
              >
                {busy === 'tests' ? 'Creating…' : 'Create tests'}
              </Button>
              <Button
                disabled={!!busy || !status?.wiki_ready}
                onClick={() => run('overnight', async () => {
                  const res = await runOvernight(productId);
                  setMsg(`Automated run started (${res.journey_count} flows).`);
                })}
              >
                {busy === 'overnight' ? 'Starting…' : 'Run tests overnight'}
              </Button>
            </div>
          </div>
          <ul className="divide-y text-sm max-h-48 overflow-y-auto">
            {requirements.length === 0 ? (
              <li className="p-4 text-gray-400">Create tests after the summary is ready.</li>
            ) : (
              requirements.map((r) => (
                <li key={r.id} className="p-3">
                  <div className="font-medium">{r.title}</div>
                  {r.customerOutcome && <div className="text-gray-500 text-xs mt-1">{r.customerOutcome}</div>}
                </li>
              ))
            )}
          </ul>
        </Card>

        <EditProductModal
          productId={productId}
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
          onSaved={() => { setMsg('Product settings saved.'); load(); }}
        />
      </div>
    </Layout>
  );
};
