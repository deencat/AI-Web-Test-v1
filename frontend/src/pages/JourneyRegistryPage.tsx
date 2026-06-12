import React, { useCallback, useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import {
  JourneyRegistryEntry,
  createJourneyRegistryEntry,
  deleteJourneyRegistryEntry,
  getRegistrySnapshotStatus,
  JourneySnapshotStatus,
  listJourneyRegistry,
} from '../services/journeyFactoryService';

function isAdmin(): boolean {
  try {
    const raw = localStorage.getItem('user');
    if (!raw) return false;
    const user = JSON.parse(raw) as { role?: string };
    const role = (user.role || 'user').toLowerCase();
    return role === 'admin' || role === 'superadmin';
  } catch {
    return false;
  }
}

const DEFAULT_PROJECT = 'Three-HK';

export const JourneyRegistryPage: React.FC = () => {
  const [items, setItems] = useState<JourneyRegistryEntry[]>([]);
  const [snapshotStatus, setSnapshotStatus] = useState<Record<string, JourneySnapshotStatus>>({});
  const [projectMeta, setProjectMeta] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    slug: '',
    name: '',
    feature_url: '',
    tags: '',
    capability_keys: '',
  });

  const allowed = isAdmin();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [res, status] = await Promise.all([
        listJourneyRegistry(DEFAULT_PROJECT),
        getRegistrySnapshotStatus(DEFAULT_PROJECT).catch(() => ({})),
      ]);
      setItems(res.items);
      setSnapshotStatus(status);
      setProjectMeta(res.project_meta?.reqiq_project_id ?? null);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load registry');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (allowed) load();
  }, [allowed, load]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createJourneyRegistryEntry({
        slug: form.slug.trim(),
        project: DEFAULT_PROJECT,
        name: form.name.trim(),
        feature_url: form.feature_url.trim(),
        tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : undefined,
        capability_keys: form.capability_keys
          ? form.capability_keys.split(',').map((t) => t.trim()).filter(Boolean)
          : undefined,
      });
      setShowForm(false);
      setForm({ slug: '', name: '', feature_url: '', tags: '', capability_keys: '' });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this journey from the registry?')) return;
    try {
      await deleteJourneyRegistryEntry(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  if (!allowed) {
    return (
      <Layout>
        <div className="p-8 text-gray-600">Admin access required to manage the journey registry.</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8 max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Journey Registry</h1>
            <p className="text-gray-600 text-sm mt-1">
              UAT journeys for factory test generation ({DEFAULT_PROJECT})
              {projectMeta ? ` · ReqIQ: ${projectMeta}` : ''}
            </p>
          </div>
          <Button onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancel' : 'Add journey'}</Button>
        </div>

        {error && <div className="text-red-600 text-sm">{error}</div>}

        {showForm && (
          <Card>
            <form onSubmit={handleCreate} className="space-y-3 p-4">
              <input
                className="w-full border rounded px-3 py-2"
                placeholder="slug (e.g. diy-dashboard)"
                value={form.slug}
                onChange={(e) => setForm({ ...form, slug: e.target.value })}
                required
              />
              <input
                className="w-full border rounded px-3 py-2"
                placeholder="Display name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
              <input
                className="w-full border rounded px-3 py-2"
                placeholder="Feature URL"
                value={form.feature_url}
                onChange={(e) => setForm({ ...form, feature_url: e.target.value })}
                required
              />
              <input
                className="w-full border rounded px-3 py-2"
                placeholder="Tags (comma-separated)"
                value={form.tags}
                onChange={(e) => setForm({ ...form, tags: e.target.value })}
              />
              <input
                className="w-full border rounded px-3 py-2"
                placeholder="Capability keys (comma-separated)"
                value={form.capability_keys}
                onChange={(e) => setForm({ ...form, capability_keys: e.target.value })}
              />
              <Button type="submit">Save journey</Button>
            </form>
          </Card>
        )}

        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : items.length === 0 ? (
            <p className="p-4 text-gray-500">No journeys in registry. Run migration or add one.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="p-3">Slug</th>
                  <th className="p-3">Name</th>
                  <th className="p-3">URL</th>
                  <th className="p-3">Tags</th>
                  <th className="p-3">Change</th>
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-mono text-xs">{row.slug}</td>
                    <td className="p-3">{row.name}</td>
                    <td className="p-3 truncate max-w-xs" title={row.feature_url}>
                      {row.feature_url}
                    </td>
                    <td className="p-3">{(row.tags || []).join(', ')}</td>
                    <td className="p-3">
                      {(() => {
                        const st = snapshotStatus[row.slug];
                        if (!st) return <span className="text-gray-400 text-xs">—</span>;
                        if (!st.has_baseline) {
                          return <span className="text-gray-500 text-xs" title={st.summary}>Baseline</span>;
                        }
                        if (st.material_change) {
                          return (
                            <span
                              className="px-2 py-0.5 rounded text-xs bg-orange-100 text-orange-800"
                              title={st.summary}
                            >
                              Changed
                            </span>
                          );
                        }
                        return (
                          <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-800" title={st.summary}>
                            Stable
                          </span>
                        );
                      })()}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
                        className="text-red-600 hover:underline text-xs"
                        onClick={() => handleDelete(row.id)}
                      >
                        Delete
                      </button>
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
