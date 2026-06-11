import React, { useCallback, useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import {
  JourneyBacklogItem,
  JourneyRegistryEntry,
  enqueueJourney,
  listJourneyBacklog,
  listJourneyRegistry,
} from '../services/journeyFactoryService';

function canAccessBacklog(): boolean {
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

const DEFAULT_PROJECT = 'Three-HK';

export const BacklogQueuePage: React.FC = () => {
  const [items, setItems] = useState<JourneyBacklogItem[]>([]);
  const [journeys, setJourneys] = useState<JourneyRegistryEntry[]>([]);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [selectedSlug, setSelectedSlug] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const allowed = canAccessBacklog();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [backlog, registry] = await Promise.all([
        listJourneyBacklog({ project: DEFAULT_PROJECT, status: statusFilter || undefined, limit: 100 }),
        listJourneyRegistry(DEFAULT_PROJECT).catch(() => ({ items: [], total: 0 })),
      ]);
      setItems(backlog.items);
      setJourneys(registry.items);
      setSelectedSlug((prev) => prev || (registry.items[0]?.slug ?? ''));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load backlog');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    if (allowed) load();
  }, [allowed, load]);

  const handleEnqueue = async () => {
    if (!selectedSlug) return;
    try {
      await enqueueJourney({ journey_slug: selectedSlug, project: DEFAULT_PROJECT });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Enqueue failed');
    }
  };

  if (!allowed) {
    return (
      <Layout>
        <div className="p-8 text-gray-600">Agent operator access required for the journey backlog.</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Journey Backlog</h1>
          <p className="text-gray-600 text-sm mt-1">Queue items for Loop A drain ({DEFAULT_PROJECT})</p>
        </div>

        {error && <div className="text-red-600 text-sm">{error}</div>}

        <Card>
          <div className="p-4 flex flex-wrap gap-3 items-end">
            <label className="text-sm text-gray-700">
              Journey
              <select
                className="block mt-1 border rounded px-3 py-2 min-w-[200px]"
                value={selectedSlug}
                onChange={(e) => setSelectedSlug(e.target.value)}
              >
                {journeys.map((j) => (
                  <option key={j.id} value={j.slug}>
                    {j.slug} — {j.name}
                  </option>
                ))}
              </select>
            </label>
            <Button onClick={handleEnqueue} disabled={!selectedSlug}>
              Enqueue
            </Button>
            <label className="text-sm text-gray-700 ml-auto">
              Status filter
              <select
                className="block mt-1 border rounded px-3 py-2"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In progress</option>
                <option value="done">Done</option>
                <option value="failed">Failed</option>
              </select>
            </label>
          </div>
        </Card>

        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <p className="p-4 text-gray-500">No backlog items match the filter.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="p-3">ID</th>
                  <th className="p-3">Journey</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Job</th>
                  <th className="p-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id} className="border-b">
                    <td className="p-3">{row.id}</td>
                    <td className="p-3 font-mono text-xs">{row.journey_slug}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs ${
                          row.status === 'pending'
                            ? 'bg-amber-100 text-amber-800'
                            : row.status === 'done'
                              ? 'bg-green-100 text-green-800'
                              : row.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {row.status}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-xs">{row.factory_job_id || '—'}</td>
                    <td className="p-3 text-gray-500">{new Date(row.created_at).toLocaleString()}</td>
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
