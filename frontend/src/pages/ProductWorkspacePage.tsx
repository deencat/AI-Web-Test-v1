import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { isAdmin } from '../utils/roles';
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
  syncProductProgram,
  uploadAcceptAttribute,
  uploadProductDocuments,
} from '../services/productWorkspaceService';

type ReqRow = { id: string; title: string; state: string; customerOutcome?: string };

export const ProductWorkspacePage: React.FC = () => {
  const { productId = '' } = useParams();
  const fileRef = useRef<HTMLInputElement>(null);
  const admin = isAdmin();

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [status, setStatus] = useState<ProductWorkspaceStatus | null>(null);
  const [sources, setSources] = useState<unknown[]>([]);
  const [requirements, setRequirements] = useState<ReqRow[]>([]);
  const [wikiText, setWikiText] = useState('');
  const [wikiEditing, setWikiEditing] = useState(false);
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
      setErr(e instanceof Error ? e.message : 'Failed to load workspace');
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
      setErr(ax.response?.data?.detail || (e instanceof Error ? e.message : 'Action failed'));
    } finally {
      setBusy(null);
    }
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files?.length) return;
    await run('upload', async () => {
      await uploadProductDocuments(productId, Array.from(files));
      setMsg(`Uploaded ${files.length} file(s). Recompile wiki when ready.`);
    });
    if (fileRef.current) fileRef.current.value = '';
  };

  if (loading && !product) {
    return <Layout><div className="p-8">Loading…</div></Layout>;
  }
  if (!product) {
    return <Layout><div className="p-8 text-red-600">{err || 'Product not found'}</div></Layout>;
  }

  const wikiStatus = !status?.wiki_ready
    ? 'Not compiled'
    : status.wiki_stale
      ? 'Stale — new documents'
      : 'Ready';

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto space-y-6">
        <div>
          <Link to="/products" className="text-sm text-gray-500 hover:underline">Products</Link>
          <h1 className="text-2xl font-bold mt-1">{product.title}</h1>
          {product.title_zh && <p className="text-gray-600">{product.title_zh}</p>}
        </div>

        {err && <p className="text-red-600 text-sm bg-red-50 p-3 rounded">{String(err)}</p>}
        {msg && <p className="text-green-700 text-sm bg-green-50 p-3 rounded">{msg}</p>}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <Card><div className="p-3"><div className="text-gray-500">Documents</div><div className="text-xl font-bold">{status?.source_count ?? sources.length}</div></div></Card>
          <Card><div className="p-3"><div className="text-gray-500">Wiki</div><div className="text-xl font-bold">{wikiStatus}</div></div></Card>
          <Card><div className="p-3"><div className="text-gray-500">Test scenarios</div><div className="text-xl font-bold">{status?.requirement_count ?? requirements.length}</div></div></Card>
          <Card><div className="p-3"><div className="text-gray-500">Drafts</div><div className="text-xl font-bold">{status?.draft_requirement_count ?? 0}</div></div></Card>
        </div>

        {/* Step 1 — Documents */}
        <Card>
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold">Step 1 — Documents</h2>
            <label className={`cursor-pointer ${busy === 'upload' ? 'opacity-50' : ''}`}>
              <span className="inline-block px-4 py-2 bg-blue-700 text-white text-sm rounded-lg hover:bg-blue-800">
                {busy === 'upload' ? 'Uploading…' : 'Upload files'}
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
          <div className="p-4 text-sm text-gray-600">
            PowerPoint, PDF, Word, images (SMCD UI), MVP configs, T&C, notification templates — add anytime.
          </div>
          <ul className="divide-y text-sm max-h-48 overflow-y-auto">
            {sources.length === 0 ? (
              <li className="p-4 text-gray-400">No documents yet</li>
            ) : (
              sources.map((s, i) => {
                const row = s as { id?: string; filename?: string; name?: string };
                return (
                  <li key={row.id || i} className="p-3 flex justify-between">
                    <span>{row.filename || row.name || 'Document'}</span>
                  </li>
                );
              })
            )}
          </ul>
        </Card>

        {/* Step 2 — Wiki */}
        <Card>
          <div className="p-4 border-b flex flex-wrap gap-2 justify-between items-center">
            <h2 className="font-semibold">Step 2 — Wiki summary</h2>
            <div className="flex gap-2">
              <Button
                disabled={!!busy}
                onClick={() => run('compile', async () => {
                  await compileProductWiki(productId);
                  setMsg('Wiki compiled. Review below and edit if needed.');
                })}
              >
                {busy === 'compile' ? 'Compiling…' : 'Recompile wiki'}
              </Button>
              {wikiText && !wikiEditing && (
                <Button onClick={() => setWikiEditing(true)}>Edit</Button>
              )}
              {wikiEditing && (
                <>
                  <Button
                    onClick={() => run('save-wiki', async () => {
                      await saveProductWiki(productId, wikiText);
                      setWikiEditing(false);
                      setMsg('Wiki saved.');
                    })}
                  >
                    Save
                  </Button>
                  <Button onClick={() => { setWikiEditing(false); load(); }}>Cancel</Button>
                </>
              )}
            </div>
          </div>
          <div className="p-4">
            {wikiEditing ? (
              <textarea
                className="w-full min-h-64 font-mono text-xs border rounded p-3"
                value={wikiText}
                onChange={(e) => setWikiText(e.target.value)}
              />
            ) : wikiText ? (
              <pre className="whitespace-pre-wrap text-sm text-gray-800 max-h-96 overflow-y-auto bg-gray-50 p-4 rounded">{wikiText}</pre>
            ) : (
              <p className="text-gray-400 text-sm">Upload documents, then click Recompile wiki.</p>
            )}
          </div>
        </Card>

        {/* Step 3 — Tests */}
        <Card>
          <div className="p-4 border-b flex flex-wrap gap-2 justify-between items-center">
            <h2 className="font-semibold">Step 3 — Tests</h2>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={!!busy || !status?.wiki_ready}
                onClick={() => run('generate', async () => {
                  const res = await generateTestsFromWiki(productId);
                  setMsg(`${res.message} (${res.created} created)`);
                })}
              >
                {busy === 'generate' ? 'Generating…' : 'Generate test scenarios'}
              </Button>
              <Button
                disabled={!!busy}
                onClick={() => run('overnight', async () => {
                  const res = await runOvernight(productId);
                  setMsg(`Overnight run queued (job ${res.job_id}, ${res.journey_count} journeys).`);
                })}
              >
                {busy === 'overnight' ? 'Queueing…' : 'Run overnight'}
              </Button>
              {admin && (
                <Button
                  disabled={!!busy || !wikiText}
                  onClick={() => run('sync', async () => {
                    const res = await syncProductProgram(productId);
                    setMsg(`Synced ${res.initiatives_synced} initiatives; retired ${res.tests_retired} tests.`);
                  })}
                >
                  {busy === 'sync' ? 'Syncing…' : 'Sync automation'}
                </Button>
              )}
            </div>
          </div>
          <ul className="divide-y text-sm max-h-64 overflow-y-auto">
            {requirements.length === 0 ? (
              <li className="p-4 text-gray-400">Generate scenarios from wiki to see them here.</li>
            ) : (
              requirements.map((r) => (
                <li key={r.id} className="p-3">
                  <div className="font-medium">{r.title}</div>
                  {r.customerOutcome && <div className="text-gray-500 text-xs mt-1">{r.customerOutcome}</div>}
                  <span className="text-xs text-gray-400">{r.state}</span>
                </li>
              ))
            )}
          </ul>
          <p className="p-4 text-xs text-gray-500 border-t">
            Advanced: <Link to="/knowledge-base" className="text-blue-600 hover:underline">Knowledge Base</Link>
            {admin && <> · <Link to={`/programs/${product.program_slug}`} className="text-blue-600 hover:underline">Program admin</Link></>}
          </p>
        </Card>
      </div>
    </Layout>
  );
};
