import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { getProgramManifestRaw, saveProgramManifest } from '../services/programService';

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

export const ProgramManifestEditorPage: React.FC = () => {
  const { slug = '' } = useParams();
  const [yaml, setYaml] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin()) return;
    getProgramManifestRaw(slug)
      .then((r) => setYaml(r.yaml_content))
      .catch((e) => setError(e instanceof Error ? e.message : 'Load failed'));
  }, [slug]);

  if (!isAdmin()) {
    return <Layout><div className="p-8">Admin access required.</div></Layout>;
  }

  const handleSave = async () => {
    try {
      const res = await saveProgramManifest(slug, yaml);
      setMsg(res.message);
      setError(null);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail || (e instanceof Error ? e.message : 'Save failed'));
    }
  };

  return (
    <Layout>
      <div className="p-8 max-w-5xl mx-auto space-y-4">
        <Link to={`/programs/${slug}`} className="text-sm text-gray-500 hover:underline">← Program hub</Link>
        <h1 className="text-xl font-bold">Edit manifest: {slug}</h1>
        <p className="text-sm text-gray-600">YAML is validated on save. Redeploy not required — file updates in place.</p>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        {msg && <p className="text-green-700 text-sm">{msg}</p>}
        <Card>
          <textarea
            className="w-full min-h-[32rem] font-mono text-xs p-4 border-0 focus:ring-0"
            value={yaml}
            onChange={(e) => setYaml(e.target.value)}
            spellCheck={false}
          />
        </Card>
        <Button onClick={handleSave}>Save manifest</Button>
      </div>
    </Layout>
  );
};
