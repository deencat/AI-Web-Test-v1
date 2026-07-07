import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CreateProgramModal } from '../components/CreateProgramModal';
import { listPrograms, ProgramSummary } from '../services/programService';

function isAdmin(): boolean {
  try {
    const raw = localStorage.getItem('user');
    if (!raw) return false;
    const role = (JSON.parse(raw) as { role?: string }).role?.toLowerCase() || 'user';
    return role === 'admin' || role === 'superadmin';
  } catch {
    return false;
  }
}

export const ProgramsListPage: React.FC = () => {
  const [items, setItems] = useState<ProgramSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const admin = isAdmin();

  const load = () => {
    setLoading(true);
    listPrograms()
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">Programs</h1>
            <p className="text-gray-600 text-sm">Product lines and initiatives from YAML manifests.</p>
          </div>
          {admin && <Button onClick={() => setShowCreate(true)}>New program</Button>}
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <Card>
          {loading ? (
            <p className="p-4 text-gray-500">Loading…</p>
          ) : (
            <ul className="divide-y">
              {items.map((p) => (
                <li key={p.slug} className="p-4 flex justify-between hover:bg-gray-50">
                  <Link to={`/programs/${p.slug}`} className="text-blue-700 font-semibold hover:underline">
                    {p.title}
                  </Link>
                  <span className="text-sm text-gray-500">
                    {p.active_initiative_count}/{p.initiative_count} active
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <CreateProgramModal
          isOpen={showCreate}
          onClose={() => setShowCreate(false)}
          onSuccess={load}
        />
      </div>
    </Layout>
  );
};
