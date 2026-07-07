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
            <p className="text-gray-600 text-sm mt-1 max-w-xl">
              One place for Marketing, SSCO, and SMCD documents — the system builds a summary and tests for each product line.
            </p>
          </div>
          <Button onClick={() => setShowCreate(true)}>+ New product</Button>
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>No products yet.</p>
              <Button className="mt-4" onClick={() => setShowCreate(true)}>Create your first product</Button>
            </div>
          ) : (
            <ul className="divide-y">
              {items.map((p) => (
                <li key={p.id} className="p-4 hover:bg-gray-50">
                  <Link to={`/products/${p.id}`} className="block">
                    <span className="text-blue-700 font-semibold text-lg hover:underline">{p.title}</span>
                    {p.title_zh && <span className="ml-2 text-gray-500">{p.title_zh}</span>}
                    <p className="text-sm text-gray-500 mt-1">Upload docs → update summary → create tests</p>
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
