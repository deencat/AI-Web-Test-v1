import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CreateProductModal } from '../components/CreateProductModal';
import { listProducts, ProductSummary } from '../services/productWorkspaceService';

export const ProductsListPage: React.FC = () => {
  const [items, setItems] = useState<ProductSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const load = () => {
    setLoading(true);
    listProducts()
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Layout>
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-start gap-4">
          <div>
            <h1 className="text-2xl font-bold">Products &amp; offers</h1>
            <p className="text-gray-600 text-sm mt-2 max-w-2xl leading-relaxed">
              One workspace per product line or offer. Upload documents, build a summary, create tests.
              Each product links to its own ReqIQ workspace — e.g. Voucher Plan (DNS bundle) and
              5G Voucher Monthly Plan are separate entries.
            </p>
          </div>
          <Button onClick={() => setShowCreate(true)}>+ New product</Button>
        </div>

        <Card>
          <ol className="p-4 text-sm text-gray-700 space-y-1 list-decimal list-inside bg-gray-50 rounded-lg">
            <li>Add documents (PPT, URS, UI images, T&amp;C, notifications…)</li>
            <li>Update summary — AI reads everything and tracks base vs timed offers</li>
            <li>Create &amp; run tests — outdated promos are retired automatically</li>
          </ol>
        </Card>

        {error && <p className="text-red-600 text-sm">{error}</p>}
        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p className="mb-4">No products yet. Create one per offer line (e.g. Voucher Plan DNS bundle, 5G Voucher Monthly Plan).</p>
              <Button onClick={() => setShowCreate(true)}>Create your first product</Button>
            </div>
          ) : (
            <ul className="divide-y">
              {items.map((p) => (
                <li key={p.id} className="p-4 hover:bg-gray-50">
                  <Link to={`/products/${p.id}`} className="block">
                    <span className="text-blue-700 font-semibold text-lg hover:underline">{p.title}</span>
                    {p.title_zh && <span className="ml-2 text-gray-500">{p.title_zh}</span>}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <CreateProductModal isOpen={showCreate} onClose={() => setShowCreate(false)} onSuccess={load} />
      </div>
    </Layout>
  );
};
