import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './common/Button';
import {
  createProgram,
  listPlatformProfiles,
  PlatformProfileSummary,
} from '../services/programService';

interface CreateProgramModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export const CreateProgramModal: React.FC<CreateProgramModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const navigate = useNavigate();
  const [slug, setSlug] = useState('');
  const [title, setTitle] = useState('');
  const [kind, setKind] = useState<'pilot' | 'production' | 'example'>('pilot');
  const [testScope, setTestScope] = useState('DT_ONLY');
  const [platformProfile, setPlatformProfile] = useState('dt-telecom-default');
  const [initiativeTitle, setInitiativeTitle] = useState('');
  const [profiles, setProfiles] = useState<PlatformProfileSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    listPlatformProfiles()
      .then((res) => setProfiles(res.items))
      .catch(() => setProfiles([{ name: 'dt-telecom-default', title: 'DT telecom default' }]));
  }, [isOpen]);

  const reset = () => {
    setSlug('');
    setTitle('');
    setKind('pilot');
    setTestScope('DT_ONLY');
    setPlatformProfile('dt-telecom-default');
    setInitiativeTitle('');
    setError('');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalized = slug.trim().toLowerCase();
    if (!SLUG_PATTERN.test(normalized)) {
      setError('Slug must be lowercase letters, numbers, and hyphens only');
      return;
    }
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await createProgram({
        slug: normalized,
        title: title.trim(),
        kind,
        test_scope: testScope.trim() || 'DT_ONLY',
        platform_profile: platformProfile || null,
        initiative_title: initiativeTitle.trim() || undefined,
      });
      onSuccess();
      handleClose();
      navigate(`/programs/${res.slug}/edit`);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(ax.response?.data?.detail || (err instanceof Error ? err.message : 'Create failed'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold">New program</h2>
          <button type="button" onClick={handleClose} className="text-gray-500 hover:text-gray-800">×</button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div>
            <label className="block text-sm font-medium mb-1">Slug</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm font-mono"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="my-product-line"
              required
            />
            <p className="text-xs text-gray-500 mt-1">Manifest file: backend/config/programs/&lt;slug&gt;.yaml</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Title</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Display name"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Kind</label>
              <select
                className="w-full border rounded px-3 py-2 text-sm"
                value={kind}
                onChange={(e) => setKind(e.target.value as typeof kind)}
              >
                <option value="pilot">pilot</option>
                <option value="production">production</option>
                <option value="example">example</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Test scope</label>
              <input
                className="w-full border rounded px-3 py-2 text-sm"
                value={testScope}
                onChange={(e) => setTestScope(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Platform profile</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={platformProfile}
              onChange={(e) => setPlatformProfile(e.target.value)}
            >
              <option value="">None (inline WebApp only)</option>
              {profiles.map((p) => (
                <option key={p.name} value={p.name}>{p.title || p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">First initiative title (optional)</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm"
              value={initiativeTitle}
              onChange={(e) => setInitiativeTitle(e.target.value)}
              placeholder="Defaults to “{title} — base”"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" onClick={handleClose} disabled={loading}>Cancel</Button>
            <Button type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create & edit YAML'}</Button>
          </div>
        </form>
      </div>
    </div>
  );
};
