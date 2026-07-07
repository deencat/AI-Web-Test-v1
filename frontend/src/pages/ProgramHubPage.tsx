import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import {
  getOrchestrationSuites,
  getProgram,
  getReqIQOnboarding,
  ProgramDetail,
  seedProgramJourneys,
} from '../services/programService';

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

export const ProgramHubPage: React.FC = () => {
  const { slug = '' } = useParams();
  const [detail, setDetail] = useState<ProgramDetail | null>(null);
  const [suites, setSuites] = useState<unknown[]>([]);
  const [onboarding, setOnboarding] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seedMsg, setSeedMsg] = useState<string | null>(null);
  const admin = isAdmin();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [prog, orch, req] = await Promise.all([
        getProgram(slug),
        getOrchestrationSuites(slug).catch(() => ({ suites: [] })),
        getReqIQOnboarding(slug).catch(() => ({ steps: [] })),
      ]);
      setDetail(prog);
      setSuites(orch.suites || []);
      setOnboarding(req.steps || []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSeed = async () => {
    const res = await seedProgramJourneys(slug);
    setSeedMsg(`Seeded ${res.journeys_upserted}, retired ${res.journeys_retired} journeys, ${res.tests_retired} tests`);
  };

  if (loading) return <Layout><div className="p-8">Loading…</div></Layout>;
  if (!detail || error) return <Layout><div className="p-8 text-red-600">{error}</div></Layout>;

  return (
    <Layout>
      <div className="p-8 max-w-6xl mx-auto space-y-6">
        <div className="flex justify-between">
          <div>
            <Link to="/programs" className="text-sm text-gray-500 hover:underline">Programs</Link>
            <h1 className="text-2xl font-bold mt-1">{String(detail.program.title)}</h1>
            <p className="text-sm text-gray-600">{String(detail.program.test_scope || '')}</p>
          </div>
          {admin && (
            <div className="flex gap-2">
              <Link to={`/programs/${slug}/edit`}><Button>Edit YAML</Button></Link>
              <Button onClick={handleSeed}>Seed journeys</Button>
            </div>
          )}
        </div>
        {seedMsg && <p className="text-green-700 text-sm">{seedMsg}</p>}

        <Card>
          <h2 className="font-semibold p-4 border-b">Platform</h2>
          <div className="p-4 grid grid-cols-2 gap-2 text-sm">
            {detail.platform_components.map((c) => (
              <div key={c.id} className="border rounded p-2">{c.title} <span className="text-gray-400 font-mono text-xs">{c.id}</span></div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold p-4 border-b">Reference (not tested)</h2>
          <ul className="p-4 text-sm space-y-2">
            {detail.reference_layers.map((r) => (
              <li key={r.id} className="bg-gray-50 border rounded p-2">{r.title}</li>
            ))}
          </ul>
        </Card>

        <Card>
          <h2 className="font-semibold p-4 border-b">Initiatives</h2>
          <table className="w-full text-sm">
            <thead><tr className="border-b text-gray-600"><th className="p-2 text-left">Title</th><th className="p-2">Kind</th><th className="p-2">Dates</th><th className="p-2">Rel</th><th className="p-2">Audience</th></tr></thead>
            <tbody>
              {detail.initiatives.map((i) => (
                <tr key={i.id} className="border-b">
                  <td className="p-2"><Link className="text-blue-700 hover:underline" to={`/programs/${slug}/initiatives/${i.id}`}>{i.title}</Link></td>
                  <td className="p-2">{i.kind}</td>
                  <td className="p-2 text-xs">{i.effective_from} → {i.resolved_effective_to || 'open'}</td>
                  <td className="p-2 text-xs">{i.relationship || '—'}</td>
                  <td className="p-2 text-xs">{i.audience || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {suites.length > 0 && (
          <Card>
            <h2 className="font-semibold p-4 border-b">Orchestration suites</h2>
            <ul className="p-4 text-sm">{suites.map((s, idx) => {
              const suite = s as { id?: string; title?: string };
              return <li key={suite.id || idx}>{suite.title || suite.id}</li>;
            })}</ul>
          </Card>
        )}

        {onboarding.length > 0 && (
          <Card>
            <h2 className="font-semibold p-4 border-b">ReqIQ onboarding</h2>
            <ol className="list-decimal p-4 pl-8 text-sm">{onboarding.map((s) => <li key={s}>{s}</li>)}</ol>
          </Card>
        )}
      </div>
    </Layout>
  );
};
