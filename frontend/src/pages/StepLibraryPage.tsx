import React, { useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { RenameModuleModal } from '../components/RenameModuleModal';
import stepLibraryService from '../services/stepLibraryService';
import type { StepLibraryModule, StepLibraryModuleCreate, StepLibraryModuleUpdate } from '../types/stepLibrary.types';

type FormMode = 'create' | 'edit';

interface ModuleFormState {
  name: string;
  display_name: string;
  description: string;
  steps: string;          // newline-separated textarea value
  parameters: string;     // comma-separated
  tags: string;           // comma-separated
}

const EMPTY_FORM: ModuleFormState = {
  name: '',
  display_name: '',
  description: '',
  steps: '',
  parameters: '',
  tags: '',
};

function moduleToForm(m: StepLibraryModule): ModuleFormState {
  return {
    name: m.name,
    display_name: m.display_name,
    description: m.description ?? '',
    steps: (m.steps ?? []).join('\n'),
    parameters: (m.parameters ?? []).join(', '),
    tags: (m.tags ?? []).join(', '),
  };
}

function formToCreate(f: ModuleFormState): StepLibraryModuleCreate {
  return {
    name: f.name.trim(),
    display_name: f.display_name.trim(),
    description: f.description.trim() || undefined,
    steps: f.steps.split('\n').map(s => s.trim()).filter(Boolean),
    parameters: f.parameters ? f.parameters.split(',').map(p => p.trim()).filter(Boolean) : undefined,
    tags: f.tags ? f.tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
  };
}

export function StepLibraryPage() {
  const [modules, setModules] = useState<StepLibraryModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<FormMode>('create');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<ModuleFormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Rename modal state
  const [renameTarget, setRenameTarget] = useState<StepLibraryModule | null>(null);
  const [renameToast, setRenameToast] = useState<string | null>(null);

  useEffect(() => {
    loadModules();
  }, []);

  async function loadModules() {
    setLoading(true);
    setError(null);
    try {
      const data = await stepLibraryService.list();
      setModules(data);
    } catch {
      setError('Failed to load step library modules.');
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setForm(EMPTY_FORM);
    setFormMode('create');
    setEditingId(null);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(module: StepLibraryModule) {
    setForm(moduleToForm(module));
    setFormMode('edit');
    setEditingId(module.id);
    setFormError(null);
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setFormError(null);
  }

  async function handleSave() {
    setFormError(null);
    const payload = formToCreate(form);
    if (!payload.name) { setFormError('Module name is required.'); return; }
    if (!payload.display_name) { setFormError('Display name is required.'); return; }
    if (!payload.steps.length) { setFormError('At least one step is required.'); return; }

    setSaving(true);
    try {
      if (formMode === 'create') {
        const created = await stepLibraryService.create(payload);
        setModules(prev => [...prev, created]);
      } else if (editingId !== null) {
        const update: StepLibraryModuleUpdate = { ...payload };
        const updated = await stepLibraryService.update(editingId, update);
        setModules(prev => prev.map(m => m.id === editingId ? updated : m));
      }
      setFormOpen(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Save failed.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  }

  function handleRenameSuccess(updated: StepLibraryModule, updatedCount: number) {
    setModules(prev => prev.map(m => m.id === updated.id ? updated : m));
    setRenameTarget(null);
    const msg =
      updatedCount === 0
        ? `Module renamed to "${updated.name}".`
        : `Module renamed to "${updated.name}". ${updatedCount} test case${updatedCount !== 1 ? 's' : ''} updated.`;
    setRenameToast(msg);
    setTimeout(() => setRenameToast(null), 5000);
  }

  async function handleDelete(id: number) {
    if (!window.confirm('Delete this module? Tests referencing it via @module: will produce an error step.')) return;
    try {
      await stepLibraryService.delete(id);
      setModules(prev => prev.filter(m => m.id !== id));
    } catch {
      alert('Failed to delete module.');
    }
  }

  const filtered = modules.filter(m =>
    m.display_name.toLowerCase().includes(search.toLowerCase()) ||
    m.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Step Library</h1>
          <button
            onClick={openCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            + New Module
          </button>
        </div>

        <div className="mb-4">
          <input
            type="text"
            placeholder="Search modules..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {loading && <p className="text-gray-500">Loading modules...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {!loading && !error && filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No step library modules found.</p>
            <p className="text-sm mt-1">
              Create reusable step sequences and reference them in test cases using{' '}
              <code className="bg-gray-100 px-1 rounded">@module:name()</code>
            </p>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="space-y-3">
            {filtered.map(module => (
              <div
                key={module.id}
                className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between shadow-sm"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{module.display_name}</span>
                    <code className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                      {module.name}
                    </code>
                    {(module.tags ?? []).map(tag => (
                      <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                  {module.description && (
                    <p className="text-sm text-gray-500 mt-1">{module.description}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {module.steps.length} step{module.steps.length !== 1 ? 's' : ''}
                    {module.usage_count != null && ` · Used by ${module.usage_count} test${module.usage_count !== 1 ? 's' : ''}`}
                  </p>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => openEdit(module)}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                    aria-label="Edit"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => setRenameTarget(module)}
                    className="px-3 py-1.5 text-sm border border-purple-300 text-purple-600 rounded hover:bg-purple-50"
                    aria-label="Rename"
                  >
                    Rename
                  </button>
                  <button
                    onClick={() => handleDelete(module.id)}
                    className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
                    aria-label="Delete"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Success toast for rename */}
        {renameToast && (
          <div className="fixed bottom-6 right-6 z-50 bg-green-600 text-white px-5 py-3 rounded-lg shadow-lg text-sm">
            {renameToast}
          </div>
        )}

        {/* Rename slug modal */}
        {renameTarget && (
          <RenameModuleModal
            module={renameTarget}
            onClose={() => setRenameTarget(null)}
            onRenamed={handleRenameSuccess}
          />
        )}

        {/* Module form modal */}
        {formOpen && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4">
                  {formMode === 'create' ? 'New Module' : 'Edit Module'}
                </h2>

                {formError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
                    {formError}
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label htmlFor="module-name" className="block text-sm font-medium text-gray-700 mb-1">
                      Module Name (slug)
                    </label>
                    <input
                      id="module-name"
                      type="text"
                      value={form.name}
                      onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                      placeholder="e.g. login_three_hk"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    />
                  </div>

                  <div>
                    <label htmlFor="display-name" className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name
                    </label>
                    <input
                      id="display-name"
                      type="text"
                      value={form.display_name}
                      onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))}
                      placeholder="e.g. Three HK Login Flow"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="steps" className="block text-sm font-medium text-gray-700 mb-1">
                      Steps <span className="text-gray-400 font-normal">(one per line)</span>
                    </label>
                    <textarea
                      id="steps"
                      value={form.steps}
                      onChange={e => setForm(f => ({ ...f, steps: e.target.value }))}
                      rows={6}
                      placeholder={"Navigate to https://...\nClick Login button\nEnter username: {username}"}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    />
                  </div>

                  <div>
                    <label htmlFor="parameters" className="block text-sm font-medium text-gray-700 mb-1">
                      Parameters <span className="text-gray-400 font-normal">(comma-separated)</span>
                    </label>
                    <input
                      id="parameters"
                      type="text"
                      value={form.parameters}
                      onChange={e => setForm(f => ({ ...f, parameters: e.target.value }))}
                      placeholder="username, password"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                      Description <span className="text-gray-400 font-normal">(optional)</span>
                    </label>
                    <input
                      id="description"
                      type="text"
                      value={form.description}
                      onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                      placeholder="Describe what this module does..."
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
                      Tags <span className="text-gray-400 font-normal">(comma-separated)</span>
                    </label>
                    <input
                      id="tags"
                      type="text"
                      value={form.tags}
                      onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                      placeholder="e2e, checkout"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={closeForm}
                    className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-60"
                  >
                    {saving ? 'Saving...' : 'Save Module'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

export default StepLibraryPage;
