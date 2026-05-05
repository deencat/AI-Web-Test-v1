import React, { useEffect, useState } from 'react';
import stepLibraryService from '../services/stepLibraryService';
import type { StepLibraryModule } from '../types/stepLibrary.types';

interface InsertModulePickerProps {
  onInsert: (moduleRef: string) => void;
  onClose: () => void;
}

export function InsertModulePicker({ onInsert, onClose }: InsertModulePickerProps) {
  const [modules, setModules] = useState<StepLibraryModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<StepLibraryModule | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});

  useEffect(() => {
    stepLibraryService.list().then(setModules).finally(() => setLoading(false));
  }, []);

  function handleSelect(module: StepLibraryModule) {
    setSelected(module);
    // Reset params when switching module
    const initial: Record<string, string> = {};
    for (const p of (module.parameters ?? [])) {
      initial[p] = '';
    }
    setParamValues(initial);
  }

  function buildModuleRef(): string {
    if (!selected) return '';
    const params = selected.parameters ?? [];
    if (params.length === 0) {
      return `@module:${selected.name}()`;
    }
    const paramStr = params.map(p => `${p}=${paramValues[p] ?? ''}`).join(',');
    return `@module:${selected.name}(${paramStr})`;
  }

  function handleInsert() {
    if (!selected) return;
    onInsert(buildModuleRef());
  }

  const filtered = modules.filter(m =>
    m.display_name.toLowerCase().includes(search.toLowerCase()) ||
    m.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="border border-gray-200 rounded-xl shadow-lg bg-white w-full max-w-md">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-2">Insert Module</h3>
        <input
          type="text"
          placeholder="Search modules..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 text-sm"
        />
      </div>

      <div className="max-h-48 overflow-y-auto">
        {loading && <p className="p-4 text-gray-400 text-sm">Loading...</p>}
        {!loading && filtered.length === 0 && (
          <p className="p-4 text-gray-400 text-sm">No modules found.</p>
        )}
        {!loading && filtered.map(module => (
          <button
            key={module.id}
            onClick={() => handleSelect(module)}
            className={`w-full text-left px-4 py-3 hover:bg-blue-50 border-b border-gray-100 last:border-0 transition-colors ${
              selected?.id === module.id ? 'bg-blue-50' : ''
            }`}
          >
            <div className="font-medium text-sm text-gray-900">{module.display_name}</div>
            <div className="text-xs text-gray-500 font-mono">{module.name}</div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="p-4 border-t border-gray-100 bg-gray-50">
          <p className="text-xs font-medium text-gray-600 mb-2">
            Preview ({selected.steps.length} step{selected.steps.length !== 1 ? 's' : ''})
          </p>
          <ol className="text-xs text-gray-700 space-y-0.5 mb-3 list-decimal list-inside">
            {selected.steps.slice(0, 5).map((step, i) => (
              <li key={i} className="truncate">{step}</li>
            ))}
            {selected.steps.length > 5 && (
              <li className="text-gray-400">... {selected.steps.length - 5} more</li>
            )}
          </ol>

          {(selected.parameters ?? []).length > 0 && (
            <div className="space-y-2 mb-3">
              {(selected.parameters ?? []).map(param => (
                <div key={param}>
                  <label
                    htmlFor={`param-${param}`}
                    className="block text-xs font-medium text-gray-700 mb-0.5 capitalize"
                  >
                    {param}
                  </label>
                  <input
                    id={`param-${param}`}
                    type="text"
                    value={paramValues[param] ?? ''}
                    onChange={e => setParamValues(v => ({ ...v, [param]: e.target.value }))}
                    placeholder={`Enter ${param}...`}
                    className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              ))}
            </div>
          )}

          <code className="block text-xs bg-gray-100 rounded px-2 py-1 text-gray-700 break-all mb-3">
            {buildModuleRef()}
          </code>
        </div>
      )}

      <div className="flex justify-end gap-2 p-4 border-t border-gray-100">
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleInsert}
          disabled={!selected}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Insert ↙
        </button>
      </div>
    </div>
  );
}
