import React, { useCallback, useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import {
  HealReviewItem,
  listHealReview,
  resolveHealReviewItem,
} from '../services/agentFactoryService';

function canAccessHealReview(): boolean {
  try {
    const raw = localStorage.getItem('user');
    if (!raw) return false;
    const user = JSON.parse(raw) as { role?: string };
    const role = (user.role || 'user').toLowerCase();
    const rank: Record<string, number> = {
      viewer: 0,
      user: 1,
      tester: 1,
      agent_operator: 2,
      admin: 3,
      superadmin: 4,
    };
    return (rank[role] ?? 1) >= 2;
  } catch {
    return false;
  }
}

export const HealReviewPage: React.FC = () => {
  const [items, setItems] = useState<HealReviewItem[]>([]);
  const [statusFilter, setStatusFilter] = useState('open');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const allowed = canAccessHealReview();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listHealReview(statusFilter || undefined);
      setItems(data.items);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load heal review queue');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    if (allowed) load();
  }, [allowed, load]);

  const handleResolve = async (id: number) => {
    try {
      await resolveHealReviewItem(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Resolve failed');
    }
  };

  if (!allowed) {
    return (
      <Layout>
        <div className="p-8 text-gray-600">Agent operator access required for heal review.</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-900">Heal Review</h1>
          <Button variant="secondary" onClick={load} disabled={loading}>
            Refresh
          </Button>
        </div>

        <p className="text-sm text-gray-600">
          Executions that failed automated healing twice appear here for manual follow-up.
        </p>

        <div className="flex gap-2">
          {['open', 'resolved', ''].map((s) => (
            <button
              key={s || 'all'}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 rounded text-sm ${
                statusFilter === s ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {s || 'all'}
            </button>
          ))}
        </div>

        {error && <div className="text-red-600 text-sm">{error}</div>}

        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <p className="p-4 text-gray-500">No heal review items match the filter.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="p-3">ID</th>
                  <th className="p-3">Execution</th>
                  <th className="p-3">Test case</th>
                  <th className="p-3">Reason</th>
                  <th className="p-3">Status</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b border-gray-100">
                    <td className="p-3">{item.id}</td>
                    <td className="p-3">#{item.execution_id}</td>
                    <td className="p-3">{item.test_case_id ?? '—'}</td>
                    <td className="p-3 max-w-md truncate" title={item.reason}>
                      {item.reason}
                    </td>
                    <td className="p-3">{item.status}</td>
                    <td className="p-3">
                      {item.status === 'open' && (
                        <Button variant="secondary" onClick={() => handleResolve(item.id)}>
                          Resolve
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </Layout>
  );
};

export default HealReviewPage;
