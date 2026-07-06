import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { getInitiative, InitiativeDetailResponse } from '../services/programService';

export const InitiativeDetailPage: React.FC = () => {
  const { slug = '', initiativeId = '' } = useParams();
  const [data, setData] = useState<InitiativeDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInitiative(slug, initiativeId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed'));
  }, [slug, initiativeId]);

  if (error) return <Layout><div className="p-8 text-red-600">{error}</div></Layout>;
  if (!data) return <Layout><div className="p-8">Loading…</div></Layout>;

  const init = data.initiative;
  return (
    <Layout>
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <Link to={`/programs/${slug}`} className="text-sm text-gray-500 hover:underline">← Back to program</Link>
        <h1 className="text-2xl font-bold">{init.title}</h1>
        <p className="text-sm text-gray-600">{init.kind} · {init.id}</p>

        <Card>
          <div className="p-4 text-sm space-y-2">
            <div><strong>Dates:</strong> {init.effective_from} → {init.resolved_effective_to || 'open'}</div>
            <div><strong>Relationship:</strong> {init.relationship || '—'} {init.relates_to?.length ? `(${init.relates_to.join(', ')})` : ''}</div>
            <div><strong>Audience:</strong> {init.audience || '—'}</div>
            <div><strong>Platform:</strong> {init.platform_components.join(', ')}</div>
            <div><strong>Capabilities:</strong> {init.capability_keys.join(', ')}</div>
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold p-4 border-b">Linked journeys</h2>
          {data.journeys.length === 0 ? (
            <p className="p-4 text-gray-500 text-sm">No journeys seeded yet. Use Seed journeys on program hub.</p>
          ) : (
            <table className="w-full text-sm">
              <thead><tr className="border-b"><th className="p-2 text-left">Slug</th><th className="p-2">Status</th></tr></thead>
              <tbody>
                {data.journeys.map((j) => (
                  <tr key={j.id} className="border-b">
                    <td className="p-2 font-mono text-xs">{j.slug}</td>
                    <td className="p-2">{j.retired ? <span className="text-orange-700">Retired</span> : 'Active'}</td>
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
