import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { listProducts, ProductSummary } from '../services/productWorkspaceService';

export const ProductsListPage: React.FC = () => {
  const [items, setItems] = useState<ProductSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProducts()
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Products</h1>
          <p className="text-gray-600 text-sm mt-1">
            Upload marketing and SSCO documents, build a wiki summary, and generate tests.
          </p>
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <p className="p-4 text-gray-500">No products configured.</p>
          ) : (
            <ul className="divide-y">
              {items.map((p) => (
                <li key={p.id} className="p-4 hover:bg-gray-50">
                  <Link to={`/products/${p.id}`} className="block">
                    <span className="text-blue-700 font-semibold text-lg hover:underline">{p.title}</span>
                    {p.title_zh && <span className="ml-2 text-gray-500">{p.title_zh}</span>}
                    {p.pilot && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Pilot</span>
                    )}
                    <p className="text-sm text-gray-500 mt-1">Open workspace → upload documents → wiki → tests</p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </Layout>
  );
};
